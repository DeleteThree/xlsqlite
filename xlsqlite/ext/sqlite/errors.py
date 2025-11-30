"""
Error handling for SQLITE Excel function.

All exceptions follow SQLite's native error message format.
"""


class SQLiteExcelError(Exception):
    """Base exception for SQLITE function errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Error: {message}")


class TableNotFoundError(SQLiteExcelError):
    """Raised when a referenced table or range cannot be found."""
    
    def __init__(self, table_name: str):
        super().__init__(f"no such table: {table_name}")


class ColumnNotFoundError(SQLiteExcelError):
    """Raised when a referenced column does not exist."""
    
    def __init__(self, column_name: str):
        super().__init__(f"no such column: {column_name}")


class DuplicateColumnError(SQLiteExcelError):
    """Raised when header row contains duplicate column names."""
    
    def __init__(self, column_name: str):
        super().__init__(f"duplicate column name: {column_name}")


class EmptyColumnNameError(SQLiteExcelError):
    """Raised when header row contains empty column names."""
    
    def __init__(self, position: int | None = None):
        if position is not None:
            super().__init__(f"column name cannot be empty (position {position})")
        else:
            super().__init__("column name cannot be empty")


class QuerySyntaxError(SQLiteExcelError):
    """Raised for SQL syntax errors."""
    
    def __init__(self, near_token: str | None = None, details: str | None = None):
        if near_token:
            super().__init__(f'near "{near_token}": syntax error')
        elif details:
            super().__init__(details)
        else:
            super().__init__("syntax error")


class RangeResolutionError(SQLiteExcelError):
    """Raised when an Excel range cannot be resolved."""
    
    def __init__(self, range_ref: str, reason: str | None = None):
        if reason:
            super().__init__(f"cannot resolve range: {range_ref} ({reason})")
        else:
            super().__init__(f"cannot resolve range: {range_ref}")


class EmptyRangeError(SQLiteExcelError):
    """Raised when a range contains no data rows (only headers or empty)."""
    
    def __init__(self, range_ref: str):
        super().__init__(f"range contains no data: {range_ref}")


class TypeInferenceError(SQLiteExcelError):
    """Raised when column type cannot be inferred."""
    
    def __init__(self, column_name: str, reason: str | None = None):
        if reason:
            super().__init__(f"cannot infer type for column '{column_name}': {reason}")
        else:
            super().__init__(f"cannot infer type for column '{column_name}'")


class ExecutionError(SQLiteExcelError):
    """Raised for query execution errors."""
    
    def __init__(self, message: str):
        super().__init__(message)


class TimeoutError(SQLiteExcelError):
    """Raised when query execution times out."""
    
    def __init__(self, timeout_seconds: float | None = None):
        if timeout_seconds:
            super().__init__(f"query execution timed out after {timeout_seconds}s")
        else:
            super().__init__("query execution timed out")


class OutputLimitError(SQLiteExcelError):
    """Raised when result set exceeds safe limits."""
    
    def __init__(self, row_count: int, limit: int):
        super().__init__(
            f"result set too large: {row_count} rows (limit: {limit}). "
            f"Use LIMIT clause to reduce output."
        )


def normalize_sqlite_error(error: Exception) -> SQLiteExcelError:
    """
    Convert a native sqlite3 exception to SQLiteExcelError.
    
    Preserves the original SQLite error message format.
    """
    import sqlite3
    
    error_msg = str(error)
    
    # Handle specific sqlite3 error types
    if isinstance(error, sqlite3.OperationalError):
        # Check for common patterns
        if "no such table" in error_msg:
            # Extract table name
            parts = error_msg.split("no such table:")
            if len(parts) > 1:
                table_name = parts[1].strip()
                return TableNotFoundError(table_name)
        
        if "no such column" in error_msg:
            parts = error_msg.split("no such column:")
            if len(parts) > 1:
                column_name = parts[1].strip()
                return ColumnNotFoundError(column_name)
        
        if "syntax error" in error_msg.lower():
            return QuerySyntaxError(details=error_msg)
        
        return ExecutionError(error_msg)
    
    elif isinstance(error, sqlite3.IntegrityError):
        return ExecutionError(f"integrity error: {error_msg}")
    
    elif isinstance(error, sqlite3.ProgrammingError):
        return ExecutionError(f"programming error: {error_msg}")
    
    elif isinstance(error, sqlite3.DatabaseError):
        return ExecutionError(error_msg)
    
    # Generic fallback
    return ExecutionError(str(error))


def format_error_for_excel(error: Exception) -> str:
    """
    Format an error for display in an Excel cell.
    
    Returns a string suitable for Excel error display.
    """
    if isinstance(error, SQLiteExcelError):
        return str(error)
    else:
        # Normalize and format
        normalized = normalize_sqlite_error(error)
        return str(normalized)
