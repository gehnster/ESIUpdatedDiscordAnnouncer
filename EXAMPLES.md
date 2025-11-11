# Examples

This document shows examples of how the system works in practice.

## Discord Notification Example

When the ESI compatibility date changes, you'll receive a notification in your Discord channel:

```
ESI Updates BOT  12:15 PM
The compatibility date of ESI has been updated to 2024-06-15
```

## Workflow Run Examples

### First Run (Initial Setup)

The first time the workflow runs, it will:

1. **Fetch** the current ESI compatibility date
2. **Store** it in `last_esi_date.txt`
3. **Post** to Discord with the current date
4. **Commit** the date file to the repository

**Discord Message:**
```
The compatibility date of ESI has been updated to 2024-05-20
```

**File Created:** `last_esi_date.txt`
```
2024-05-20
```

### Subsequent Run - No Change

When the compatibility date hasn't changed:

1. **Fetch** the current date from ESI: `2024-05-20`
2. **Read** stored date: `2024-05-20`
3. **Compare**: Dates match
4. **Result**: No action taken, no Discord message

**Workflow Output:**
```
Fetching ESI compatibility dates...
Received data: ['2024-05-20']
Latest compatibility date: 2024-05-20
Last known date: 2024-05-20
No change in compatibility date
```

### Subsequent Run - Date Changed

When ESI updates their compatibility date:

1. **Fetch** the current date from ESI: `2024-06-15`
2. **Read** stored date: `2024-05-20`
3. **Compare**: Dates differ!
4. **Post** to Discord
5. **Update** `last_esi_date.txt`

**Workflow Output:**
```
Fetching ESI compatibility dates...
Received data: ['2024-05-20', '2024-06-15']
Latest compatibility date: 2024-06-15
Last known date: 2024-05-20
Compatibility date has changed!
Posting to Discord: The compatibility date of ESI has been updated to 2024-06-15
Successfully posted to Discord
Updated last known date
```

**Discord Message:**
```
The compatibility date of ESI has been updated to 2024-06-15
```

**Updated File:** `last_esi_date.txt`
```
2024-06-15
```

## Manual Testing

You can manually trigger the workflow to test it:

### Using GitHub UI

1. Go to **Actions** tab
2. Select **"Check ESI Compatibility Updates"**
3. Click **"Run workflow"**
4. Select your branch
5. Click **"Run workflow"**

### Viewing Results

After the workflow completes, check:

1. **Discord**: Should see a new message (if date changed or first run)
2. **Repository**: Check if `last_esi_date.txt` was created/updated
3. **Actions logs**: Review the detailed execution logs

## Testing with Mock Data

If you want to test the notification system without waiting for ESI to update:

1. Manually delete `last_esi_date.txt` from the repository
2. Run the workflow manually
3. It will treat this as a "first run" and post to Discord

**⚠️ Warning:** This will send a notification to your Discord channel.

## ESI API Response Examples

The ESI API returns an array of ISO 8601 date strings:

### Example Response 1: Single Date
```json
["2024-05-20"]
```

### Example Response 2: Multiple Dates
```json
["2024-05-20", "2024-06-15"]
```

The script automatically selects the latest date (last in sorted order).

## Error Examples

### Missing Discord Webhook

If the `DISCORD_WEBHOOK_URL` secret is not set:

**Workflow Output:**
```
Error: DISCORD_WEBHOOK_URL environment variable not set
Error: Process completed with exit code 1.
```

**Solution:** Add the secret in repository settings.

### ESI API Unavailable

If the ESI API is down or unreachable:

**Workflow Output:**
```
Fetching ESI compatibility dates...
Error fetching ESI compatibility dates: <urlopen error [Errno -2] Name or service not known>
Error: Process completed with exit code 1.
```

**Result:** No changes made, workflow will retry on next scheduled run.

### Discord Webhook Error

If the Discord webhook URL is invalid:

**Workflow Output:**
```
Posting to Discord: The compatibility date of ESI has been updated to 2024-06-15
Error posting to Discord: HTTP Error 404: Not Found
Error: Process completed with exit code 1.
```

**Solution:** Verify the webhook URL in repository secrets.

## Commit History Example

After several runs, your commit history will look like:

```
5bdd759 Add architecture documentation with system flow diagrams
ae40608 Add comprehensive setup guide for users
01eb6fb Fix workflow permissions for security compliance
b0cc095 Add unit tests for ESI update checker
5008fde Implement ESI compatibility date monitoring with Discord notifications
a1b2c3d Update last known ESI compatibility date  ← Automated commits
d4e5f6g Update last known ESI compatibility date
```

The automated commits are made by `github-actions[bot]` whenever the date changes.

## Logs Location

All workflow runs are logged in:
- **GitHub UI**: Actions tab → Select workflow → Select run → View logs
- **Log retention**: 90 days (GitHub default)

## Scheduling Examples

The workflow is scheduled for `18:15 UTC`:

| Timezone | Standard Time | Daylight Saving |
|----------|--------------|-----------------|
| Central  | 12:15 PM CST | 1:15 PM CDT     |
| Eastern  | 1:15 PM EST  | 2:15 PM EDT     |
| Pacific  | 10:15 AM PST | 11:15 AM PDT    |
| UTC      | 6:15 PM UTC  | 6:15 PM UTC     |

## Notification Frequency

- **Maximum**: Once per day (on scheduled run)
- **Typical**: 1-2 times per month (when ESI updates)
- **First run**: Always sends a notification
- **Subsequent runs**: Only when date changes

This prevents notification spam while ensuring you're always informed of changes.
