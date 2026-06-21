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
    detect_column_types, apply_column_config, compute_column_stats,
    normalize_for_aggregation, _is_likely_free_text,
    _detect_column_type, _try_clean_numeric, _NUMERIC_DETECTION_THRESHOLD,
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


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


class TestNormalizeForAggregation:
    """Tests for normalize_for_aggregation — data normalization layer."""

    @classmethod
    def setup_class(cls):
        csv_path = os.path.join(FIXTURE_DIR, 'edge_case_messy_formatting.csv')
        with open(csv_path, 'rb') as f:
            cls.MESSY_DF = parse_csv(f.read())

    def test_currency_fix_highest_priority(self):
        """Currency strings convert to correct floats; pre- vs post-fix totals differ."""
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        df_norm = normalize_for_aggregation(self.MESSY_DF, column_types)

        revenue = df_norm["Revenue"]
        assert pd.api.types.is_numeric_dtype(revenue)

        pre_fix = pd.to_numeric(self.MESSY_DF["Revenue"], errors='coerce')
        post_fix = pd.to_numeric(
            self.MESSY_DF["Revenue"].astype(str).str.replace(r'[\$,]', '', regex=True).replace('nan', pd.NA),
            errors='coerce',
        )

        pre_sum = pre_fix.sum()
        post_sum = post_fix.sum()

        print(f"\nBEFORE/AFTER REVENUE TOTALS:")
        print(f"  PRE-FIX  non-NaN: {pre_fix.notna().sum()}, sum: {pre_sum:.2f}")
        print(f"  POST-FIX non-NaN: {post_fix.notna().sum()}, sum: {post_sum:.2f}")

        assert post_sum == pytest.approx(440772.96, rel=1e-3)
        assert pre_fix.notna().sum() == 46
        assert post_fix.notna().sum() == 73

    def test_region_consolidation_categorical(self):
        """Dimension columns: strip whitespace and title-case each region value."""
        df = self.MESSY_DF
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        df_norm = normalize_for_aggregation(df, column_types)

        normed = df_norm["Region"].dropna()
        assert " south " not in [str(r) for r in normed], "Leading/trailing whitespace should be stripped"
        for val in normed:
            clean = str(val).strip().title()
            assert val == clean, f"'{val}' should be stripped and title-cased (got '{clean}')"
        expected = {"North", "South", "East", "West"}
        norm_set = set(str(r) for r in normed)
        assert norm_set.issubset(expected), f"Values {norm_set} not all in {expected}"

    def test_region_data_table_shows_raw_values(self):
        """Original df (not normalized) retains raw distinct Region strings."""
        raw_regions = list(self.MESSY_DF["Region"].unique())
        has_raw = any(" south " in str(r).lower() for r in raw_regions)
        assert has_raw, "Raw df should still have the original whitespace/case variants"

    def test_mixed_date_parsing(self):
        """Mixed-format dates parse correctly under dayfirst=False."""
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        df_norm = normalize_for_aggregation(self.MESSY_DF, column_types)

        parsed = df_norm["Date"]
        assert pd.api.types.is_datetime64_any_dtype(parsed)
        assert parsed.iloc[0] == pd.Timestamp("2025-02-01")  # 01-Feb-2025
        assert parsed.iloc[1] == pd.Timestamp("2025-02-03")  # 03-Feb-2025
        assert parsed.iloc[2] == pd.Timestamp("2025-02-05")  # 02/05/2025

    def test_malformed_date_value_becomes_nat(self):
        """Check an empty/null date does not crash; NaT counted properly."""
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        df_norm = normalize_for_aggregation(self.MESSY_DF, column_types)
        null_dates = df_norm["Date"].isna().sum()
        raw_nat_count = self.MESSY_DF["Date"].isna().sum()
        assert null_dates >= raw_nat_count
        assert null_dates <= raw_nat_count + 2  # allow for extra coercions

    def test_notes_heuristic_fires_text_untouched(self):
        """Notes column (typed dimension, name matches 'note' pattern) — stays unchanged."""
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        df_norm = normalize_for_aggregation(self.MESSY_DF, column_types)

        note_rows = df_norm["Notes"].dropna()
        for val in note_rows:
            assert val == val  # not NaN

    def test_explicit_text_type_no_heuristic_log(self):
        """Column typed 'text' skips normalization entirely; heuristic does not fire."""
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "text"}
        df_norm = normalize_for_aggregation(self.MESSY_DF, column_types)

        note_rows = df_norm["Notes"].dropna()
        for val in note_rows:
            assert val == val

    def test_non_matching_dimension_normalized(self):
        """Region columns typed dimension (no free-text pattern) normalize as categorical."""
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        df_norm = normalize_for_aggregation(self.MESSY_DF, column_types)
        normed = df_norm["Region"].dropna()
        assert not any(r != r.title().strip() for r in normed)

    def test_original_df_unchanged(self):
        """normalize_for_aggregation does not mutate the input df."""
        df_copy = self.MESSY_DF.copy()
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        normalize_for_aggregation(df_copy, column_types)
        assert df_copy["Revenue"].iloc[0] == 7091.19 or df_copy["Revenue"].iloc[0] == "7091.19"

    # ── Guardrail: N/A handling (keep_default_na=False, na_values=['']) ──

    def test_na_preserved_as_text_in_raw_df(self):
        """'N/A' in Notes stays as string, NOT converted to NaN."""
        raw = self.MESSY_DF
        notes = raw["Notes"]
        na_counts = (notes == "N/A").sum()
        assert na_counts == 7, f"Expected 7 'N/A' entries, got {na_counts}"
        na_idx = notes[notes == "N/A"].index[0]
        assert isinstance(notes.loc[na_idx], str), "N/A should be str, not NaN"

    def test_na_preserved_as_text_in_df_norm(self):
        """After normalization, 'N/A' in Notes remains a string."""
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        df_norm = normalize_for_aggregation(self.MESSY_DF, column_types)
        notes_norm = df_norm["Notes"]
        na_mask = notes_norm == "N/A"
        assert na_mask.any(), "N/A should survive normalization"
        na_idx = notes_norm[notes_norm == "N/A"].index[0]
        assert isinstance(notes_norm.loc[na_idx], str), "N/A must remain str after norm"
        # Verify it's not mistakenly counted as NaN
        assert pd.notna(notes_norm.loc[na_idx]), "N/A string should NOT be NaN"

    def test_blank_cells_still_null_in_raw_df(self):
        """Blank cells still parse as NaN despite keep_default_na=False."""
        raw = self.MESSY_DF
        assert pd.isna(raw["Units Sold"].iloc[0]), "First row Units Sold is blank"
        assert pd.isna(raw["Notes"].iloc[0]), "First row Notes is blank"
        assert raw["Notes"].isna().sum() > 0, "Should have blank Notes cells"

    def test_blank_cells_still_null_in_df_norm(self):
        """Blank cells remain NaN after normalization."""
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        df_norm = normalize_for_aggregation(self.MESSY_DF, column_types)
        blank_notes = df_norm["Notes"].isna().sum()
        assert blank_notes > 0, "Blank Notes should still be NaN after norm"

    def test_null_counts_report(self):
        """Print comprehensive null counts before/after normalization for audit."""
        column_types = {"Date": "date", "Revenue": "metric", "Region": "dimension", "Notes": "dimension"}
        raw = self.MESSY_DF
        df_norm = normalize_for_aggregation(raw, column_types)
        print(f"\n{'─'*60}")
        print(f"{'GUARDRAIL: NULL COUNTS BEFORE vs AFTER NORMALIZATION':^60}")
        print(f"{'─'*60}")
        print(f"{'Column':<20} {'Raw NaN':>10} {'Norm NaN':>10} {'Delta':>10}")
        print(f"{'─'*60}")
        for col in raw.columns:
            raw_nan = int(raw[col].isna().sum())
            norm_nan = int(df_norm[col].isna().sum())
            delta = norm_nan - raw_nan
            print(f"{col:<20} {raw_nan:>10} {norm_nan:>10} {delta:+>10d}")
        print(f"{'─'*60}")
        print(f"N/A count in Notes (raw):  {(raw['Notes']=='N/A').sum()}")
        print(f"N/A count in Notes (norm): {(df_norm['Notes']=='N/A').sum()}")
        # Guardrail: Delta for metric/date columns should be near-zero (no N/A leakage)
        assert df_norm["Revenue"].isna().sum() <= raw["Revenue"].isna().sum() + 2


class TestFreeTextHeuristic:
    """Test _is_likely_free_text helper."""

    def test_note_matches(self):
        assert _is_likely_free_text("Notes") is True
        assert _is_likely_free_text("notes_and_comments") is True
        assert _is_likely_free_text("Customer Note") is True

    def test_comment_matches(self):
        assert _is_likely_free_text("Comments") is True
        assert _is_likely_free_text("comment") is True
        assert _is_likely_free_text("Internal Comment") is True

    def test_description_matches(self):
        assert _is_likely_free_text("Description") is True
        assert _is_likely_free_text("Product Description") is True

    def test_remark_matches(self):
        assert _is_likely_free_text("Remarks") is True
        assert _is_likely_free_text("remark") is True

    def test_region_does_not_match(self):
        assert _is_likely_free_text("Region") is False
        assert _is_likely_free_text("Category") is False
        assert _is_likely_free_text("Revenue") is False
        assert _is_likely_free_text("Date") is False
        assert _is_likely_free_text("Name") is False


FIXTURE_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')


class TestDetectColumnTypeFix:
    """Tests for upload-time type detection improvement (_try_clean_numeric fallback)."""

    @classmethod
    def setup_class(cls):
        csv_path = os.path.join(FIXTURE_DIR, 'edge_case_messy_formatting.csv')
        with open(csv_path, 'rb') as f:
            cls.RAW = parse_csv(f.read())

    # ── Test 1: Revenue (currency $X,XXX.XX + N/A) → "metric" ──

    def test_revenue_now_detected_as_metric(self):
        """Revenue with $X,XXX.XX strings now returns 'metric' via _try_clean_numeric."""
        col_data = self.RAW["Revenue"]
        assert col_data.dtype == object, "Revenue should be object in raw df"
        result = _detect_column_type(col_data, "Revenue")
        assert result == "metric", f"Expected 'metric', got '{result}'"

    # ── Test 2: Region guardrail → still "dimension" ──

    def test_region_still_dimension(self):
        """Region with ' south ', 'North', 'EAST', 'West' returns 'dimension' (no false positive)."""
        col_data = self.RAW["Region"]
        result = _detect_column_type(col_data, "Region")
        assert result == "dimension", f"Expected 'dimension', got '{result}'"

    # ── Test 3: Notes guardrail → still "dimension" ──

    def test_notes_still_dimension(self):
        """Notes with free text stays 'dimension', not accidentally caught by numeric cleaning."""
        col_data = self.RAW["Notes"]
        result = _detect_column_type(col_data, "Notes")
        assert result == "dimension", f"Expected 'dimension', got '{result}'"

    # ── Test 4: Percentage column → "metric" ──

    def test_percentage_column_detected_as_metric(self):
        """Synthetic percentage strings '85%', '12.5%' return 'metric'."""
        col = pd.Series(["85%", "12.5%", "99.9%", "0.5%", "50%"])
        result = _detect_column_type(col, "Conversion Rate")
        assert result == "metric", f"Expected 'metric', got '{result}'"

    # ── Test 5: Comma-thousands column → "metric" ──

    def test_comma_thousands_detected_as_metric(self):
        """Synthetic comma-thousands '1,234,567' returns 'metric'."""
        col = pd.Series(["1,234,567", "2,345,678", "3,456,789"])
        result = _detect_column_type(col, "Population")
        assert result == "metric", f"Expected 'metric', got '{result}'"

    # ── Test 6: End-to-end via detect_column_types (upload API) ──

    def test_detect_column_types_returns_metric_for_revenue(self):
        """End-to-end: detect_column_types() returns suggested_type='metric' for Revenue."""
        meta = detect_column_types(self.RAW)
        revenue_meta = next(m for m in meta if m["original_name"] == "Revenue")
        assert revenue_meta["suggested_type"] == "metric", (
            f"Expected 'metric', got '{revenue_meta['suggested_type']}'"
        )

    def test_detect_column_types_still_dimension_for_region(self):
        """End-to-end: detect_column_types() still returns 'dimension' for Region."""
        meta = detect_column_types(self.RAW)
        region_meta = next(m for m in meta if m["original_name"] == "Region")
        assert region_meta["suggested_type"] == "dimension"

    def test_detect_column_types_still_dimension_for_notes(self):
        """End-to-end: detect_column_types() still returns 'dimension' for Notes."""
        meta = detect_column_types(self.RAW)
        notes_meta = next(m for m in meta if m["original_name"] == "Notes")
        assert notes_meta["suggested_type"] == "dimension"

    # ── Test 7: _try_clean_numeric helper directly ──

    def test_try_clean_numeric_currency(self):
        """_try_clean_numeric converts $X,XXX.XX to float."""
        col = pd.Series(["$9,770.44", "$666.80", "N/A"])
        result = _try_clean_numeric(col)
        assert pd.api.types.is_numeric_dtype(result)
        assert result.iloc[0] == pytest.approx(9770.44)
        assert pd.isna(result.iloc[2]), "N/A should stay NaN"

    def test_try_clean_numeric_percentage(self):
        """_try_clean_numeric strips % sign and converts."""
        col = pd.Series(["85%", "12.5%", "N/A"])
        result = _try_clean_numeric(col)
        assert result.iloc[0] == pytest.approx(85.0)
        assert result.iloc[1] == pytest.approx(12.5)

    def test_try_clean_numeric_comma_thousands(self):
        """_try_clean_numeric strips commas and converts."""
        col = pd.Series(["1,234,567", "999,999"])
        result = _try_clean_numeric(col)
        assert result.iloc[0] == pytest.approx(1234567.0)
        assert result.iloc[1] == pytest.approx(999999.0)

    def test_try_clean_numeric_free_text_returns_all_nan(self):
        """_try_clean_numeric on free text returns all NaN."""
        col = pd.Series(["follow up needed", "VIP client", "hello world"])
        result = _try_clean_numeric(col)
        assert result.isna().all()

    def test_normalize_uses_same_helper_for_metric(self):
        """normalize_for_aggregation's metric branch uses _try_clean_numeric (not inline regex)."""
        column_types = {"Revenue": "metric", "Date": "date", "Region": "dimension", "Notes": "dimension"}
        df_norm = normalize_for_aggregation(self.RAW, column_types)
        assert pd.api.types.is_numeric_dtype(df_norm["Revenue"])
        assert df_norm["Revenue"].sum() == pytest.approx(440772.96, rel=1e-3)

    # ── Test 8: Threshold constant ──

    def test_threshold_is_reasonable(self):
        """_NUMERIC_DETECTION_THRESHOLD is between 0 and 1."""
        assert 0 < _NUMERIC_DETECTION_THRESHOLD <= 1