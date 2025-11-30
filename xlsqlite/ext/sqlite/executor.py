"""
Query Execution Engine for SQLITE Excel function.

This module handles:
- Creating in-memory SQLite connections
- Executing queries with parameters
- Handling multiple statements
- Execution plan analysis
"""

from dataclasses import dataclass
from typing import Optional, Any
import sqlite3
import time


@dataclass
class ExecutionResult:
    """
    Result of SQL query execution.
    
    Attributes:
        columns: List of column names in result set
        rows: List of result rows as tuples
        rowcount: Number of rows affected (for INSERT/UPDATE/DELETE)
        lastrowid: ID of last inserted row (for INSERT)
        execution_time_ms: Query execution time in milliseconds
        query_type: Type of query executed (SELECT, INSERT, etc.)
    """
    columns: list[str]
    rows: list[tuple]
    rowcount: int
    lastrowid: Optional[int]
    execution_time_ms: float
    query_type: str
    
    @property
    def is_select(self) -> bool:
        """True if this was a SELECT query with results."""
        return self.query_type.upper() == "SELECT"
    
    @property
    def has_results(self) -> bool:
        """True if result set is not empty."""
        return len(self.rows) > 0


def create_connection() -> sqlite3.Connection:
    """
    Create a new in-memory SQLite connection.
    
    Configures the connection with optimal settings for
    query execution in the Python in Excel environment.
    
    Returns:
        Configured sqlite3.Connection
    """
    conn = sqlite3.connect(":memory:")
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Return rows as tuples (default, but explicit)
    conn.row_factory = None
    
    return conn


def detect_query_type(query: str) -> str:
    """
    Detect the type of SQL query.
    
    Args:
        query: SQL query string
        
    Returns:
        Query type: SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, PRAGMA, EXPLAIN, OTHER
    """
    # Strip whitespace and get first word
    stripped = query.strip().upper()
    
    # Handle WITH (CTE) - look for the main query after
    if stripped.startswith("WITH"):
        # Find the main statement after the CTE
        # This is simplified - CTEs are usually followed by SELECT
        if "SELECT" in stripped:
            return "SELECT"
        return "OTHER"
    
    # Check common statement types
    for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "PRAGMA", "EXPLAIN"]:
        if stripped.startswith(keyword):
            return keyword
    
    return "OTHER"


def execute_query(
    conn: sqlite3.Connection,
    query: str,
    params: tuple = ()
) -> ExecutionResult:
    """
    Execute a single SQL query.
    
    Args:
        conn: SQLite connection
        query: SQL query string
        params: Query parameters (for ? placeholders)
        
    Returns:
        ExecutionResult with query results
        
    Raises:
        sqlite3.Error: For database errors (will be normalized by caller)
    """
    query_type = detect_query_type(query)
    
    start_time = time.perf_counter()
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    # Get results based on query type
    if query_type in ("SELECT", "PRAGMA", "EXPLAIN"):
        # Fetch column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        rowcount = len(rows)
        lastrowid = None
    else:
        # DML/DDL - no result set
        columns = []
        rows = []
        rowcount = cursor.rowcount
        lastrowid = cursor.lastrowid
    
    end_time = time.perf_counter()
    execution_time_ms = (end_time - start_time) * 1000
    
    return ExecutionResult(
        columns=columns,
        rows=rows,
        rowcount=rowcount,
        lastrowid=lastrowid,
        execution_time_ms=execution_time_ms,
        query_type=query_type
    )


def execute_multiple_statements(
    conn: sqlite3.Connection,
    sql: str,
    params_list: Optional[list[tuple]] = None
) -> ExecutionResult:
    """
    Execute multiple SQL statements separated by semicolons.
    
    Returns the result of the last SELECT statement, or the
    last statement if no SELECTs are present.
    
    Args:
        conn: SQLite connection
        sql: SQL with potentially multiple statements
        params_list: Optional list of parameter tuples (one per statement)
        
    Returns:
        ExecutionResult from the last relevant statement
    """
    # Split statements (simple approach - doesn't handle semicolons in strings)
    statements = split_statements(sql)
    
    if not statements:
        return ExecutionResult(
            columns=[],
            rows=[],
            rowcount=0,
            lastrowid=None,
            execution_time_ms=0,
            query_type="EMPTY"
        )
    
    last_select_result: Optional[ExecutionResult] = None
    last_result: Optional[ExecutionResult] = None
    total_time_ms = 0
    
    for i, stmt in enumerate(statements):
        stmt = stmt.strip()
        if not stmt:
            continue
        
        # Get params for this statement if provided
        params = params_list[i] if params_list and i < len(params_list) else ()
        
        result = execute_query(conn, stmt, params)
        total_time_ms += result.execution_time_ms
        last_result = result
        
        if result.is_select:
            last_select_result = result
    
    # Return last SELECT result if any, otherwise last result
    final_result = last_select_result or last_result
    
    if final_result:
        # Update total execution time
        return ExecutionResult(
            columns=final_result.columns,
            rows=final_result.rows,
            rowcount=final_result.rowcount,
            lastrowid=final_result.lastrowid,
            execution_time_ms=total_time_ms,
            query_type=final_result.query_type
        )
    
    return ExecutionResult(
        columns=[],
        rows=[],
        rowcount=0,
        lastrowid=None,
        execution_time_ms=total_time_ms,
        query_type="EMPTY"
    )


def split_statements(sql: str) -> list[str]:
    """
    Split SQL into individual statements.
    
    Handles semicolons inside string literals.
    
    Args:
        sql: SQL string with potentially multiple statements
        
    Returns:
        List of individual statements
    """
    statements = []
    current = []
    in_string = False
    string_char = None
    
    i = 0
    while i < len(sql):
        char = sql[i]
        
        # Handle string literals
        if char in ("'", '"') and not in_string:
            in_string = True
            string_char = char
            current.append(char)
        elif char == string_char and in_string:
            # Check for escaped quote
            if i + 1 < len(sql) and sql[i + 1] == string_char:
                current.append(char)
                current.append(char)
                i += 1
            else:
                in_string = False
                string_char = None
                current.append(char)
        elif char == ';' and not in_string:
            # Statement separator
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
        else:
            current.append(char)
        
        i += 1
    
    # Don't forget the last statement
    stmt = ''.join(current).strip()
    if stmt:
        statements.append(stmt)
    
    return statements


def get_execution_plan(conn: sqlite3.Connection, query: str) -> str:
    """
    Get the query execution plan.
    
    Args:
        conn: SQLite connection (must have tables loaded)
        query: Query to analyze
        
    Returns:
        Execution plan as formatted string
    """
    # Use EXPLAIN QUERY PLAN for human-readable output
    explain_query = f"EXPLAIN QUERY PLAN {query}"
    
    cursor = conn.cursor()
    cursor.execute(explain_query)
    
    rows = cursor.fetchall()
    
    # Format the plan
    lines = []
    for row in rows:
        # EXPLAIN QUERY PLAN returns (id, parent, notused, detail)
        if len(row) >= 4:
            detail = row[3]
            lines.append(detail)
        else:
            lines.append(str(row))
    
    return "\n".join(lines)


def get_table_info(conn: sqlite3.Connection, table_name: str) -> ExecutionResult:
    """
    Get schema information for a table.
    
    Args:
        conn: SQLite connection
        table_name: Name of table
        
    Returns:
        ExecutionResult with PRAGMA table_info output
    """
    return execute_query(conn, f"PRAGMA table_info({table_name})")


def get_sqlite_version() -> str:
    """
    Get the SQLite library version.
    
    Returns:
        Version string (e.g., "3.35.4")
    """
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("SELECT sqlite_version()")
    version = cursor.fetchone()[0]
    conn.close()
    return version


def check_feature_support() -> dict[str, bool]:
    """
    Check which SQLite features are available.
    
    Returns:
        Dict of feature_name -> is_supported
    """
    features = {}
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Check window functions (3.25+)
    try:
        cursor.execute("SELECT row_number() OVER () FROM (SELECT 1)")
        features["window_functions"] = True
    except sqlite3.OperationalError:
        features["window_functions"] = False
    
    # Check CTEs (3.8.3+)
    try:
        cursor.execute("WITH cte AS (SELECT 1) SELECT * FROM cte")
        features["cte"] = True
    except sqlite3.OperationalError:
        features["cte"] = False
    
    # Check UPSERT (3.24+)
    try:
        cursor.execute("CREATE TABLE t(x PRIMARY KEY)")
        cursor.execute("INSERT INTO t VALUES(1) ON CONFLICT DO NOTHING")
        features["upsert"] = True
    except sqlite3.OperationalError:
        features["upsert"] = False
    
    # Check JSON functions (3.9+)
    try:
        cursor.execute("SELECT json_extract('{\"a\":1}', '$.a')")
        features["json"] = True
    except sqlite3.OperationalError:
        features["json"] = False
    
    conn.close()
    return features
