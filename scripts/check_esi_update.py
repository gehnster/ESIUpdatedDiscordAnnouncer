#!/usr/bin/env python3
"""
Script to check ESI compatibility dates and post to Discord if updated.
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional, Union, List, Dict, Any
from urllib import request
from urllib.error import URLError, HTTPError

# Constants
ESI_COMPAT_URL = "https://esi.evetech.net/meta/compatibility-dates"
LAST_DATE_FILE = "last_esi_date.txt"


def fetch_esi_compatibility_dates() -> Dict[str, Any]:
    """Fetch the latest compatibility dates from ESI API.
    
    Returns:
        The full JSON object returned by the ESI API.
        Expected format: {"compatibility_dates": ["2025-11-06", ...]}
    
    Raises:
        SystemExit: On network errors or invalid JSON responses.
    """
    try:
        with request.urlopen(ESI_COMPAT_URL, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            # Validate the response structure
            if not isinstance(data, dict):
                print(f"Error: ESI API returned unexpected data type: {type(data).__name__}")
                print(f"Expected a JSON object with 'compatibility_dates' key")
                sys.exit(1)
            
            return data
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response from ESI API: {e}")
        sys.exit(1)
    except (URLError, HTTPError) as e:
        print(f"Error fetching ESI compatibility dates from {ESI_COMPAT_URL}: {e}")
        sys.exit(1)


def extract_compatibility_dates(dates_data: Union[Dict[str, Any], List[str]]) -> List[str]:
    """Extract the list of date strings from the API response.
    
    Args:
        dates_data: Either a dict with 'compatibility_dates' key or a list of date strings
                   (for backward compatibility).
    
    Returns:
        A list of date strings.
    
    Raises:
        ValueError: If the data structure is invalid or missing expected keys.
    """
    if isinstance(dates_data, list):
        # Backward compatibility: handle raw list
        return dates_data
    
    if isinstance(dates_data, dict):
        if 'compatibility_dates' not in dates_data:
            raise ValueError(
                f"Missing 'compatibility_dates' key in response. "
                f"Available keys: {list(dates_data.keys())}"
            )
        
        dates = dates_data['compatibility_dates']
        if not isinstance(dates, list):
            raise ValueError(
                f"'compatibility_dates' should be a list, got {type(dates).__name__}"
            )
        
        return dates
    
    raise ValueError(f"Unexpected data type: {type(dates_data).__name__}")


def parse_iso_date(date_str: str) -> datetime:
    """Parse a date string in YYYY-MM-DD or ISO 8601 format.
    
    Args:
        date_str: Date string to parse.
    
    Returns:
        A datetime object.
    
    Raises:
        ValueError: If the date string cannot be parsed.
    """
    # Try parsing as simple YYYY-MM-DD format first
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass
    
    # Try parsing as full ISO 8601 format with time
    try:
        # Handle timezone-aware ISO 8601 strings
        if 'T' in date_str:
            # Remove timezone info for simple parsing
            date_part = date_str.split('T')[0]
            return datetime.strptime(date_part, "%Y-%m-%d")
    except ValueError:
        pass
    
    raise ValueError(f"Unable to parse date string: {date_str}")


def get_latest_date(dates_data: Union[Dict[str, Any], List[str]]) -> Optional[str]:
    """Extract the latest compatibility date from the API response.
    
    Args:
        dates_data: Either a dict with 'compatibility_dates' key or a list of date strings.
    
    Returns:
        The latest date string, or None if no dates available.
    """
    if not dates_data:
        return None
    
    try:
        dates = extract_compatibility_dates(dates_data)
    except ValueError as e:
        print(f"Error extracting compatibility dates: {e}")
        return None
    
    if not dates:
        return None
    
    # Parse all dates and find the latest one
    try:
        parsed_dates = [(date_str, parse_iso_date(date_str)) for date_str in dates]
        # Sort by parsed datetime and get the latest
        parsed_dates.sort(key=lambda x: x[1])
        return parsed_dates[-1][0] if parsed_dates else None
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        # Fallback to simple string sorting
        sorted_dates = sorted(dates)
        return sorted_dates[-1] if sorted_dates else None


def read_last_known_date(file_path: str) -> Optional[str]:
    """Read the last known compatibility date from file.
    
    Args:
        file_path: Path to the file containing the last known date.
    
    Returns:
        The last known date string, or None if file doesn't exist or is empty.
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            return content if content else None
    except Exception as e:
        print(f"Error reading last known date from {file_path}: {e}")
        return None


def write_latest_date(file_path: str, date: str) -> None:
    """Write the latest compatibility date to file.
    
    Args:
        file_path: Path to the file to write.
        date: Date string to write.
    
    Raises:
        SystemExit: On write errors.
    """
    try:
        with open(file_path, 'w') as f:
            f.write(date)
    except Exception as e:
        print(f"Error writing latest date to {file_path}: {e}")
        sys.exit(1)


def post_to_discord(webhook_url: str, message: str) -> None:
    """Post a message to Discord via webhook.
    
    Args:
        webhook_url: Discord webhook URL.
        message: Message to post.
    
    Raises:
        SystemExit: On missing webhook URL or posting errors.
    """
    if not webhook_url:
        print("Error: Discord webhook URL not provided")
        sys.exit(1)
    
    data = json.dumps({"content": message}).encode('utf-8')
    
    req = request.Request(
        webhook_url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with request.urlopen(req, timeout=10) as response:
            if response.status == 204:
                print("Successfully posted to Discord")
            else:
                print(f"Discord webhook returned status: {response.status}")
    except (URLError, HTTPError) as e:
        print(f"Error posting to Discord: {e}")
        sys.exit(1)


def main() -> None:
    """Main function to check ESI updates and notify Discord."""
    # Get Discord webhook URL from environment
    discord_webhook = os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not discord_webhook:
        print("Error: DISCORD_WEBHOOK_URL environment variable not set")
        sys.exit(1)
    
    print("Fetching ESI compatibility dates...")
    dates_data = fetch_esi_compatibility_dates()
    
    # Log the structure of the response for debugging
    if isinstance(dates_data, dict):
        print(f"Received JSON object with keys: {list(dates_data.keys())}")
    else:
        print(f"Received data type: {type(dates_data).__name__}")
    
    latest_date = get_latest_date(dates_data)
    
    if not latest_date:
        print("Error: No valid dates found in ESI API response")
        sys.exit(1)
    
    print(f"Latest compatibility date: {latest_date}")
    
    # Read the last known date
    last_known_date = read_last_known_date(LAST_DATE_FILE)
    print(f"Last known date: {last_known_date}")
    
    # Check if the date has changed
    if last_known_date != latest_date:
        print("Compatibility date has changed!")
        
        # Post to Discord
        message = f"The compatibility date of ESI has been updated to {latest_date}"
        print(f"Posting to Discord: {message}")
        post_to_discord(discord_webhook, message)
        
        # Update the stored date
        write_latest_date(LAST_DATE_FILE, latest_date)
        print("Updated last known date")
    else:
        print("No change in compatibility date")


if __name__ == "__main__":
    main()
