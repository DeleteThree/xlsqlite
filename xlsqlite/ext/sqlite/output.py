"""
Output Formatter for SQLITE Excel function.

This module handles:
- Converting query results to Excel-compatible format
- Type preservation for numeric values
- NULL handling for Excel display
- DataFrame formatting for spill output
"""

from typing import Optional, Any
import pandas as pd

from .executor import ExecutionResult


def format_result(
    result: ExecutionResult,
    include_headers: bool = True
) -> pd.DataFrame:
    """
    Convert ExecutionResult to pandas DataFrame for Excel output.
    
    Args:
        result: Query execution result
        include_headers: If True, column names become first row
        
    Returns:
        DataFrame ready for Excel spill output
    """
    if not result.columns or not result.rows:
        # Empty result - return empty DataFrame with message
        if result.query_type in ("INSERT", "UPDATE", "DELETE"):
            # DML - return affected row count
            return pd.DataFrame([{"Result": f"{result.rowcount} rows affected"}])
        elif result.query_type in ("CREATE", "DROP"):
            # DDL - return success message
            return pd.DataFrame([{"Result": "OK"}])
        else:
            # Empty SELECT
            return pd.DataFrame()
    
    # Create DataFrame from rows
    df = pd.DataFrame(result.rows, columns=result.columns)
    
    # Convert types for Excel compatibility
    df = convert_types_for_excel(df)
    
    return df


def convert_types_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert DataFrame types for optimal Excel display.
    
    Conversions:
    - Integers stay as integers (not float)
    - Floats stay as floats
    - Text stays as text
    - None/NULL -> None (Excel empty cell)
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with Excel-friendly types
    """
    result = df.copy()
    
    for col in result.columns:
        series = result[col]
        
        # Skip if all null
        if series.isna().all():
            continue
        
        # Try to infer best type
        non_null = series.dropna()
        
        if len(non_null) == 0:
            continue
        
        # Check if all integers
        try:
            if all(isinstance(x, (int, float)) and float(x).is_integer() 
                   for x in non_null):
                # Convert to nullable integer
                result[col] = series.astype('Int64')  # Nullable integer
                continue
        except (ValueError, TypeError):
            pass
        
        # Check if all numeric
        try:
            if all(isinstance(x, (int, float)) for x in non_null):
                result[col] = series.astype(float)
                continue
        except (ValueError, TypeError):
            pass
        
        # Keep as-is (likely string or mixed)
    
    return result


def handle_null_display(
    df: pd.DataFrame,
    null_repr: Optional[str] = None
) -> pd.DataFrame:
    """
    Handle NULL/None values for Excel display.
    
    By default, None becomes empty cell (Excel's default).
    Optionally can convert to a specific string like "NULL".
    
    Args:
        df: Input DataFrame
        null_repr: String representation for NULL (None = empty cell)
        
    Returns:
        DataFrame with handled nulls
    """
    if null_repr is None:
        # Keep as None - Excel will show empty cell
        return df
    
    # Replace None/NaN with the specified string
    return df.fillna(null_repr)


def format_for_debug(result: ExecutionResult) -> str:
    """
    Format result for debug output.
    
    Useful for EXPLAIN or diagnostic queries.
    
    Args:
        result: Query execution result
        
    Returns:
        Human-readable string representation
    """
    lines = []
    
    # Header
    lines.append(f"Query type: {result.query_type}")
    lines.append(f"Execution time: {result.execution_time_ms:.2f}ms")
    
    if result.columns:
        lines.append(f"Columns: {', '.join(result.columns)}")
        lines.append(f"Row count: {len(result.rows)}")
        
        # Show first few rows
        if result.rows:
            lines.append("\nSample rows:")
            for i, row in enumerate(result.rows[:5]):
                lines.append(f"  {row}")
            if len(result.rows) > 5:
                lines.append(f"  ... ({len(result.rows) - 5} more rows)")
    else:
        lines.append(f"Rows affected: {result.rowcount}")
        if result.lastrowid:
            lines.append(f"Last row ID: {result.lastrowid}")
    
    return "\n".join(lines)


def result_to_list_of_lists(
    result: ExecutionResult,
    include_headers: bool = True
) -> list[list[Any]]:
    """
    Convert result to list of lists format.
    
    This format is sometimes useful for Excel array formulas.
    
    Args:
        result: Query execution result
        include_headers: If True, first list is column names
        
    Returns:
        List of lists representing the table
    """
    if not result.columns:
        return []
    
    rows = []
    
    if include_headers:
        rows.append(list(result.columns))
    
    for row in result.rows:
        rows.append(list(row))
    
    return rows


def estimate_output_size(result: ExecutionResult) -> dict[str, int]:
    """
    Estimate the size of output for warnings.
    
    Args:
        result: Query execution result
        
    Returns:
        Dict with row_count, column_count, cell_count
    """
    return {
        "row_count": len(result.rows),
        "column_count": len(result.columns),
        "cell_count": len(result.rows) * len(result.columns)
    }


# Excel limits
EXCEL_MAX_ROWS = 1_048_576
EXCEL_MAX_COLS = 16_384
RECOMMENDED_MAX_ROWS = 100_000  # For performance


def check_output_limits(result: ExecutionResult) -> Optional[str]:
    """
    Check if result exceeds recommended or hard limits.
    
    Args:
        result: Query execution result
        
    Returns:
        Warning message if limits exceeded, None otherwise
    """
    row_count = len(result.rows)
    col_count = len(result.columns)
    
    if row_count > EXCEL_MAX_ROWS:
        return (
            f"Result has {row_count:,} rows, exceeding Excel's limit of "
            f"{EXCEL_MAX_ROWS:,}. Use LIMIT clause to reduce output."
        )
    
    if col_count > EXCEL_MAX_COLS:
        return (
            f"Result has {col_count:,} columns, exceeding Excel's limit of "
            f"{EXCEL_MAX_COLS:,}."
        )
    
    if row_count > RECOMMENDED_MAX_ROWS:
        return (
            f"Warning: Result has {row_count:,} rows. Large outputs may "
            f"impact Excel performance. Consider using LIMIT clause."
        )
    
    return None
