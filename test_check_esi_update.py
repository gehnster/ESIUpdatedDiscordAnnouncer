#!/usr/bin/env python3
"""
Unit tests for check_esi_update.py
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

import check_esi_update


class TestESIUpdateChecker(unittest.TestCase):
    """Test cases for ESI update checker functions."""

    def test_extract_compatibility_dates_from_dict(self):
        """Test extracting dates from dict response."""
        data = {"compatibility_dates": ["2024-05-01", "2024-06-15", "2024-03-20"]}
        result = check_esi_update.extract_compatibility_dates(data)
        self.assertEqual(result, ["2024-05-01", "2024-06-15", "2024-03-20"])

    def test_extract_compatibility_dates_from_list(self):
        """Test extracting dates from list response (backward compatibility)."""
        data = ["2024-05-01", "2024-06-15", "2024-03-20"]
        result = check_esi_update.extract_compatibility_dates(data)
        self.assertEqual(result, ["2024-05-01", "2024-06-15", "2024-03-20"])

    def test_extract_compatibility_dates_missing_key(self):
        """Test extracting dates from dict without compatibility_dates key."""
        data = {"other_key": ["2024-05-01"]}
        with self.assertRaises(ValueError) as context:
            check_esi_update.extract_compatibility_dates(data)
        self.assertIn("Missing 'compatibility_dates' key", str(context.exception))

    def test_extract_compatibility_dates_invalid_type(self):
        """Test extracting dates from invalid type."""
        with self.assertRaises(ValueError) as context:
            check_esi_update.extract_compatibility_dates("invalid")
        self.assertIn("Unexpected data type", str(context.exception))

    def test_parse_iso_date_simple_format(self):
        """Test parsing simple YYYY-MM-DD date."""
        result = check_esi_update.parse_iso_date("2024-06-15")
        self.assertEqual(result, datetime(2024, 6, 15))

    def test_parse_iso_date_with_time(self):
        """Test parsing ISO 8601 date with time."""
        result = check_esi_update.parse_iso_date("2024-06-15T10:30:00Z")
        self.assertEqual(result, datetime(2024, 6, 15))

    def test_parse_iso_date_invalid(self):
        """Test parsing invalid date string."""
        with self.assertRaises(ValueError):
            check_esi_update.parse_iso_date("not-a-date")

    def test_get_latest_date_with_dict_data(self):
        """Test getting latest date from dict response."""
        data = {"compatibility_dates": ["2024-05-01", "2024-06-15", "2024-03-20"]}
        result = check_esi_update.get_latest_date(data)
        self.assertEqual(result, "2024-06-15")

    def test_get_latest_date_with_valid_data(self):
        """Test getting latest date from valid list data (backward compatibility)."""
        dates = ["2024-05-01", "2024-06-15", "2024-03-20"]
        result = check_esi_update.get_latest_date(dates)
        self.assertEqual(result, "2024-06-15")

    def test_get_latest_date_with_single_date(self):
        """Test getting latest date with single date."""
        dates = ["2024-05-01"]
        result = check_esi_update.get_latest_date(dates)
        self.assertEqual(result, "2024-05-01")

    def test_get_latest_date_with_empty_list(self):
        """Test getting latest date with empty list."""
        dates = []
        result = check_esi_update.get_latest_date(dates)
        self.assertIsNone(result)

    def test_get_latest_date_with_empty_dict(self):
        """Test getting latest date with empty compatibility_dates in dict."""
        data = {"compatibility_dates": []}
        result = check_esi_update.get_latest_date(data)
        self.assertIsNone(result)

    def test_get_latest_date_with_none(self):
        """Test getting latest date with None."""
        result = check_esi_update.get_latest_date(None)
        self.assertIsNone(result)
    
    def test_get_latest_date_with_iso_8601_dates(self):
        """Test getting latest date with ISO 8601 formatted dates."""
        data = {"compatibility_dates": [
            "2024-05-01T00:00:00Z",
            "2024-06-15T12:30:00Z",
            "2024-03-20T08:15:00Z"
        ]}
        result = check_esi_update.get_latest_date(data)
        self.assertEqual(result, "2024-06-15T12:30:00Z")

    def test_read_write_last_known_date(self):
        """Test reading and writing last known date."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name
        
        try:
            # Test writing
            test_date = "2024-06-15"
            check_esi_update.write_latest_date(temp_file, test_date)
            
            # Test reading
            result = check_esi_update.read_last_known_date(temp_file)
            self.assertEqual(result, test_date)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_read_last_known_date_nonexistent_file(self):
        """Test reading from nonexistent file."""
        result = check_esi_update.read_last_known_date("/tmp/nonexistent_file_12345.txt")
        self.assertIsNone(result)
    
    def test_read_last_known_date_empty_file(self):
        """Test reading from empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name
            # Write nothing to create empty file
        
        try:
            result = check_esi_update.read_last_known_date(temp_file)
            self.assertIsNone(result)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @patch('check_esi_update.request.urlopen')
    def test_fetch_esi_compatibility_dates_success(self, mock_urlopen):
        """Test successful fetch of ESI dates with new JSON structure."""
        mock_response = MagicMock()
        test_data = {"compatibility_dates": ["2024-05-01", "2024-06-15"]}
        mock_response.read.return_value = json.dumps(test_data).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        result = check_esi_update.fetch_esi_compatibility_dates()
        self.assertEqual(result, test_data)
    
    @patch('check_esi_update.request.urlopen')
    def test_fetch_esi_compatibility_dates_invalid_json(self, mock_urlopen):
        """Test fetch with invalid JSON response."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"not valid json"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        with self.assertRaises(SystemExit):
            check_esi_update.fetch_esi_compatibility_dates()
    
    @patch('check_esi_update.request.urlopen')
    def test_fetch_esi_compatibility_dates_wrong_type(self, mock_urlopen):
        """Test fetch when API returns list instead of dict."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(["2024-05-01"]).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        with self.assertRaises(SystemExit):
            check_esi_update.fetch_esi_compatibility_dates()

    @patch('check_esi_update.request.urlopen')
    def test_post_to_discord_success(self, mock_urlopen):
        """Test successful Discord post."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        # Should not raise exception
        check_esi_update.post_to_discord(
            "https://discord.com/api/webhooks/test",
            "Test message"
        )


if __name__ == '__main__':
    unittest.main()
