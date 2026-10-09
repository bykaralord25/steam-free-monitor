#!/usr/bin/env python3
"""
Steam Free Game Monitor - state management and Discord notification.

Usage:
    python steam_monitor.py                        # read state, print report
    python steam_monitor.py --update <games.json>  # save new games to state
    python steam_monitor.py --notify <games.json>  # send new games to Discord
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

STATE_FILE = Path.home() / ".hermes" / "steam-free-monitor" / "state.json"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"seen_apps": {}, "last_check": None, "total_alerts": 0}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def update_state(games: list[dict], state: dict) -> list[dict]:
    new = []
    for game in games:
        app_id = game["app_id"]
        if app_id not in state["seen_apps"]:
            state["seen_apps"][app_id] = {
                "name": game["name"],
                "type": game["type"],
                "first_seen": game.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                "started": game.get("started", ""),
                "expires": game.get("expires", ""),
            }
            new.append(game)
        else:
            entry = state["seen_apps"][app_id]
            entry["last_seen"] = datetime.now(timezone.utc).isoformat()
            if game.get("expires"):
                entry["expires"] = game["expires"]
    return new


def send_discord_notification(games: list[dict]) -> bool:
    if not DISCORD_WEBHOOK:
        print("DISCORD_WEBHOOK_URL not set.")
        return False
    fields = []
    for game in games[:10]:
        emoji = "gift" if game["type"] == "free_to_keep" else "game"
        label = "Free to keep forever" if game["type"] == "free_to_keep" else "Free weekend"
        value = f"[Steam Store]({game['store_url']})\n{label}"
        if game.get("expires"):
            value += f"\nExpires: {game['expires']}"
        fields.append({"name": f"{emoji} {game['name']}", "value": value, "inline": False})
    payload = {
        "username": "Steam Free Game Monitor",
        "embeds": [{
            "title": f"{len(games)} new free Steam game(s) found!",
            "color": 0x1b2838,
            "fields": fields,
            "footer": {"text": "SteamDB - automated tracking"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(DISCORD_WEBHOOK, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in (200, 204):
                print(f"Sent {len(games)} notification(s) to Discord.")
                return True
            print(f"Discord HTTP {resp.status}")
            return False
    except Exception as e:
        print(f"Discord error: {e}")
        return False


def format_table(games: list[dict]) -> str:
    if not games:
        return "No free games found."
    lines = [f"{'Game':<50} {'Type':<18} {'Expires':<35}", "-" * 105]
    for g in games:
        name = g["name"][:48] + ".." if len(g["name"]) > 50 else g["name"]
        tp = "Free to Keep" if g["type"] == "free_to_keep" else "Play for Free"
        exp = g.get("expires", "").replace("Expires: ", "")[:33]
        lines.append(f"{name:<50} {tp:<18} {exp:<35}")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    notify_mode = "--notify" in args
    update_mode = "--update" in args

    if update_mode or notify_mode:
        games_file = None
        for a in args:
            if a.endswith(".json") and os.path.isfile(a):
                games_file = a
                break
        if games_file:
            with open(games_file, "r", encoding="utf-8") as f:
                games = json.load(f)
        else:
            games = json.loads(sys.stdin.read())

        state = load_state()
        new_games = update_state(games, state)
        state["last_check"] = datetime.now(timezone.utc).isoformat()
        if new_games:
            state["total_alerts"] += len(new_games)
        save_state(state)

        if new_games:
            print(f"Found {len(new_games)} new free game(s)!")
            print(format_table(new_games))
            if notify_mode:
                send_discord_notification(new_games)
        else:
            print(f"Processed {len(games)} game(s), no new entries.")
        print(f"\nTotal tracked: {len(state['seen_apps'])} | Total alerts: {state['total_alerts']}")
        return 0

    state = load_state()
    print(f"Steam Free Game Monitor - State")
    print(f"File: {STATE_FILE}")
    print(f"Total tracked: {len(state['seen_apps'])} | Total alerts: {state['total_alerts']}")
    if state.get("last_check"):
        print(f"Last check: {state['last_check']}")
    if state["seen_apps"]:
        print("\n=== Tracked Games ===")
        games = [{"app_id": k, **v} for k, v in state["seen_apps"].items()]
        print(format_table(games))


if __name__ == "__main__":
    sys.exit(main())
