"""
SQL Parser and Reference Extraction for SQLITE Excel function.

This module handles:
- Extracting table/range references from SQL queries
- Parsing reference formats (Sheet.Table, Range, etc.)
- Query rewriting with SQLite-compatible table names
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class TableReference:
    """
    Represents a reference to Excel data within a SQL query.
    
    Attributes:
        original: Original reference string from query (e.g., "Sheet1.Table1")
        sheet_name: Sheet name if specified (e.g., "Sheet1")
        table_name: Named table name if specified (e.g., "Table1")
        range_ref: Cell range if specified (e.g., "A1:M100")
        sqlite_name: Sanitized name for use in SQLite (e.g., "sheet1_table1")
    """
    original: str
    sheet_name: Optional[str]
    table_name: Optional[str]
    range_ref: Optional[str]
    sqlite_name: str
    
    @property
    def is_named_table(self) -> bool:
        """True if this references a named Excel table."""
        return self.table_name is not None
    
    @property
    def is_range(self) -> bool:
        """True if this references a cell range."""
        return self.range_ref is not None


def extract_table_references(query: str) -> list[TableReference]:
    """
    Extract all table/range references from a SQL query.

    Handles:
    - Sheet.Table format: Sheet1.Orders
    - Table only: Orders
    - Cell range: A1:M100
    - Cross-sheet range: Sheet2!A1:B50
    - Absolute refs: $A$1:$M$100
    - Quoted sheet names: 'Sheet Name'.Table1

    Args:
        query: SQL query string

    Returns:
        List of TableReference objects

    TODO: Implement full parsing logic
    """
    # Remove comments and string literals to avoid false matches
    cleaned_query = _remove_string_literals(query)
    cleaned_query = _remove_comments(cleaned_query)

    references = []
    seen = set()

    # Pattern for SQL keywords that precede table references
    # Matches: FROM, JOIN (including LEFT JOIN, INNER JOIN, etc.)
    table_keyword_pattern = r'\b(?:FROM|JOIN)\s+'

    # Find all positions where table references should appear
    # Extract from the cleaned query to get the reference text
    matches = re.finditer(table_keyword_pattern, cleaned_query, re.IGNORECASE)

    for match in matches:
        start_pos = match.end()
        # Extract from cleaned query, not original
        ref_text = _extract_reference_at_position(cleaned_query, start_pos)

        if ref_text and ref_text not in seen:
            try:
                ref = parse_reference(ref_text)
                references.append(ref)
                seen.add(ref_text)
            except ValueError:
                # Skip invalid references
                pass

    # Also check for references in UPDATE and INSERT INTO statements
    update_pattern = r'\bUPDATE\s+([^\s,;]+)'
    for match in re.finditer(update_pattern, cleaned_query, re.IGNORECASE):
        ref_text = match.group(1).strip()
        if ref_text and ref_text not in seen:
            try:
                ref = parse_reference(ref_text)
                references.append(ref)
                seen.add(ref_text)
            except ValueError:
                pass

    insert_pattern = r'\bINSERT\s+INTO\s+([^\s,;(]+)'
    for match in re.finditer(insert_pattern, cleaned_query, re.IGNORECASE):
        ref_text = match.group(1).strip()
        if ref_text and ref_text not in seen:
            try:
                ref = parse_reference(ref_text)
                references.append(ref)
                seen.add(ref_text)
            except ValueError:
                pass

    return references


def parse_reference(ref: str) -> TableReference:
    """
    Parse a single reference string into a TableReference.

    Args:
        ref: Reference string (e.g., "Sheet1.Table1", "A1:M100")

    Returns:
        TableReference object

    Raises:
        ValueError: If reference format is invalid

    TODO: Implement parsing logic
    """
    if not ref or not ref.strip():
        raise ValueError("Reference cannot be empty")

    ref = ref.strip()
    original = ref
    sheet_name = None
    table_name = None
    range_ref = None

    # Pattern for cell range: A1:M100, $A$1:$M$100, etc.
    # Excel ranges have letters for columns and numbers for rows
    range_pattern = r'^(\$?[A-Z]+\$?\d+):(\$?[A-Z]+\$?\d+)$'

    # Pattern for cross-sheet range: Sheet1!A1:B10 or 'Sheet Name'!A1:B10
    cross_sheet_range_pattern = r"^(?:'([^']+)'|([^!]+))!(\$?[A-Z]+\$?\d+:\$?[A-Z]+\$?\d+)$"

    # Pattern for sheet.table: Sheet1.Table1 or 'Sheet Name'.Table1
    sheet_table_pattern = r"^(?:'([^']+)'|([^.]+))\.(.+)$"

    # Try to match cross-sheet range first (Sheet!A1:B10)
    match = re.match(cross_sheet_range_pattern, ref, re.IGNORECASE)
    if match:
        sheet_name = match.group(1) or match.group(2)
        range_ref = match.group(3).upper()
        sqlite_name = _generate_sqlite_name(sheet_name, None, range_ref)
        return TableReference(original, sheet_name, None, range_ref, sqlite_name)

    # Try to match simple range (A1:M100)
    match = re.match(range_pattern, ref, re.IGNORECASE)
    if match:
        range_ref = ref.upper()
        sqlite_name = _generate_sqlite_name(None, None, range_ref)
        return TableReference(original, None, None, range_ref, sqlite_name)

    # Try to match sheet.table format
    match = re.match(sheet_table_pattern, ref)
    if match:
        sheet_name = match.group(1) or match.group(2)
        table_name = match.group(3)
        # Remove quotes if present
        if table_name.startswith('"') and table_name.endswith('"'):
            table_name = table_name[1:-1].replace('""', '"')
        sqlite_name = _generate_sqlite_name(sheet_name, table_name, None)
        return TableReference(original, sheet_name, table_name, None, sqlite_name)

    # Otherwise, treat as a simple table name
    table_name = ref
    # Remove quotes if present
    if table_name.startswith('"') and table_name.endswith('"'):
        table_name = table_name[1:-1].replace('""', '"')
    sqlite_name = _generate_sqlite_name(None, table_name, None)
    return TableReference(original, None, table_name, None, sqlite_name)


def validate_query_syntax(query: str) -> None:
    """
    Perform basic SQL syntax validation.
    
    Args:
        query: SQL query string
        
    Raises:
        QuerySyntaxError: If basic syntax issues detected
        
    Note: This is not a full SQL parser. SQLite will catch most
    syntax errors during execution.
    
    TODO: Implement basic validation
    """
    # TODO: Check for unclosed quotes
    # TODO: Check for unclosed parentheses
    # TODO: Check for empty query
    pass


def is_parameterized_query(query: str) -> bool:
    """
    Check if query contains parameter placeholders.

    Args:
        query: SQL query string

    Returns:
        True if query contains ? placeholders
    """
    return count_parameters(query) > 0


def count_parameters(query: str) -> int:
    """
    Count parameter placeholders in query.

    Args:
        query: SQL query string

    Returns:
        Number of ? placeholders

    TODO: Improve to handle quoted strings
    """
    count = 0
    in_string = False
    string_char = None
    i = 0

    while i < len(query):
        char = query[i]

        # Handle string literals
        if char in ("'", '"') and not in_string:
            in_string = True
            string_char = char
        elif char == string_char and in_string:
            # Check for escaped quote
            if i + 1 < len(query) and query[i + 1] == string_char:
                i += 1  # Skip the escaped quote
            else:
                in_string = False
                string_char = None
        elif char == '?' and not in_string:
            count += 1

        i += 1

    return count


def substitute_references(query: str, mapping: dict[str, str]) -> str:
    """
    Rewrite query replacing Excel references with SQLite table names.

    Args:
        query: Original SQL query with Excel references
        mapping: Dict of original_ref -> sqlite_table_name

    Returns:
        Query with references replaced

    Example:
        query = "SELECT * FROM Sheet1.Orders"
        mapping = {"Sheet1.Orders": "sheet1_orders"}
        result = "SELECT * FROM sheet1_orders"

    TODO: Implement substitution logic
    """
    if not mapping:
        return query

    result = query

    # Sort mapping by length (longest first) to avoid partial replacements
    sorted_refs = sorted(mapping.keys(), key=len, reverse=True)

    for original_ref in sorted_refs:
        sqlite_name = mapping[original_ref]

        # Create a regex pattern that matches the reference as a whole identifier
        # This handles both quoted and unquoted identifiers
        # Pattern should match the reference but not as part of a larger word

        # Escape special regex characters in the reference
        escaped_ref = re.escape(original_ref)

        # Replace the dots with literal dots in the pattern
        # Handle both quoted ('Sheet Name'.Table) and unquoted (Sheet1.Table) formats
        pattern = r'\b' + escaped_ref + r'\b'

        # For references with quotes, we need a different pattern
        if "'" in original_ref:
            # Use the escaped pattern as-is for quoted references
            pattern = escaped_ref

        # Replace all occurrences
        # Use word boundaries to ensure we don't replace partial matches
        result = re.sub(pattern, sqlite_name, result, flags=re.IGNORECASE)

    return result


def sanitize_identifier(name: str) -> str:
    """
    Convert a name to a valid SQLite identifier.

    Args:
        name: Original name (may contain spaces, special chars)

    Returns:
        Valid SQLite identifier (quoted if necessary)
    """
    # Check if quoting is needed
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        # Valid unquoted identifier
        return name
    else:
        # Needs quoting - escape any double quotes
        escaped = name.replace('"', '""')
        return f'"{escaped}"'


# Helper functions

def _remove_string_literals(query: str) -> str:
    """
    Replace string literals with placeholders to avoid false matches.

    Preserves single-quoted strings that are followed by . or ! as they
    are likely sheet references, not string literals.

    Args:
        query: SQL query string

    Returns:
        Query with string literals replaced by spaces (but sheet refs preserved)
    """
    result = []
    in_string = False
    string_char = None
    i = 0

    while i < len(query):
        char = query[i]

        if char in ("'", '"') and not in_string:
            # Check if this single quote is a sheet reference (followed by . or !)
            if char == "'":
                # Find the closing quote
                j = i + 1
                while j < len(query):
                    if query[j] == "'" and (j + 1 >= len(query) or query[j + 1] != "'"):
                        # Found closing quote
                        # Check what follows
                        if j + 1 < len(query) and query[j + 1] in ('.', '!'):
                            # This is a sheet reference, preserve it
                            while i <= j + 1:
                                result.append(query[i])
                                i += 1
                            i -= 1  # Back up one because loop will increment
                            break
                        else:
                            # Regular string literal, replace it
                            in_string = True
                            string_char = char
                            result.append(' ')
                            break
                    j += 1
                else:
                    # No closing quote found, treat as string
                    in_string = True
                    string_char = char
                    result.append(' ')
            else:
                # Double quote - always an identifier, keep it
                in_string = True
                string_char = char
                result.append(char)
        elif char == string_char and in_string:
            # Check for escaped quote
            if i + 1 < len(query) and query[i + 1] == string_char:
                i += 1  # Skip the escaped quote
                if string_char == '"':
                    result.append(char)
                    result.append(char)
                else:
                    result.append(' ')
                    result.append(' ')
            else:
                # Closing quote
                is_double_quote = (string_char == '"')
                in_string = False
                string_char = None
                if is_double_quote:
                    result.append(char)
                else:
                    result.append(' ')
        elif in_string:
            if string_char == '"':
                result.append(char)  # Preserve double-quoted content
            else:
                result.append(' ')  # Replace single-quoted content with space
        else:
            result.append(char)

        i += 1

    return ''.join(result)


def _remove_comments(query: str) -> str:
    """
    Remove SQL comments from query.

    Args:
        query: SQL query string

    Returns:
        Query with comments removed
    """
    # Remove single-line comments (-- comment)
    query = re.sub(r'--[^\n]*', ' ', query)

    # Remove multi-line comments (/* comment */)
    query = re.sub(r'/\*.*?\*/', ' ', query, flags=re.DOTALL)

    return query


def _extract_reference_at_position(query: str, start_pos: int) -> Optional[str]:
    """
    Extract a table reference starting at the given position.

    Args:
        query: SQL query string
        start_pos: Position to start extracting from

    Returns:
        The extracted reference string, or None if not found
    """
    # Skip whitespace
    while start_pos < len(query) and query[start_pos].isspace():
        start_pos += 1

    if start_pos >= len(query):
        return None

    # Check if it starts with a quote (for sheet names with spaces)
    if query[start_pos] == "'":
        # Extract quoted sheet name
        end_quote = query.find("'", start_pos + 1)
        if end_quote == -1:
            return None

        # Check if there's a dot or exclamation mark after the quote
        next_pos = end_quote + 1
        if next_pos < len(query) and query[next_pos] in ('.', '!'):
            # Continue extracting the rest (table name or range)
            rest_start = next_pos + 1
            rest = _extract_identifier(query, rest_start)
            if rest:
                return query[start_pos:end_quote + 1] + query[next_pos] + rest
        return None

    # Extract identifier (could be sheet name, table name, or range)
    identifier = _extract_identifier(query, start_pos)

    if not identifier:
        return None

    # Check if there's a dot or exclamation mark after the identifier
    next_pos = start_pos + len(identifier)
    if next_pos < len(query) and query[next_pos] in ('.', '!'):
        # There's more - extract the rest
        rest_start = next_pos + 1
        # Skip whitespace after the separator
        while rest_start < len(query) and query[rest_start].isspace():
            rest_start += 1

        # Check for quoted identifier
        if rest_start < len(query) and query[rest_start] == "'":
            end_quote = query.find("'", rest_start + 1)
            if end_quote != -1:
                rest = query[rest_start:end_quote + 1]
            else:
                rest = _extract_identifier(query, rest_start)
        else:
            rest = _extract_identifier(query, rest_start)

        if rest:
            return identifier + query[next_pos] + rest

    return identifier


def _extract_identifier(query: str, start_pos: int) -> Optional[str]:
    """
    Extract a SQL identifier or Excel range starting at the given position.

    Args:
        query: SQL query string
        start_pos: Position to start extracting from

    Returns:
        The extracted identifier, or None if not found
    """
    if start_pos >= len(query):
        return None

    # Check for quoted identifier
    if query[start_pos] == '"':
        # Extract until closing quote
        end_pos = start_pos + 1
        while end_pos < len(query):
            if query[end_pos] == '"':
                # Check for escaped quote
                if end_pos + 1 < len(query) and query[end_pos + 1] == '"':
                    end_pos += 2
                else:
                    return query[start_pos:end_pos + 1]
            else:
                end_pos += 1
        return None

    # Check for single-quoted identifier (sheet names)
    if query[start_pos] == "'":
        end_pos = start_pos + 1
        while end_pos < len(query):
            if query[end_pos] == "'":
                # Check for escaped quote
                if end_pos + 1 < len(query) and query[end_pos + 1] == "'":
                    end_pos += 2
                else:
                    return query[start_pos:end_pos + 1]
            else:
                end_pos += 1
        return None

    # Extract unquoted identifier or range
    # Valid characters: letters, numbers, underscore, $, colon (for ranges)
    end_pos = start_pos
    while end_pos < len(query):
        char = query[end_pos]
        if char.isalnum() or char in ('_', '$', ':'):
            end_pos += 1
        else:
            break

    if end_pos > start_pos:
        return query[start_pos:end_pos]

    return None


def _generate_sqlite_name(
    sheet_name: Optional[str],
    table_name: Optional[str],
    range_ref: Optional[str]
) -> str:
    """
    Generate a sanitized SQLite table name.

    Args:
        sheet_name: Sheet name (if any)
        table_name: Table name (if any)
        range_ref: Range reference (if any)

    Returns:
        Sanitized name suitable for SQLite (lowercase, alphanumeric + underscore)
    """
    parts = []

    if sheet_name:
        # Sanitize sheet name
        sanitized = re.sub(r'[^a-zA-Z0-9_]+', '_', sheet_name.lower())
        parts.append(sanitized.strip('_'))

    if table_name:
        # Sanitize table name
        sanitized = re.sub(r'[^a-zA-Z0-9_]+', '_', table_name.lower())
        parts.append(sanitized.strip('_'))

    if range_ref:
        # Sanitize range (e.g., A1:M100 -> a1_m100)
        sanitized = re.sub(r'[^a-zA-Z0-9]+', '_', range_ref.lower())
        parts.append(sanitized.strip('_'))

    # Join parts with underscore
    name = '_'.join(parts)

    # Ensure the name starts with a letter or underscore
    if name and name[0].isdigit():
        name = 'r_' + name

    # If name is empty, use a default
    if not name:
        name = 'table_ref'

    return name
