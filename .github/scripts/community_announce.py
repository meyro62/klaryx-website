#!/usr/bin/env python3
"""
KLARYX – Woechentliche Community-Ankuendigung (serverlos, GitHub Actions)
Zieht Community-Zahlen aus Supabase und postet sie nach Discord (Webhook)
und/oder Telegram (Bot-API). Beide optional: fehlt ein Secret, wird der
Kanal einfach uebersprungen. Zustandslos, laeuft einmal und beendet sich.

Benoetigte Secrets (alle optional, aber mind. eines fuer Sinn):
  SUPABASE_SERVICE_ROLE_KEY   (fuer die Zahlen)
  DISCORD_WEBHOOK_URL         (Discord: Kanal -> Integrationen -> Webhook)
  TELEGRAM_BOT_TOKEN          (Telegram: via @BotFather)
  TELEGRAM_CHAT_ID            (Kanal/Gruppen-ID, z.B. @meinkanal oder -100...)
"""
import os
import json
import urllib.request
from datetime import datetime, timedelta

SUPABASE_URL = os.environ.get('VITE_SUPABASE_URL', 'https://wpxcgducfkbozecknfdw.supabase.co')
SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')


KLRX_MINT = "2Dc81HQDDSCUWVUD1XeyUmv8nyLD46ai9VuDBsr7z2RD"
HOLDERS_URL = "https://klaryx-bot.mahirgulabi.workers.dev/holders?mint=" + KLRX_MINT


def get_onchain_holders():
    """Echte On-Chain-Holderzahl (deckt sich mit Solscan), via Worker."""
    try:
        req = urllib.request.Request(HOLDERS_URL, headers={"User-Agent": "Klaryx-Announce/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
        h = d.get("holders")
        return h if isinstance(h, int) else None
    except Exception as e:
        print(f"WARN On-Chain-Holder-Fehler: {e}")
        return None


def get_stats():
    try:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/wallets?select=registered_at,einladungen,wallet_address",
            headers={"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            wallets = json.loads(r.read().decode())
        # Gesamt-Holder = echte On-Chain-Zahl (deckt sich mit Solscan). Fallback: Portal-Registrierungen.
        onchain = get_onchain_holders()
        total = onchain if onchain is not None else len(wallets)
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        # "Neue diese Woche" bleibt aus der Portal-DB (on-chain ist das nicht zuverlässig ableitbar).
        new = sum(1 for w in wallets if w.get('registered_at') and
                  datetime.fromisoformat(w['registered_at']).date() >= week_start.date())
        top = max(wallets, key=lambda w: w.get('einladungen', 0) or 0, default=None)
        top_txt = "-"
        if top and (top.get('einladungen', 0) or 0) > 0:
            a = top['wallet_address']
            top_txt = f"{a[:4]}..{a[-4:]} ({top['einladungen']} Einladungen)"
        return total, new, top_txt
    except Exception as e:
        print(f"WARN Stats-Fehler: {e}")
        return 0, 0, "-"


def get_watchlist_stats():
    """Aggregierte Wächter-Zahlen (keine einzelnen Token/Wallets – Privatsphäre)."""
    try:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/watchlist?select=token_address,last_snapshot",
            headers={"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            rows = json.loads(r.read().decode())
        seen = {}
        for row in rows:
            tk = row.get('token_address')
            if tk and tk not in seen:
                seen[tk] = row.get('last_snapshot') or {}
        watched = len(seen)
        auff = 0
        for snap in seen.values():
            if not snap:
                continue
            liq = snap.get('liq')
            top10 = snap.get('top10')
            risk = (bool(snap.get('mint_active')) or bool(snap.get('freeze_active'))
                    or (top10 is not None and top10 > 60)
                    or (liq is not None and liq < 2000))
            if risk:
                auff += 1
        return watched, auff
    except Exception as e:
        print(f"WARN Watchlist-Fehler: {e}")
        return 0, 0


def build_message():
    total, new, top = get_stats()
    watched, auff = get_watchlist_stats()
    kw = datetime.now().isocalendar()[1]
    lines = [
        f"📊 Klaryx – Wochenupdate (KW {kw})",
        f"👥 {total} Holder insgesamt",
        f"🆕 {new} neue Wallets diese Woche",
        f"🔗 Aktivster Einlader: {top}",
    ]
    if watched > 0:
        lines.append(f"👀 Wächter: {watched} Token beobachtet · ⚠️ {auff} aktuell auffällig")
    lines += [
        "",
        "Solana-Coins selbst auf Scam prüfen: https://klaryx.de/check.html",
        "— Kein Finanzprodukt, kein Gewinnversprechen.",
    ]
    return "\n".join(lines)


def post_discord(msg):
    if not DISCORD_WEBHOOK_URL:
        print("Discord: kein Webhook-Secret -> uebersprungen")
        return
    try:
        data = json.dumps({"content": msg}).encode()
        req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=data,
                                     headers={"Content-Type": "application/json", "User-Agent": "Klaryx-Announce/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=20)
        print("Discord: gepostet ✅")
    except Exception as e:
        print(f"Discord FEHLER: {e}")


def post_telegram(msg):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print("Telegram: kein Token/Chat-ID -> uebersprungen")
        return
    try:
        data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": msg,
                           "disable_web_page_preview": True}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json", "User-Agent": "Klaryx-Announce/1.0"}, method="POST")
        urllib.request.urlopen(req, timeout=20)
        print("Telegram: gepostet ✅")
    except Exception as e:
        print(f"Telegram FEHLER: {e}")


def run():
    print("KLARYX Community-Announce")
    if not SERVICE_KEY:
        print("FEHLER: SUPABASE_SERVICE_ROLE_KEY fehlt."); return
    msg = build_message()
    print("--- Nachricht ---\n" + msg + "\n-----------------")
    post_discord(msg)
    post_telegram(msg)
    print("Fertig.")


if __name__ == "__main__":
    run()
