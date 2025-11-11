#!/usr/bin/env python3
"""
Unit tests for check_esi_update.py
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

import check_esi_update


class TestESIUpdateChecker(unittest.TestCase):
    """Test cases for ESI update checker functions."""

    def test_get_latest_date_with_valid_data(self):
        """Test getting latest date from valid data."""
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

    def test_get_latest_date_with_none(self):
        """Test getting latest date with None."""
        result = check_esi_update.get_latest_date(None)
        self.assertIsNone(result)

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

    @patch('check_esi_update.request.urlopen')
    def test_fetch_esi_compatibility_dates_success(self, mock_urlopen):
        """Test successful fetch of ESI dates."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(["2024-05-01", "2024-06-15"]).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        result = check_esi_update.fetch_esi_compatibility_dates()
        self.assertEqual(result, ["2024-05-01", "2024-06-15"])

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
