import io
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

FREE_TEXT_NAME_PATTERNS = ('note', 'comment', 'description', 'remark')


def parse_csv(content: bytes) -> pd.DataFrame:
    """
    Parse CSV or Excel file from bytes in memory.
    
    Args:
        content: Raw file bytes
        
    Returns:
        pd.DataFrame: Parsed data
        
    Raises:
        ValueError: If file cannot be parsed
    """
    try:
        # Try CSV first
        try:
            df = pd.read_csv(io.BytesIO(content), keep_default_na=False, na_values=[''])
            return df
        except Exception as csv_error:
            # If CSV fails, try Excel
            try:
                df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
                return df
            except Exception as excel_error:
                # Both failed
                raise ValueError(
                    f"Cannot parse file as CSV or Excel. "
                    f"CSV error: {str(csv_error)}. "
                    f"Excel error: {str(excel_error)}"
                )
    except Exception as e:
        raise ValueError(f"Failed to parse file: {str(e)}")


def validate_csv(df: pd.DataFrame) -> None:
    """
    Validate DataFrame for basic constraints.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        ValueError: If validation fails
    """
    # Check row count
    if len(df) > 50000:
        raise ValueError("Too many rows. Maximum is 50,000.")
    
    # Check column count
    if len(df.columns) < 2:
        raise ValueError("File must have at least 2 columns.")


def validate_for_injection(df: pd.DataFrame) -> None:
    """
    Scan string cells for formula injection patterns.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        ValueError: If dangerous content detected
    """
    injection_pattern = re.compile(r'^[=+\-@].*', re.IGNORECASE)
    
    for col in df.columns:
        # Only check string columns
        if df[col].dtype == 'object':
            # Check each cell in the column
            for idx, cell in df[col].items():
                if pd.isna(cell):
                    continue
                    
                # Convert to string if needed
                cell_str = str(cell).strip()
                if injection_pattern.match(cell_str):
                    raise ValueError(
                        f"File contains potentially dangerous formula content. "
                        f"Found in column '{col}', row {idx + 2}: '{cell_str}'"
                    )


def detect_column_types(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect column types and generate metadata.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        List[Dict]: Column metadata for each column
    """
    columns_meta = []
    
    for col_name in df.columns:
        col_data = df[col_name]
        
        # Calculate basic stats
        null_count = col_data.isna().sum()
        unique_count = col_data.nunique()
        
        # Get sample values (first 3 non-null)
        sample_values: List[str] = []
        for val in col_data.head(10):  # Check first 10 rows for samples
            if pd.notna(val) and len(sample_values) < 3:
                sample_values.append(str(val))
        
        # Clean column name for suggested name
        suggested_name = _clean_column_name(col_name)
        
        # Detect type
        suggested_type = _detect_column_type(col_data, col_name)
        
        columns_meta.append({
            "original_name": str(col_name),
            "suggested_name": suggested_name,
            "suggested_type": suggested_type,
            "sample_values": sample_values,
            "null_count": int(null_count),
            "unique_count": int(unique_count)
        })
    
    return columns_meta


def apply_column_config(df: pd.DataFrame, column_config: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Apply column configuration to DataFrame.
    
    Args:
        df: Original DataFrame
        column_config: List of column config dicts
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    # Create mapping for renaming
    rename_map = {}
    drop_columns = []
    
    for config in column_config:
        original_name = config["original_name"]
        
        if not config.get("include", True):
            drop_columns.append(original_name)
        else:
            display_name = config.get("display_name")
            if display_name and display_name != original_name:
                rename_map[original_name] = display_name
    
    # Apply operations
    df_clean = df.copy()
    
    # Drop excluded columns
    if drop_columns:
        df_clean = df_clean.drop(columns=drop_columns)
    
    # Rename columns
    if rename_map:
        df_clean = df_clean.rename(columns=rename_map)
    
    return df_clean


def compute_column_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute comprehensive column statistics.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dict: Column statistics in SDD Section 4.1 format
    """
    columns_stats = []
    date_column = None
    date_range = None
    
    for col_name in df.columns:
        col_data = df[col_name]
        
        # Basic stats for all columns
        stats = {
            "name": str(col_name),
            "type": _detect_column_type(col_data, col_name),
            "null_count": int(col_data.isna().sum()),
            "row_count": len(col_data),
        }
        
        # For date columns, track date range
        if stats["type"] == "date":
            date_column = col_name
            # Convert to datetime and get range
            try:
                date_series = pd.to_datetime(col_data.dropna())
                if len(date_series) > 0:
                    date_range = {
                        "from": date_series.min().strftime("%Y-%m-%d"),
                        "to": date_series.max().strftime("%Y-%m-%d")
                    }
            except Exception:
                pass
        
        # For numeric (metric) columns, compute additional stats
        if pd.api.types.is_numeric_dtype(col_data):
            numeric_data = pd.to_numeric(col_data, errors='coerce')
            numeric_data_clean = numeric_data.dropna()
            
            if len(numeric_data_clean) > 0:
                stats.update({
                    "mean": float(numeric_data_clean.mean()),
                    "min": float(numeric_data_clean.min()),
                    "max": float(numeric_data_clean.max()),
                    "latest_value": float(numeric_data_clean.iloc[-1]),
                    "trend": _compute_trend(numeric_data_clean),
                    "trend_pct_change": _compute_trend_percentage(numeric_data_clean)
                })
        
        columns_stats.append(stats)
    
    return {
        "columns": columns_stats,
        "date_column": date_column,
        "date_range": date_range or {"from": None, "to": None}
    }


def _is_likely_free_text(column_name: str) -> bool:
    name_lower = column_name.lower()
    return any(pattern in name_lower for pattern in FREE_TEXT_NAME_PATTERNS)


def normalize_for_aggregation(df: pd.DataFrame, column_types: Dict[str, str]) -> pd.DataFrame:
    normalized = df.copy()

    for col, col_type in column_types.items():
        if col not in normalized.columns:
            continue

        if col_type == 'text':
            continue

        if col_type == 'dimension':
            if _is_likely_free_text(col):
                logger.info(
                    "Free-text heuristic fired for column '%s' "
                    "(typed 'dimension', name matched free-text pattern)",
                    col,
                )
                continue
            normalized[col] = normalized[col].str.strip().str.title()

        elif col_type == 'date':
            normalized[col] = pd.to_datetime(
                normalized[col], format='mixed', dayfirst=False, errors='coerce'
            )

        elif col_type == 'metric' and normalized[col].dtype == object:
            normalized[col] = (
                normalized[col]
                .astype(str)
                .str.replace(r'[\$,]', '', regex=True)
                .replace('nan', pd.NA)
            )
            normalized[col] = pd.to_numeric(normalized[col], errors='coerce')

    return normalized


def _clean_column_name(col_name: str) -> str:
    """
    Clean column name for display.
    
    Args:
        col_name: Original column name
        
    Returns:
        str: Cleaned column name
    """
    # Convert to string
    name = str(col_name)
    
    # Replace underscores and dashes with spaces
    name = re.sub(r'[_\-]+', ' ', name)
    
    # Capitalize first letter of each word
    name = name.title()
    
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    return name


def _detect_column_type(col_data: pd.Series, col_name: str) -> str:
    """
    Detect column type based on data and column name.
    
    Args:
        col_data: Column data
        col_name: Column name
        
    Returns:
        str: "date", "metric", or "dimension"
    """
    col_name_lower = str(col_name).lower()
    
    # Check for date indicators in column name
    date_keywords = ['date', 'time', 'month', 'year', 'day', 'week', 'quarter']
    if any(keyword in col_name_lower for keyword in date_keywords):
        # Try to parse as date
        try:
            # Sample first non-null values to check
            sample = col_data.dropna().head(10)
            if len(sample) > 0:
                # Try with explicit format to avoid warning
                pd.to_datetime(sample, errors='raise', format='mixed')
                return "date"
        except Exception:
            pass
    
    # Check if numeric
    if pd.api.types.is_numeric_dtype(col_data):
        return "metric"
    
    # Try to convert to numeric
    try:
        numeric_data = pd.to_numeric(col_data, errors='raise')
        if numeric_data.notna().any():
            return "metric"
    except Exception:
        pass
    
    # Default to dimension
    return "dimension"


def _compute_trend(data: pd.Series) -> str:
    """
    Compute trend direction for a numeric series.
    
    Args:
        data: Numeric series
        
    Returns:
        str: "increasing", "decreasing", or "flat"
    """
    if len(data) < 2:
        return "flat"
    
    # Simple trend detection
    values = data.values
    first_half = values[:len(values)//2]
    second_half = values[len(values)//2:]
    
    mean_first = np.mean(first_half)
    mean_second = np.mean(second_half)
    
    if mean_second > mean_first * 1.05:  # 5% increase
        return "increasing"
    elif mean_second < mean_first * 0.95:  # 5% decrease
        return "decreasing"
    else:
        return "flat"


def _compute_trend_percentage(data: pd.Series) -> float:
    """
    Compute percentage change from first to last value.
    
    Args:
        data: Numeric series
        
    Returns:
        float: Percentage change
    """
    if len(data) < 2:
        return 0.0
    
    first = data.iloc[0]
    last = data.iloc[-1]
    
    if first == 0:
        return 0.0
    
    return ((last - first) / abs(first)) * 100