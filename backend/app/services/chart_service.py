import logging

import matplotlib
matplotlib.use('Agg')

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from app.core.design_tokens import PAPER, INDIGO, MINT, AMBER, RED

logger = logging.getLogger(__name__)

FONT_DIR = Path(__file__).resolve().parent.parent / 'static' / 'fonts'
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexSans-Regular.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexSans-Italic.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexMono-Regular.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexMono-Bold.ttf'))

SECONDARY_PALETTE = ['#6366F1', '#0E9F6E', '#F59E0B', '#EF4444']  # INDIGO, MINT, AMBER, RED

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
    col1_is_categorical = (
        df[col1].dtype == object
        or (df[col1].nunique() <= 10 and not pd.api.types.is_numeric_dtype(df[col1]))
    )
    col2_is_numeric = pd.api.types.is_numeric_dtype(df[col2])

    if col1_is_date and col2_is_numeric:
        return 'line'
    if col1_is_categorical and col2_is_numeric:
        return 'bar'
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
            df_sorted = df.sort_values(x_col)
            agg_func = 'mean' if any(x in y_col.lower()
                for x in ['%', 'percent', 'rate', 'ratio', 'score']) else 'sum'
            df_sorted = df_sorted.groupby(x_col)[y_col].agg(agg_func).reset_index()
            x = pd.to_datetime(df_sorted[x_col])
            y = df_sorted[y_col]
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
) -> list[tuple[str, str]]:
    MAX_CHARTS = 3

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

    chart_paths: list[tuple[str, str]] = []
    for x_col, y_col in pairs:
        if x_col not in df.columns or y_col not in df.columns:
            continue
        chart_type = select_chart_type(x_col, y_col, df)
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