import matplotlib
matplotlib.use('Agg')

import shutil
from pathlib import Path

import pandas as pd
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

FONT_DIR = Path(__file__).resolve().parent.parent / 'static' / 'fonts'
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexMono-Regular.ttf'))
fm.fontManager.addfont(str(FONT_DIR / 'IBMPlexMono-Bold.ttf'))
matplotlib.rcParams['font.family'] = 'IBM Plex Mono'

SECONDARY_COLOR = '#94A3B8'
GRID_COLOR = '#E5E7EB'
SPINE_COLOR = '#D1D5DB'
TICK_COLOR = '#6B7280'
LABEL_COLOR = '#374151'
TITLE_COLOR = '#1F2937'

CHART_DIR = Path('/tmp/naxely')


def _apply_chart_style(fig, ax, brand_color: str) -> None:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(SPINE_COLOR)
    ax.spines['bottom'].set_color(SPINE_COLOR)
    ax.grid(True, axis='y', color=GRID_COLOR, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis='both', labelsize=10, colors=TICK_COLOR)
    ax.xaxis.label.set_size(12)
    ax.xaxis.label.set_color(LABEL_COLOR)
    ax.xaxis.label.set_fontweight('bold')
    ax.yaxis.label.set_size(12)
    ax.yaxis.label.set_color(LABEL_COLOR)
    ax.yaxis.label.set_fontweight('bold')
    ax.set_title(
        ax.get_title() or '',
        fontsize=14, fontweight='bold', color=TITLE_COLOR, pad=12,
    )


def _is_date_column(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    try:
        pd.to_datetime(series.dropna().head(20))
        return True
    except (ValueError, TypeError):
        return False


def _is_categorical_column(series: pd.Series) -> bool:
    return series.dtype == object or isinstance(series.dtype, pd.CategoricalDtype)


def select_chart_type(df: pd.DataFrame, column_name: str, date_column: str | None = None) -> str:
    if column_name not in df.columns:
        return 'bar'

    col = df[column_name]
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    if date_column and date_column in df.columns and pd.api.types.is_numeric_dtype(col):
        return 'line'

    if _is_categorical_column(col) and numeric_cols:
        return 'bar'

    if len(numeric_cols) >= 2 and date_column and date_column in df.columns:
        return 'multi_line'

    if len(numeric_cols) == 2 and not date_column:
        non_date_numeric = [c for c in numeric_cols if c != date_column]
        if len(non_date_numeric) >= 2:
            return 'scatter'

    try:
        total = col.dropna().sum()
        if abs(total - 100.0) <= 5.0 and col.dropna().between(0, 100).all():
            return 'pie'
    except (TypeError, ValueError):
        pass

    if pd.api.types.is_numeric_dtype(col):
        return 'histogram'

    return 'bar'


def generate_chart(df: pd.DataFrame, column_name: str, chart_type: str,
                   report_id: str, chart_index: int,
                   brand_color: str = '#6366F1') -> str:
    import matplotlib.pyplot as plt

    output_dir = CHART_DIR / report_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f'chart_{chart_index}.png'

    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_chart_style(fig, ax, brand_color)

    display_name = column_name.replace('_', ' ').title()

    if chart_type == 'line':
        date_col = None
        for c in df.columns:
            if _is_date_column(df[c]):
                date_col = c
                break
        if date_col:
            plot_df = df.sort_values(date_col)
            ax.plot(plot_df[date_col], plot_df[column_name], color=brand_color, linewidth=2)
            ax.set_xlabel(date_col.replace('_', ' ').title())
        else:
            ax.plot(df.index, df[column_name], color=brand_color, linewidth=2)
        ax.set_ylabel(display_name)

    elif chart_type == 'bar':
        if _is_categorical_column(df[column_name]):
            counts = df[column_name].value_counts()
            ax.bar(counts.index.astype(str), counts.values, color=brand_color)
            ax.set_xlabel(display_name)
            ax.set_ylabel('Count')
        else:
            values = df[column_name].dropna()
            ax.bar(range(len(values)), values, color=brand_color)
            ax.set_xlabel('Row')
            ax.set_ylabel(display_name)

    elif chart_type == 'histogram':
        ax.hist(df[column_name].dropna(), bins=20, color=brand_color, edgecolor='white')
        ax.set_xlabel(display_name)
        ax.set_ylabel('Frequency')

    elif chart_type == 'pie':
        values = df[column_name].dropna()
        labels = values.index.astype(str) if values.index.dtype != int else range(len(values))
        colors = [brand_color] + [c for c in CHART_COLORS if c != brand_color]
        colors = colors[:len(values)]
        ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_aspect('equal')

    elif chart_type == 'scatter':
        other_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != column_name]
        if other_cols:
            x_col = other_cols[0]
            y_col = column_name
        else:
            x_col = column_name
            y_col = column_name
        ax.scatter(df[x_col], df[y_col], color=brand_color, alpha=0.6, s=40)
        ax.set_xlabel(x_col.replace('_', ' ').title())
        ax.set_ylabel(y_col.replace('_', ' ').title())

    elif chart_type == 'multi_line':
        date_col = None
        for c in df.columns:
            if _is_date_column(df[c]):
                date_col = c
                break
        if date_col:
            plot_df = df.sort_values(date_col)
            ax.plot(plot_df[date_col], plot_df[column_name], color=brand_color, linewidth=2)
            ax.set_xlabel(date_col.replace('_', ' ').title())
            ax.set_ylabel(display_name)

    fig.tight_layout()
    fig.savefig(str(output_path), dpi=150)
    plt.close(fig)

    return str(output_path)


def generate_sync(df: pd.DataFrame, report_id: str, config: dict,
                  brand_color: str = '#6366F1') -> list[tuple[str, str]]:
    chart_data: list[tuple[str, str]] = []

    date_column = config.get('date_column')

    metric_columns = config.get('metric_columns', [])
    if not metric_columns:
        metric_columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    metric_columns = metric_columns[:8]

    scatter_pairs_seen = set()
    chart_index = 0
    for col_name in metric_columns:
        chart_type = select_chart_type(df, col_name, date_column)
        if chart_type == 'scatter':
            other_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != col_name]
            if other_cols:
                x_col = other_cols[0]
                y_col = col_name
            else:
                x_col = col_name
                y_col = col_name
            pair = tuple(sorted([x_col, y_col]))
            if pair in scatter_pairs_seen:
                continue
            scatter_pairs_seen.add(pair)
        path = generate_chart(df, col_name, chart_type, report_id, chart_index, brand_color)
        chart_data.append((path, col_name))
        chart_index += 1

    return chart_data


def cleanup_charts(report_id: str) -> None:
    chart_dir = CHART_DIR / report_id
    shutil.rmtree(str(chart_dir), ignore_errors=True)
