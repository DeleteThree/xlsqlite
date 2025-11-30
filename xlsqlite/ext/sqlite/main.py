"""
SQLITE Excel Function - Main Entry Point

This is the main =SQLITE() function for Python in Excel.

Usage:
    =SQLITE("SELECT * FROM Sheet1.Table1")
    =SQLITE("SELECT * FROM A1:M100")
    =SQLITE("SELECT * FROM Orders WHERE id = ?", A1)
"""

from typing import Any, Optional
import pandas as pd

from .parser import (
    extract_table_references,
    substitute_references,
    is_parameterized_query,
    count_parameters,
    TableReference,
)
from .schema import (
    resolve_reference,
    build_table_schema,
    load_data_to_sqlite,
    validate_headers,
)
from .executor import (
    create_connection,
    execute_query,
    execute_multiple_statements,
    split_statements,
    ExecutionResult,
)
from .output import (
    format_result,
    check_output_limits,
)
from .errors import (
    SQLiteExcelError,
    QuerySyntaxError,
    normalize_sqlite_error,
    format_error_for_excel,
)


def SQLITE(query: str, *params: Any) -> Any:
    """
    Execute SQL query against Excel data.
    
    This function allows you to run SQLite queries directly against
    Excel tables and ranges from within Python in Excel.
    
    Args:
        query: SQL query string (SQLite dialect)
        *params: Optional parameters for ? placeholders in query
        
    Returns:
        pandas DataFrame with query results (spills in Excel)
        For DML queries (INSERT/UPDATE/DELETE): affected row count
        For errors: Error message string
        
    Examples:
        Basic query:
            =SQLITE("SELECT * FROM Sheet1.Orders")
        
        With filter:
            =SQLITE("SELECT * FROM Orders WHERE status = 'active'")
        
        Join:
            =SQLITE("SELECT o.*, c.name FROM Orders o JOIN Customers c ON o.cust_id = c.id")
        
        Range reference:
            =SQLITE("SELECT * FROM A1:M100 WHERE amount > 1000")
        
        Parameterized:
            =SQLITE("SELECT * FROM Orders WHERE id = ?", A1)
        
        Window function:
            =SQLITE("SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY date) as rn FROM Sales")
        
        CTE:
            =SQLITE("WITH ranked AS (SELECT *, RANK() OVER (ORDER BY score DESC) as r FROM Scores) SELECT * FROM ranked WHERE r <= 10")
    """
    try:
        return _execute_sqlite(query, params)
    except SQLiteExcelError as e:
        # Return formatted error message
        return str(e)
    except Exception as e:
        # Normalize and return other errors
        return format_error_for_excel(e)


def _execute_sqlite(query: str, params: tuple) -> Any:
    """
    Internal implementation of SQLITE function.
    
    Raises exceptions instead of returning error strings.
    """
    # Validate query is not empty
    if not query or not query.strip():
        raise QuerySyntaxError(details="empty query")
    
    # Validate parameter count
    if params:
        expected = count_parameters(query)
        if len(params) != expected:
            raise QuerySyntaxError(
                details=f"expected {expected} parameters, got {len(params)}"
            )
    
    # Extract table references from query
    references = extract_table_references(query)
    
    # Create in-memory database
    conn = create_connection()
    
    try:
        # Build mapping of original ref -> SQLite table name
        ref_mapping = {}
        
        # Load each referenced table into SQLite
        for ref in references:
            # Resolve Excel reference to DataFrame
            df = resolve_reference(ref)
            
            # Build schema
            schema = build_table_schema(df, ref.sqlite_name)
            
            # Load into SQLite
            load_data_to_sqlite(conn, schema, df)
            
            # Track mapping
            ref_mapping[ref.original] = ref.sqlite_name
        
        # Rewrite query with SQLite table names
        rewritten_query = substitute_references(query, ref_mapping)
        
        # Execute query
        if ';' in query:
            # Multiple statements
            result = execute_multiple_statements(conn, rewritten_query)
        else:
            # Single statement
            result = execute_query(conn, rewritten_query, params)
        
        # Check output limits
        warning = check_output_limits(result)
        if warning and "exceeding" in warning:
            # Hard limit exceeded
            raise SQLiteExcelError(warning)
        
        # Format and return result
        return format_result(result)
        
    finally:
        conn.close()


def SQLITE_VERSION() -> str:
    """
    Return the SQLite library version.
    
    Usage:
        =SQLITE_VERSION()
        
    Returns:
        SQLite version string (e.g., "3.35.4")
    """
    from .executor import get_sqlite_version
    return get_sqlite_version()


def SQLITE_FEATURES() -> pd.DataFrame:
    """
    Check available SQLite features.
    
    Usage:
        =SQLITE_FEATURES()
        
    Returns:
        DataFrame showing feature availability
    """
    from .executor import check_feature_support
    features = check_feature_support()
    
    rows = [
        {"Feature": k, "Supported": "Yes" if v else "No"}
        for k, v in features.items()
    ]
    return pd.DataFrame(rows)


def SQLITE_EXPLAIN(query: str) -> pd.DataFrame:
    """
    Get query execution plan without executing.
    
    Useful for debugging and optimizing queries.
    
    Usage:
        =SQLITE_EXPLAIN("SELECT * FROM Table1 WHERE id > 100")
        
    Args:
        query: SQL query to analyze
        
    Returns:
        DataFrame with execution plan
    """
    # Wrap query in EXPLAIN QUERY PLAN
    explain_query = f"EXPLAIN QUERY PLAN {query}"
    return SQLITE(explain_query)


# Aliases for common patterns
SQL = SQLITE  # Shorter alias


# Export public API
__all__ = [
    "SQLITE",
    "SQLITE_VERSION", 
    "SQLITE_FEATURES",
    "SQLITE_EXPLAIN",
    "SQL",
]
