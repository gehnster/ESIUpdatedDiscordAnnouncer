# ESIUpdatedDiscordAnnouncer

Sends a message to your Discord server when EVE Online's ESI (EVE Swagger Interface) compatibility date is updated.

## Overview

This GitHub Action runs daily at 12:15 PM Central Time to check the [ESI compatibility dates API](https://esi.evetech.net/latest/meta/compatibility-dates/). When the latest compatibility date changes, it automatically posts a notification to your Discord server.

## Setup

### 1. Configure Discord Webhook

1. In your Discord server, go to Server Settings → Integrations → Webhooks
2. Click "New Webhook" or select an existing webhook
3. Copy the webhook URL
4. In your GitHub repository, go to Settings → Secrets and variables → Actions
5. Create a new repository secret named `DISCORD_WEBHOOK_URL` and paste the webhook URL as the value

### 2. Enable GitHub Actions

The workflow is located at `.github/workflows/check-esi-updates.yml` and will automatically run:
- **Daily at 12:15 PM CST** (18:15 UTC during standard time)
- **Note**: During daylight saving time (CDT), this runs at 1:15 PM Central

You can also trigger the workflow manually:
1. Go to the Actions tab in your repository
2. Select "Check ESI Compatibility Updates" workflow
3. Click "Run workflow"

## How It Works

1. **Fetch Latest Date**: The script queries the ESI API to get the current compatibility dates
2. **Compare**: It compares the latest date with the previously stored date (in `last_esi_date.txt`)
3. **Notify**: If the date has changed, it posts a message to Discord: "The compatibility date of ESI has been updated to {new_date}"
4. **Update**: The new date is stored in the repository for future comparisons

## Files

- `scripts/check_esi_update.py` - Python script that checks ESI and posts to Discord
- `.github/workflows/check-esi-updates.yml` - GitHub Actions workflow configuration
- `last_esi_date.txt` - Stores the last known compatibility date (auto-generated)

## Requirements

- GitHub Actions enabled on your repository
- Discord webhook URL configured as a repository secret
- Python 3.11+ (automatically provided by GitHub Actions runner)

## Troubleshooting

- **No Discord notifications**: Verify the `DISCORD_WEBHOOK_URL` secret is set correctly
- **Check workflow runs**: Go to Actions tab to see execution logs
- **Manual testing**: Use the "Run workflow" button to test without waiting for the scheduled time
