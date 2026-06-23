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


def select_chart_type(
    df: pd.DataFrame,
    metric_column: str,
    date_column: str | None = None,
    dimension_columns: list[str] | None = None,
) -> str:
    """
    Decision tree:
    1. Date column present -> line chart (time series)
    2. Dimension column with <=10 unique values -> horizontal bar (grouped by dimension)
    3. Two or more numeric columns -> scatter (metric vs metric)
    4. Fallback -> histogram (distribution)
    """
    if date_column and date_column in df.columns:
        return 'line'

    if dimension_columns:
        for dim in dimension_columns:
            if dim in df.columns and df[dim].nunique() <= 10:
                return 'bar'

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(numeric_cols) >= 2:
        return 'scatter'

    return 'histogram'


def _generate_single_chart(
    df: pd.DataFrame,
    metric_column: str,
    chart_type: str,
    date_column: str | None,
    dimension_columns: list[str],
    report_id: str,
    brand_color: str,
) -> str | None:
    """Generate one chart PNG. Returns path or None on failure."""
    import matplotlib.ticker as mticker

    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)

    try:
        if chart_type == 'line' and date_column and date_column in df.columns:
            df_sorted = df.sort_values(date_column)
            x = pd.to_datetime(df_sorted[date_column])
            y = df_sorted[metric_column]
            ax.plot(x, y, color=brand_color, linewidth=2.0,
                    marker='o', markersize=4,
                    markerfacecolor='white', markeredgecolor=brand_color,
                    markeredgewidth=1.5)
            ax.fill_between(x, y, alpha=0.08, color=brand_color)
            ax.set_xlabel(date_column, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_title(f'{metric_column} Over Time', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10,
                        fontfamily='IBM Plex Sans')

        elif chart_type == 'bar' and dimension_columns:
            dim = dimension_columns[0]
            if any(x in metric_column.lower() for x in ['%', 'percent', 'rate', 'ratio', 'score', 'avg', 'average']):
                grouped = df.groupby(dim)[metric_column].mean().sort_values()
            else:
                grouped = df.groupby(dim)[metric_column].sum().sort_values()
            ax.barh(grouped.index, grouped.values,
                    color=brand_color, alpha=0.85, height=0.55)
            # Value labels at bar end
            for i, (val, label) in enumerate(zip(grouped.values, grouped.index)):
                ax.text(val * 1.01, i, f'{val:,.0f}',
                       va='center', fontsize=9, color='#4B5563',
                       fontfamily='IBM Plex Mono')
            ax.set_xlabel(metric_column, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_title(f'{metric_column} by {dim}', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10,
                        fontfamily='IBM Plex Sans')

        elif chart_type == 'scatter':
            numeric_cols = [c for c in df.columns
                           if pd.api.types.is_numeric_dtype(df[c])
                           and c != metric_column]
            if not numeric_cols:
                return None
            y_col = numeric_cols[0]
            ax.scatter(df[metric_column], df[y_col],
                      color=brand_color, alpha=0.7,
                      edgecolors='white', linewidths=0.5, s=60)
            ax.set_xlabel(metric_column, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_ylabel(y_col, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_title(f'{metric_column} vs {y_col}', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10,
                        fontfamily='IBM Plex Sans')

        else:  # histogram
            ax.hist(df[metric_column].dropna(), bins=20,
                   color=brand_color, alpha=0.85, edgecolor='white')
            ax.set_xlabel(metric_column, fontsize=10, color='#4B5563',
                         fontfamily='IBM Plex Sans')
            ax.set_title(f'{metric_column} Distribution', fontsize=13,
                        fontweight='bold', color='#14131F', pad=10,
                        fontfamily='IBM Plex Sans')

        # --- Shared styling ---
        _apply_chart_style(ax)

        # Save
        out_dir = CHART_DIR / report_id
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_col = metric_column.replace(' ', '_').replace('/', '_')
        path = str(out_dir / f'chart_{safe_col}_{chart_type}.png')
        fig.savefig(path, bbox_inches='tight', facecolor=fig.get_facecolor())
        return path

    except Exception as e:
        logger.warning(f'[chart_service] Chart generation failed for {metric_column}: {e}')
        return None
    finally:
        plt.close(fig)


def generate_sync(
    df: pd.DataFrame,
    report_id: str,
    config: dict,
    brand_color: str = '#6366F1',
) -> list[str]:
    MAX_CHARTS = 3

    metric_columns = config.get('metric_columns') or [
        c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
    ]
    date_column = config.get('date_column')
    column_config = config.get('column_config', [])

    # Identify dimension columns: non-numeric, non-date, <=10 unique values
    dimension_columns = [
        c for c in df.columns
        if c != date_column
        and not pd.api.types.is_numeric_dtype(df[c])
        and df[c].nunique() <= 10
    ]

    chart_paths = []
    for metric_col in metric_columns[:MAX_CHARTS]:
        chart_type = select_chart_type(df, metric_col, date_column, dimension_columns)
        path = _generate_single_chart(
            df=df,
            metric_column=metric_col,
            chart_type=chart_type,
            date_column=date_column,
            dimension_columns=dimension_columns,
            report_id=report_id,
            brand_color=brand_color,
        )
        if path:
            chart_paths.append((path, metric_col))

    return chart_paths


def cleanup_charts(report_id: str) -> None:
    chart_dir = CHART_DIR / report_id
    shutil.rmtree(str(chart_dir), ignore_errors=True)