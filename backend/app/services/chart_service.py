import json
import logging

import matplotlib
matplotlib.use('Agg')

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import squarify
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from app.core.design_tokens import PAPER, INDIGO, MINT, AMBER, RED

logger = logging.getLogger(__name__)

FONT_DIR = Path(__file__).resolve().parent.parent / 'static' / 'fonts'
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexSans-Regular.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexSans-Italic.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexMono-Regular.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexMono-Bold.ttf'))

SECONDARY_PALETTE = ['#6366F1', '#0E9F6E', '#F59E0B', '#EF4444']  # INDIGO, MINT, AMBER, RED


def _lighten(hex_color: str, factor: float) -> str:
    """Blend hex_color toward white by factor (0.0–1.0)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * factor * 0.6)
    g = int(g + (255 - g) * factor * 0.6)
    b = int(b + (255 - b) * factor * 0.6)
    return f"#{r:02x}{g:02x}{b:02x}"


def _fmt_axis(val: float) -> str:
    """Format axis tick values as K/M without scientific notation."""
    if abs(val) >= 1_000_000:
        return f'{val/1_000_000:.1f}M'
    if abs(val) >= 1_000:
        return f'{val/1_000:.0f}K'
    return f'{val:.0f}'


CHART_DIR = Path('/tmp/naxely')


def _apply_chart_style(ax) -> None:
    """Apply Naxely visual standards to any chart axes."""
    # Grid: horizontal only, dashed, light
    ax.yaxis.grid(True, color='#E5E7EB', linewidth=0.6, linestyle='--', zorder=0)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    # Spines: hide top/right, style left/bottom
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#D1D5DB')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_color('#D1D5DB')
    ax.spines['bottom'].set_linewidth(0.8)

    # Tick labels
    ax.tick_params(colors='#6B7280', labelsize=9)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily('IBM Plex Mono')


def select_chart_type(col1: str, col2: str, df: pd.DataFrame) -> str:
    col1_is_date = pd.api.types.is_datetime64_any_dtype(df[col1])
    col1_is_cat = (
        df[col1].dtype == object
        or (df[col1].nunique() <= 10 and not pd.api.types.is_numeric_dtype(df[col1]))
    )
    col2_is_cat = (
        df[col2].dtype == object
        or (df[col2].nunique() <= 10 and not pd.api.types.is_numeric_dtype(df[col2]))
    )
    col2_is_numeric = pd.api.types.is_numeric_dtype(df[col2])

    if col1_is_date and col2_is_numeric:
        return 'line'
    if col1_is_cat and col2_is_cat:
        return 'heatmap'
    if col1_is_cat and col2_is_numeric:
        n_unique = df[col1].nunique()
        return 'donut' if n_unique <= 2 else 'bar'
    if col1 == col2 and pd.api.types.is_numeric_dtype(df[col1]):
        return 'histogram'
    if pd.api.types.is_numeric_dtype(df[col1]) and col2_is_numeric:
        return 'scatter'
    return 'histogram'


def _select_chart_pairs(
    df: pd.DataFrame,
    date_column: str | None,
    metric_columns: list[str],
    dimension_columns: list[str],
    max_charts: int = 3,
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    primary_metric = metric_columns[0] if metric_columns else None

    # Priority 1: one line chart (date + primary metric)
    if date_column and date_column in df.columns and primary_metric:
        pairs.append((date_column, primary_metric))

    # Priority 2: bar charts for each dimension against primary metric
    if primary_metric:
        for dim in dimension_columns:
            if len(pairs) >= max_charts:
                break
            pairs.append((dim, primary_metric))

    # Priority 3: remaining slots fill with additional line charts
    for metric in metric_columns[1:]:
        if len(pairs) >= max_charts:
            break
        if date_column and (date_column, metric) not in pairs:
            pairs.append((date_column, metric))

    return pairs[:max_charts]


def select_charts_with_ai(
    df: pd.DataFrame,
    config: dict,
    provider: str,
    api_key: str,
    max_charts: int = 3,
) -> list[dict] | None:
    """
    Asks the AI to pick chart types and column pairings.
    Returns list of {x, y, type, title} dicts, or None on failure.
    Falls back to None so caller can use rule-based selection.
    """
    from app.services.ai_service import _call_ai

    SUPPORTED = [
        "line", "area", "bar", "lollipop", "pie", "donut",
        "scatter", "histogram", "box", "heatmap",
        "grouped_bar", "stacked_bar", "combo",
        "waterfall", "funnel", "bullet", "treemap",
    ]

    col_meta = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            dtype = "date"
        elif pd.api.types.is_numeric_dtype(df[col]):
            dtype = f"numeric (min={df[col].min():.0f}, max={df[col].max():.0f}, mean={df[col].mean():.0f})"
        else:
            nunique = df[col].nunique()
            sample_vals = df[col].unique()[:4].tolist()
            dtype = f"categorical ({nunique} unique values, e.g. {sample_vals})"
        col_meta.append(f"- {col}: {dtype}")

    sample_csv = df.head(5).to_csv(index=False)

    system = (
        "You are a data visualization expert for a B2B reporting platform. "
        "Return ONLY valid JSON. No explanation, no markdown."
    )

    prompt = (
        f"Choose up to {max_charts} charts that best reveal business insights "
        f"from this dataset. Prioritize charts that show trends, comparisons, "
        f"distributions, or correlations a business executive would care about.\n\n"
        f"Columns:\n" + "\n".join(col_meta) + "\n\n"
        f"Sample data:\n{sample_csv}\n\n"
        f"Available chart types:\n"
        f"- line: date + numeric (trend over time)\n"
        f"- area: date + numeric (volume/cumulative trend)\n"
        f"- bar: categorical + numeric (horizontal ranked bars)\n"
        f"- lollipop: categorical + numeric (cleaner ranked list)\n"
        f"- pie: categorical + numeric, ≤6 unique values (share of total)\n"
        f"- donut: same as pie with hollow center\n"
        f"- scatter: two numerics (correlation analysis)\n"
        f"- histogram: single numeric (value distribution)\n"
        f"- box: categorical + numeric (spread and outliers per group)\n"
        f"- heatmap: two categoricals (frequency or value matrix)\n"
        f"- grouped_bar: categorical + two numerics (side-by-side comparison)\n"
        f"- stacked_bar: categorical showing part-to-whole\n"
        f"- combo: date + two numerics (bar + line on same axis)\n"
        f"- waterfall: sequential numeric changes (additions/subtractions)\n"
        f"- funnel: stage-based numeric drop-off\n"
        f"- bullet: single KPI vs target (needs Value and Target columns)\n"
        f"- treemap: hierarchical part-to-whole by category\n\n"
        f"Return ONLY a JSON array:\n"
        f'[{{"x": "col_name", "y": "col_name", "type": "chart_type", "title": "Chart Title"}}]\n\n'
        f"Rules:\n"
        f"- x and y must be exact column names from the dataset above\n"
        f"- type must be one of the supported types listed above\n"
        f"- Maximum {max_charts} charts\n"
        f"- bullet requires columns named 'Value' and 'Target' — only suggest if they exist\n"
        f"- waterfall and funnel only make sense with sequential/stage data\n"
        f"- Return ONLY the JSON array, nothing else"
    )

    try:
        raw = _call_ai(provider, prompt, system, api_key, timeout=20)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(
                l for l in lines
                if not l.strip().startswith("```")
            ).strip()

        specs = json.loads(cleaned)
        if not isinstance(specs, list):
            return None

        df_cols = set(df.columns)
        valid = []
        for spec in specs:
            if not isinstance(spec, dict):
                continue
            if spec.get("x") not in df_cols:
                logger.warning(f"AI chart spec: unknown x column '{spec.get('x')}'")
                continue
            if spec.get("y") not in df_cols:
                logger.warning(f"AI chart spec: unknown y column '{spec.get('y')}'")
                continue
            if spec.get("type") not in SUPPORTED:
                logger.warning(f"AI chart spec: unsupported type '{spec.get('type')}'")
                continue
            valid.append(spec)

        if valid:
            logger.info(f"AI selected {len(valid)} chart specs: {[s['type'] for s in valid]}")
            return valid[:max_charts]

        logger.warning("AI chart selection returned 0 valid specs — falling back to rules")
        return None

    except Exception as e:
        logger.warning(f"AI chart selection failed: {e} — falling back to rules")
        return None


def _generate_single_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    chart_type: str,
    report_id: str,
    brand_color: str,
) -> str | None:
    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    try:
        if chart_type == 'line':
            df_sorted = df.sort_values(x_col).copy()
            df_sorted[x_col] = pd.to_datetime(df_sorted[x_col])

            agg_func = 'mean' if any(x in y_col.lower()
                for x in ['%', 'percent', 'rate', 'ratio', 'score', 'pct']) else 'sum'

            unique_dates = df_sorted[x_col].nunique()
            if unique_dates > 60:
                df_plot = (
                    df_sorted.set_index(x_col)[y_col]
                    .resample('W')
                    .agg(agg_func)
                    .reset_index()
                )
            else:
                df_plot = df_sorted.groupby(x_col)[y_col].agg(agg_func).reset_index()

            x = pd.to_datetime(df_plot[x_col])
            y = df_plot[y_col]

            ax.plot(x, y, color=brand_color, linewidth=2.0,
                    marker='o', markersize=4,
                    markerfacecolor='white', markeredgecolor=brand_color,
                    markeredgewidth=1.5)
            ax.fill_between(x, y, alpha=0.08, color=brand_color)
            ax.set_xlabel(x_col, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_title(f'{y_col} Over Time', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10,
                        fontfamily='IBM Plex Sans')

            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda val, _: _fmt_axis(val))
            )

        elif chart_type == 'bar':
            grouped = df.groupby(x_col)[y_col].mean().sort_values(ascending=True)
            ax.barh(grouped.index, grouped.values,
                    color=brand_color, alpha=0.85, height=0.55)
            for i, (val, _) in enumerate(zip(grouped.values, grouped.index)):
                ax.text(val * 1.01, i, f'{val:,.0f}',
                       va='center', fontsize=9, color='#4B5563',
                       fontfamily='IBM Plex Mono')
            ax.set_xlabel(f'Mean {y_col}', fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_title(f'{y_col} by {x_col}', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10,
                        fontfamily='IBM Plex Sans')

        elif chart_type == 'scatter':
            ax.scatter(df[x_col], df[y_col],
                      color=brand_color, alpha=0.7,
                      edgecolors='white', linewidths=0.5, s=60)
            ax.set_xlabel(x_col, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_ylabel(y_col, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_title(f'{x_col} vs {y_col}', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10,
                        fontfamily='IBM Plex Sans')

        elif chart_type == 'area':
            df_sorted = df.sort_values(x_col)
            x = pd.to_datetime(df_sorted[x_col])
            y = df_sorted[y_col]
            ax.fill_between(x, y, color=brand_color, alpha=0.35)
            ax.plot(x, y, color=brand_color, linewidth=1.8)
            ax.set_xlabel(x_col, fontsize=10, color='#4B5563', fontfamily='IBM Plex Sans')
            ax.set_title(f'{y_col} Over Time (Area)', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type in ('pie', 'donut'):
            agg = df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
            n = len(agg)
            colors = [_lighten(brand_color, i / max(n - 1, 1) * 0.65) for i in range(n)]
            wedge_props = {'linewidth': 1.2, 'edgecolor': PAPER}
            ax.pie(
                agg.values,
                labels=agg.index.astype(str),
                colors=colors,
                autopct='%1.1f%%',
                wedgeprops=wedge_props,
                startangle=90,
                textprops={'fontsize': 9, 'fontfamily': 'IBM Plex Sans'},
            )
            if chart_type == 'donut':
                centre = plt.Circle((0, 0), 0.60, fc=PAPER)
                ax.add_artist(centre)
            ax.axis('equal')
            ax.set_title(f'{y_col} by {x_col}', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'lollipop':
            agg = df.groupby(x_col)[y_col].mean().sort_values(ascending=True)
            y_pos = range(len(agg))
            ax.hlines(list(agg.index.astype(str)), 0, agg.values,
                     color='#D1D5DB', linewidth=1.5)
            ax.plot(agg.values, list(agg.index.astype(str)),
                   'o', color=brand_color, markersize=10, zorder=5)
            for val, label in zip(agg.values, agg.index):
                ax.text(val * 1.01, str(label), f'{val:,.0f}',
                       va='center', fontsize=9, color='#4B5563', fontfamily='IBM Plex Mono')
            ax.set_xlabel(f'Mean {y_col}', fontsize=10, color='#4B5563', fontfamily='IBM Plex Sans')
            ax.set_title(f'{y_col} by {x_col}', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'box':
            groups = [grp[y_col].dropna().values for _, grp in df.groupby(x_col)]
            labels = [str(k) for k in df.groupby(x_col).groups.keys()]
            bp = ax.boxplot(
                groups, labels=labels, patch_artist=True,
                medianprops={'color': '#14131F', 'linewidth': 2},
                whiskerprops={'color': '#9CA3AF'},
                capprops={'color': '#9CA3AF'},
                flierprops={'marker': 'o', 'color': RED, 'markersize': 4},
            )
            for patch in bp['boxes']:
                patch.set_facecolor(brand_color)
                patch.set_alpha(0.55)
            ax.set_xlabel(x_col, fontsize=10, color='#4B5563', fontfamily='IBM Plex Sans')
            ax.set_ylabel(y_col, fontsize=10, color='#4B5563', fontfamily='IBM Plex Sans')
            plt.xticks(rotation=45, ha='right', fontsize=7, fontfamily='IBM Plex Sans')
            plt.tight_layout()
            ax.set_title(f'{y_col} Distribution by {x_col}', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'heatmap':
            pivot = pd.crosstab(df[x_col], df[y_col])
            im = ax.imshow(pivot.values, aspect='auto', cmap='YlOrRd')
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels(pivot.columns.astype(str), rotation=40,
                               ha='right', fontsize=8, fontfamily='IBM Plex Sans')
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels(pivot.index.astype(str), fontsize=8, fontfamily='IBM Plex Sans')
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    ax.text(j, i, str(pivot.values[i, j]),
                           ha='center', va='center', fontsize=8, color='#14131F')
            plt.colorbar(im, ax=ax, shrink=0.8)
            ax.set_title(f'{x_col} × {y_col} Frequency', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'grouped_bar':
            numerics = [c for c in df.columns
                       if pd.api.types.is_numeric_dtype(df[c])][:2]
            if len(numerics) < 2:
                numerics = numerics * 2
            agg = df.groupby(x_col)[numerics].mean()
            x_pos = np.arange(len(agg))
            w = 0.38
            ax.bar(x_pos - w/2, agg[numerics[0]], w,
                  label=numerics[0], color=brand_color, alpha=0.85)
            ax.bar(x_pos + w/2, agg[numerics[1]], w,
                  label=numerics[1], color=_lighten(brand_color, 0.45), alpha=0.85)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(agg.index.astype(str), rotation=30,
                              fontsize=9, fontfamily='IBM Plex Sans')
            ax.legend(fontsize=8, frameon=False)
            ax.set_title(f'{" & ".join(numerics)} by {x_col}', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'stacked_bar':
            numerics = [c for c in df.columns
                       if pd.api.types.is_numeric_dtype(df[c])][:3]
            agg = df.groupby(x_col)[numerics].mean()
            bottom = np.zeros(len(agg))
            for i, col in enumerate(numerics):
                ax.bar(agg.index.astype(str), agg[col], bottom=bottom,
                      label=col, color=_lighten(brand_color, i * 0.3), alpha=0.85)
                bottom += agg[col].values
            ax.legend(fontsize=8, frameon=False)
            plt.xticks(rotation=30, fontsize=9, fontfamily='IBM Plex Sans')
            ax.set_title(f'Stacked {" + ".join(numerics)} by {x_col}', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'combo':
            df_sorted = df.sort_values(x_col)
            numerics = [c for c in df.columns
                       if pd.api.types.is_numeric_dtype(df[c])][:2]
            if len(numerics) < 2:
                numerics = [y_col, y_col]
            ax2 = ax.twinx()
            x_vals = pd.to_datetime(df_sorted[x_col]) if pd.api.types.is_datetime64_any_dtype(df_sorted[x_col]) else df_sorted[x_col]
            ax.bar(x_vals, df_sorted[numerics[0]],
                  color=brand_color, alpha=0.35, label=numerics[0])
            ax2.plot(x_vals, df_sorted[numerics[1]],
                    color='#14131F', linewidth=1.8, marker='o',
                    markersize=3, label=numerics[1])
            ax.set_ylabel(numerics[0], fontsize=9, color='#4B5563', fontfamily='IBM Plex Sans')
            ax2.set_ylabel(numerics[1], fontsize=9, color='#4B5563', fontfamily='IBM Plex Sans')
            ax2.spines['top'].set_visible(False)
            ax2.tick_params(colors='#6B7280', labelsize=9)
            ax.set_title(f'{numerics[0]} & {numerics[1]} Over Time', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'waterfall':
            values = df[y_col].values.astype(float)
            labels = df[x_col].astype(str).values
            running = np.concatenate([[0.0], np.cumsum(values[:-1])])
            bar_colors = [brand_color if v >= 0 else RED for v in values]
            ax.bar(labels, values, bottom=running,
                  color=bar_colors, alpha=0.85, edgecolor=PAPER, linewidth=0.5)
            ax.axhline(0, color='#9CA3AF', linewidth=0.8, linestyle='--')
            plt.xticks(rotation=30, fontsize=9, fontfamily='IBM Plex Sans')
            ax.set_ylabel(y_col, fontsize=10, color='#4B5563', fontfamily='IBM Plex Sans')
            ax.set_title(f'{y_col} Waterfall', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'funnel':
            values = df[y_col].values.astype(float)
            labels = df[x_col].astype(str).values
            max_val = max(values) if max(values) > 0 else 1
            n = len(values)
            for i, (val, label) in enumerate(zip(values, labels)):
                width = val / max_val
                left = (1 - width) / 2
                ax.barh(i, width, left=left,
                       color=_lighten(brand_color, i / max(n - 1, 1) * 0.5),
                       edgecolor=PAPER, height=0.65, alpha=0.9)
                ax.text(0.5, i, f'{label}: {val:,.0f}',
                       ha='center', va='center', fontsize=9,
                       color='#14131F', fontfamily='IBM Plex Sans', fontweight='bold')
            ax.set_xlim(0, 1)
            ax.set_yticks([])
            ax.set_xticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.set_title(f'{y_col} Funnel', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'bullet':
            val = float(df['Value'].iloc[0]) if 'Value' in df.columns else float(df[y_col].iloc[0])
            target = float(df['Target'].iloc[0]) if 'Target' in df.columns else val * 1.25
            label = str(df[x_col].iloc[0]) if x_col in df.columns else y_col
            pct = (val / target * 100) if target > 0 else 0
            ax.barh([label], [target], color='#E5E7EB', height=0.5, label='Target')
            ax.barh([label], [val], color=brand_color, height=0.28, label=f'Actual ({pct:.0f}%)')
            ax.axvline(target, color='#14131F', linewidth=2.5, linestyle='--', label=f'Target ({target:,.0f})')
            ax.legend(fontsize=8, frameon=False, loc='lower right')
            ax.set_xlabel('Value', fontsize=10, color='#4B5563', fontfamily='IBM Plex Sans')
            ax.set_title(f'{label} vs Target', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        elif chart_type == 'treemap':
            agg = df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
            n = len(agg)
            colors = [_lighten(brand_color, i / max(n - 1, 1) * 0.6) for i in range(n)]
            squarify.plot(
                sizes=agg.values,
                label=[f'{k}\n{v:,.0f}' for k, v in zip(agg.index.astype(str), agg.values)],
                color=colors,
                alpha=0.85,
                ax=ax,
                text_kwargs={'fontsize': 8, 'color': '#14131F',
                            'fontfamily': 'IBM Plex Sans', 'fontweight': 'bold'},
            )
            ax.set_axis_off()
            ax.set_title(f'{y_col} by {x_col} (Treemap)', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10, fontfamily='IBM Plex Sans')

        else:  # histogram
            ax.hist(df[y_col].dropna(), bins=20,
                   color=brand_color, alpha=0.85, edgecolor='white')
            ax.set_xlabel(y_col, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_title(f'{y_col} Distribution', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10,
                        fontfamily='IBM Plex Sans')

        _apply_chart_style(ax)

        out_dir = CHART_DIR / report_id
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_x = x_col.replace(' ', '_').replace('/', '_')
        safe_y = y_col.replace(' ', '_').replace('/', '_')
        path = str(out_dir / f'chart_{safe_y}_{safe_x}_{chart_type}.png')
        fig.savefig(path, bbox_inches='tight', facecolor=fig.get_facecolor())
        return path

    except Exception as e:
        logger.warning(f'[chart_service] Chart generation failed for {x_col} vs {y_col}: {e}')
        return None
    finally:
        plt.close(fig)


def generate_sync(
    df: pd.DataFrame,
    report_id: str,
    config: dict,
    brand_color: str = '#6366F1',
    chart_specs: list[dict] | None = None,
) -> list[tuple[str, str]]:
    MAX_CHARTS = 3

    if chart_specs:
        pairs_with_type = [
            (s['x'], s['y'], s['type'], s.get('title', ''))
            for s in chart_specs[:MAX_CHARTS]
        ]
    else:
        metric_columns = config.get('metric_columns') or [
            c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
        ]
        date_column = config.get('date_column')
        dimension_columns = [
            c for c in df.columns
            if c != date_column
            and not pd.api.types.is_numeric_dtype(df[c])
            and df[c].nunique() <= 10
        ]
        pairs = _select_chart_pairs(df, date_column, metric_columns, dimension_columns, MAX_CHARTS)
        pairs_with_type = [
            (x, y, select_chart_type(x, y, df), '')
            for x, y in pairs
        ]

    chart_paths: list[tuple[str, str]] = []
    for x_col, y_col, chart_type, title in pairs_with_type:
        if x_col not in df.columns or y_col not in df.columns:
            logger.warning(f"Skipping chart: column '{x_col}' or '{y_col}' not in df")
            continue
        path = _generate_single_chart(
            df=df,
            x_col=x_col,
            y_col=y_col,
            chart_type=chart_type,
            report_id=report_id,
            brand_color=brand_color,
        )
        if path:
            chart_paths.append((path, y_col))

    return chart_paths


def cleanup_charts(report_id: str) -> None:
    chart_dir = CHART_DIR / report_id
    shutil.rmtree(str(chart_dir), ignore_errors=True)