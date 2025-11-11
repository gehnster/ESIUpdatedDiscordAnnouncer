# Setup Guide

This guide will help you set up the ESI Compatibility Date Monitor to post updates to your Discord server.

## Prerequisites

- A Discord server where you have administrative access
- This GitHub repository

## Step-by-Step Setup

### 1. Create a Discord Webhook

1. Open your Discord server
2. Go to **Server Settings** → **Integrations** → **Webhooks**
3. Click **New Webhook** (or **Create Webhook**)
4. Give it a name (e.g., "ESI Updates")
5. Choose the channel where you want notifications to appear
6. Click **Copy Webhook URL**
7. Save the webhook URL for the next step

### 2. Add the Webhook to GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** (repository settings, not your account)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Name: `DISCORD_WEBHOOK_URL`
6. Value: Paste the Discord webhook URL you copied in step 1
7. Click **Add secret**

### 3. Enable GitHub Actions

The workflow should be automatically enabled once you merge this PR. To verify:

1. Go to the **Actions** tab in your repository
2. You should see "Check ESI Compatibility Updates" in the workflows list
3. If prompted, click **"I understand my workflows, go ahead and enable them"**

### 4. Test the Workflow (Optional)

You can test the workflow manually without waiting for the scheduled time:

1. Go to the **Actions** tab
2. Click on **"Check ESI Compatibility Updates"** workflow
3. Click **"Run workflow"** button (on the right side)
4. Select the branch (usually `main`)
5. Click **"Run workflow"**

The first run will:
- Fetch the current ESI compatibility date
- Store it in `last_esi_date.txt`
- Post a notification to Discord with the current date
- Commit the date file back to the repository

Subsequent runs will only post to Discord if the date has changed.

## How It Works

### Daily Checks
- The workflow runs automatically every day at **12:15 PM Central Time** (CST)
- During daylight saving time (CDT), it runs at **1:15 PM Central Time**

### What Happens Each Run
1. Fetches the latest compatibility dates from the ESI API
2. Compares with the previously stored date
3. If the date has changed:
   - Posts a message to your Discord channel
   - Updates the stored date in the repository
4. If the date hasn't changed:
   - Does nothing (no Discord notification)

### Discord Message Format
When a change is detected, you'll receive a message like:
```
The compatibility date of ESI has been updated to 2024-06-15
```

## Troubleshooting

### No Discord Notifications
- Verify the `DISCORD_WEBHOOK_URL` secret is set correctly in repository settings
- Check the Actions tab for workflow run logs to see any error messages
- Test the webhook manually using the Discord webhook URL

### Workflow Not Running
- Check that GitHub Actions are enabled for your repository
- Verify the workflow file exists at `.github/workflows/check-esi-updates.yml`
- Check the Actions tab for any error messages

### Want to Change the Schedule?
Edit `.github/workflows/check-esi-updates.yml` and modify the cron expression on line 8:
```yaml
- cron: '15 18 * * *'  # Minute Hour Day Month DayOfWeek
```

Use [crontab.guru](https://crontab.guru/) to help create cron expressions.

## Viewing Logs

To view the logs from a workflow run:

1. Go to the **Actions** tab
2. Click on a specific workflow run
3. Click on the **check-esi** job
4. Expand the steps to see detailed logs

## Files Created

The workflow will create a file called `last_esi_date.txt` in the root of your repository. This file stores the last known compatibility date and should be committed to the repository. **Do not delete this file** or you'll receive duplicate notifications.

## Support

If you encounter issues, check the workflow logs in the Actions tab for detailed error messages.
