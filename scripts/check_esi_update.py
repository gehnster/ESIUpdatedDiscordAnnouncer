#!/usr/bin/env python3
"""
Script to check ESI compatibility dates and post to Discord if updated.
"""

import json
import os
import sys
from datetime import datetime
from urllib import request
from urllib.error import URLError, HTTPError


def fetch_esi_compatibility_dates():
    """Fetch the latest compatibility dates from ESI API."""
    url = "https://esi.evetech.net/meta/compatibility-dates"
    try:
        with request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except (URLError, HTTPError) as e:
        print(f"Error fetching ESI compatibility dates: {e}")
        sys.exit(1)


def get_latest_date(dates_data):
    """Extract the latest compatibility date from the API response."""
    if not dates_data:
        return None
    
    # The API returns a list of dates in ISO 8601 format
    # Sort them and get the latest one
    dates = sorted(dates_data)
    return dates[-1] if dates else None


def read_last_known_date(file_path):
    """Read the last known compatibility date from file."""
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error reading last known date: {e}")
        return None


def write_latest_date(file_path, date):
    """Write the latest compatibility date to file."""
    try:
        with open(file_path, 'w') as f:
            f.write(date)
    except Exception as e:
        print(f"Error writing latest date: {e}")
        sys.exit(1)


def post_to_discord(webhook_url, message):
    """Post a message to Discord via webhook."""
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


def main():
    """Main function to check ESI updates and notify Discord."""
    # File to store the last known date
    last_date_file = "last_esi_date.txt"
    
    # Get Discord webhook URL from environment
    discord_webhook = os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not discord_webhook:
        print("Error: DISCORD_WEBHOOK_URL environment variable not set")
        sys.exit(1)
    
    print("Fetching ESI compatibility dates...")
    dates_data = fetch_esi_compatibility_dates()
    
    print(f"Received data: {dates_data}")
    latest_date = get_latest_date(dates_data)
    
    if not latest_date:
        print("Error: No dates returned from ESI API")
        sys.exit(1)
    
    print(f"Latest compatibility date: {latest_date}")
    
    # Read the last known date
    last_known_date = read_last_known_date(last_date_file)
    print(f"Last known date: {last_known_date}")
    
    # Check if the date has changed
    if last_known_date != latest_date:
        print("Compatibility date has changed!")
        
        # Post to Discord
        message = f"The compatibility date of ESI has been updated to {latest_date}"
        print(f"Posting to Discord: {message}")
        post_to_discord(discord_webhook, message)
        
        # Update the stored date
        write_latest_date(last_date_file, latest_date)
        print("Updated last known date")
    else:
        print("No change in compatibility date")


if __name__ == "__main__":
    main()
