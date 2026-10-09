# Steam Free Game Monitor

Automatically tracks free game promotions on Steam. Scrapes SteamDB's free promotions page, detects new free to keep and play for free games, and sends a Discord notification when something new drops. Runs on a cron schedule. Set it once and forget about it.

## How It Works

1. Opens SteamDB's `/upcoming/free/` page through a headless browser
2. Extracts active promotions: game name, app ID, type (Free to Keep / Play for Free), expiry date, store link
3. Saves to a local state file (`~/.hermes/steam-free-monitor/state.json`)
4. Compares against previously seen games. Only new ones trigger a notification.
5. Sends a Discord webhook message with game details and store link
6. Repeats automatically every 6 hours via cron

## Why Browser Instead of HTTP?

SteamDB returns HTTP 403 on direct requests (bot protection). This tool uses a real browser session to load the page and extract data from the DOM via JavaScript evaluation. No API key needed, no scraping endpoint involved.

## Files

| File | What it does |
|------|-------------|
| `steam_monitor.py` | State management, deduplication, Discord webhook notification |
| `steam_free_monitor.py` | HTTP based fetcher (fallback, blocked by SteamDB 403, kept for reference) |
| `games.json` | Current promotion data extracted from the browser |
| `run_cron.sh` | Cron tick shell script |
| `DISCORD_SHARE.md` | Draft text for sharing the project |

## Setup

```bash
# Clone
git clone https://github.com/bykaralord25/steam-free-monitor.git
cd steam-free-monitor

# Check current state
python steam_monitor.py

# Update state with latest promotions
python steam_monitor.py --update games.json

# Send new promotions to Discord
export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK
python steam_monitor.py --notify games.json
```

## Discord Notification Format

When a new free game is detected, the webhook sends a Discord embed:

- **Title**: Number of new free games found
- **Fields**: Game name, store link, promotion type, expiry date
- **Color**: Steam dark blue (#1b2838)
- **Footer**: Source attribution

## Promotion Types

| Type | Meaning |
|------|---------|
| Free to Keep | Claim it now, it's yours forever even after the promotion ends |
| Play for Free | Free weekend. Play for free until the period ends, then you lose access. |

## Cron Schedule

The cron job runs every 6 hours. Each tick:

1. Browser opens SteamDB `/upcoming/free/`
2. Extracts all active promotions from the DOM
3. Saves results to `games.json`
4. Runs `steam_monitor.py --notify games.json` to update state and send Discord notifications for new games

If no new games are found, it stays silent. No spam.

## State File

Located at `~/.hermes/steam-free-monitor/state.json`. Tracks:

- `seen_apps`: every app ID we've already notified about (deduplication)
- `last_check`: ISO timestamp of the last successful run
- `total_alerts`: cumulative count of notifications sent

Delete the file to reset tracking from scratch.

## Requirements

- Python 3.14+
- A browser automation tool or headless browser
- Discord webhook URL (optional, only needed for notifications)
