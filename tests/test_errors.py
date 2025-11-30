"""
Tests for errors.py module.

Tests all exception classes and error handling functions.
"""

import pytest
import sqlite3
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from errors import (
    SQLiteExcelError,
    TableNotFoundError,
    ColumnNotFoundError,
    DuplicateColumnError,
    EmptyColumnNameError,
    QuerySyntaxError,
    RangeResolutionError,
    EmptyRangeError,
    TypeInferenceError,
    ExecutionError,
    TimeoutError,
    OutputLimitError,
    normalize_sqlite_error,
    format_error_for_excel,
)


class TestSQLiteExcelError:
    """Tests for base SQLiteExcelError exception."""

    def test_message_with_error_prefix(self):
        error = SQLiteExcelError("something went wrong")
        assert str(error) == "Error: something went wrong"

    def test_message_attribute(self):
        error = SQLiteExcelError("test message")
        assert error.message == "test message"

    def test_string_representation(self):
        error = SQLiteExcelError("custom error")
        assert str(error) == "Error: custom error"

    def test_inherits_from_exception(self):
        error = SQLiteExcelError("test")
        assert isinstance(error, Exception)

    def test_can_be_raised(self):
        with pytest.raises(SQLiteExcelError) as exc_info:
            raise SQLiteExcelError("test error")
        assert str(exc_info.value) == "Error: test error"


class TestTableNotFoundError:
    """Tests for TableNotFoundError exception."""

    def test_message_format(self):
        error = TableNotFoundError("users")
        assert str(error) == "Error: no such table: users"

    def test_with_different_table_names(self):
        error1 = TableNotFoundError("orders")
        assert str(error1) == "Error: no such table: orders"

        error2 = TableNotFoundError("my_table")
        assert str(error2) == "Error: no such table: my_table"

    def test_inherits_from_sqlite_excel_error(self):
        error = TableNotFoundError("test")
        assert isinstance(error, SQLiteExcelError)

    def test_message_attribute(self):
        error = TableNotFoundError("products")
        assert error.message == "no such table: products"


class TestColumnNotFoundError:
    """Tests for ColumnNotFoundError exception."""

    def test_message_format(self):
        error = ColumnNotFoundError("email")
        assert str(error) == "Error: no such column: email"

    def test_with_different_column_names(self):
        error1 = ColumnNotFoundError("id")
        assert str(error1) == "Error: no such column: id"

        error2 = ColumnNotFoundError("total_price")
        assert str(error2) == "Error: no such column: total_price"

    def test_inherits_from_sqlite_excel_error(self):
        error = ColumnNotFoundError("test")
        assert isinstance(error, SQLiteExcelError)


class TestDuplicateColumnError:
    """Tests for DuplicateColumnError exception."""

    def test_message_format(self):
        error = DuplicateColumnError("id")
        assert str(error) == "Error: duplicate column name: id"

    def test_with_different_column_names(self):
        error1 = DuplicateColumnError("name")
        assert str(error1) == "Error: duplicate column name: name"

        error2 = DuplicateColumnError("Status")
        assert str(error2) == "Error: duplicate column name: Status"

    def test_inherits_from_sqlite_excel_error(self):
        error = DuplicateColumnError("test")
        assert isinstance(error, SQLiteExcelError)


class TestEmptyColumnNameError:
    """Tests for EmptyColumnNameError exception."""

    def test_with_position(self):
        error = EmptyColumnNameError(position=3)
        assert str(error) == "Error: column name cannot be empty (position 3)"

    def test_with_different_positions(self):
        error1 = EmptyColumnNameError(position=0)
        assert str(error1) == "Error: column name cannot be empty (position 0)"

        error2 = EmptyColumnNameError(position=10)
        assert str(error2) == "Error: column name cannot be empty (position 10)"

    def test_without_position(self):
        error = EmptyColumnNameError()
        assert str(error) == "Error: column name cannot be empty"

    def test_with_none_position(self):
        error = EmptyColumnNameError(position=None)
        assert str(error) == "Error: column name cannot be empty"

    def test_inherits_from_sqlite_excel_error(self):
        error = EmptyColumnNameError()
        assert isinstance(error, SQLiteExcelError)


class TestQuerySyntaxError:
    """Tests for QuerySyntaxError exception."""

    def test_with_near_token(self):
        error = QuerySyntaxError(near_token="FROM")
        assert str(error) == 'Error: near "FROM": syntax error'

    def test_with_different_tokens(self):
        error1 = QuerySyntaxError(near_token="SELECT")
        assert str(error1) == 'Error: near "SELECT": syntax error'

        error2 = QuerySyntaxError(near_token=";")
        assert str(error2) == 'Error: near ";": syntax error'

    def test_with_details(self):
        error = QuerySyntaxError(details="incomplete input")
        assert str(error) == "Error: incomplete input"

    def test_with_detailed_message(self):
        error = QuerySyntaxError(details="table name required")
        assert str(error) == "Error: table name required"

    def test_without_either(self):
        error = QuerySyntaxError()
        assert str(error) == "Error: syntax error"

    def test_near_token_takes_precedence(self):
        # When both are provided, near_token is used
        error = QuerySyntaxError(near_token="WHERE", details="ignored")
        assert 'near "WHERE"' in str(error)

    def test_inherits_from_sqlite_excel_error(self):
        error = QuerySyntaxError()
        assert isinstance(error, SQLiteExcelError)


class TestRangeResolutionError:
    """Tests for RangeResolutionError exception."""

    def test_with_reason(self):
        error = RangeResolutionError("A1:B10", reason="sheet not found")
        assert str(error) == "Error: cannot resolve range: A1:B10 (sheet not found)"

    def test_with_different_reasons(self):
        error1 = RangeResolutionError("Sheet1!A:A", reason="invalid reference")
        assert str(error1) == "Error: cannot resolve range: Sheet1!A:A (invalid reference)"

        error2 = RangeResolutionError("C5:D100", reason="circular reference")
        assert str(error2) == "Error: cannot resolve range: C5:D100 (circular reference)"

    def test_without_reason(self):
        error = RangeResolutionError("A1:Z100")
        assert str(error) == "Error: cannot resolve range: A1:Z100"

    def test_with_none_reason(self):
        error = RangeResolutionError("B2:C3", reason=None)
        assert str(error) == "Error: cannot resolve range: B2:C3"

    def test_inherits_from_sqlite_excel_error(self):
        error = RangeResolutionError("A1:A1")
        assert isinstance(error, SQLiteExcelError)


class TestEmptyRangeError:
    """Tests for EmptyRangeError exception."""

    def test_message_format(self):
        error = EmptyRangeError("A1:B10")
        assert str(error) == "Error: range contains no data: A1:B10"

    def test_with_different_ranges(self):
        error1 = EmptyRangeError("Sheet1!A:B")
        assert str(error1) == "Error: range contains no data: Sheet1!A:B"

        error2 = EmptyRangeError("C5:D5")
        assert str(error2) == "Error: range contains no data: C5:D5"

    def test_inherits_from_sqlite_excel_error(self):
        error = EmptyRangeError("A1:A1")
        assert isinstance(error, SQLiteExcelError)


class TestTypeInferenceError:
    """Tests for TypeInferenceError exception."""

    def test_with_reason(self):
        error = TypeInferenceError("age", reason="mixed types")
        assert str(error) == "Error: cannot infer type for column 'age': mixed types"

    def test_with_different_reasons(self):
        error1 = TypeInferenceError("price", reason="all null values")
        assert str(error1) == "Error: cannot infer type for column 'price': all null values"

        error2 = TypeInferenceError("status", reason="inconsistent format")
        assert str(error2) == "Error: cannot infer type for column 'status': inconsistent format"

    def test_without_reason(self):
        error = TypeInferenceError("column1")
        assert str(error) == "Error: cannot infer type for column 'column1'"

    def test_with_none_reason(self):
        error = TypeInferenceError("test", reason=None)
        assert str(error) == "Error: cannot infer type for column 'test'"

    def test_inherits_from_sqlite_excel_error(self):
        error = TypeInferenceError("col")
        assert isinstance(error, SQLiteExcelError)


class TestExecutionError:
    """Tests for ExecutionError exception."""

    def test_message_format(self):
        error = ExecutionError("constraint failed")
        assert str(error) == "Error: constraint failed"

    def test_with_different_messages(self):
        error1 = ExecutionError("foreign key constraint failed")
        assert str(error1) == "Error: foreign key constraint failed"

        error2 = ExecutionError("database is locked")
        assert str(error2) == "Error: database is locked"

    def test_inherits_from_sqlite_excel_error(self):
        error = ExecutionError("test")
        assert isinstance(error, SQLiteExcelError)


class TestTimeoutError:
    """Tests for TimeoutError exception."""

    def test_with_timeout_seconds(self):
        error = TimeoutError(timeout_seconds=30.5)
        assert str(error) == "Error: query execution timed out after 30.5s"

    def test_with_different_timeouts(self):
        error1 = TimeoutError(timeout_seconds=5.0)
        assert str(error1) == "Error: query execution timed out after 5.0s"

        error2 = TimeoutError(timeout_seconds=120.75)
        assert str(error2) == "Error: query execution timed out after 120.75s"

    def test_without_timeout_seconds(self):
        error = TimeoutError()
        assert str(error) == "Error: query execution timed out"

    def test_with_none_timeout(self):
        error = TimeoutError(timeout_seconds=None)
        assert str(error) == "Error: query execution timed out"

    def test_inherits_from_sqlite_excel_error(self):
        error = TimeoutError()
        assert isinstance(error, SQLiteExcelError)


class TestOutputLimitError:
    """Tests for OutputLimitError exception."""

    def test_message_format(self):
        error = OutputLimitError(row_count=200000, limit=100000)
        expected = (
            "Error: result set too large: 200000 rows (limit: 100000). "
            "Use LIMIT clause to reduce output."
        )
        assert str(error) == expected

    def test_with_different_values(self):
        error = OutputLimitError(row_count=1500000, limit=1000000)
        assert "1500000 rows" in str(error)
        assert "limit: 1000000" in str(error)
        assert "Use LIMIT clause" in str(error)

    def test_inherits_from_sqlite_excel_error(self):
        error = OutputLimitError(100, 50)
        assert isinstance(error, SQLiteExcelError)


class TestNormalizeSQLiteError:
    """Tests for normalize_sqlite_error() function."""

    def test_table_not_found_error(self):
        original = sqlite3.OperationalError("no such table: users")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, TableNotFoundError)
        assert "users" in str(normalized)

    def test_column_not_found_error(self):
        original = sqlite3.OperationalError("no such column: email")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, ColumnNotFoundError)
        assert "email" in str(normalized)

    def test_syntax_error(self):
        original = sqlite3.OperationalError("near \"FROM\": syntax error")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, QuerySyntaxError)

    def test_generic_operational_error(self):
        original = sqlite3.OperationalError("database is locked")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, ExecutionError)
        assert "database is locked" in str(normalized)

    def test_integrity_error(self):
        original = sqlite3.IntegrityError("UNIQUE constraint failed")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, ExecutionError)
        assert "integrity error" in str(normalized)

    def test_programming_error(self):
        original = sqlite3.ProgrammingError("incorrect number of bindings")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, ExecutionError)
        assert "programming error" in str(normalized)

    def test_database_error(self):
        original = sqlite3.DatabaseError("malformed database schema")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, ExecutionError)

    def test_generic_exception(self):
        original = ValueError("invalid value")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, ExecutionError)
        assert "invalid value" in str(normalized)

    def test_preserves_error_message(self):
        original = sqlite3.OperationalError("custom error message")
        normalized = normalize_sqlite_error(original)

        assert "custom error message" in str(normalized)

    def test_table_name_extraction(self):
        original = sqlite3.OperationalError("no such table: my_table")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, TableNotFoundError)
        assert str(normalized) == "Error: no such table: my_table"

    def test_column_name_extraction(self):
        original = sqlite3.OperationalError("no such column: my_column")
        normalized = normalize_sqlite_error(original)

        assert isinstance(normalized, ColumnNotFoundError)
        assert str(normalized) == "Error: no such column: my_column"


class TestFormatErrorForExcel:
    """Tests for format_error_for_excel() function."""

    def test_sqlite_excel_error(self):
        error = TableNotFoundError("users")
        formatted = format_error_for_excel(error)

        assert formatted == "Error: no such table: users"

    def test_custom_sqlite_excel_error(self):
        error = QuerySyntaxError(near_token="SELECT")
        formatted = format_error_for_excel(error)

        assert formatted == 'Error: near "SELECT": syntax error'

    def test_native_sqlite_error(self):
        error = sqlite3.OperationalError("no such table: products")
        formatted = format_error_for_excel(error)

        # Should normalize and format
        assert "Error:" in formatted
        assert "products" in formatted

    def test_integrity_error_formatting(self):
        error = sqlite3.IntegrityError("UNIQUE constraint failed: users.email")
        formatted = format_error_for_excel(error)

        assert "Error:" in formatted
        assert "integrity error" in formatted

    def test_generic_exception(self):
        error = ValueError("test error")
        formatted = format_error_for_excel(error)

        assert "Error:" in formatted
        assert "test error" in formatted

    def test_returns_string(self):
        error = TableNotFoundError("test")
        formatted = format_error_for_excel(error)

        assert isinstance(formatted, str)

    def test_multiple_error_types(self):
        errors = [
            TableNotFoundError("t1"),
            ColumnNotFoundError("c1"),
            EmptyRangeError("A1:A1"),
            QuerySyntaxError(near_token="WHERE"),
        ]

        for error in errors:
            formatted = format_error_for_excel(error)
            assert formatted.startswith("Error:")
            assert isinstance(formatted, str)


class TestErrorInheritance:
    """Tests for error class inheritance hierarchy."""

    def test_all_inherit_from_sqlite_excel_error(self):
        errors = [
            TableNotFoundError("t"),
            ColumnNotFoundError("c"),
            DuplicateColumnError("d"),
            EmptyColumnNameError(),
            QuerySyntaxError(),
            RangeResolutionError("r"),
            EmptyRangeError("e"),
            TypeInferenceError("t"),
            ExecutionError("e"),
            TimeoutError(),
            OutputLimitError(100, 50),
        ]

        for error in errors:
            assert isinstance(error, SQLiteExcelError)
            assert isinstance(error, Exception)

    def test_all_have_error_prefix(self):
        errors = [
            TableNotFoundError("t"),
            ColumnNotFoundError("c"),
            DuplicateColumnError("d"),
            EmptyColumnNameError(),
            QuerySyntaxError(),
            RangeResolutionError("r"),
            EmptyRangeError("e"),
            TypeInferenceError("t"),
            ExecutionError("e"),
            TimeoutError(),
            OutputLimitError(100, 50),
        ]

        for error in errors:
            assert str(error).startswith("Error:")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
