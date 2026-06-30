"""Generate a real sample PDF from the sample CSV using the Naxely pipeline."""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tempfile
import shutil
from pathlib import Path

import pandas as pd

os.environ['TEMP_DIR'] = tempfile.gettempdir()

import matplotlib
matplotlib.use('Agg')

from app.services import data_service, chart_service, pdf_service

CSV_PATH = Path(__file__).resolve().parent.parent / 'app' / 'static' / 'samples' / 'agency_billable_hours.csv'
OUT_DIR = Path(__file__).resolve().parent.parent.parent / 'frontend' / 'public' / 'sample'
REPORT_ID = 'sample-report'

with open(CSV_PATH, 'rb') as f:
    csv_bytes = f.read()

df = data_service.parse_csv(csv_bytes)

date_column = next(
    (col for col in df.columns if col.lower() in ['date', 'datetime', 'timestamp', 'time', 'week', 'month', 'year']),
    None
)

metric_columns = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
dimension_columns = [
    c for c in df.columns
    if c != date_column and not pd.api.types.is_numeric_dtype(df[c]) and df[c].nunique() <= 10
]

config = {
    'title': 'Agency Billable Hours — Sample Report',
    'report_id': REPORT_ID,
    'date_column': date_column,
    'metric_columns': metric_columns,
    'sections': ['charts', 'kpi_overview', 'data_table'],
    'brand': {'color': '#D97A34'},
    'column_config': [],
}

df_norm = df.copy()
df_norm[date_column] = pd.to_datetime(df_norm[date_column], format='mixed', dayfirst=False, errors='coerce')

for c in metric_columns:
    if df_norm[c].dtype == object:
        df_norm[c] = pd.to_numeric(
            df_norm[c].astype(str).str.replace('$', '').str.replace(',', ''),
            errors='coerce',
        )

pairs = chart_service._select_chart_pairs(df_norm, date_column, metric_columns, dimension_columns, 3)
chart_specs = [
    {'x': x, 'y': y, 'type': chart_service.select_chart_type(x, y, df_norm), 'title': f'{y} by {x}'}
    for x, y in pairs
]

chart_paths = chart_service.generate_sync(
    df=df_norm,
    report_id=REPORT_ID,
    config=config,
    brand_color='#D97A34',
    chart_specs=chart_specs,
)

ai_content = {
    'summary': None,
    'insights': [],
    'recommendations': [],
    'anomalies': [],
    'trends': [],
}

user_data = {
    'brand_color': '#D97A34',
    'tier': 'free',
    'logo_url': None,
    'company_name': 'Acme Agency',
}

pdf_path = pdf_service.build_sync(
    df=df,
    chart_paths=[p for p, _ in chart_paths],
    ai_content=ai_content,
    config=config,
    user_data=user_data,
)

OUT_DIR.mkdir(parents=True, exist_ok=True)
out_pdf = OUT_DIR / 'report.pdf'
shutil.copy2(pdf_path, str(out_pdf))
print(f'PDF saved to {out_pdf} ({out_pdf.stat().st_size} bytes)')

csv_out = OUT_DIR / 'agency_billable_hours.csv'
print(f'CSV at {csv_out} ({csv_out.stat().st_size} bytes)')

chart_service.cleanup_charts(REPORT_ID)
os.unlink(pdf_path)
parent_dir = Path(pdf_path).parent
if parent_dir.exists():
    shutil.rmtree(str(parent_dir), ignore_errors=True)

print('Done.')
