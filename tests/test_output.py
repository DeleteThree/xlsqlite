"""
Tests for output.py module.

Tests all output formatting and type conversion functions.
"""

import pytest
import pandas as pd
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import ExecutionResult first
from executor import ExecutionResult

# Patch sys.modules to handle relative import
import importlib
import types

# Create a fake parent module to make relative imports work
fake_parent = types.ModuleType('__fake_parent__')
sys.modules['__fake_parent__'] = fake_parent

# Import executor into the fake parent
fake_parent.executor = importlib.import_module('executor')

# Now read and modify output.py to use absolute import
output_file = os.path.join(os.path.dirname(__file__), "output.py")
with open(output_file, 'r') as f:
    output_code = f.read()

# Replace relative import with absolute
output_code = output_code.replace('from .executor import ExecutionResult', 'from executor import ExecutionResult')

# Execute the modified code
output_module = types.ModuleType('output')
exec(output_code, output_module.__dict__)

# Import functions from the module
format_result = output_module.format_result
convert_types_for_excel = output_module.convert_types_for_excel
handle_null_display = output_module.handle_null_display
format_for_debug = output_module.format_for_debug
result_to_list_of_lists = output_module.result_to_list_of_lists
estimate_output_size = output_module.estimate_output_size
check_output_limits = output_module.check_output_limits
EXCEL_MAX_ROWS = output_module.EXCEL_MAX_ROWS
EXCEL_MAX_COLS = output_module.EXCEL_MAX_COLS
RECOMMENDED_MAX_ROWS = output_module.RECOMMENDED_MAX_ROWS


class TestFormatResult:
    """Tests for format_result() function."""

    def test_select_query_with_data(self):
        result = ExecutionResult(
            columns=["id", "name", "value"],
            rows=[(1, "Alice", 100.5), (2, "Bob", 200.0)],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=5.0,
            query_type="SELECT"
        )

        df = format_result(result, include_headers=True)

        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["id", "name", "value"]
        assert len(df) == 2
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[1]["name"] == "Bob"

    def test_empty_select_query(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=0,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        df = format_result(result, include_headers=True)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_insert_query(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=3,
            lastrowid=10,
            execution_time_ms=2.0,
            query_type="INSERT"
        )

        df = format_result(result, include_headers=True)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["Result"] == "3 rows affected"

    def test_update_query(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=5,
            lastrowid=None,
            execution_time_ms=3.0,
            query_type="UPDATE"
        )

        df = format_result(result, include_headers=True)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["Result"] == "5 rows affected"

    def test_delete_query(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=1.5,
            query_type="DELETE"
        )

        df = format_result(result, include_headers=True)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["Result"] == "2 rows affected"

    def test_create_query(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=0,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="CREATE"
        )

        df = format_result(result, include_headers=True)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["Result"] == "OK"

    def test_drop_query(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=0,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="DROP"
        )

        df = format_result(result, include_headers=True)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["Result"] == "OK"

    def test_with_include_headers_true(self):
        result = ExecutionResult(
            columns=["col1", "col2"],
            rows=[(1, 2), (3, 4)],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        df = format_result(result, include_headers=True)

        # Headers should be the column names
        assert list(df.columns) == ["col1", "col2"]

    def test_with_include_headers_false(self):
        result = ExecutionResult(
            columns=["col1", "col2"],
            rows=[(1, 2), (3, 4)],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        df = format_result(result, include_headers=False)

        # Headers should still be set (parameter name is misleading)
        assert list(df.columns) == ["col1", "col2"]

    def test_type_conversion_applied(self):
        result = ExecutionResult(
            columns=["int_col", "float_col", "text_col"],
            rows=[(1, 1.5, "text"), (2, 2.5, "more")],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        df = format_result(result, include_headers=True)

        # Should convert types appropriately
        assert df["int_col"].dtype in [int, 'Int64']
        assert df["float_col"].dtype == float


class TestConvertTypesForExcel:
    """Tests for convert_types_for_excel() function."""

    def test_integers_preserved(self):
        df = pd.DataFrame({"col": [1, 2, 3, 4, 5]})
        result = convert_types_for_excel(df)

        assert result["col"].dtype in [int, 'int64', 'Int64']

    def test_floats_preserved(self):
        df = pd.DataFrame({"col": [1.5, 2.7, 3.9]})
        result = convert_types_for_excel(df)

        assert result["col"].dtype == float

    def test_strings_preserved(self):
        df = pd.DataFrame({"col": ["a", "b", "c"]})
        result = convert_types_for_excel(df)

        assert result["col"].dtype == object

    def test_mixed_numeric_types(self):
        df = pd.DataFrame({
            "integers": [1, 2, 3],
            "floats": [1.1, 2.2, 3.3],
            "strings": ["a", "b", "c"]
        })
        result = convert_types_for_excel(df)

        assert result["integers"].dtype in [int, 'int64', 'Int64']
        assert result["floats"].dtype == float
        assert result["strings"].dtype == object

    def test_null_values_preserved(self):
        df = pd.DataFrame({"col": [1, None, 3]})
        result = convert_types_for_excel(df)

        # Should use nullable integer type
        assert pd.isna(result.iloc[1]["col"])

    def test_all_null_column(self):
        df = pd.DataFrame({"col": [None, None, None]})
        result = convert_types_for_excel(df)

        # Should skip conversion for all-null columns
        assert result["col"].isna().all()

    def test_integers_as_floats_converted(self):
        # Floats that are actually integers
        df = pd.DataFrame({"col": [1.0, 2.0, 3.0]})
        result = convert_types_for_excel(df)

        # Should convert to integer type
        assert result["col"].dtype in [int, 'int64', 'Int64']

    def test_mixed_int_and_float(self):
        df = pd.DataFrame({"col": [1, 2.5, 3]})
        result = convert_types_for_excel(df)

        # Should stay as float since not all are integers
        assert result["col"].dtype == float

    def test_mixed_types_stay_mixed(self):
        df = pd.DataFrame({"col": [1, "text", 3]})
        result = convert_types_for_excel(df)

        # Should keep as object type
        assert result["col"].dtype == object

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = convert_types_for_excel(df)

        assert len(result) == 0

    def test_dataframe_not_modified(self):
        df = pd.DataFrame({"col": [1, 2, 3]})
        original_dtype = df["col"].dtype
        result = convert_types_for_excel(df)

        # Original should not be modified
        assert df["col"].dtype == original_dtype

    def test_multiple_columns_with_nulls(self):
        df = pd.DataFrame({
            "int_col": [1, None, 3],
            "float_col": [1.5, 2.5, None],
            "text_col": ["a", None, "c"]
        })
        result = convert_types_for_excel(df)

        # All should preserve nulls
        assert pd.isna(result.iloc[1]["int_col"])
        assert pd.isna(result.iloc[2]["float_col"])
        assert pd.isna(result.iloc[1]["text_col"])


class TestHandleNullDisplay:
    """Tests for handle_null_display() function."""

    def test_default_keeps_none(self):
        df = pd.DataFrame({"col": [1, None, 3]})
        result = handle_null_display(df)

        assert pd.isna(result.iloc[1]["col"])

    def test_with_null_repr_string(self):
        df = pd.DataFrame({"col": [1, None, 3]})
        result = handle_null_display(df, null_repr="NULL")

        assert result.iloc[1]["col"] == "NULL"

    def test_with_empty_string_repr(self):
        df = pd.DataFrame({"col": [1, None, 3]})
        result = handle_null_display(df, null_repr="")

        assert result.iloc[1]["col"] == ""

    def test_with_custom_repr(self):
        df = pd.DataFrame({"col": [1, None, 3]})
        result = handle_null_display(df, null_repr="N/A")

        assert result.iloc[1]["col"] == "N/A"

    def test_multiple_columns(self):
        df = pd.DataFrame({
            "col1": [1, None, 3],
            "col2": ["a", None, "c"]
        })
        result = handle_null_display(df, null_repr="EMPTY")

        assert result.iloc[1]["col1"] == "EMPTY"
        assert result.iloc[1]["col2"] == "EMPTY"

    def test_no_nulls(self):
        df = pd.DataFrame({"col": [1, 2, 3]})
        result = handle_null_display(df, null_repr="NULL")

        # Should not add any "NULL" strings
        assert "NULL" not in result["col"].values


class TestFormatForDebug:
    """Tests for format_for_debug() function."""

    def test_select_query(self):
        result = ExecutionResult(
            columns=["id", "name"],
            rows=[(1, "Alice"), (2, "Bob")],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=5.5,
            query_type="SELECT"
        )

        debug_str = format_for_debug(result)

        assert "Query type: SELECT" in debug_str
        assert "Execution time: 5.50ms" in debug_str
        assert "Columns: id, name" in debug_str
        assert "Row count: 2" in debug_str

    def test_insert_query(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=3,
            lastrowid=42,
            execution_time_ms=2.3,
            query_type="INSERT"
        )

        debug_str = format_for_debug(result)

        assert "Query type: INSERT" in debug_str
        assert "Execution time: 2.30ms" in debug_str
        assert "Rows affected: 3" in debug_str
        assert "Last row ID: 42" in debug_str

    def test_many_rows_shows_sample(self):
        rows = [(i, f"name{i}") for i in range(10)]
        result = ExecutionResult(
            columns=["id", "name"],
            rows=rows,
            rowcount=10,
            lastrowid=None,
            execution_time_ms=10.0,
            query_type="SELECT"
        )

        debug_str = format_for_debug(result)

        assert "Sample rows:" in debug_str
        assert "... (5 more rows)" in debug_str

    def test_few_rows_shows_all(self):
        result = ExecutionResult(
            columns=["id"],
            rows=[(1,), (2,), (3,)],
            rowcount=3,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        debug_str = format_for_debug(result)

        assert "Sample rows:" in debug_str
        assert "..." not in debug_str  # No truncation for 3 rows


class TestResultToListOfLists:
    """Tests for result_to_list_of_lists() function."""

    def test_with_headers(self):
        result = ExecutionResult(
            columns=["id", "name"],
            rows=[(1, "Alice"), (2, "Bob")],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        lists = result_to_list_of_lists(result, include_headers=True)

        assert lists[0] == ["id", "name"]
        assert lists[1] == [1, "Alice"]
        assert lists[2] == [2, "Bob"]
        assert len(lists) == 3

    def test_without_headers(self):
        result = ExecutionResult(
            columns=["id", "name"],
            rows=[(1, "Alice"), (2, "Bob")],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        lists = result_to_list_of_lists(result, include_headers=False)

        assert lists[0] == [1, "Alice"]
        assert lists[1] == [2, "Bob"]
        assert len(lists) == 2

    def test_empty_result(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=0,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        lists = result_to_list_of_lists(result, include_headers=True)

        assert lists == []

    def test_single_row(self):
        result = ExecutionResult(
            columns=["value"],
            rows=[(42,)],
            rowcount=1,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        lists = result_to_list_of_lists(result, include_headers=True)

        assert lists[0] == ["value"]
        assert lists[1] == [42]

    def test_tuples_converted_to_lists(self):
        result = ExecutionResult(
            columns=["a", "b"],
            rows=[(1, 2), (3, 4)],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        lists = result_to_list_of_lists(result, include_headers=False)

        assert isinstance(lists[0], list)
        assert isinstance(lists[1], list)


class TestEstimateOutputSize:
    """Tests for estimate_output_size() function."""

    def test_basic_calculation(self):
        result = ExecutionResult(
            columns=["a", "b", "c"],
            rows=[(1, 2, 3), (4, 5, 6)],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        size = estimate_output_size(result)

        assert size["row_count"] == 2
        assert size["column_count"] == 3
        assert size["cell_count"] == 6

    def test_large_result(self):
        rows = [(i,) for i in range(1000)]
        result = ExecutionResult(
            columns=["id"],
            rows=rows,
            rowcount=1000,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        size = estimate_output_size(result)

        assert size["row_count"] == 1000
        assert size["column_count"] == 1
        assert size["cell_count"] == 1000

    def test_empty_result(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=0,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        size = estimate_output_size(result)

        assert size["row_count"] == 0
        assert size["column_count"] == 0
        assert size["cell_count"] == 0


class TestCheckOutputLimits:
    """Tests for check_output_limits() function."""

    def test_small_result_no_warning(self):
        result = ExecutionResult(
            columns=["a", "b"],
            rows=[(i, i*2) for i in range(100)],
            rowcount=100,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        warning = check_output_limits(result)

        assert warning is None

    def test_exceeds_recommended_max(self):
        rows = [(i,) for i in range(RECOMMENDED_MAX_ROWS + 1000)]
        result = ExecutionResult(
            columns=["id"],
            rows=rows,
            rowcount=len(rows),
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        warning = check_output_limits(result)

        assert warning is not None
        assert "Warning" in warning
        assert "Consider using LIMIT clause" in warning
        # Number is formatted with commas (e.g., "101,000")
        assert f"{len(rows):,}" in warning

    def test_exceeds_excel_max_rows(self):
        # Create a result that exceeds Excel's row limit
        result = ExecutionResult(
            columns=["id"],
            rows=[(i,) for i in range(EXCEL_MAX_ROWS + 100)],
            rowcount=EXCEL_MAX_ROWS + 100,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        warning = check_output_limits(result)

        assert warning is not None
        assert "exceeding Excel's limit" in warning
        assert "Use LIMIT clause" in warning

    def test_exceeds_excel_max_cols(self):
        # Create many columns
        columns = [f"col{i}" for i in range(EXCEL_MAX_COLS + 10)]
        result = ExecutionResult(
            columns=columns,
            rows=[(i for i in range(len(columns)))],
            rowcount=1,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        warning = check_output_limits(result)

        assert warning is not None
        assert "columns" in warning
        assert "exceeding Excel's limit" in warning

    def test_at_recommended_limit_no_warning(self):
        rows = [(i,) for i in range(RECOMMENDED_MAX_ROWS)]
        result = ExecutionResult(
            columns=["id"],
            rows=rows,
            rowcount=len(rows),
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        warning = check_output_limits(result)

        # Should not warn at exactly the limit
        assert warning is None

    def test_empty_result_no_warning(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=0,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        warning = check_output_limits(result)

        assert warning is None


class TestOutputConstants:
    """Tests for output module constants."""

    def test_excel_limits_defined(self):
        assert EXCEL_MAX_ROWS == 1_048_576
        assert EXCEL_MAX_COLS == 16_384
        assert RECOMMENDED_MAX_ROWS == 100_000

    def test_recommended_less_than_max(self):
        assert RECOMMENDED_MAX_ROWS < EXCEL_MAX_ROWS


class TestIntegrationScenarios:
    """Integration tests combining multiple output functions."""

    def test_complete_select_workflow(self):
        # Simulate a complete query result workflow
        result = ExecutionResult(
            columns=["id", "name", "value"],
            rows=[(1, "Alice", 100), (2, "Bob", 200), (3, None, 300)],
            rowcount=3,
            lastrowid=None,
            execution_time_ms=5.5,
            query_type="SELECT"
        )

        # Format for Excel
        df = format_result(result, include_headers=True)
        assert len(df) == 3

        # Check limits
        warning = check_output_limits(result)
        assert warning is None

        # Estimate size
        size = estimate_output_size(result)
        assert size["cell_count"] == 9

    def test_complete_dml_workflow(self):
        result = ExecutionResult(
            columns=[],
            rows=[],
            rowcount=5,
            lastrowid=10,
            execution_time_ms=2.0,
            query_type="INSERT"
        )

        df = format_result(result, include_headers=True)
        assert "rows affected" in df.iloc[0]["Result"]

        debug = format_for_debug(result)
        assert "INSERT" in debug
        assert "Last row ID: 10" in debug

    def test_type_conversion_integration(self):
        result = ExecutionResult(
            columns=["int_val", "float_val", "text_val"],
            rows=[(1, 1.5, "a"), (2, 2.5, "b")],
            rowcount=2,
            lastrowid=None,
            execution_time_ms=1.0,
            query_type="SELECT"
        )

        df = format_result(result, include_headers=True)

        # Verify types are converted appropriately
        assert df["int_val"].dtype in [int, 'int64', 'Int64']
        assert df["float_val"].dtype == float

        # Convert to lists
        lists = result_to_list_of_lists(result, include_headers=True)
        assert lists[0] == ["int_val", "float_val", "text_val"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
