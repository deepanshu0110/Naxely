import json
import logging

import matplotlib
matplotlib.use('Agg')

import shutil
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import squarify
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from app.core.design_tokens import PAPER_BG, INDIGO, MINT, AMBER, RED

logger = logging.getLogger(__name__)

FONT_DIR = Path(__file__).resolve().parent.parent / 'static' / 'fonts'
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexSans-Regular.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexSans-Italic.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexSans-Bold.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexMono-Regular.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexMono-Bold.ttf'))

# Global matplotlib defaults — charts must inherit IBM Plex everywhere, so any
# text that omits an explicit fontfamily (legends, cell annotations, etc.)
# still matches the document instead of silently falling back to DejaVu Sans.
plt.rcParams['font.family'] = 'IBM Plex Sans'
plt.rcParams['font.sans-serif'] = ['IBM Plex Sans', 'DejaVu Sans']
plt.rcParams['font.monospace'] = ['IBM Plex Mono', 'DejaVu Sans Mono']

SECONDARY_PALETTE = ['#6366F1', '#0E9F6E', '#F59E0B', '#EF4444']  # INDIGO, MINT, AMBER, RED

TRACK = '#E7E2D4'  # ledger light rail behind bars (track-and-fill treatment)

NEUTRAL_BAR = '#CFCAB8'  # muted tan for non-highlight bars — desaturated, same family as TRACK
DONUT_NEUTRALS = ['#D6D0C2', '#CFCAB8', '#BFB9A8', '#ABA89A', '#9E9B8E', '#8C8A7D']  # progressive muted neutrals for donut slices

TIER_CHART_CAPS = {"free": 3, "pro": 8, "agency": 16}


def chart_cap_for_tier(tier: str | None) -> int:
    """Max charts a given tier may select. Unknown/None tiers fall back to Free."""
    tier = (tier or "free").lower()
    return TIER_CHART_CAPS.get(tier, 3)


def _lighten(hex_color: str, factor: float) -> str:
    """Blend hex_color toward white by factor (0.0–1.0)."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * factor * 0.6)
    g = int(g + (255 - g) * factor * 0.6)
    b = int(b + (255 - b) * factor * 0.6)
    return f"#{r:02x}{g:02x}{b:02x}"


def _emphasize_endpoint(ax, x, y, brand_color: str) -> None:
    """Ring the final data point and annotate it with its mono value so the
    latest figure reads as the 'current' value on line charts."""
    last_x, last_y = x.iloc[-1], y.iloc[-1]
    ax.plot([last_x], [last_y], marker='o', markersize=11,
            markerfacecolor=PAPER_BG, markeredgecolor=brand_color,
            markeredgewidth=1.8, zorder=6)
    ax.plot([last_x], [last_y], marker='o', markersize=4,
            markerfacecolor=brand_color, markeredgecolor=brand_color,
            zorder=7)
    ax.annotate(
        _fmt_axis(float(last_y)),
        (last_x, last_y),
        xytext=(0, 14),
        textcoords='offset points',
        ha='center',
        va='bottom',
        fontsize=8.5,
        color='#14131F',
        fontfamily='IBM Plex Mono',
        zorder=8,
    )


def _fmt_axis(val: float) -> str:
    """Format axis tick values as K/M without scientific notation.

    Uses a whole-number shorthand only when exact (1000 -> '1K'); otherwise
    keeps one decimal (1500 -> '1.5K') so distinct tick values never
    collapse into duplicate labels like two '1K's.
    """
    if abs(val) >= 1_000_000:
        return f'{val/1_000_000:.1f}M'
    if abs(val) >= 1_000:
        v = val / 1_000
        if abs(v - round(v)) < 1e-9:
            return f'{v:.0f}K'
        return f'{v:.1f}K'
    return f'{val:.0f}'


def _drop_incomplete_last_bucket(resampled, raw_df, date_col, freq):
    if len(resampled) <= 1:
        return resampled

    last_bucket_start = pd.Timestamp(resampled[date_col].iloc[-1])
    last_data_date = pd.Timestamp(raw_df[date_col].max())
    days_in_last_bucket = (last_data_date - last_bucket_start).days

    if 'W' in str(freq):
        if days_in_last_bucket < 4:
            return resampled.iloc[:-1]
    elif 'M' in str(freq):
        if days_in_last_bucket < 15:
            return resampled.iloc[:-1]

    return resampled


CHART_DIR = Path('/tmp/naxely')


def _apply_chart_style(ax) -> None:
    """Apply Naxely visual standards to any chart axes."""
    # Grid: none — clean ledger look, no default grid clutter
    ax.yaxis.grid(False)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    # Spines: hide top/right, style left/bottom as thin RULE-toned hairlines
    # (matches pdf_service.RULE #D8D6CE — the document's ledger rule language)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#D8D6CE')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_color('#D8D6CE')
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
        # Donut only for the meaningful 3-6 slice range; 1-2 slices are
        # degenerate (a 2-slice donut is a half-bar) and >6 gets too busy.
        return 'donut' if 3 <= n_unique <= 6 else 'bar'
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


def all_chart_candidates(df: pd.DataFrame, config: dict) -> list[dict]:
    """Enumerate every generatable {x, y, type, title} chart candidate.

    Used by preview-charts to return the full selectable list (the frontend then
    filters against the user's tier cap). Groups candidates by relationship:
    trends over time (line), category comparisons (bar), distributions
    (histogram), correlations (scatter), and cross-tabs (heatmap).
    """
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    date_column = config.get("date_column")
    dimension_columns = [
        c for c in df.columns
        if c != date_column
        and not pd.api.types.is_numeric_dtype(df[c])
        and df[c].nunique() <= 10
    ]
    primary_metric = numeric_cols[0] if numeric_cols else None

    candidates: list[dict] = []

    def add(x: str, y: str, chart_type: str) -> None:
        title = f"{y} Distribution" if x == y else f"{y} by {x}"
        candidates.append({"x": x, "y": y, "type": chart_type, "title": title})

    if date_column and date_column in df.columns:
        for metric in numeric_cols:
            add(date_column, metric, 'line')

    if primary_metric:
        for dim in dimension_columns:
            add(dim, primary_metric, 'bar')

    for metric in numeric_cols:
        add(metric, metric, 'histogram')

    for i in range(len(numeric_cols)):
        for j in range(i + 1, len(numeric_cols)):
            add(numeric_cols[i], numeric_cols[j], 'scatter')

    for i in range(len(dimension_columns)):
        for j in range(i + 1, len(dimension_columns)):
            add(dimension_columns[i], dimension_columns[j], 'heatmap')

    return candidates


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


def _bar_datetime_frequency(df: pd.DataFrame, x_col: str) -> str | None:
    """Pick a resample frequency for bar charts over a datetime x-axis.

    Mirrors the density policy used by line charts (see the 'line' branch
    of _generate_single_chart): keep daily bars for short ranges, roll up
    to weekly when there are many unique dates, and monthly when the span
    exceeds a year. Returns None when raw daily bars are fine.
    """
    x = pd.to_datetime(df[x_col])
    unique_dates = x.nunique()
    date_range_days = (x.max() - x.min()).days
    if date_range_days > 365:
        return 'ME'
    if unique_dates > 60:
        return 'W'
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
    fig.patch.set_facecolor(PAPER_BG)
    ax.set_facecolor(PAPER_BG)

    try:
        if chart_type == 'line':
            df_sorted = df.sort_values(x_col).copy()
            df_sorted[x_col] = pd.to_datetime(df_sorted[x_col])

            agg_func = 'mean' if any(x in y_col.lower()
                for x in ['%', 'percent', 'rate', 'ratio', 'score', 'pct']) else 'sum'

            unique_dates = df_sorted[x_col].nunique()
            date_range_days = (df_sorted[x_col].max() - df_sorted[x_col].min()).days

            if date_range_days > 365:
                resample_freq = 'ME'
            elif unique_dates > 60:
                resample_freq = 'W'
            else:
                resample_freq = None

            if resample_freq:
                df_plot = (
                    df_sorted.set_index(x_col)[y_col]
                    .resample(resample_freq)
                    .agg(agg_func)
                    .reset_index()
                )
                df_plot = _drop_incomplete_last_bucket(df_plot, df_sorted, x_col, resample_freq)
            else:
                df_plot = df_sorted.groupby(x_col)[y_col].agg(agg_func).reset_index()

            x = pd.to_datetime(df_plot[x_col])
            y = df_plot[y_col]

            ax.plot(x, y, color=brand_color, linewidth=1.8,
                    marker='o', markersize=3)
            # Endpoint emphasis: ring the final point and label it with the
            # current value so the latest figure reads as "now".
            _emphasize_endpoint(ax, x, y, brand_color)
            ax.set_xlabel(x_col, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')

            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6, prune='both'))
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda val, _: _fmt_axis(val))
            )

        elif chart_type == 'bar':
            if pd.api.types.is_datetime64_any_dtype(df[x_col]):
                freq = _bar_datetime_frequency(df, x_col)
                x_sorted = df.sort_values(x_col)
                if freq:
                    agg_func = 'mean' if any(k in y_col.lower()
                        for k in ['%', 'percent', 'rate', 'ratio', 'score', 'pct']) else 'sum'
                    grouped = (
                        x_sorted.set_index(x_col)[y_col]
                        .resample(freq)
                        .agg(agg_func)
                        .dropna()
                    )
                else:
                    grouped = df.groupby(x_col)[y_col].mean()
                grouped = grouped.sort_values(ascending=True)
                freq_label = cast("dict[str | None, str]", {"ME": "Month", "W": "Week"}).get(freq)
                if freq_label:
                    bar_labels = [d.strftime('%b %d, %Y') for d in grouped.index]
                else:
                    bar_labels = [d.strftime('%b %d') for d in grouped.index]
                agg_label = 'Sum' if freq and agg_func == 'sum' else 'Mean'
                xlabel = f'{agg_label} {y_col}'
            else:
                grouped = df.groupby(x_col)[y_col].mean().sort_values(ascending=True)
                bar_labels = [str(v) for v in grouped.index]
                xlabel = f'Mean {y_col}'

            n_bars = len(grouped)
            bar_range = np.arange(n_bars)
            max_val = grouped.values.max()
            ax.barh(bar_range, [max_val] * n_bars,
                    color=TRACK, height=0.7, zorder=0)
            # Accent-vs-neutral: max bar gets brand_color, others muted
            bar_colors = [NEUTRAL_BAR] * n_bars
            bar_colors[-1] = brand_color
            ax.barh(bar_range, grouped.values,
                    color=bar_colors, height=0.34, zorder=1)
            label_step = max(1, n_bars // 20)
            bar_ticks = list(range(0, n_bars, label_step))
            ax.set_yticks(bar_ticks)
            ax.set_yticklabels([bar_labels[t] for t in bar_ticks],
                               fontsize=8, fontfamily='IBM Plex Sans')
            for i, (val, _) in enumerate(zip(grouped.values, grouped.index)):
                ax.text(val * 1.01, i, f'{val:,.0f}',
                       va='center', fontsize=9, color='#4B5563',
                       fontfamily='IBM Plex Mono')
            ax.set_xlabel(xlabel, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')

        elif chart_type == 'scatter':
            ax.scatter(df[x_col], df[y_col],
                      color=brand_color, alpha=0.7,
                      edgecolors='white', linewidths=0.5, s=60)
            ax.set_xlabel(x_col, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_ylabel(y_col, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')

        elif chart_type == 'area':
            df_sorted = df.sort_values(x_col)
            x = pd.to_datetime(df_sorted[x_col])
            y = df_sorted[y_col]
            ax.fill_between(x, y, color=brand_color, alpha=0.35)
            ax.plot(x, y, color=brand_color, linewidth=1.8)
            ax.set_xlabel(x_col, fontsize=10, color='#4B5563', fontfamily='IBM Plex Sans')

        elif chart_type in ('pie', 'donut'):
            agg = df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
            n = len(agg)
            # Accent-vs-neutral: largest slice brand_color, rest muted neutrals
            colors = [brand_color] + (DONUT_NEUTRALS[: max(0, n-1)] if n > 1 else [])
            # If more slices than neutrals, extend with last neutral
            if len(colors) < n:
                colors += [DONUT_NEUTRALS[-1]] * (n - len(colors))
            wedge_props = {'linewidth': 1.2, 'edgecolor': PAPER_BG}
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
                centre = plt.Circle((0, 0), 0.60, fc=PAPER_BG)
                ax.add_artist(centre)
            ax.axis('equal')

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

        elif chart_type == 'grouped_bar':
            numerics = [c for c in df.columns
                       if pd.api.types.is_numeric_dtype(df[c])][:2]
            if len(numerics) < 2:
                numerics = numerics * 2
            agg = df.groupby(x_col)[numerics].mean()
            x_pos = np.arange(len(agg))
            w = 0.38
            ax.bar(x_pos - w/2, agg[numerics[0]], w,
                  label=numerics[0], color=brand_color, alpha=0.9)
            ax.bar(x_pos + w/2, agg[numerics[1]], w,
                  label=numerics[1], color=_lighten(brand_color, 0.6), alpha=0.6)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(agg.index.astype(str), rotation=30,
                              fontsize=9, fontfamily='IBM Plex Sans')
            ax.legend(fontsize=8, frameon=False)

        elif chart_type == 'stacked_bar':
            numerics = [c for c in df.columns
                       if pd.api.types.is_numeric_dtype(df[c])][:3]
            agg = df.groupby(x_col)[numerics].mean()
            bottom = np.zeros(len(agg))
            for i, col in enumerate(numerics):
                if i == 0:
                    c, a = brand_color, 0.9
                else:
                    c, a = _lighten(brand_color, 0.4 + i * 0.15), 0.6
                ax.bar(agg.index.astype(str), agg[col], bottom=bottom,
                      label=col, color=c, alpha=a)
                bottom += agg[col].values
            ax.legend(fontsize=8, frameon=False)
            plt.xticks(rotation=30, fontsize=9, fontfamily='IBM Plex Sans')

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
            # Despine the twin axis too: hide the right spine so no box border
            # surrounds the plot; style ticks to match the shared chart style.
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.yaxis.grid(False)
            ax2.tick_params(colors='#6B7280', labelsize=9)
            for _lbl in ax2.get_yticklabels():
                _lbl.set_fontfamily('IBM Plex Mono')
            # Cap y-ticks at 6 per axis and share the K/M shorthand so labels
            # stay consistent between the bar and line side of the combo.
            ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6, prune='both'))
            ax2.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6, prune='both'))
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda val, _: _fmt_axis(val)))
            ax2.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda val, _: _fmt_axis(val)))

        elif chart_type == 'waterfall':
            values = df[y_col].values.astype(float)
            labels = df[x_col].astype(str).values
            running = np.concatenate([[0.0], np.cumsum(values[:-1])])
            bar_colors = [brand_color if v >= 0 else RED for v in values]
            ax.bar(labels, values, bottom=running,
                  color=bar_colors, alpha=0.85, edgecolor=PAPER_BG, linewidth=0.5)
            ax.axhline(0, color='#9CA3AF', linewidth=0.8, linestyle='--')
            plt.xticks(rotation=30, fontsize=9, fontfamily='IBM Plex Sans')
            ax.set_ylabel(y_col, fontsize=10, color='#4B5563', fontfamily='IBM Plex Sans')

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
                       edgecolor=PAPER_BG, height=0.65, alpha=0.9)
                ax.text(0.5, i, f'{label}: {val:,.0f}',
                       ha='center', va='center', fontsize=9,
                       color='#14131F', fontfamily='IBM Plex Sans', fontweight='bold')
            ax.set_xlim(0, 1)
            ax.set_yticks([])
            ax.set_xticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)

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

        else:  # histogram
            ax.hist(df[y_col].dropna(), bins=20,
                   color=brand_color, alpha=0.85, edgecolor='white')
            ax.set_xlabel(y_col, fontsize=10, color='#4B5563',
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


def _fmt_caption_number(v) -> str:
    """Format a numeric value for chart captions: thousands separators,
    trimmed decimals, K/M shorthand for large magnitudes."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if pd.isna(f):
        return '0'
    if abs(f) >= 1_000_000:
        return f'{f / 1_000_000:.1f}M'
    if f == int(f):
        return f'{int(f):,}'
    return f'{f:,.2f}'.rstrip('0').rstrip('.')


def _caption_bar_label(v) -> str:
    if isinstance(v, pd.Timestamp):
        return v.strftime('%b %d, %Y')
    return str(v)


def build_chart_caption(df, x_col, y_col, chart_type) -> str:
    """One-line, data-driven caption for a chart, key figures wrapped in <b>
    markup so the PDF can emphasise them. Mirrors the aggregation used in
    _generate_single_chart so the figures match the rendered chart."""
    try:
        if chart_type == 'line':
            s = df.sort_values(x_col)
            if pd.api.types.is_datetime64_any_dtype(s[x_col]):
                unique_dates = s[x_col].nunique()
                date_range_days = (s[x_col].max() - s[x_col].min()).days
                freq = 'ME' if date_range_days > 365 else ('W' if unique_dates > 60 else None)
                if freq:
                    agg_func = 'mean' if any(
                        k in y_col.lower() for k in ['%', 'percent', 'rate', 'ratio', 'score', 'pct']
                    ) else 'sum'
                    s = (
                        s.set_index(x_col)[y_col]
                        .resample(freq)
                        .agg(agg_func)
                        .dropna()
                        .reset_index()
                    )
            series = pd.to_numeric(s[y_col], errors='coerce').dropna()
            if len(series) == 0:
                raise ValueError('empty series')
            if len(series) == 1:
                return f"{y_col} holds at <b>{_fmt_caption_number(series.iloc[0])}</b> across the period."
            v0, v1 = series.iloc[0], series.iloc[-1]
            direction = 'rose' if v1 >= v0 else 'fell'
            pct = (v1 - v0) / v0 * 100 if v0 else 0.0
            sign = '+' if pct >= 0 else ''
            span = 'the period' if len(series) < 2 else f'{len(series)} points'
            return (
                f"{y_col} {direction} from <b>{_fmt_caption_number(v0)}</b> "
                f"to <b>{_fmt_caption_number(v1)}</b> across {span} "
                f"({sign}{pct:.0f}% from first to last)."
            )

        if chart_type == 'bar':
            if pd.api.types.is_datetime64_any_dtype(df[x_col]):
                freq = _bar_datetime_frequency(df, x_col)
                if freq:
                    agg_func = 'mean' if any(
                        k in y_col.lower() for k in ['%', 'percent', 'rate', 'ratio', 'score', 'pct']
                    ) else 'sum'
                    grouped = (
                        df.sort_values(x_col)
                        .set_index(x_col)[y_col]
                        .resample(freq)
                        .agg(agg_func)
                        .dropna()
                    )
                else:
                    grouped = df.groupby(x_col)[y_col].mean()
            else:
                grouped = df.groupby(x_col)[y_col].mean()
            grouped = grouped.sort_values(ascending=True)
            if len(grouped) == 0:
                raise ValueError('empty groups')
            high_label = _caption_bar_label(grouped.index[-1])
            low_label = _caption_bar_label(grouped.index[0])
            high_val = grouped.iloc[-1]
            low_val = grouped.iloc[0]
            if len(grouped) == 1:
                return f"{high_label} leads {y_col} at <b>{_fmt_caption_number(high_val)}</b>."
            return (
                f"{high_label} tops {y_col} at <b>{_fmt_caption_number(high_val)}</b>; "
                f"{low_label} trails at <b>{_fmt_caption_number(low_val)}</b>."
            )

        series = pd.to_numeric(df[y_col], errors='coerce').dropna()
        if len(series) == 0:
            return f"Chart of {y_col} by {x_col}."
        return (
            f"Across <b>{len(df):,}</b> records, {y_col} ranges from "
            f"<b>{_fmt_caption_number(series.min())}</b> to <b>{_fmt_caption_number(series.max())}</b>."
        )
    except Exception:
        return f"Chart of {y_col} by {x_col}."


def _insight_title(df, x_col, y_col, chart_type) -> str:
    """Short headline for chart title, derived from local stats already in scope."""
    try:
        if chart_type == 'line':
            s = df.sort_values(x_col)
            if pd.api.types.is_datetime64_any_dtype(s[x_col]):
                unique_dates = s[x_col].nunique()
                date_range_days = (s[x_col].max() - s[x_col].min()).days
                freq = 'ME' if date_range_days > 365 else ('W' if unique_dates > 60 else None)
                if freq:
                    agg_func = 'mean' if any(k in y_col.lower() for k in ['%', 'percent', 'rate', 'ratio', 'score', 'pct']) else 'sum'
                    s = s.set_index(x_col)[y_col].resample(freq).agg(agg_func).dropna().reset_index()
            series = pd.to_numeric(s[y_col], errors='coerce').dropna()
            if len(series) >= 2:
                v0, v1 = series.iloc[0], series.iloc[-1]
                pct = (v1 - v0) / v0 * 100 if v0 else 0.0
                direction = 'rose' if pct >= 0 else 'fell'
                return f"{y_col} {direction} {abs(pct):.0f}%"
            elif len(series) == 1:
                return f"{y_col} steady at {_fmt_caption_number(series.iloc[0])}"
        elif chart_type == 'bar':
            if pd.api.types.is_datetime64_any_dtype(df[x_col]):
                freq = _bar_datetime_frequency(df, x_col)
                if freq:
                    agg_func = 'mean' if any(k in y_col.lower() for k in ['%', 'percent', 'rate', 'ratio', 'score', 'pct']) else 'sum'
                    grouped = df.sort_values(x_col).set_index(x_col)[y_col].resample(freq).agg(agg_func).dropna()
                else:
                    grouped = df.groupby(x_col)[y_col].mean()
            else:
                grouped = df.groupby(x_col)[y_col].mean()
            grouped = grouped.sort_values(ascending=True)
            if len(grouped) >= 2:
                high = grouped.index[-1]
                return f"{high} leads {y_col}"
            elif len(grouped) == 1:
                return f"{grouped.index[0]} leads {y_col}"
        elif chart_type in ('pie', 'donut'):
            agg = df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
            if len(agg) > 0:
                top_label = str(agg.index[0])
                top_pct = agg.iloc[0] / agg.sum() * 100 if agg.sum() else 0
                return f"{top_label} drives {top_pct:.1f}% of {y_col}"
    except Exception:
        pass
    # fallback — short mechanical but less redundant than "HOURS BY PROJECT"
    if y_col == x_col:
        return y_col
    return f"{y_col} by {x_col}"


def generate_sync(
    df: pd.DataFrame,
    report_id: str,
    config: dict,
    brand_color: str = '#6366F1',
    chart_specs: list[dict] | None = None,
) -> list[tuple[str, str, str, str]]:
    max_charts = chart_cap_for_tier(config.get("tier"))
    date_column = config.get('date_column')

    if chart_specs:
        pairs_with_type = [
            (s['x'], s['y'], s['type'], s.get('title', ''))
            for s in chart_specs[:max_charts]
        ]
    else:
        metric_columns = config.get('metric_columns') or [
            c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
        ]
        dimension_columns = [
            c for c in df.columns
            if c != date_column
            and not pd.api.types.is_numeric_dtype(df[c])
            and df[c].nunique() <= 10
        ]
        pairs = _select_chart_pairs(df, date_column, metric_columns, dimension_columns, max_charts)
        pairs_with_type = [
            (x, y, select_chart_type(x, y, df), '')
            for x, y in pairs
        ]

    chart_paths: list[tuple[str, str, str, str]] = []
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
            caption = build_chart_caption(df, x_col, y_col, chart_type)
            is_mechanical = not title or title == f'{y_col} by {x_col}' or title == f'{y_col} Over Time' or title == f'{y_col} Distribution' or title == y_col
            if is_mechanical:
                insight = _insight_title(df, x_col, y_col, chart_type)
                if insight and insight.strip() != '':
                    title = insight
                elif not title:
                    if y_col == x_col:
                        title = y_col
                    elif date_column and x_col == date_column:
                        title = f'{y_col} Over Time'
                    else:
                        title = f'{y_col} by {x_col}'
            chart_paths.append((path, y_col, caption, title))

    return chart_paths


def cleanup_charts(report_id: str) -> None:
    chart_dir = CHART_DIR / report_id
    shutil.rmtree(str(chart_dir), ignore_errors=True)