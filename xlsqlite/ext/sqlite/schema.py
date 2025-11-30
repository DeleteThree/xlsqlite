"""
Schema Builder and Type Inference for SQLITE Excel function.

This module handles:
- Resolving Excel references to data via xl()
- Inferring SQLite column types from data
- Validating headers (no duplicates, no empty)
- Creating SQLite tables and loading data
"""

from dataclasses import dataclass
from typing import Optional, Any
import sqlite3

# Note: In Python in Excel, pandas is available
import pandas as pd

from parser import TableReference
from errors import (
    DuplicateColumnError,
    EmptyColumnNameError,
    RangeResolutionError,
    EmptyRangeError,
    TypeInferenceError,
)


# SQLite type constants
SQLITE_INTEGER = "INTEGER"
SQLITE_REAL = "REAL"
SQLITE_TEXT = "TEXT"
SQLITE_BLOB = "BLOB"


@dataclass
class ColumnSchema:
    """Schema information for a single column."""
    name: str
    sqlite_name: str  # Quoted if necessary
    sqlite_type: str
    nullable: bool = True


@dataclass
class TableSchema:
    """Complete schema for a table."""
    name: str
    sqlite_name: str
    columns: list[ColumnSchema]
    row_count: int


def resolve_reference(ref: TableReference) -> pd.DataFrame:
    """
    Resolve an Excel reference to a pandas DataFrame.

    In Python in Excel, this uses the xl() function to fetch data from Excel ranges or tables.

    The xl() function syntax:
        - Named tables: xl("Sheet1.Table1") or xl("Table1")
        - Range references: xl("A1:M100") or xl("Sheet2!A1:B10")

    Args:
        ref: TableReference object containing parsed Excel reference details

    Returns:
        DataFrame with the referenced data (headers as columns, data as rows)

    Raises:
        RangeResolutionError: If reference cannot be resolved or xl() is not available
        EmptyRangeError: If range contains no data rows
    """
    # Try to import xl() function from Python in Excel environment
    try:
        from xl import xl
    except ImportError:
        # xl() not available - not in Python in Excel environment
        raise RangeResolutionError(
            ref.original,
            "xl() function not available - must run in Python in Excel environment"
        )

    # Build the Excel reference string for xl()
    try:
        if ref.is_named_table:
            # Named table reference
            if ref.sheet_name:
                # Sheet-qualified table: "Sheet1.Table1"
                excel_ref = f"{ref.sheet_name}.{ref.table_name}"
            else:
                # Simple table name: "Table1"
                excel_ref = ref.table_name
        else:
            # Range reference
            if ref.sheet_name:
                # Cross-sheet range: "Sheet2!A1:B10"
                excel_ref = f"{ref.sheet_name}!{ref.range_ref}"
            else:
                # Simple range: "A1:M100"
                excel_ref = ref.range_ref

        # Call xl() to fetch data
        df = xl(excel_ref, headers=True)

    except Exception as e:
        # xl() call failed - could be invalid reference, permission issue, etc.
        raise RangeResolutionError(
            ref.original,
            f"failed to resolve Excel reference: {str(e)}"
        )

    # Validate the result
    if df is None:
        raise RangeResolutionError(
            ref.original,
            "xl() returned None - reference may not exist"
        )

    if not isinstance(df, pd.DataFrame):
        raise RangeResolutionError(
            ref.original,
            f"xl() returned unexpected type: {type(df).__name__} (expected DataFrame)"
        )

    # Check if DataFrame is empty (no data rows)
    if len(df) == 0:
        raise EmptyRangeError(ref.original)

    # Check if DataFrame has columns
    if len(df.columns) == 0:
        raise RangeResolutionError(
            ref.original,
            "range contains no columns"
        )

    return df


def infer_column_type(series: pd.Series) -> str:
    """
    Infer SQLite type for a pandas Series.

    Type inference hierarchy (strictest that fits):
    1. All integers (ignoring NULL) -> INTEGER
    2. All numeric (ignoring NULL) -> REAL
    3. Dates/Datetimes -> TEXT (stored as ISO 8601)
    4. Booleans -> INTEGER (stored as 0/1)
    5. Otherwise -> TEXT

    Args:
        series: pandas Series to analyze

    Returns:
        SQLite type string (INTEGER, REAL, or TEXT)
    """
    # Drop null values for analysis
    non_null = series.dropna()

    if len(non_null) == 0:
        # All nulls - default to TEXT
        return SQLITE_TEXT

    # Check for boolean first (before numeric check, since bools are numeric in pandas)
    if pd.api.types.is_bool_dtype(series):
        return SQLITE_INTEGER  # SQLite stores bools as 0/1

    # Check for datetime types - return TEXT (will be stored as ISO 8601)
    if pd.api.types.is_datetime64_any_dtype(series):
        return SQLITE_TEXT

    # Check if numeric (integers or floats)
    try:
        if pd.api.types.is_numeric_dtype(non_null):
            # Check if all non-null values are whole numbers
            if all(float(x).is_integer() for x in non_null if pd.notna(x)):
                return SQLITE_INTEGER
            return SQLITE_REAL
    except (ValueError, TypeError):
        pass

    # Default to TEXT
    return SQLITE_TEXT


def infer_column_types(df: pd.DataFrame) -> dict[str, str]:
    """
    Infer SQLite types for all columns in a DataFrame.
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dict mapping column names to SQLite types
    """
    return {col: infer_column_type(df[col]) for col in df.columns}


def validate_headers(headers: list[Any]) -> list[str]:
    """
    Validate and normalize column headers.
    
    Rules (DBA expectations - strict):
    - No duplicate names (case-insensitive comparison)
    - No empty/null names
    - All values converted to strings
    
    Args:
        headers: List of header values from first row
        
    Returns:
        List of validated string headers
        
    Raises:
        DuplicateColumnError: If duplicate column name found
        EmptyColumnNameError: If empty column name found
    """
    validated = []
    seen = {}  # lowercase -> original for duplicate detection
    
    for i, header in enumerate(headers):
        # Check for empty/null
        if header is None or (isinstance(header, str) and header.strip() == ""):
            raise EmptyColumnNameError(position=i + 1)
        
        # Convert to string
        header_str = str(header).strip()
        
        if header_str == "":
            raise EmptyColumnNameError(position=i + 1)
        
        # Check for duplicates (case-insensitive)
        lower = header_str.lower()
        if lower in seen:
            raise DuplicateColumnError(header_str)
        
        seen[lower] = header_str
        validated.append(header_str)
    
    return validated


def sanitize_column_name(name: str) -> str:
    """
    Convert column name to valid SQLite identifier.
    
    Names with spaces or special characters are double-quoted.
    
    Args:
        name: Original column name
        
    Returns:
        SQLite-safe column name (quoted if necessary)
    """
    import re
    
    # Check if valid unquoted identifier
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        # Check if reserved word
        reserved = {
            'select', 'from', 'where', 'and', 'or', 'not', 'null', 'true', 'false',
            'insert', 'update', 'delete', 'create', 'drop', 'table', 'index',
            'order', 'by', 'group', 'having', 'join', 'left', 'right', 'inner',
            'outer', 'on', 'as', 'in', 'between', 'like', 'is', 'case', 'when',
            'then', 'else', 'end', 'distinct', 'limit', 'offset', 'union', 'all'
        }
        if name.lower() not in reserved:
            return name
    
    # Quote the name - escape internal double quotes
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def create_table_ddl(table_name: str, columns: list[ColumnSchema]) -> str:
    """
    Generate CREATE TABLE DDL statement.
    
    Args:
        table_name: Name for the SQLite table
        columns: List of column schemas
        
    Returns:
        CREATE TABLE SQL statement
    """
    col_defs = []
    for col in columns:
        nullable = "" if col.nullable else " NOT NULL"
        col_defs.append(f"    {col.sqlite_name} {col.sqlite_type}{nullable}")
    
    cols_sql = ",\n".join(col_defs)
    return f"CREATE TABLE {table_name} (\n{cols_sql}\n)"


def build_table_schema(df: pd.DataFrame, table_name: str) -> TableSchema:
    """
    Build complete table schema from DataFrame.

    Args:
        df: DataFrame with data (headers are df.columns)
        table_name: Name for the table

    Returns:
        TableSchema object

    Raises:
        DuplicateColumnError: If duplicate column names found
        EmptyColumnNameError: If empty column names found
    """
    # Validate headers first
    validated_headers = validate_headers(df.columns.tolist())

    # Infer types for all columns
    types = infer_column_types(df)

    # Build column schemas
    columns = []
    for col_name in validated_headers:
        columns.append(ColumnSchema(
            name=col_name,
            sqlite_name=sanitize_column_name(col_name),
            sqlite_type=types[col_name],
            nullable=True
        ))

    return TableSchema(
        name=table_name,
        sqlite_name=sanitize_column_name(table_name),
        columns=columns,
        row_count=len(df)
    )


def load_data_to_sqlite(
    conn: sqlite3.Connection,
    schema: TableSchema,
    df: pd.DataFrame
) -> None:
    """
    Create table and load data into SQLite.
    
    Args:
        conn: SQLite connection
        schema: Table schema
        df: DataFrame with data to load
    """
    # Create table
    ddl = create_table_ddl(schema.sqlite_name, schema.columns)
    conn.execute(ddl)
    
    # Prepare data - convert types appropriately
    prepared_df = prepare_data_for_sqlite(df, schema)
    
    # Insert data
    if len(prepared_df) > 0:
        placeholders = ", ".join(["?" for _ in schema.columns])
        col_names = ", ".join([c.sqlite_name for c in schema.columns])
        insert_sql = f"INSERT INTO {schema.sqlite_name} ({col_names}) VALUES ({placeholders})"
        
        # Convert DataFrame to list of tuples
        rows = [tuple(row) for row in prepared_df.values]
        conn.executemany(insert_sql, rows)
    
    conn.commit()


def prepare_data_for_sqlite(df: pd.DataFrame, schema: TableSchema) -> pd.DataFrame:
    """
    Prepare DataFrame data for SQLite insertion.

    Conversions:
    - Dates/Datetimes -> ISO 8601 strings (YYYY-MM-DDTHH:MM:SS)
    - Booleans -> 0/1 (native Python int)
    - NaN/None/NaT -> None (NULL)
    - Excel errors -> None (NULL)
    - Numpy types -> native Python types

    Args:
        df: Original DataFrame
        schema: Table schema

    Returns:
        Prepared DataFrame with SQLite-compatible types
    """
    result = df.copy()

    for col in result.columns:
        series = result[col]

        # Handle datetime - convert to ISO 8601 strings, preserving NaT as None
        if pd.api.types.is_datetime64_any_dtype(series):
            # First replace NaT with None, then format non-null datetimes
            result[col] = series.apply(
                lambda x: x.strftime('%Y-%m-%dT%H:%M:%S') if pd.notna(x) else None
            )

        # Handle boolean - convert to 0/1 for SQLite (use Python int, not numpy int64)
        elif pd.api.types.is_bool_dtype(series):
            # Use list comprehension to ensure Python int type, not numpy.int64
            result[col] = pd.Series([int(x) if pd.notna(x) else None for x in series], dtype=object)

        # Handle NaN/None -> None (NULL) for all other types
        else:
            result[col] = result[col].where(pd.notna(result[col]), None)

    return result


def convert_excel_date(value: Any) -> Optional[str]:
    """
    Convert Excel date serial number to ISO string.
    
    Args:
        value: Excel date value (serial number or datetime)
        
    Returns:
        ISO 8601 date string or None
    """
    if pd.isna(value):
        return None
    
    try:
        if isinstance(value, (int, float)):
            # Excel serial date - convert
            # Excel epoch is 1899-12-30 (accounting for the 1900 leap year bug)
            from datetime import datetime, timedelta
            excel_epoch = datetime(1899, 12, 30)
            dt = excel_epoch + timedelta(days=value)
            return dt.strftime('%Y-%m-%d')
        elif hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        else:
            return str(value)
    except Exception:
        return str(value)
