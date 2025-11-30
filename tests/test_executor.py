"""
Tests for executor.py module.

These tests can run standalone without Excel/xl() dependencies.
"""

import pytest
import sqlite3
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from executor import (
    create_connection,
    execute_query,
    execute_multiple_statements,
    split_statements,
    detect_query_type,
    get_execution_plan,
    get_sqlite_version,
    check_feature_support,
    ExecutionResult,
)


class TestCreateConnection:
    """Tests for create_connection()"""
    
    def test_creates_in_memory_db(self):
        conn = create_connection()
        assert conn is not None
        
        # Verify it's in-memory
        cursor = conn.cursor()
        cursor.execute("PRAGMA database_list")
        dbs = cursor.fetchall()
        assert any(":memory:" in str(db) or db[2] == "" for db in dbs)
        conn.close()
    
    def test_foreign_keys_enabled(self):
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        assert result[0] == 1
        conn.close()


class TestDetectQueryType:
    """Tests for detect_query_type()"""
    
    def test_select(self):
        assert detect_query_type("SELECT * FROM t") == "SELECT"
        assert detect_query_type("  SELECT * FROM t") == "SELECT"
        assert detect_query_type("select * from t") == "SELECT"
    
    def test_insert(self):
        assert detect_query_type("INSERT INTO t VALUES (1)") == "INSERT"
    
    def test_update(self):
        assert detect_query_type("UPDATE t SET x = 1") == "UPDATE"
    
    def test_delete(self):
        assert detect_query_type("DELETE FROM t") == "DELETE"
    
    def test_create(self):
        assert detect_query_type("CREATE TABLE t (x INT)") == "CREATE"
    
    def test_drop(self):
        assert detect_query_type("DROP TABLE t") == "DROP"
    
    def test_pragma(self):
        assert detect_query_type("PRAGMA table_info(t)") == "PRAGMA"
    
    def test_explain(self):
        assert detect_query_type("EXPLAIN QUERY PLAN SELECT * FROM t") == "EXPLAIN"
    
    def test_cte_with_select(self):
        query = "WITH cte AS (SELECT 1) SELECT * FROM cte"
        assert detect_query_type(query) == "SELECT"


class TestSplitStatements:
    """Tests for split_statements()"""
    
    def test_single_statement(self):
        result = split_statements("SELECT * FROM t")
        assert result == ["SELECT * FROM t"]
    
    def test_multiple_statements(self):
        result = split_statements("SELECT 1; SELECT 2")
        assert result == ["SELECT 1", "SELECT 2"]
    
    def test_semicolon_in_string(self):
        result = split_statements("SELECT 'a;b' FROM t")
        assert result == ["SELECT 'a;b' FROM t"]
    
    def test_double_quote_string(self):
        result = split_statements('SELECT "a;b" FROM t')
        assert result == ['SELECT "a;b" FROM t']
    
    def test_escaped_quote(self):
        result = split_statements("SELECT 'it''s' FROM t")
        assert result == ["SELECT 'it''s' FROM t"]
    
    def test_empty_statements_filtered(self):
        result = split_statements("SELECT 1; ; SELECT 2")
        assert result == ["SELECT 1", "SELECT 2"]
    
    def test_trailing_semicolon(self):
        result = split_statements("SELECT 1;")
        assert result == ["SELECT 1"]


class TestExecuteQuery:
    """Tests for execute_query()"""
    
    @pytest.fixture
    def conn_with_data(self):
        """Create connection with test table."""
        conn = create_connection()
        conn.execute("CREATE TABLE test (id INTEGER, name TEXT, value REAL)")
        conn.execute("INSERT INTO test VALUES (1, 'Alice', 100.5)")
        conn.execute("INSERT INTO test VALUES (2, 'Bob', 200.0)")
        conn.execute("INSERT INTO test VALUES (3, 'Carol', NULL)")
        conn.commit()
        yield conn
        conn.close()
    
    def test_simple_select(self, conn_with_data):
        result = execute_query(conn_with_data, "SELECT * FROM test")
        
        assert result.query_type == "SELECT"
        assert result.columns == ["id", "name", "value"]
        assert len(result.rows) == 3
        assert result.rows[0] == (1, "Alice", 100.5)
    
    def test_select_with_where(self, conn_with_data):
        result = execute_query(
            conn_with_data, 
            "SELECT * FROM test WHERE id > ?",
            (1,)
        )
        
        assert len(result.rows) == 2
    
    def test_select_with_order(self, conn_with_data):
        result = execute_query(
            conn_with_data,
            "SELECT * FROM test ORDER BY name"
        )
        
        assert result.rows[0][1] == "Alice"
        assert result.rows[1][1] == "Bob"
        assert result.rows[2][1] == "Carol"
    
    def test_insert_returns_rowcount(self, conn_with_data):
        result = execute_query(
            conn_with_data,
            "INSERT INTO test VALUES (4, 'Dave', 300.0)"
        )
        
        assert result.query_type == "INSERT"
        assert result.rowcount == 1
        assert result.lastrowid == 4
    
    def test_update_returns_rowcount(self, conn_with_data):
        result = execute_query(
            conn_with_data,
            "UPDATE test SET value = 999 WHERE id <= 2"
        )
        
        assert result.query_type == "UPDATE"
        assert result.rowcount == 2
    
    def test_delete_returns_rowcount(self, conn_with_data):
        result = execute_query(
            conn_with_data,
            "DELETE FROM test WHERE id = 1"
        )
        
        assert result.query_type == "DELETE"
        assert result.rowcount == 1
    
    def test_execution_time_recorded(self, conn_with_data):
        result = execute_query(conn_with_data, "SELECT * FROM test")
        
        assert result.execution_time_ms >= 0
    
    def test_pragma(self, conn_with_data):
        result = execute_query(conn_with_data, "PRAGMA table_info(test)")
        
        assert result.query_type == "PRAGMA"
        assert len(result.rows) == 3  # 3 columns
    
    def test_aggregation(self, conn_with_data):
        result = execute_query(
            conn_with_data,
            "SELECT COUNT(*), SUM(value), AVG(value) FROM test"
        )
        
        assert result.rows[0][0] == 3  # COUNT
        assert result.rows[0][1] == 300.5  # SUM (100.5 + 200.0)


class TestExecuteMultipleStatements:
    """Tests for execute_multiple_statements()"""
    
    def test_multiple_selects_returns_last(self):
        conn = create_connection()
        conn.execute("CREATE TABLE t1 (x INT)")
        conn.execute("CREATE TABLE t2 (y INT)")
        conn.execute("INSERT INTO t1 VALUES (1)")
        conn.execute("INSERT INTO t2 VALUES (2)")
        conn.commit()
        
        result = execute_multiple_statements(
            conn,
            "SELECT * FROM t1; SELECT * FROM t2"
        )
        
        # Should return result of last SELECT
        assert result.columns == ["y"]
        assert result.rows == [(2,)]
        conn.close()
    
    def test_ddl_then_select(self):
        conn = create_connection()
        
        result = execute_multiple_statements(
            conn,
            "CREATE TABLE t (x INT); INSERT INTO t VALUES (42); SELECT * FROM t"
        )
        
        assert result.query_type == "SELECT"
        assert result.rows == [(42,)]
        conn.close()
    
    def test_empty_sql(self):
        conn = create_connection()
        result = execute_multiple_statements(conn, "")
        
        assert result.query_type == "EMPTY"
        assert result.rows == []
        conn.close()


class TestWindowFunctions:
    """Tests for window function support."""
    
    @pytest.fixture
    def conn_with_sales(self):
        conn = create_connection()
        conn.execute("""
            CREATE TABLE sales (
                id INTEGER,
                category TEXT,
                amount REAL,
                date TEXT
            )
        """)
        conn.execute("INSERT INTO sales VALUES (1, 'A', 100, '2024-01-01')")
        conn.execute("INSERT INTO sales VALUES (2, 'A', 150, '2024-01-02')")
        conn.execute("INSERT INTO sales VALUES (3, 'B', 200, '2024-01-01')")
        conn.execute("INSERT INTO sales VALUES (4, 'B', 250, '2024-01-02')")
        conn.execute("INSERT INTO sales VALUES (5, 'A', 120, '2024-01-03')")
        conn.commit()
        yield conn
        conn.close()
    
    def test_row_number(self, conn_with_sales):
        result = execute_query(
            conn_with_sales,
            """
            SELECT id, category, 
                   ROW_NUMBER() OVER (PARTITION BY category ORDER BY date) as rn
            FROM sales
            """
        )
        
        assert "rn" in result.columns
        # Check row numbers are assigned
        assert len(result.rows) == 5
    
    def test_rank(self, conn_with_sales):
        result = execute_query(
            conn_with_sales,
            """
            SELECT id, amount,
                   RANK() OVER (ORDER BY amount DESC) as rank
            FROM sales
            """
        )
        
        assert "rank" in result.columns
    
    def test_running_total(self, conn_with_sales):
        result = execute_query(
            conn_with_sales,
            """
            SELECT id, amount,
                   SUM(amount) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING) as running_total
            FROM sales
            ORDER BY date
            """
        )
        
        assert "running_total" in result.columns
    
    def test_lag_lead(self, conn_with_sales):
        result = execute_query(
            conn_with_sales,
            """
            SELECT id, amount,
                   LAG(amount, 1) OVER (ORDER BY date) as prev_amount,
                   LEAD(amount, 1) OVER (ORDER BY date) as next_amount
            FROM sales
            ORDER BY date
            """
        )
        
        assert "prev_amount" in result.columns
        assert "next_amount" in result.columns


class TestCTEs:
    """Tests for Common Table Expression support."""
    
    def test_simple_cte(self):
        conn = create_connection()
        conn.execute("CREATE TABLE t (x INT)")
        conn.execute("INSERT INTO t VALUES (1), (2), (3)")
        conn.commit()
        
        result = execute_query(
            conn,
            "WITH doubled AS (SELECT x * 2 as d FROM t) SELECT * FROM doubled"
        )
        
        assert result.rows == [(2,), (4,), (6,)]
        conn.close()
    
    def test_multiple_ctes(self):
        conn = create_connection()
        conn.execute("CREATE TABLE t (x INT)")
        conn.execute("INSERT INTO t VALUES (1), (2), (3)")
        conn.commit()
        
        result = execute_query(
            conn,
            """
            WITH 
                a AS (SELECT x FROM t WHERE x <= 2),
                b AS (SELECT x * 10 as y FROM a)
            SELECT * FROM b
            """
        )
        
        assert result.rows == [(10,), (20,)]
        conn.close()
    
    def test_recursive_cte(self):
        conn = create_connection()
        
        result = execute_query(
            conn,
            """
            WITH RECURSIVE cnt(x) AS (
                SELECT 1
                UNION ALL
                SELECT x + 1 FROM cnt WHERE x < 5
            )
            SELECT x FROM cnt
            """
        )
        
        assert result.rows == [(1,), (2,), (3,), (4,), (5,)]
        conn.close()


class TestJoins:
    """Tests for JOIN operations."""
    
    @pytest.fixture
    def conn_with_orders(self):
        conn = create_connection()
        conn.execute("CREATE TABLE customers (id INT, name TEXT)")
        conn.execute("CREATE TABLE orders (id INT, customer_id INT, total REAL)")
        conn.execute("INSERT INTO customers VALUES (1, 'Alice'), (2, 'Bob')")
        conn.execute("INSERT INTO orders VALUES (1, 1, 100), (2, 1, 150), (3, 2, 200)")
        conn.commit()
        yield conn
        conn.close()
    
    def test_inner_join(self, conn_with_orders):
        result = execute_query(
            conn_with_orders,
            """
            SELECT c.name, o.total 
            FROM customers c 
            JOIN orders o ON c.id = o.customer_id
            """
        )
        
        assert len(result.rows) == 3
    
    def test_left_join(self, conn_with_orders):
        # Add customer with no orders
        conn_with_orders.execute("INSERT INTO customers VALUES (3, 'Carol')")
        conn_with_orders.commit()
        
        result = execute_query(
            conn_with_orders,
            """
            SELECT c.name, o.total 
            FROM customers c 
            LEFT JOIN orders o ON c.id = o.customer_id
            """
        )
        
        assert len(result.rows) == 4  # 3 orders + 1 NULL for Carol


class TestSQLiteVersion:
    """Tests for version and feature checking."""
    
    def test_get_version(self):
        version = get_sqlite_version()
        
        # Should be in format X.Y.Z
        parts = version.split('.')
        assert len(parts) >= 2
        assert all(p.isdigit() for p in parts)
    
    def test_feature_support(self):
        features = check_feature_support()
        
        # We know these should be available in SQLite 3.30+
        assert "window_functions" in features
        assert "cte" in features
        
        # In Python 3.9 with SQLite 3.30+, these should be True
        assert features["window_functions"] is True
        assert features["cte"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
