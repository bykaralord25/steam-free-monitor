#!/usr/bin/env bash
# Steam Free Game Monitor — Cron tick
# Bu betik Hermes Agent cron job tarafından çalıştırılır.
# SteamDB /upcoming/free/ sayfasını browser ile tarar, oyunları çıkarır,
# steam_monitor.py ile state'e kaydeder ve yeni oyunları Discord'a bildirir.

set -e

SCRIPT_DIR="$HOME/steam-free-monitor"
GAMES_JSON="$SCRIPT_DIR/games.json"

# SteamDB sayfasını browser ile tarayarak oyunları çıkar
# Bu kısım Hermes Agent'ın browser_exec tool'u ile yapılır
# Cron prompt'u şöyle olmalı:
#   "SteamDB /upcoming/free/ sayfasını browser ile aç, aktif promosyonları çıkar,
#    sonuçları ~/steam-free-monitor/games.json dosyasına JSON olarak kaydet,
#    sonra steam_monitor.py --notify games.json çalıştır."

echo "🔍 Steam Free Game Monitor — Cron tick"
echo "⏰ $(date -u)"

# Eğer games.json varsa, state'i güncelle ve bildir
if [ -f "$GAMES_JSON" ]; then
    cd "$SCRIPT_DIR"
    python steam_monitor.py --notify "$GAMES_JSON"
else
    echo "⚠️  games.json bulunamadı — önce browser ile veri çekilmeli."
    exit 1
fi

echo "✅ Cron tick tamamlandı."
