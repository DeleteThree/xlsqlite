"""
Basic tests for parser.py implementation
"""

from parser import (
    extract_table_references,
    parse_reference,
    substitute_references,
    is_parameterized_query,
    count_parameters,
    TableReference
)


def test_parse_simple_table():
    """Test parsing a simple table name"""
    ref = parse_reference("Orders")
    assert ref.table_name == "Orders"
    assert ref.sheet_name is None
    assert ref.range_ref is None
    assert ref.sqlite_name == "orders"
    print("[PASS] test_parse_simple_table")


def test_parse_sheet_table():
    """Test parsing Sheet.Table format"""
    ref = parse_reference("Sheet1.Orders")
    assert ref.table_name == "Orders"
    assert ref.sheet_name == "Sheet1"
    assert ref.range_ref is None
    assert ref.sqlite_name == "sheet1_orders"
    print("[PASS] test_parse_sheet_table")


def test_parse_quoted_sheet_table():
    """Test parsing 'Sheet Name'.Table format"""
    ref = parse_reference("'Sheet Name'.Orders")
    assert ref.table_name == "Orders"
    assert ref.sheet_name == "Sheet Name"
    assert ref.range_ref is None
    assert ref.sqlite_name == "sheet_name_orders"
    print("[PASS] test_parse_quoted_sheet_table")


def test_parse_simple_range():
    """Test parsing a simple range"""
    ref = parse_reference("A1:M100")
    assert ref.range_ref == "A1:M100"
    assert ref.table_name is None
    assert ref.sheet_name is None
    assert ref.sqlite_name == "a1_m100"
    print("[PASS] test_parse_simple_range")


def test_parse_cross_sheet_range():
    """Test parsing Sheet!A1:B10 format"""
    ref = parse_reference("Sheet2!A1:B50")
    assert ref.range_ref == "A1:B50"
    assert ref.sheet_name == "Sheet2"
    assert ref.table_name is None
    assert ref.sqlite_name == "sheet2_a1_b50"
    print("[PASS] test_parse_cross_sheet_range")


def test_extract_simple_query():
    """Test extracting references from a simple query"""
    query = "SELECT * FROM Orders"
    refs = extract_table_references(query)
    assert len(refs) == 1
    assert refs[0].table_name == "Orders"
    print("[PASS] test_extract_simple_query")


def test_extract_join_query():
    """Test extracting references from a JOIN query"""
    query = "SELECT * FROM Orders JOIN Customers ON Orders.customer_id = Customers.id"
    refs = extract_table_references(query)
    assert len(refs) == 2
    table_names = {ref.table_name for ref in refs}
    assert "Orders" in table_names
    assert "Customers" in table_names
    print("[PASS] test_extract_join_query")


def test_extract_sheet_qualified():
    """Test extracting sheet-qualified references"""
    query = "SELECT * FROM Sheet1.Orders JOIN Sheet2.Customers ON Orders.id = Customers.order_id"
    refs = extract_table_references(query)
    assert len(refs) == 2
    print("[PASS] test_extract_sheet_qualified")


def test_substitute_simple():
    """Test substituting references"""
    query = "SELECT * FROM Orders WHERE id = 1"
    mapping = {"Orders": "orders_temp"}
    result = substitute_references(query, mapping)
    assert "orders_temp" in result
    assert "Orders" not in result or result.count("Orders") == 0
    print("[PASS] test_substitute_simple")


def test_substitute_sheet_qualified():
    """Test substituting sheet-qualified references"""
    query = "SELECT * FROM Sheet1.Orders"
    mapping = {"Sheet1.Orders": "sheet1_orders"}
    result = substitute_references(query, mapping)
    assert "sheet1_orders" in result
    print("[PASS] test_substitute_sheet_qualified")


def test_count_parameters_none():
    """Test counting parameters with no placeholders"""
    query = "SELECT * FROM Orders"
    count = count_parameters(query)
    assert count == 0
    print("[PASS] test_count_parameters_none")


def test_count_parameters_single():
    """Test counting parameters with one placeholder"""
    query = "SELECT * FROM Orders WHERE id = ?"
    count = count_parameters(query)
    assert count == 1
    print("[PASS] test_count_parameters_single")


def test_count_parameters_multiple():
    """Test counting parameters with multiple placeholders"""
    query = "SELECT * FROM Orders WHERE id = ? AND status = ?"
    count = count_parameters(query)
    assert count == 2
    print("[PASS] test_count_parameters_multiple")


def test_count_parameters_in_string():
    """Test that ? inside strings are not counted"""
    query = "SELECT * FROM Orders WHERE note = 'What? Why?'"
    count = count_parameters(query)
    assert count == 0
    print("[PASS] test_count_parameters_in_string")


def test_is_parameterized_true():
    """Test is_parameterized_query returns True"""
    query = "SELECT * FROM Orders WHERE id = ?"
    assert is_parameterized_query(query) is True
    print("[PASS] test_is_parameterized_true")


def test_is_parameterized_false():
    """Test is_parameterized_query returns False"""
    query = "SELECT * FROM Orders"
    assert is_parameterized_query(query) is False
    print("[PASS] test_is_parameterized_false")


def test_extract_cte():
    """Test extracting references from CTE query"""
    query = """
    WITH top_orders AS (
        SELECT * FROM Orders WHERE amount > 1000
    )
    SELECT * FROM top_orders JOIN Customers ON top_orders.customer_id = Customers.id
    """
    refs = extract_table_references(query)
    # Should extract Orders and Customers (top_orders is a CTE, not a table reference)
    table_names = {ref.table_name for ref in refs}
    assert "Orders" in table_names
    assert "Customers" in table_names
    print("[PASS] test_extract_cte")


def test_extract_with_string_literals():
    """Test that string literals don't interfere with extraction"""
    query = "SELECT * FROM Orders WHERE status = 'FROM pending'"
    refs = extract_table_references(query)
    assert len(refs) == 1
    assert refs[0].table_name == "Orders"
    print("[PASS] test_extract_with_string_literals")


if __name__ == "__main__":
    # Run all tests
    test_parse_simple_table()
    test_parse_sheet_table()
    test_parse_quoted_sheet_table()
    test_parse_simple_range()
    test_parse_cross_sheet_range()
    test_extract_simple_query()
    test_extract_join_query()
    test_extract_sheet_qualified()
    test_substitute_simple()
    test_substitute_sheet_qualified()
    test_count_parameters_none()
    test_count_parameters_single()
    test_count_parameters_multiple()
    test_count_parameters_in_string()
    test_is_parameterized_true()
    test_is_parameterized_false()
    test_extract_cte()
    test_extract_with_string_literals()

    print("\n[SUCCESS] All tests passed!")
