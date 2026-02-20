
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from librephone.device import DeviceData
from librephone.import_dev import DeviceImport


class TestSQLInjection(unittest.TestCase):
    """Test class for SQL injection vulnerabilities."""

    @patch("librephone.import_dev.psycopg")
    def test_create_entry_injection(self, mock_psycopg):
        """Test create_entry for SQL injection vulnerabilities."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        # Make execute return the cursor so fetchone works if called on result
        mock_cursor.execute.return_value = mock_cursor

        # Initialize DeviceImport
        importer = DeviceImport()

        # Test with malicious input
        vendor = "vendor'; DROP TABLE devices; --"
        model = "model"
        build = "build"

        importer.create_entry(vendor, model, build)

        # specific check for the SQL injection pattern
        call_args = mock_cursor.execute.call_args
        sql_query = call_args[0][0]
        sql_args = call_args[0][1]

        print(f"Executed SQL (create_entry): {sql_query}")
        print(f"Executed Args (create_entry): {sql_args}")

        # Verify parameterized query
        self.assertIn("VALUES(%s, %s, %s)", sql_query)
        self.assertNotIn(vendor, sql_query) # Vendor should NOT be in the query string
        self.assertEqual(sql_args, (vendor, model, build, vendor, model, build))

    @patch("librephone.import_dev.psycopg")
    def test_write_db_injection(self, mock_psycopg):
        """Test write_db for SQL injection vulnerabilities."""
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_psycopg.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        # Make execute return the cursor
        mock_cursor.execute.return_value = mock_cursor

        # Initialize DeviceImport
        importer = DeviceImport()

        # Create a mock DeviceData
        mock_device = MagicMock(spec=DeviceData)
        mock_device.build = "build'; DROP TABLE devices; --"
        mock_device.files = {"test_category": [{"file": "test.bin"}]}

        # Mock the initial SELECT query return value
        # First call is SELECT jsonb_array_length
        # Second call is UPDATE
        mock_cursor.fetchone.return_value = [1] # Indicate existing JSON array

        importer.write_db(mock_device)

        # Check the SQL execution calls
        # write_db executes multiple queries.

        select_call = mock_cursor.execute.call_args_list[0]
        update_call = mock_cursor.execute.call_args_list[1]

        # Check SELECT
        select_sql = select_call[0][0]
        select_args = select_call[0][1]
        print(f"Executed SQL (SELECT): {select_sql}")
        self.assertIn("WHERE build=%s", select_sql)
        self.assertNotIn(mock_device.build, select_sql)
        self.assertEqual(select_args, (mock_device.build,))

        # Check UPDATE
        update_sql = update_call[0][0]
        update_args = update_call[0][1]
        print(f"Executed SQL (UPDATE): {update_sql}")

        self.assertIn("UPDATE devices SET blobs =", update_sql)
        self.assertIn("WHERE build=%s", update_sql)
        self.assertNotIn(mock_device.build, update_sql)
        self.assertNotIn("test_category", update_sql) # JSON should be passed as arg

        # Check args: (json_string, build)
        self.assertEqual(update_args[1], mock_device.build)
        self.assertEqual(json.loads(update_args[0]), [{"file": "test.bin"}])

if __name__ == "__main__":
    unittest.main()
