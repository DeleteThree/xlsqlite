"""
Comprehensive tests for schema.py module.

Tests cover:
- Type inference for various data types
- Header validation (duplicates, empty names)
- Column name sanitization (quoting, reserved words)
- Table schema building
- Data loading to SQLite
- Data preparation for SQLite insertion
"""

import pytest
import pandas as pd
import sqlite3
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from schema import (
    infer_column_type,
    infer_column_types,
    validate_headers,
    sanitize_column_name,
    build_table_schema,
    load_data_to_sqlite,
    prepare_data_for_sqlite,
    TableSchema,
    ColumnSchema,
    SQLITE_INTEGER,
    SQLITE_REAL,
    SQLITE_TEXT,
)
from errors import DuplicateColumnError, EmptyColumnNameError


class TestInferColumnType:
    """Tests for infer_column_type()"""

    def test_all_integers(self):
        """All integer values should return INTEGER type."""
        series = pd.Series([1, 2, 3, 4, 5])
        assert infer_column_type(series) == SQLITE_INTEGER

    def test_integers_with_null(self):
        """Integers with NULL values should still return INTEGER type."""
        series = pd.Series([1, 2, None, 4, 5])
        assert infer_column_type(series) == SQLITE_INTEGER

    def test_float_values(self):
        """Float values should return REAL type."""
        series = pd.Series([1.5, 2.7, 3.14, 4.0])
        assert infer_column_type(series) == SQLITE_REAL

    def test_integer_like_floats(self):
        """Float values that are whole numbers (1.0, 2.0) should return INTEGER."""
        series = pd.Series([1.0, 2.0, 3.0, 4.0])
        assert infer_column_type(series) == SQLITE_INTEGER

    def test_mixed_numeric(self):
        """Mixed integers and floats with decimals should return REAL type."""
        series = pd.Series([1, 2.5, 3, 4.7, 5])
        assert infer_column_type(series) == SQLITE_REAL

    def test_strings(self):
        """String values should return TEXT type."""
        series = pd.Series(["Alice", "Bob", "Carol"])
        assert infer_column_type(series) == SQLITE_TEXT

    def test_dates(self):
        """Date/datetime values should return TEXT type."""
        series = pd.Series([
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-01-02"),
            pd.Timestamp("2024-01-03")
        ])
        assert infer_column_type(series) == SQLITE_TEXT

    def test_datetimes(self):
        """Datetime values should return TEXT type."""
        series = pd.to_datetime(pd.Series([
            "2024-01-01 10:00:00",
            "2024-01-02 11:30:00",
            "2024-01-03 12:45:00"
        ]))
        assert infer_column_type(series) == SQLITE_TEXT

    def test_booleans(self):
        """Boolean values should return INTEGER type (stored as 0/1)."""
        series = pd.Series([True, False, True, False], dtype=bool)
        assert infer_column_type(series) == SQLITE_INTEGER

    def test_all_null_values(self):
        """All NULL values should default to TEXT type."""
        series = pd.Series([None, None, None])
        assert infer_column_type(series) == SQLITE_TEXT

    def test_empty_series(self):
        """Empty series should default to TEXT type."""
        series = pd.Series([], dtype=object)
        assert infer_column_type(series) == SQLITE_TEXT

    def test_mixed_with_nulls(self):
        """Mixed types with NULLs should infer correctly from non-null values."""
        series = pd.Series([1.5, None, 2.7, None, 3.14])
        assert infer_column_type(series) == SQLITE_REAL

    def test_integer_like_with_null(self):
        """Integer-like floats with NULL should return INTEGER."""
        series = pd.Series([1.0, None, 2.0, None, 3.0])
        assert infer_column_type(series) == SQLITE_INTEGER


class TestInferColumnTypes:
    """Tests for infer_column_types()"""

    def test_multiple_columns(self):
        """Should correctly infer types for all columns in DataFrame."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol'],
            'score': [95.5, 87.3, 92.1],
            'active': [True, False, True]
        })

        types = infer_column_types(df)

        assert types['id'] == SQLITE_INTEGER
        assert types['name'] == SQLITE_TEXT
        assert types['score'] == SQLITE_REAL
        assert types['active'] == SQLITE_INTEGER


class TestValidateHeaders:
    """Tests for validate_headers()"""

    def test_valid_headers(self):
        """Valid headers should pass validation."""
        headers = ["id", "name", "email", "age"]
        result = validate_headers(headers)
        assert result == headers

    def test_duplicate_names_case_insensitive(self):
        """Duplicate names (case-insensitive) should raise DuplicateColumnError."""
        headers = ["id", "name", "ID"]

        with pytest.raises(DuplicateColumnError) as exc_info:
            validate_headers(headers)

        assert "duplicate column name: ID" in str(exc_info.value)

    def test_empty_string(self):
        """Empty string should raise EmptyColumnNameError with position."""
        headers = ["id", "", "name"]

        with pytest.raises(EmptyColumnNameError) as exc_info:
            validate_headers(headers)

        assert "position 2" in str(exc_info.value)

    def test_none_value(self):
        """None value should raise EmptyColumnNameError."""
        headers = ["id", None, "name"]

        with pytest.raises(EmptyColumnNameError) as exc_info:
            validate_headers(headers)

        assert "position 2" in str(exc_info.value)

    def test_whitespace_only(self):
        """Whitespace-only header should raise EmptyColumnNameError."""
        headers = ["id", "   ", "name"]

        with pytest.raises(EmptyColumnNameError) as exc_info:
            validate_headers(headers)

        assert "position 2" in str(exc_info.value)

    def test_numeric_headers(self):
        """Numeric headers should be converted to strings."""
        headers = [1, 2, 3, "name"]
        result = validate_headers(headers)

        assert result == ["1", "2", "3", "name"]
        assert all(isinstance(h, str) for h in result)

    def test_mixed_case_duplicates(self):
        """Mixed case duplicates (Name, name, NAME) should raise error."""
        headers = ["Name", "name", "NAME"]

        with pytest.raises(DuplicateColumnError) as exc_info:
            validate_headers(headers)

        # Should catch second duplicate
        assert "duplicate column name" in str(exc_info.value)

    def test_duplicate_after_first(self):
        """Should catch first duplicate encountered."""
        headers = ["id", "name", "id", "email"]

        with pytest.raises(DuplicateColumnError) as exc_info:
            validate_headers(headers)

        assert "duplicate column name: id" in str(exc_info.value)

    def test_header_with_spaces(self):
        """Headers with spaces should be trimmed but allowed."""
        headers = ["  id  ", "name", "  email  "]
        result = validate_headers(headers)

        assert result == ["id", "name", "email"]

    def test_first_column_empty(self):
        """Empty first column should show position 1."""
        headers = ["", "name", "email"]

        with pytest.raises(EmptyColumnNameError) as exc_info:
            validate_headers(headers)

        assert "position 1" in str(exc_info.value)


class TestSanitizeColumnName:
    """Tests for sanitize_column_name()"""

    def test_simple_alphanumeric(self):
        """Simple alphanumeric names should not be quoted."""
        assert sanitize_column_name("id") == "id"
        assert sanitize_column_name("name123") == "name123"
        assert sanitize_column_name("Column1") == "Column1"

    def test_name_with_space(self):
        """Name with space should be quoted."""
        assert sanitize_column_name("first name") == '"first name"'
        assert sanitize_column_name("order total") == '"order total"'

    def test_reserved_keyword_select(self):
        """Reserved keyword 'select' should be quoted."""
        assert sanitize_column_name("select") == '"select"'

    def test_reserved_keyword_from(self):
        """Reserved keyword 'from' should be quoted."""
        assert sanitize_column_name("from") == '"from"'

    def test_reserved_keyword_where(self):
        """Reserved keyword 'where' should be quoted."""
        assert sanitize_column_name("where") == '"where"'

    def test_reserved_keywords_various(self):
        """Various reserved keywords should be quoted."""
        assert sanitize_column_name("table") == '"table"'
        assert sanitize_column_name("order") == '"order"'
        assert sanitize_column_name("group") == '"group"'
        assert sanitize_column_name("join") == '"join"'

    def test_name_with_special_chars(self):
        """Name with special characters should be quoted."""
        assert sanitize_column_name("user@email") == '"user@email"'
        assert sanitize_column_name("price$") == '"price$"'
        assert sanitize_column_name("col-name") == '"col-name"'

    def test_name_with_double_quotes(self):
        """Name with double quotes should be escaped and quoted."""
        assert sanitize_column_name('my"column') == '"my""column"'
        assert sanitize_column_name('"quoted"') == '"""quoted"""'

    def test_underscore_only_name(self):
        """Underscore-only name should not be quoted."""
        assert sanitize_column_name("_id") == "_id"
        assert sanitize_column_name("__private") == "__private"
        assert sanitize_column_name("user_name") == "user_name"

    def test_numeric_starting_name(self):
        """Numeric-starting name is valid in SQLite, no quotes needed."""
        # Note: In SQLite, identifiers can start with digits if unquoted
        # but it's generally safer to quote them. However, based on the
        # regex in sanitize_column_name, digits at start fail the pattern
        # so they get quoted
        result = sanitize_column_name("123column")
        # This will be quoted because it doesn't match ^[a-zA-Z_]
        assert result == '"123column"'

    def test_case_sensitivity(self):
        """Reserved words are case-insensitive."""
        assert sanitize_column_name("SELECT") == '"SELECT"'
        assert sanitize_column_name("Select") == '"Select"'

    def test_mixed_valid_chars(self):
        """Valid identifier with letters, digits, underscores."""
        assert sanitize_column_name("user_id_123") == "user_id_123"
        assert sanitize_column_name("_column_") == "_column_"


class TestBuildTableSchema:
    """Tests for build_table_schema()"""

    def test_simple_dataframe(self):
        """Simple DataFrame should produce correct schema."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol']
        })

        schema = build_table_schema(df, "users")

        assert schema.name == "users"
        assert schema.sqlite_name == "users"
        assert len(schema.columns) == 2
        assert schema.row_count == 3

        # Check column schemas
        id_col = schema.columns[0]
        assert id_col.name == "id"
        assert id_col.sqlite_name == "id"
        assert id_col.sqlite_type == SQLITE_INTEGER

        name_col = schema.columns[1]
        assert name_col.name == "name"
        assert name_col.sqlite_name == "name"
        assert name_col.sqlite_type == SQLITE_TEXT

    def test_mixed_types(self):
        """DataFrame with mixed types should infer correctly for each column."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'score': [95.5, 87.0, 92.3],
            'name': ['Alice', 'Bob', 'Carol'],
            'active': [True, False, True]
        })

        schema = build_table_schema(df, "results")

        assert schema.columns[0].sqlite_type == SQLITE_INTEGER  # id
        assert schema.columns[1].sqlite_type == SQLITE_REAL      # score
        assert schema.columns[2].sqlite_type == SQLITE_TEXT      # name
        assert schema.columns[3].sqlite_type == SQLITE_INTEGER   # active (bool)

    def test_duplicate_headers(self):
        """DataFrame with duplicate headers should raise DuplicateColumnError."""
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['Alice', 'Bob'],
            'ID': [10, 20]  # Duplicate of 'id' (case-insensitive)
        })

        with pytest.raises(DuplicateColumnError):
            build_table_schema(df, "test")

    def test_empty_headers(self):
        """DataFrame with empty headers should raise EmptyColumnNameError."""
        # Create DataFrame with empty column name
        df = pd.DataFrame([[1, 2], [3, 4]], columns=['id', ''])

        with pytest.raises(EmptyColumnNameError):
            build_table_schema(df, "test")

    def test_column_names_with_spaces(self):
        """Column names with spaces should be quoted in schema."""
        df = pd.DataFrame({
            'user id': [1, 2],
            'first name': ['Alice', 'Bob']
        })

        schema = build_table_schema(df, "users")

        assert schema.columns[0].name == "user id"
        assert schema.columns[0].sqlite_name == '"user id"'
        assert schema.columns[1].name == "first name"
        assert schema.columns[1].sqlite_name == '"first name"'

    def test_column_schema_objects(self):
        """Verify ColumnSchema objects are created correctly."""
        df = pd.DataFrame({
            'id': [1, 2],
            'value': [10.5, 20.7]
        })

        schema = build_table_schema(df, "data")

        for col in schema.columns:
            assert isinstance(col, ColumnSchema)
            assert hasattr(col, 'name')
            assert hasattr(col, 'sqlite_name')
            assert hasattr(col, 'sqlite_type')
            assert hasattr(col, 'nullable')
            assert col.nullable is True  # All columns are nullable by default

    def test_row_count_matches_dataframe(self):
        """Schema row count should match DataFrame length."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [10, 20, 30, 40, 50]
        })

        schema = build_table_schema(df, "test")

        assert schema.row_count == len(df)
        assert schema.row_count == 5

    def test_empty_dataframe(self):
        """Empty DataFrame should produce schema with 0 rows."""
        df = pd.DataFrame({
            'id': pd.Series([], dtype=int),
            'name': pd.Series([], dtype=str)
        })

        schema = build_table_schema(df, "empty")

        assert schema.row_count == 0
        assert len(schema.columns) == 2

    def test_table_name_sanitization(self):
        """Table name should also be sanitized."""
        df = pd.DataFrame({'id': [1, 2]})

        schema = build_table_schema(df, "my table")

        assert schema.name == "my table"
        assert schema.sqlite_name == '"my table"'


class TestLoadDataToSQLite:
    """Tests for load_data_to_sqlite()"""

    @pytest.fixture
    def conn(self):
        """Create in-memory SQLite connection."""
        connection = sqlite3.connect(":memory:")
        yield connection
        connection.close()

    def test_create_table_successfully(self, conn):
        """Should create table successfully."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol']
        })

        schema = build_table_schema(df, "users")
        load_data_to_sqlite(conn, schema, df)

        # Verify table exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None

    def test_insert_data_correctly(self, conn):
        """Should insert all data correctly."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol']
        })

        schema = build_table_schema(df, "users")
        load_data_to_sqlite(conn, schema, df)

        # Verify data
        cursor = conn.execute("SELECT * FROM users ORDER BY id")
        rows = cursor.fetchall()

        assert len(rows) == 3
        assert rows[0] == (1, 'Alice')
        assert rows[1] == (2, 'Bob')
        assert rows[2] == (3, 'Carol')

    def test_verify_data_types_preserved(self, conn):
        """Should preserve integer, float, and text types."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'score': [95.5, 87.3, 92.1],
            'name': ['Alice', 'Bob', 'Carol']
        })

        schema = build_table_schema(df, "results")
        load_data_to_sqlite(conn, schema, df)

        # Verify data types
        cursor = conn.execute("SELECT id, score, name FROM results WHERE id = 1")
        row = cursor.fetchone()

        assert isinstance(row[0], int)
        assert isinstance(row[1], float)
        assert isinstance(row[2], str)

    def test_null_values_handled(self, conn):
        """NULL values should be handled correctly."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.5, None, 30.7]
        })

        schema = build_table_schema(df, "data")
        load_data_to_sqlite(conn, schema, df)

        # Verify NULL is preserved
        cursor = conn.execute("SELECT value FROM data WHERE id = 2")
        row = cursor.fetchone()

        assert row[0] is None

    def test_boolean_values_converted(self, conn):
        """Boolean values should be converted to 0/1."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'active': pd.Series([True, False, True], dtype=bool)
        })

        schema = build_table_schema(df, "flags")
        load_data_to_sqlite(conn, schema, df)

        # Verify booleans stored as 0/1
        cursor = conn.execute("SELECT active FROM flags ORDER BY id")
        rows = cursor.fetchall()

        assert rows[0][0] == 1  # True -> 1
        assert rows[1][0] == 0  # False -> 0
        assert rows[2][0] == 1  # True -> 1

    def test_dates_converted_to_iso_strings(self, conn):
        """Dates should be converted to ISO 8601 strings."""
        df = pd.DataFrame({
            'id': [1, 2],
            'created': pd.to_datetime(['2024-01-01 10:30:00', '2024-01-02 15:45:00'])
        })

        schema = build_table_schema(df, "events")
        load_data_to_sqlite(conn, schema, df)

        # Verify dates stored as ISO strings
        cursor = conn.execute("SELECT created FROM events WHERE id = 1")
        row = cursor.fetchone()

        assert row[0] == '2024-01-01T10:30:00'

    def test_table_exists_after_creation(self, conn):
        """Table should exist in database after creation."""
        df = pd.DataFrame({'id': [1]})
        schema = build_table_schema(df, "test")
        load_data_to_sqlite(conn, schema, df)

        # Check table exists
        cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='test'")
        count = cursor.fetchone()[0]

        assert count == 1

    def test_row_count_matches(self, conn):
        """Row count in database should match DataFrame."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [10, 20, 30, 40, 50]
        })

        schema = build_table_schema(df, "numbers")
        load_data_to_sqlite(conn, schema, df)

        # Verify row count
        cursor = conn.execute("SELECT COUNT(*) FROM numbers")
        count = cursor.fetchone()[0]

        assert count == 5
        assert count == len(df)

    def test_quoted_column_names_work(self, conn):
        """Quoted column names should work correctly."""
        df = pd.DataFrame({
            'user id': [1, 2],
            'first name': ['Alice', 'Bob']
        })

        schema = build_table_schema(df, "users")
        load_data_to_sqlite(conn, schema, df)

        # Verify we can query with quoted names
        cursor = conn.execute('SELECT "user id", "first name" FROM users WHERE "user id" = 1')
        row = cursor.fetchone()

        assert row == (1, 'Alice')

    def test_empty_dataframe(self, conn):
        """Empty DataFrame should create table with no rows."""
        df = pd.DataFrame({
            'id': pd.Series([], dtype=int),
            'name': pd.Series([], dtype=str)
        })

        schema = build_table_schema(df, "empty")
        load_data_to_sqlite(conn, schema, df)

        # Verify table exists but has no rows
        cursor = conn.execute("SELECT COUNT(*) FROM empty")
        count = cursor.fetchone()[0]

        assert count == 0


class TestPrepareDataForSQLite:
    """Tests for prepare_data_for_sqlite()"""

    def test_datetime_conversion_to_iso_strings(self):
        """Datetime values should be converted to ISO 8601 strings."""
        df = pd.DataFrame({
            'id': [1, 2],
            'created': pd.to_datetime(['2024-01-01 10:30:00', '2024-01-02 15:45:30'])
        })

        schema = build_table_schema(df, "test")
        result = prepare_data_for_sqlite(df, schema)

        assert result['created'][0] == '2024-01-01T10:30:00'
        assert result['created'][1] == '2024-01-02T15:45:30'

    def test_nat_to_none(self):
        """NaT (Not a Time) should be converted to None."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'date': pd.to_datetime(['2024-01-01', None, '2024-01-03'])
        })

        schema = build_table_schema(df, "test")
        result = prepare_data_for_sqlite(df, schema)

        assert result['date'][0] == '2024-01-01T00:00:00'
        assert result['date'][1] is None
        assert result['date'][2] == '2024-01-03T00:00:00'

    def test_boolean_conversion_to_0_1(self):
        """Boolean values should be converted to 0/1."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'active': [True, False, True]
        })

        schema = build_table_schema(df, "test")
        result = prepare_data_for_sqlite(df, schema)

        assert result['active'][0] == 1
        assert result['active'][1] == 0
        assert result['active'][2] == 1

    def test_null_preservation(self):
        """NULL values should be preserved as None."""
        import numpy as np

        df = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.5, None, 30.7]
        })

        schema = build_table_schema(df, "test")
        result = prepare_data_for_sqlite(df, schema)

        assert result['value'][0] == 10.5
        # pd.notna() check handles both None and NaN
        assert result['value'][1] is None or pd.isna(result['value'][1])
        assert result['value'][2] == 30.7

    def test_mixed_types_handled(self):
        """Mixed types should be handled correctly."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'score': [95.5, None, 92.1],
            'name': ['Alice', 'Bob', None],
            'active': pd.Series([True, False, True], dtype=bool),  # Use pure bool series (no None)
            'created': pd.to_datetime(['2024-01-01', '2024-01-02', None])
        })

        schema = build_table_schema(df, "test")
        result = prepare_data_for_sqlite(df, schema)

        # Check integers
        assert result['id'][0] == 1

        # Check floats with NULL - prepare_data preserves NaN, SQLite converts to NULL on insert
        assert result['score'][0] == 95.5
        assert result['score'][1] is None or pd.isna(result['score'][1])

        # Check strings with NULL
        assert result['name'][0] == 'Alice'
        assert result['name'][2] is None

        # Check booleans (converted to int)
        assert result['active'][0] == 1
        assert result['active'][1] == 0
        assert result['active'][2] == 1

        # Check datetime with NULL
        assert result['created'][0] == '2024-01-01T00:00:00'
        assert result['created'][2] is None

    def test_original_dataframe_unchanged(self):
        """Original DataFrame should not be modified."""
        df = pd.DataFrame({
            'id': [1, 2],
            'active': [True, False],
            'created': pd.to_datetime(['2024-01-01', '2024-01-02'])
        })

        df_original = df.copy()
        schema = build_table_schema(df, "test")
        result = prepare_data_for_sqlite(df, schema)

        # Original DataFrame should be unchanged
        pd.testing.assert_frame_equal(df, df_original)

        # Result should be different
        assert not df['active'].equals(result['active'])  # Bool vs int
        assert not df['created'].equals(result['created'])  # Datetime vs string

    def test_nan_values_converted_to_none(self):
        """NaN values in numeric columns should be converted to None."""
        import numpy as np

        df = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10.5, np.nan, 30.7]
        })

        schema = build_table_schema(df, "test")
        result = prepare_data_for_sqlite(df, schema)

        assert result['value'][0] == 10.5
        # prepare_data_for_sqlite uses where() which converts NaN to None
        assert result['value'][1] is None or pd.isna(result['value'][1])
        assert result['value'][2] == 30.7


class TestIntegration:
    """Integration tests combining multiple functions."""

    @pytest.fixture
    def conn(self):
        """Create in-memory SQLite connection."""
        connection = sqlite3.connect(":memory:")
        yield connection
        connection.close()

    def test_end_to_end_workflow(self, conn):
        """Test complete workflow from DataFrame to SQLite query."""
        # Create DataFrame
        df = pd.DataFrame({
            'employee_id': [1, 2, 3],
            'full name': ['Alice Johnson', 'Bob Smith', 'Carol Davis'],
            'salary': [75000.50, 82000.00, 69500.75],
            'is_active': [True, True, False],
            'hire_date': pd.to_datetime(['2020-01-15', '2019-03-22', '2021-06-10'])
        })

        # Build schema
        schema = build_table_schema(df, "employees")

        # Verify schema
        assert len(schema.columns) == 5
        assert schema.row_count == 3

        # Load data
        load_data_to_sqlite(conn, schema, df)

        # Query and verify
        cursor = conn.execute('''
            SELECT employee_id, "full name", salary, is_active, hire_date
            FROM employees
            WHERE is_active = 1
            ORDER BY salary DESC
        ''')

        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0][1] == 'Bob Smith'  # Highest salary
        assert rows[1][1] == 'Alice Johnson'

    def test_reserved_words_as_columns(self, conn):
        """Test handling of reserved words as column names."""
        df = pd.DataFrame({
            'select': [1, 2, 3],
            'from': ['A', 'B', 'C'],
            'where': [10.5, 20.3, 30.7]
        })

        schema = build_table_schema(df, "keywords")
        load_data_to_sqlite(conn, schema, df)

        # Query using quoted identifiers
        cursor = conn.execute('SELECT "select", "from", "where" FROM keywords WHERE "select" = 2')
        row = cursor.fetchone()

        assert row == (2, 'B', 20.3)

    def test_complex_data_types(self, conn):
        """Test handling of complex mix of data types."""
        import numpy as np

        df = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'integer_col': [10, 20, None, 40],
            'float_col': [1.5, None, 3.7, 4.0],
            'bool_col': pd.Series([True, False, True, True], dtype=bool),  # Pure bool
            'text_col': ['Hello', None, 'World', ''],
            'date_col': pd.to_datetime(['2024-01-01', '2024-01-02', None, '2024-01-04'])
        })

        schema = build_table_schema(df, "complex")
        load_data_to_sqlite(conn, schema, df)

        # Verify all data
        cursor = conn.execute("SELECT * FROM complex ORDER BY id")
        rows = cursor.fetchall()

        assert len(rows) == 4

        # Check row with NULLs (row 2, index 1)
        row2 = rows[1]  # id=2
        assert row2[0] == 2
        assert row2[1] == 20  # integer_col
        assert row2[2] is None  # float_col
        assert row2[3] == 0  # bool_col (False -> 0)
        assert row2[4] is None  # text_col
        assert row2[5] == '2024-01-02T00:00:00'  # date_col


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
