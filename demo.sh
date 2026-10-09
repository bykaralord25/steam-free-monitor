#!/bin/bash
# Steam Free Game Monitor - Demo Script

DIR="C:/Users/patti/steam-free-monitor"

clear
sleep 1

echo "========================================"
echo "  Steam Free Game Monitor"
echo "========================================"
sleep 1.5

echo ""
echo "What it does:"
echo "  - Scrapes SteamDB for free game promotions"
echo "  - Detects new free-to-keep and play-for-free games"
echo "  - Sends Discord notifications when something new drops"
echo "  - Runs on a cron schedule (every 6h)"
sleep 2

echo ""
echo "Step 1: Check current state"
echo "----------------------------------------"
sleep 1
python "$DIR/steam_monitor.py"
sleep 2

echo ""
echo "Step 2: Fetch latest promotions from SteamDB"
echo "----------------------------------------"
sleep 1
echo "Opening https://steamdb.info/upcoming/free/ ..."
sleep 1
echo "Extracting active promotions..."
sleep 1.5
echo ""
echo "Found 9 active promotions:"
echo ""
sleep 0.5

python -c "
import json, time, sys
with open(sys.argv[1]) as f:
    games = json.load(f)
for g in games:
    tp = 'Free to Keep' if g['type'] == 'free_to_keep' else 'Play for Free'
    print(f'  {tp:<16} {g[\"name\"]}')
    time.sleep(0.3)
" "$DIR/games.json"

sleep 1.5
echo ""
echo "Step 3: Update state with latest data"
echo "----------------------------------------"
sleep 1
cd "$DIR"
python steam_monitor.py --update games.json
sleep 2

echo ""
echo "Step 4: All done"
echo "----------------------------------------"
sleep 1
echo "Monitor is running. Next cron tick: every 6h."
sleep 1
echo ""
echo "========================================"
echo "  https://github.com/bykaralord25/steam-free-monitor"
echo "========================================"
sleep 2
