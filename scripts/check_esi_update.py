#!/usr/bin/env python3
# ... (existing imports and earlier functions)
import argparse
import json
import os
import sys
from urllib import request
from urllib.error import URLError, HTTPError

LAST_DATE_FILE = "last_esi_date.txt"

# ... (fetch_esi_compatibility_dates, get_latest_date, read_last_known_date, write_latest_date)

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
        headers={"Content-Type": "application/json"},
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
