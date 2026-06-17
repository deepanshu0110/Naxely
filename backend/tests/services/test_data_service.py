import pytest
import pandas as pd
import numpy as np
import io
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.data_service import (
    parse_csv, validate_csv, validate_for_injection,
    detect_column_types, apply_column_config, compute_column_stats
)


class TestDataService:
    """Test data_service module functions."""
    
    def test_parse_csv_valid_csv(self):
        """Test parsing valid CSV content."""
        csv_content = b"Date,Revenue,Region\n2024-01-01,1000,North\n2024-01-02,1200,South"
        df = parse_csv(csv_content)
        
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 3)
        assert list(df.columns) == ['Date', 'Revenue', 'Region']
    
    def test_parse_csv_valid_excel(self):
        """Test parsing valid Excel content."""
        # Create a simple Excel file in memory
        df_input = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['x', 'y', 'z']
        })
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        df_input.to_excel(buffer, index=False, engine='openpyxl')
        excel_content = buffer.getvalue()
        
        df = parse_csv(excel_content)
        
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 2)
        # Column names might have extra spaces from Excel
        assert 'A' in df.columns
        assert 'B' in df.columns
    
    def test_parse_csv_invalid_content(self):
        """Test parsing invalid content still returns DataFrame (pandas is lenient)."""
        # Pandas is lenient and might parse binary content as CSV
        invalid_content = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
        
        # Should not crash, returns DataFrame
        df = parse_csv(invalid_content)
        assert isinstance(df, pd.DataFrame)
        # The actual validation happens in validate_csv and validate_for_injection
    
    def test_validate_csv_valid(self):
        """Test validating valid DataFrame."""
        df = pd.DataFrame({
            'A': [1, 2],
            'B': [3, 4]
        })
        
        # Should not raise
        validate_csv(df)
    
    def test_validate_csv_too_many_rows(self):
        """Test validating DataFrame with too many rows."""
        df = pd.DataFrame({'A': range(50001)})
        
        with pytest.raises(ValueError, match="Too many rows"):
            validate_csv(df)
    
    def test_validate_csv_too_few_columns(self):
        """Test validating DataFrame with too few columns."""
        df = pd.DataFrame({'A': [1,10,100]})
        
        with pytest.raises(ValueError, match="at least 2 columns"):
            validate_csv(df)
    
    def test_validate_for_injection_safe(self):
        """Test injection validation with safe content."""
        df = pd.DataFrame({
            'A': ['safe', 'normal', 'content123'],
            'B': [1, 2, 3]
        })
        
        # Should not raise
        validate_for_injection(df)
    
    def test_validate_for_injection_dangerous(self):
        """Test injection validation with dangerous content."""
        df = pd.DataFrame({
            'A': ['safe', '=cmd', '+dangerous', '@formula']
        })
        
        with pytest.raises(ValueError, match="dangerous formula"):
            validate_for_injection(df)
    
    def test_detect_column_types(self):
        """Test column type detection."""
        df = pd.DataFrame({
            'date_column': pd.date_range('2024-01-01', periods=5),
            'metric_column': [100, 200, 300, 400, 500],
            'dimension_column': ['A', 'B', 'C', 'D', 'E'],
            'month_year': ['Jan-2024', 'Feb-2024', 'Mar-2024', 'Apr-2024', 'May-2024']
        })
        
        columns_meta = detect_column_types(df)
        
        assert len(columns_meta) == 4
        
        # Check types
        col_names = {cm['original_name']: cm['suggested_type'] for cm in columns_meta}
        assert col_names['date_column'] == 'date'
        assert col_names['metric_column'] == 'metric'
        assert col_names['dimension_column'] == 'dimension'
        assert col_names['month_year'] == 'date'  # Contains 'month' in name
    
    def test_apply_column_config(self):
        """Test applying column configuration."""
        df = pd.DataFrame({
            'col_1': [1, 2, 3],
            'col_2': ['a', 'b', 'c'],
            'col_3': [10.5, 20.5, 30.5]
        })
        
        column_config = [
            {'original_name': 'col_1', 'display_name': 'ID', 'include': True},
            {'original_name': 'col_2', 'display_name': 'Category', 'include': True},
            {'original_name': 'col_3', 'display_name': 'Value', 'include': False}
        ]
        
        result = apply_column_config(df, column_config)
        
        # Check shape and columns
        assert result.shape == (3, 2)  # col_3 excluded
        assert 'col_1' not in result.columns  # Should be renamed
        assert 'ID' in result.columns
        assert 'Category' in result.columns
        assert 'Value' not in result.columns
        assert 'col_3' not in result.columns
    
    def test_compute_column_stats(self):
        """Test computing column statistics."""
        df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10),
            'Revenue': np.random.randint(1000, 2000, 10),
            'Region': ['North', 'South'] * 5
        })
        
        stats = compute_column_stats(df)
        
        assert 'columns' in stats
        assert 'date_column' in stats
        assert 'date_range' in stats
        
        assert stats['date_column'] == 'Date'
        assert isinstance(stats['date_range'], dict)
        assert 'from' in stats['date_range']
        assert 'to' in stats['date_range']
        
        # Check metric column has stats
        for col in stats['columns']:
            if col['name'] == 'Revenue':
                assert 'mean' in col
                assert 'min' in col
                assert 'max' in col
                assert 'trend' in col
                assert 'trend_pct_change' in col
                break
        
        # Check date column stats
        for col in stats['columns']:
            if col['name'] == 'Date':
                assert col['type'] == 'date'
                break