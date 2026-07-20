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


def get_stats():
    try:
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/wallets?select=registered_at,einladungen,wallet_address",
            headers={"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            wallets = json.loads(r.read().decode())
        total = len(wallets)
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
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


def build_message():
    total, new, top = get_stats()
    kw = datetime.now().isocalendar()[1]
    return (
        f"📊 Klaryx – Wochenupdate (KW {kw})\n"
        f"👥 {total} Holder insgesamt\n"
        f"🆕 {new} neue Wallets diese Woche\n"
        f"🔗 Aktivster Einlader: {top}\n\n"
        f"Kostenlos beitreten: https://klaryx.de\n"
        f"— Kein Finanzprodukt, kein Gewinnversprechen."
    )


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
