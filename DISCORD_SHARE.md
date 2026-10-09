# Discord Paylaşım Metni — hermes-agent kanalı

## Kısa Versiyon

```
🎮 Hermes Agent ile Steam Free Game Monitor yaptım!

Ne yapıyor:
→ SteamDB'yi tarayıp ücretsiz oyun promosyonlarını çıkarıyor (Free to Keep / Play for Free)
→ Yeni oyun bulunca Discord'a bildirim gönderiyor
→ Cron job ile her 6 saatte bir otomatik çalışıyor

Nasıl çalışıyor:
→ Browser tool ile SteamDB /upcoming/free/ sayfasını açıyor
→ Promosyon kartlarını parse edip app_id, isim, tür, bitiş tarihi çıkarıyor
→ State dosyasında deduplication yapıyor (aynı oyunu tekrar bildirmiyor)
→ Yeni oyun varsa Discord webhook'ına embed'li mesaj atıyor

Repo: https://github.com/bykaralord25/steam-free-monitor

Hermes Agent'ın browser tool'u + cron scheduling + product-price-monitor skill'i ile yaptım. 
SteamDB bot koruması (403) yüzünden doğrudan HTTP istek çalışmıyor — browser tool ile tarayarak bypass ettim.

Ayrıca Hermes Agent repo'suna da Türkçe README + CONTRIBUTING çevirisi PR açtım:
→ PR #135549: README.tr.md + tr.yaml
→ PR #135552: CONTRIBUTING.tr.md
```

## Uzun Versiyon (detaylı paylaşım)

```
🎮 Hermes Agent ile bir otomasyon projesi geliştirdim: Steam Free Game Monitor

### Proje
Steam'deki ücretsiz oyun promosyonlarını (Free to Keep / Play for Free) otomatik takip eden bir bot. Yeni bir oyun ücretsiz olduğunda Discord'a bildirim gönderiyor.

### Nasıl Çalışıyor?
1. Hermes Agent'ın browser tool'u ile SteamDB'nin /upcoming/free/ sayfasını tarıyor
2. Promosyon kartlarını parse edip: oyun adı, app ID, tür (Free to Keep / Play for Free), bitiş tarihi, store linki çıkarıyor
3. State dosyasında deduplication yapıyor — aynı oyunu tekrar bildirmiyor
4. Yeni oyun bulursa Discord webhook'ına embed'li mesaj atıyor
5. Cron job ile her 6 saatte bir otomatik çalışıyor

### Teknik Detaylar
- SteamDB bot koruması (HTTP 403) yüzünden doğrudan HTTP isteği çalışmıyor
- Browser tool ile tarayarak bypass ettim — JS evaluation ile DOM'dan veri çıkardım
- `product-price-monitor` skill'ini kullandım (watch contract + cron tick pattern)
- State yönetimi: `~/.hermes/steam-free-monitor/state.json`
- Discord bildirimi: webhook + embed (Steam koyu mavi renk, emoji, store link)

### Dosyalar
- `steam_monitor.py` — state yönetimi + Discord bildirimi + deduplication
- `games.json` — browser'dan çıkarılmış güncel promosyon verileri
- `run_cron.sh` — cron tick betiği
- `README.md` — proje dokümantasyonu

### Çalıştırma
```bash
# State'i kontrol et
python steam_monitor.py

# Yeni oyunları state'e kaydet
python steam_monitor.py --update games.json

# Discord'a bildirim gönder (webhook URL gerekli)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/... python steam_monitor.py --notify games.json
```

### Cron Job
Hermes Agent cron scheduling ile her 6 saatte bir otomatik çalışıyor:
- Browser ile SteamDB'yi tarar
- Yeni oyunları çıkarır
- Discord'a bildirir

### Sonuç
Şu an 9 aktif ücretsiz promosyon takip ediliyor:
- 🎁 Counter-Strike 2 (Free to Keep, 11 Ekim'e kadar)
- 🎮 Squad 44 (Play for Free)
- 🎮 Core Keeper (Play for Free)
- 🎁 Pony Island (Free to Keep)
- 🎁 World of Warships — Ning Hai (Free to Keep)
- + 4 more

Repo: https://github.com/bykaralord25/steam-free-monitor

### Hermes Agent Katkıları
Ayrıca Hermes Agent repo'suna da katkıda bulundum:
- PR #135549: Türkçe README çevirisi + tr.yaml'de çevrilmemiş 14 entry'yi düzelttim
- PR #135552: Türkçe CONTRIBUTING çevirisi (629 satır)
```
