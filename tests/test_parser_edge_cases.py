"""
Edge case tests for parser.py implementation
"""

from parser import (
    extract_table_references,
    parse_reference,
    substitute_references,
)


def test_absolute_range():
    """Test parsing absolute range with $ signs"""
    ref = parse_reference("$A$1:$M$100")
    assert ref.range_ref == "$A$1:$M$100"
    assert ref.sqlite_name == "a_1_m_100"
    print("[PASS] test_absolute_range")


def test_quoted_sheet_with_range():
    """Test parsing quoted sheet with range"""
    ref = parse_reference("'My Sheet'!A1:B10")
    assert ref.sheet_name == "My Sheet"
    assert ref.range_ref == "A1:B10"
    assert ref.sqlite_name == "my_sheet_a1_b10"
    print("[PASS] test_quoted_sheet_with_range")


def test_subquery():
    """Test extracting references from subquery"""
    query = """
    SELECT * FROM (
        SELECT * FROM Orders WHERE status = 'active'
    ) AS active_orders
    JOIN Customers ON active_orders.customer_id = Customers.id
    """
    refs = extract_table_references(query)
    table_names = {ref.table_name for ref in refs}
    assert "Orders" in table_names
    assert "Customers" in table_names
    print("[PASS] test_subquery")


def test_multiple_joins():
    """Test extracting references from multiple JOINs"""
    query = """
    SELECT * FROM Orders
    LEFT JOIN Customers ON Orders.customer_id = Customers.id
    INNER JOIN Products ON Orders.product_id = Products.id
    RIGHT JOIN Suppliers ON Products.supplier_id = Suppliers.id
    """
    refs = extract_table_references(query)
    assert len(refs) == 4
    table_names = {ref.table_name for ref in refs}
    assert "Orders" in table_names
    assert "Customers" in table_names
    assert "Products" in table_names
    assert "Suppliers" in table_names
    print("[PASS] test_multiple_joins")


def test_update_statement():
    """Test extracting reference from UPDATE statement"""
    query = "UPDATE Orders SET status = 'completed' WHERE id = 1"
    refs = extract_table_references(query)
    assert len(refs) == 1
    assert refs[0].table_name == "Orders"
    print("[PASS] test_update_statement")


def test_insert_statement():
    """Test extracting reference from INSERT statement"""
    query = "INSERT INTO Orders (customer_id, total) VALUES (1, 100.00)"
    refs = extract_table_references(query)
    assert len(refs) == 1
    assert refs[0].table_name == "Orders"
    print("[PASS] test_insert_statement")


def test_case_insensitive_keywords():
    """Test that SQL keywords are case insensitive"""
    query = "select * from Orders join Customers on Orders.id = Customers.order_id"
    refs = extract_table_references(query)
    assert len(refs) == 2
    print("[PASS] test_case_insensitive_keywords")


def test_substitute_multiple():
    """Test substituting multiple references"""
    query = "SELECT * FROM Orders JOIN Customers ON Orders.customer_id = Customers.id"
    mapping = {
        "Orders": "orders_temp",
        "Customers": "customers_temp"
    }
    result = substitute_references(query, mapping)
    assert "orders_temp" in result
    assert "customers_temp" in result
    print("[PASS] test_substitute_multiple")


def test_substitute_sheet_qualified_multiple():
    """Test substituting multiple sheet-qualified references"""
    query = "SELECT * FROM Sheet1.Orders JOIN Sheet2.Customers ON Sheet1.Orders.id = Sheet2.Customers.order_id"
    mapping = {
        "Sheet1.Orders": "sheet1_orders",
        "Sheet2.Customers": "sheet2_customers"
    }
    result = substitute_references(query, mapping)
    assert "sheet1_orders" in result
    assert "sheet2_customers" in result
    print("[PASS] test_substitute_sheet_qualified_multiple")


def test_parse_quoted_table_name():
    """Test parsing double-quoted table name"""
    ref = parse_reference('"My Table"')
    assert ref.table_name == "My Table"
    assert ref.sqlite_name == "my_table"
    print("[PASS] test_parse_quoted_table_name")


def test_range_starting_with_number():
    """Test that range names starting with numbers are prefixed"""
    ref = parse_reference("A1:B10")
    # The sqlite_name should be 'a1_b10', not starting with a digit
    assert ref.sqlite_name[0].isalpha() or ref.sqlite_name[0] == '_'
    print("[PASS] test_range_starting_with_number")


def test_complex_cte():
    """Test extracting references from complex CTE with multiple subqueries"""
    query = """
    WITH
        top_customers AS (
            SELECT * FROM Customers WHERE tier = 'gold'
        ),
        recent_orders AS (
            SELECT * FROM Orders WHERE date > '2024-01-01'
        )
    SELECT * FROM top_customers
    JOIN recent_orders ON top_customers.id = recent_orders.customer_id
    JOIN Products ON recent_orders.product_id = Products.id
    """
    refs = extract_table_references(query)
    table_names = {ref.table_name for ref in refs}
    # Should extract Customers, Orders, and Products (not the CTEs)
    assert "Customers" in table_names
    assert "Orders" in table_names
    assert "Products" in table_names
    print("[PASS] test_complex_cte")


def test_comment_in_query():
    """Test that SQL comments don't interfere with parsing"""
    query = """
    -- This is a comment with FROM keyword
    SELECT * FROM Orders
    /* Another comment
       with FROM in it */
    WHERE status = 'active'
    """
    refs = extract_table_references(query)
    assert len(refs) == 1
    assert refs[0].table_name == "Orders"
    print("[PASS] test_comment_in_query")


def test_string_with_keyword():
    """Test that keywords in strings don't create false positives"""
    query = "SELECT * FROM Orders WHERE note = 'JOIN the team'"
    refs = extract_table_references(query)
    assert len(refs) == 1
    assert refs[0].table_name == "Orders"
    print("[PASS] test_string_with_keyword")


def test_escaped_quotes_in_string():
    """Test counting parameters with escaped quotes"""
    from parser import count_parameters
    query = "SELECT * FROM Orders WHERE name = 'O''Brien' AND id = ?"
    count = count_parameters(query)
    assert count == 1
    print("[PASS] test_escaped_quotes_in_string")


if __name__ == "__main__":
    # Run all tests
    test_absolute_range()
    test_quoted_sheet_with_range()
    test_subquery()
    test_multiple_joins()
    test_update_statement()
    test_insert_statement()
    test_case_insensitive_keywords()
    test_substitute_multiple()
    test_substitute_sheet_qualified_multiple()
    test_parse_quoted_table_name()
    test_range_starting_with_number()
    test_complex_cte()
    test_comment_in_query()
    test_string_with_keyword()
    test_escaped_quotes_in_string()

    print("\n[SUCCESS] All edge case tests passed!")
