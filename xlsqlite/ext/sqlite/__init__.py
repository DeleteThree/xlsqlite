"""
xlsqlite SQL Extension - SQLITE() function for Excel

This module provides the SQLITE() user-defined function that enables
SQL queries against Excel data.

Copyright (c) 2025-present, DeleteThree
Licensed under the BSD 3-Clause License.
"""

# This will be fully implemented in Phase 4
# For now, this is a placeholder

__all__ = ['SQLITE']

def SQLITE(query, *params):
    """
    Execute SQL query against Excel data.

    This function will be fully implemented with xlwings decorators
    during Phase 4: Integration.

    Args:
        query: SQL query string (SQLite dialect)
        *params: Optional parameters for ? placeholders

    Returns:
        Results as 2D array (spills in Excel)

    Examples:
        =SQLITE("SELECT * FROM Sheet1!A1:D10")
        =SQLITE("SELECT * FROM Orders WHERE Total > 100")
        =SQLITE("SELECT * FROM Orders WHERE CustomerID = ?", A1)
    """
    raise NotImplementedError(
        "SQLITE() function will be implemented in Phase 4. "
        "Integration with xlwings UDF system pending."
    )
