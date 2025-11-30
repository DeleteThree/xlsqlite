"""
Tests for xl() integration in schema.py

These tests verify that resolve_reference() correctly calls xl()
with the appropriate reference strings.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sys

from parser import TableReference
from schema import resolve_reference
from errors import RangeResolutionError, EmptyRangeError


class TestXLIntegration:
    """Test xl() integration in resolve_reference()"""

    def test_simple_table_calls_xl_correctly(self):
        """Simple table name should call xl("TableName")"""
        # Create reference
        ref = TableReference(
            original="Orders",
            sheet_name=None,
            table_name="Orders",
            range_ref=None,
            sqlite_name="orders"
        )

        # Mock the xl module
        mock_xl_func = Mock(return_value=pd.DataFrame({'A': [1, 2], 'B': [3, 4]}))
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            # Reload schema to pick up mocked xl
            import importlib
            import schema
            importlib.reload(schema)

            result = schema.resolve_reference(ref)

            # Verify xl was called with correct reference
            mock_xl_func.assert_called_once_with("Orders", headers=True)

            # Verify result is a DataFrame
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2

    def test_sheet_qualified_table_calls_xl_correctly(self):
        """Sheet.Table should call xl("Sheet.Table")"""
        ref = TableReference(
            original="Sheet1.Orders",
            sheet_name="Sheet1",
            table_name="Orders",
            range_ref=None,
            sqlite_name="sheet1_orders"
        )

        mock_xl_func = Mock(return_value=pd.DataFrame({'A': [1, 2], 'B': [3, 4]}))
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            result = schema.resolve_reference(ref)

            # Verify xl was called with Sheet.Table format
            mock_xl_func.assert_called_once_with("Sheet1.Orders", headers=True)

    def test_simple_range_calls_xl_correctly(self):
        """Simple range should call xl("A1:M100")"""
        ref = TableReference(
            original="A1:M100",
            sheet_name=None,
            table_name=None,
            range_ref="A1:M100",
            sqlite_name="a1_m100"
        )

        mock_xl_func = Mock(return_value=pd.DataFrame({'A': [1, 2], 'B': [3, 4]}))
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            result = schema.resolve_reference(ref)

            # Verify xl was called with range
            mock_xl_func.assert_called_once_with("A1:M100", headers=True)

    def test_cross_sheet_range_calls_xl_correctly(self):
        """Cross-sheet range should call xl("Sheet2!A1:B10")"""
        ref = TableReference(
            original="Sheet2!A1:B10",
            sheet_name="Sheet2",
            table_name=None,
            range_ref="A1:B10",
            sqlite_name="sheet2_a1_b10"
        )

        mock_xl_func = Mock(return_value=pd.DataFrame({'A': [1, 2], 'B': [3, 4]}))
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            result = schema.resolve_reference(ref)

            # Verify xl was called with Sheet!Range format
            mock_xl_func.assert_called_once_with("Sheet2!A1:B10", headers=True)

    def test_xl_not_available_raises_error(self):
        """Should raise RangeResolutionError when xl() not available"""
        ref = TableReference(
            original="Orders",
            sheet_name=None,
            table_name="Orders",
            range_ref=None,
            sqlite_name="orders"
        )

        # Ensure xl is NOT in sys.modules
        if 'xl' in sys.modules:
            del sys.modules['xl']

        # Reload schema to ensure it doesn't have cached xl import
        import importlib
        import schema
        importlib.reload(schema)

        # Should raise error about xl not available
        with pytest.raises(RangeResolutionError) as exc_info:
            schema.resolve_reference(ref)

        assert "xl() function not available" in str(exc_info.value)

    def test_xl_returns_none_raises_error(self):
        """Should raise RangeResolutionError if xl() returns None"""
        ref = TableReference(
            original="Orders",
            sheet_name=None,
            table_name="Orders",
            range_ref=None,
            sqlite_name="orders"
        )

        # Mock xl to return None
        mock_xl_func = Mock(return_value=None)
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            with pytest.raises(RangeResolutionError) as exc_info:
                schema.resolve_reference(ref)

            assert "returned None" in str(exc_info.value)

    def test_xl_returns_wrong_type_raises_error(self):
        """Should raise RangeResolutionError if xl() returns non-DataFrame"""
        ref = TableReference(
            original="Orders",
            sheet_name=None,
            table_name="Orders",
            range_ref=None,
            sqlite_name="orders"
        )

        # Mock xl to return a list instead of DataFrame
        mock_xl_func = Mock(return_value=[1, 2, 3])
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            with pytest.raises(RangeResolutionError) as exc_info:
                schema.resolve_reference(ref)

            assert "unexpected type" in str(exc_info.value)

    def test_empty_dataframe_raises_error(self):
        """Should raise EmptyRangeError if DataFrame has no rows"""
        ref = TableReference(
            original="Orders",
            sheet_name=None,
            table_name="Orders",
            range_ref=None,
            sqlite_name="orders"
        )

        # Mock xl to return empty DataFrame
        mock_xl_func = Mock(return_value=pd.DataFrame(columns=['A', 'B']))
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            with pytest.raises(EmptyRangeError) as exc_info:
                schema.resolve_reference(ref)

            assert "Orders" in str(exc_info.value)

    def test_no_columns_raises_error(self):
        """Should raise EmptyRangeError if DataFrame has no rows (even with no columns)"""
        ref = TableReference(
            original="Orders",
            sheet_name=None,
            table_name="Orders",
            range_ref=None,
            sqlite_name="orders"
        )

        # Mock xl to return DataFrame with no columns and no rows
        mock_xl_func = Mock(return_value=pd.DataFrame())
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            # Empty DataFrame raises EmptyRangeError (checked before columns)
            with pytest.raises(EmptyRangeError) as exc_info:
                schema.resolve_reference(ref)

            assert "Orders" in str(exc_info.value)

    def test_xl_throws_exception_is_caught(self):
        """Should wrap xl() exceptions in RangeResolutionError"""
        ref = TableReference(
            original="Orders",
            sheet_name=None,
            table_name="Orders",
            range_ref=None,
            sqlite_name="orders"
        )

        # Mock xl to throw an exception
        mock_xl_func = Mock(side_effect=ValueError("Invalid reference"))
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            with pytest.raises(RangeResolutionError) as exc_info:
                schema.resolve_reference(ref)

            assert "failed to resolve Excel reference" in str(exc_info.value)
            assert "Invalid reference" in str(exc_info.value)


class TestXLIntegrationWithRealData:
    """Test with realistic DataFrames"""

    def test_orders_table_integration(self):
        """Simulate fetching Orders table"""
        ref = TableReference(
            original="Sheet1.Orders",
            sheet_name="Sheet1",
            table_name="Orders",
            range_ref=None,
            sqlite_name="sheet1_orders"
        )

        # Mock realistic Orders data
        orders_data = pd.DataFrame({
            'OrderID': [1, 2, 3],
            'CustomerID': [101, 102, 101],
            'Total': [150.50, 200.00, 75.25],
            'OrderDate': pd.to_datetime(['2024-01-15', '2024-01-16', '2024-01-17'])
        })

        mock_xl_func = Mock(return_value=orders_data)
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            result = schema.resolve_reference(ref)

            # Verify data structure
            assert len(result) == 3
            assert list(result.columns) == ['OrderID', 'CustomerID', 'Total', 'OrderDate']
            assert result['OrderID'].tolist() == [1, 2, 3]

    def test_range_with_headers_integration(self):
        """Simulate fetching A1:D10 with headers"""
        ref = TableReference(
            original="A1:D10",
            sheet_name=None,
            table_name=None,
            range_ref="A1:D10",
            sqlite_name="a1_d10"
        )

        # Mock range data (headers are included)
        range_data = pd.DataFrame({
            'Product': ['Widget', 'Gadget', 'Doohickey'],
            'Price': [10.99, 25.50, 5.00],
            'Stock': [100, 50, 200],
            'Category': ['A', 'B', 'A']
        })

        mock_xl_func = Mock(return_value=range_data)
        mock_xl_module = MagicMock()
        mock_xl_module.xl = mock_xl_func

        with patch.dict('sys.modules', {'xl': mock_xl_module}):
            import importlib
            import schema
            importlib.reload(schema)

            result = schema.resolve_reference(ref)

            # Verify structure
            assert len(result) == 3
            assert 'Product' in result.columns
            assert 'Price' in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
