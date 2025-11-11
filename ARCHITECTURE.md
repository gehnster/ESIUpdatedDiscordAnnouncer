# Architecture Overview

This document explains how the ESI Compatibility Date Monitor works.

## System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Scheduler                      │
│                  (Daily at 12:15 PM Central)                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                  1. Checkout Repository                          │
│                  2. Setup Python 3.11                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│              Run check_esi_update.py Script                      │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Fetch ESI API                                         │   │
│  │    GET https://esi.evetech.net/latest/meta/             │   │
│  │        compatibility-dates/                              │   │
│  │                                                          │   │
│  │ 2. Parse response and get latest date                   │   │
│  │                                                          │   │
│  │ 3. Read last known date from last_esi_date.txt         │   │
│  │                                                          │   │
│  │ 4. Compare dates                                         │   │
│  └─────────────────┬────────────────────────────────────────┘   │
│                    │                                              │
│         ┌──────────┴──────────┐                                 │
│         │                     │                                  │
│    Date Changed         Date Unchanged                           │
│         │                     │                                  │
│         ↓                     ↓                                  │
│  ┌──────────────┐      ┌──────────────┐                        │
│  │ Post to      │      │ Exit         │                         │
│  │ Discord      │      │ (no action)  │                         │
│  │              │      └──────────────┘                         │
│  │ Save new     │                                                │
│  │ date to file │                                                │
│  └──────────────┘                                                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│         Commit and Push last_esi_date.txt (if changed)          │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. GitHub Actions Workflow
- **File**: `.github/workflows/check-esi-updates.yml`
- **Trigger**: Cron schedule (daily) and manual dispatch
- **Responsibilities**:
  - Sets up the execution environment
  - Provides secrets (Discord webhook URL)
  - Commits changes back to the repository

### 2. Python Script
- **File**: `scripts/check_esi_update.py`
- **Responsibilities**:
  - HTTP requests to ESI API
  - Date comparison logic
  - Discord webhook posting
  - File I/O for state persistence

### 3. State Storage
- **File**: `last_esi_date.txt` (auto-generated)
- **Purpose**: Stores the last known compatibility date
- **Format**: Plain text, single line with ISO 8601 date
- **Location**: Repository root

### 4. External Services
- **ESI API**: `https://esi.evetech.net/latest/meta/compatibility-dates/`
  - Returns: Array of ISO 8601 date strings
  - Example: `["2024-05-01", "2024-06-15"]`
- **Discord Webhook**: Provided by user as secret
  - Method: POST with JSON payload
  - Format: `{"content": "message text"}`

## Data Flow

### First Run (No Previous Data)
1. Script fetches current dates from ESI
2. No `last_esi_date.txt` exists
3. Script considers this a "change"
4. Posts to Discord with current date
5. Creates `last_esi_date.txt` with current date
6. Workflow commits the file

### Subsequent Runs (No Change)
1. Script fetches current dates from ESI
2. Reads date from `last_esi_date.txt`
3. Dates match - no action taken
4. Script exits successfully

### Subsequent Runs (Date Changed)
1. Script fetches current dates from ESI
2. Reads date from `last_esi_date.txt`
3. Dates differ - change detected!
4. Posts notification to Discord
5. Updates `last_esi_date.txt` with new date
6. Workflow commits the updated file

## Security Considerations

### Secrets Management
- Discord webhook URL stored as GitHub Actions secret
- Never logged or exposed in code
- Accessed via environment variable

### Permissions
- Workflow uses minimal required permissions
- `contents: write` - needed only to commit state file
- No access to other resources

### API Rate Limiting
- Runs only once per day
- ESI API has generous rate limits
- Discord webhook has rate limits (30 requests per minute per webhook)

## Error Handling

The script handles several error scenarios:

1. **ESI API Unavailable**: Exits with error, no state change
2. **Discord Webhook Failed**: Exits with error, no state change
3. **File I/O Error**: Exits with error
4. **Invalid API Response**: Exits with error

All errors are logged to the workflow output for debugging.

## Testing

Unit tests cover:
- Date parsing and comparison logic
- File read/write operations
- API response handling (mocked)
- Discord posting (mocked)

Run tests: `python3 test_check_esi_update.py`

## Monitoring

Check workflow execution:
1. Go to repository Actions tab
2. View "Check ESI Compatibility Updates" runs
3. Review logs for each step

## Maintenance

### Updating Python Dependencies
This project uses only Python standard library, no external dependencies needed.

### Updating GitHub Actions
Check for updates to:
- `actions/checkout@v4`
- `actions/setup-python@v5`
- `ad-m/github-push-action@v0.8.0`

### Changing Schedule
Edit the cron expression in `.github/workflows/check-esi-updates.yml`:
```yaml
- cron: '15 18 * * *'  # minute hour day month dayofweek (UTC)
```

Remember that the time is in UTC:
- 18:15 UTC = 12:15 PM CST (Central Standard Time)
- 18:15 UTC = 1:15 PM CDT (Central Daylight Time)
