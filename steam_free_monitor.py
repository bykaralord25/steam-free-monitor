#!/usr/bin/env python3
"""
Steam Free Game Monitor — Steam'deki ücretsiz oyun promosyonlarını takip eder.
Her çalıştığında SteamDB'nin /upcoming/free/ sayfasını çeker, şimdiki aktif
promosyonları parse eder ve yeni bulunan oyunları bir state dosyasında kaydeder.

Kullanım:
    python steam_free_monitor.py                    # tek seferlik çalıştırma
    python steam_free_monitor.py --notify           # yeni oyunları Discord'a postala
    python steam_free_monitor.py --json             # JSON çıktı
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error

# --- Config ---
STEAMDB_FREE_URL = "https://steamdb.info/upcoming/free/"
STATE_FILE = Path.home() / ".hermes" / "steam-free-monitor" / "state.json"
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"


def fetch_page(url: str) -> str:
    """Fetch a web page with proper headers to avoid being blocked."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_free_promotions(html: str) -> list[dict]:
    """Parse SteamDB free promotions page to extract active free games.
    
    SteamDB renders each promotion as a card with:
    - Game name (as a heading or link)
    - Promotion type (Free to Keep / Play For Free)
    - Start/End timestamps
    - Store link
    """
    promotions = []
    
    # SteamDB uses <h3> or specific card structures for game names
    # We'll look for the promotion cards pattern
    
    # Pattern 1: Look for game names in the card structure
    # SteamDB format: <h3>Game Name</h3> or similar
    # Also: "Free to Keep" and "Play For Free" labels
    
    # Find all promotion blocks — SteamDB wraps them in specific divs
    # We'll use a simpler approach: find game names and their context
    
    # Look for store links which contain the app ID
    store_link_pattern = re.compile(
        r'store\.steampowered\.com/app/(\d+)/[^\s"\']*',
        re.IGNORECASE
    )
    
    # Look for promotion type markers
    type_patterns = [
        (r'Free to Keep', 'free_to_keep'),
        (r'Play For Free', 'play_for_free'),
        (r'Play for Free', 'play_for_free'),
    ]
    
    # Look for date/time info
    time_pattern = re.compile(
        r'(?:Started|Expires|Ends)[:\s]*(\d{1,2}\s+\w+\s+\d{4}\s*[–-]\s*\d{1,2}:\d{2}:\d{2}\s*UTC)',
        re.IGNORECASE
 )
    
    # Find all app IDs from store links
    app_ids = store_link_pattern.findall(html)
    
    # Find all game names — SteamDB uses <a> tags within cards
    # Game names are typically in <h3> or similar
    name_pattern = re.compile(r'<h3[^>]*>\s*([^<]+?)\s*</h3>', re.IGNORECASE)
    names = name_pattern.findall(html)
    
    # Also try <a> tags with specific classes
    if not names:
        # Try finding game names in other patterns
        name_pattern2 = re.compile(
            r'class="[^"]*name[^"]*"[^>]*>\s*([^<]+?)\s*</a>',
            re.IGNORECASE
        )
        names = name_pattern2.findall(html)
    
    # Find promotion types
    promotion_types = []
    for pattern, ptype in type_patterns:
        matches = [(m.start(), ptype) for m in re.finditer(pattern, html, re.IGNORECASE)]
        promotion_types.extend(matches)
    
    # Now try to build promotion objects by proximity
    # Find all <a> tags linking to steam store
    a_pattern = re.compile(
        r'<a[^>]+href="https?://store\.steampowered\.com/app/(\d+)/[^"]*"[^>]*>([^<]+)</a>',
        re.IGNORECASE
    )
    
    for match in a_pattern.finditer(html):
        app_id = match.group(1)
        name = match.group(2).strip()
        if not name or len(name) < 2:
            continue
        
        # Find the nearest promotion type
        pos = match.start()
        nearest_type = None
        min_dist = float('inf')
        for type_pos, ptype in promotion_types:
            dist = abs(type_pos - pos)
            if dist < min_dist:
                min_dist = dist
                nearest_type = ptype
        
        if not nearest_type:
            # Check if nearby text has "Free"
            context = html[max(0, pos-500):pos+500]
            if 'Free to Keep' in context:
                nearest_type = 'free_to_keep'
            elif 'Play For Free' in context or 'Play for Free' in context:
                nearest_type = 'play_for_free'
            else:
                nearest_type = 'unknown'
        
        promotions.append({
            "app_id": app_id,
            "name": name,
            "type": nearest_type,
            "store_url": f"https://store.steampowered.com/app/{app_id}/",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        })
    
    # Deduplicate by app_id
    seen = set()
    unique = []
    for p in promotions:
        if p["app_id"] not in seen:
            seen.add(p["app_id"])
            unique.append(p)
    
    return unique


def load_state() -> dict:
    """Load the state file with previously seen games."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"seen_apps": {}, "last_check": None, "total_alerts": 0}


def save_state(state: dict):
    """Save state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def find_new_games(current: list[dict], state: dict) -> list[dict]:
    """Find games that are new since last check."""
    new = []
    for game in current:
        app_id = game["app_id"]
        if app_id not in state["seen_apps"]:
            # New game!
            state["seen_apps"][app_id] = {
                "name": game["name"],
                "type": game["type"],
                "first_seen": game["retrieved_at"],
            }
            new.append(game)
        else:
            # Update name if changed
            state["seen_apps"][app_id]["last_seen"] = game["retrieved_at"]
    
    return new


def send_discord_notification(games: list[dict]):
    """Send new free games to Discord via webhook."""
    if not DISCORD_WEBHOOK:
        print("⚠️  DISCORD_WEBHOOK_URL ortam değişkeni tanımlı değil — bildirim gönderilemedi.")
        return False
    
    # Build embed
    fields = []
    for game in games[:10]:  # Max 10 fields per embed
        type_emoji = "🎁" if game["type"] == "free_to_keep" else "🎮"
        fields.append({
            "name": f"{type_emoji} {game['name']}",
            "value": f"[Steam Mağazası]({game['store_url']})\nTür: {game['type']}",
            "inline": False,
        })
    
    payload = {
        "username": "Steam Free Game Monitor",
        "embeds": [{
            "title": "🎮 Yeni Ücretsiz Steam Oyunu!",
            "color": 0x1b2838,  # Steam dark blue
            "fields": fields,
            "footer": {"text": "SteamDB · Otomatik takip"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in (200, 204):
                print(f"✅ Discord'a {len(games)} oyun bildirimi gönderildi.")
                return True
            else:
                print(f"⚠️  Discord bildirim hatası: HTTP {resp.status}")
                return False
    except Exception as e:
        print(f"⚠️  Discord bildirim hatası: {e}")
        return False


def format_table(games: list[dict]) -> str:
    """Format games as a nice table for terminal output."""
    if not games:
        return "Ücretsiz oyun bulunamadı."
    
    lines = []
    lines.append(f"{'Oyun':<45} {'Tür':<15} {'App ID':<12} {'Link'}")
    lines.append("-" * 100)
    
    for g in games:
        name = g["name"][:43] + ".." if len(g["name"]) > 45 else g["name"]
        lines.append(f"{name:<45} {g['type']:<15} {g['app_id']:<12} {g['store_url']}")
    
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    json_mode = "--json" in args
    notify_mode = "--notify" in args
    
    print("🔍 SteamDB ücretsiz promosyonlar kontrol ediliyor...")
    
    try:
        html = fetch_page(STEAMDB_FREE_URL)
    except Exception as e:
        print(f"❌ SteamDB sayfası alınamadı: {e}")
        if json_mode:
            print(json.dumps({"error": str(e)}))
        return 1
    
    games = parse_free_promotions(html)
    
    if not games:
        # Fallback: try to extract from raw HTML more aggressively
        print("⚠️  Standart parse başarısız — ham HTML'den çıkarma deneniyor...")
        # Look for any store links in the page
        store_links = re.findall(
            r'store\.steampowered\.com/app/(\d+)/([^"\'\s]+)',
            html
        )
        for app_id, slug in store_links[:20]:
            name = slug.replace("-", " ").replace("_", " ").strip()
            if len(name) > 1:
                games.append({
                    "app_id": app_id,
                    "name": name,
                    "type": "free_to_keep",
                    "store_url": f"https://store.steampowered.com/app/{app_id}/",
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                })
        # Deduplicate
        seen = set()
        unique = []
        for g in games:
            if g["app_id"] not in seen:
                seen.add(g["app_id"])
                unique.append(g)
        games = unique
    
    state = load_state()
    new_games = find_new_games(games, state)
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    
    if new_games:
        state["total_alerts"] += len(new_games)
        save_state(state)
        
        print(f"\n🎉 {len(new_games)} yeni ücretsiz oyun bulundu!\n")
        
        if json_mode:
            print(json.dumps({"new": new_games, "all": games}, indent=2, ensure_ascii=False))
        else:
            print("=== YENİ OYUNLAR ===")
            print(format_table(new_games))
            print()
        
        if notify_mode:
            send_discord_notification(new_games)
    else:
        save_state(state)
        print(f"\n✅ {len(games)} ücretsiz oyun bulundu, hepsi zaten kayıtlı (yeni yok).")
        if json_mode:
            print(json.dumps({"all": games, "new": []}, indent=2, ensure_ascii=False))
        else:
            print()
            print(format_table(games))
    
    print(f"\n📊 Toplam takip edilen: {len(state['seen_apps'])} | Toplam uyarı: {state['total_alerts']}")
    print(f"📁 State: {STATE_FILE}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
