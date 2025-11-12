#!/usr/bin/env python3
"""
Script to check ESI compatibility dates and post to Discord if updated.
"""

import argparse
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
# Only used for Discord webhook POSTs
USER_AGENT = "ESIUpdatedDiscordAnnouncer/1.0 (+https://github.com/gehnster/ESIUpdatedDiscordAnnouncer)"


def fetch_esi_compatibility_dates() -> Dict[str, Any]:
    """Fetch the latest compatibility dates from ESI API.
    
    Returns:
        The full JSON object returned by the ESI API.
        Expected format: {"compatibility_dates": ["2025-11-06", ...]}
    
    Raises:
        SystemExit: On network errors or invalid JSON responses.
    """
    try:
        # No custom User-Agent needed here per your note
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
        if 'T' in date_str:
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


def post_to_discord(
    webhook_url: str,
    message: str,
    username: str | None = None,
    avatar_url: str | None = None
) -> None:
    """Post a message to Discord via webhook with improved diagnostics."""
    if not webhook_url:
        print("Error: Discord webhook URL not provided")
        sys.exit(1)

    payload: dict[str, str] = {"content": message}
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url

    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        webhook_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT  # Only applied here
        },
        method="POST"
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            status = response.status
            if status == 204:
                print("Successfully posted to Discord (204 No Content)")
            elif status == 429:
                # Rate limit response usually has JSON body
                body = response.read().decode(errors="ignore")
                print(f"Rate limited (429). Body: {body}")
            else:
                body = response.read().decode(errors="ignore")
                print(f"Unexpected Discord status: {status}. Body: {body[:500]}")
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode(errors="ignore")
        except Exception:
            pass
        print(f"HTTPError posting to Discord: {e.code} {e.reason}. Body: {body[:500]}")
        sys.exit(1)
    except URLError as e:
        print(f"URLError posting to Discord: {e}")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check ESI updates and notify Discord.")
    parser.add_argument(
        "--force-post",
        action="store_true",
        help="Always post to Discord even if the compatibility date hasn't changed."
    )
    parser.add_argument(
        "--always-success",
        action="store_true",
        help="Do not exit with error on Discord post failure (useful for testing)."
    )
    parser.add_argument(
        "--webhook-username",
        help="Override Discord webhook username."
    )
    parser.add_argument(
        "--webhook-avatar-url",
        help="Override Discord webhook avatar image URL."
    )
    return parser.parse_args()


def main() -> None:
    """Main function to check ESI updates and notify Discord."""
    args = parse_args()

    discord_webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not discord_webhook:
        print("Error: DISCORD_WEBHOOK_URL environment variable not set")
        sys.exit(1)

    print("Fetching ESI compatibility dates...")
    dates_data = fetch_esi_compatibility_dates()

    if isinstance(dates_data, dict):
        print(f"Received JSON object with keys: {list(dates_data.keys())}")
    else:
        print(f"Received data type: {type(dates_data).__name__}")

    latest_date = get_latest_date(dates_data)
    if not latest_date:
        print("Error: No valid dates found in ESI API response")
        sys.exit(1)

    print(f"Latest compatibility date: {latest_date}")

    last_known_date = read_last_known_date(LAST_DATE_FILE)
    print(f"Last known date: {last_known_date}")

    date_changed = (last_known_date != latest_date)
    if date_changed or args.force_post:
        reason = "Compatibility date has changed!" if date_changed else "--force-post override"
        print(reason)

        message = f"The compatibility date of ESI has been updated to {latest_date}"
        print(f"Posting to Discord: {message}")

        try:
            post_to_discord(
                discord_webhook,
                message,
                username=args.webhook_username,
                avatar_url=args.webhook_avatar_url
            )
        except SystemExit as e:
            if args.always_success:
                print(f"Discord post failed but continuing due to --always-success (exit code {e.code})")
            else:
                raise

        if date_changed:
            write_latest_date(LAST_DATE_FILE, latest_date)
            print("Updated last known date")
        else:
            print("Not updating last known date (forced post).")
    else:
        print("No change in compatibility date")

if __name__ == "__main__":
    main()
