#!/usr/bin/env python3
"""
KLARYX Wächter – täglicher Watchlist-Checker (Phase 2)
======================================================
Liest die watchlist-Tabelle, prüft jeden beobachteten Token erneut
(Dexscreener + Solana-RPC), vergleicht mit dem letzten Snapshot und
schickt bei RELEVANTER Änderung einen beschreibenden Alert nach
Discord/Telegram. Danach werden die Snapshots aktualisiert.

Rein beschreibend – keine Empfehlung. Nur stdlib. Läuft in GitHub Actions.

Env:
  SUPABASE_SERVICE_ROLE_KEY  (Pflicht)
  SOLANA_RPC                 (Helius-Voll-URL empfohlen; sonst fehlen Holder-Daten)
  DISCORD_WEBHOOK_URL        (oder WAECHTER_DISCORD_WEBHOOK für eigenen Kanal)
  TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID  (oder WAECHTER_TELEGRAM_CHAT_ID)
"""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://wpxcgducfkbozecknfdw.supabase.co").rstrip("/")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
DISCORD = os.environ.get("WAECHTER_DISCORD_WEBHOOK") or os.environ.get("DISCORD_WEBHOOK_URL", "")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("WAECHTER_TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID", "")


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def sb(method, path, body=None, prefer=None):
    h = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}", "Content-Type": "application/json"}
    if prefer:
        h["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    try:
        raw = http(f"{SUPABASE_URL}/rest/v1/{path}", data=data, headers=h, method=method)
        return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        print("  ! Supabase", method, path, e.code, e.read().decode()[:200])
        return None


def rpc(method, params):
    try:
        raw = http(RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                   headers={"Content-Type": "application/json"}, method="POST")
        return json.loads(raw).get("result")
    except Exception as e:
        print("  ! RPC", method, e)
        return None


def fetch_dex(token):
    try:
        raw = http("https://api.dexscreener.com/latest/dex/tokens/" + token,
                   headers={"User-Agent": "Klaryx-Waechter/1.0"})
        pairs = json.loads(raw).get("pairs") or []
        same = [p for p in pairs if (p.get("baseToken") or {}).get("address", "").lower() == token.lower()]
        pairs = same or pairs
        if not pairs:
            return None
        pairs.sort(key=lambda p: (p.get("liquidity") or {}).get("usd", 0) or 0, reverse=True)
        return pairs[0]
    except Exception as e:
        print("  ! Dexscreener", e)
        return None


def fmt_usd(v):
    if v is None:
        return "unbekannt"
    try:
        return "$" + format(int(v), ",")
    except Exception:
        return str(v)


def snapshot(token):
    d = fetch_dex(token)
    info = rpc("getAccountInfo", [token, {"encoding": "jsonParsed"}]) or {}
    parsed = None
    try:
        parsed = (((info.get("value") or {}).get("data") or {}).get("parsed") or {}).get("info")
    except Exception:
        parsed = None
    mint_active = bool(parsed and parsed.get("mintAuthority"))
    freeze_active = bool(parsed and parsed.get("freezeAuthority"))
    decimals = (parsed or {}).get("decimals", 0) or 0
    supply = None
    if parsed and parsed.get("supply") is not None:
        try:
            supply = float(parsed["supply"]) / (10 ** decimals)
        except Exception:
            supply = None
    top10 = None
    largest = rpc("getTokenLargestAccounts", [token]) or {}
    accs = largest.get("value") or []
    if accs and supply:
        t = sum((a.get("uiAmount") or 0) for a in accs[:10])
        top10 = round(t / supply * 100, 1) if supply else None
    liq = (d.get("liquidity") or {}).get("usd") if d else None
    vol = (d.get("volume") or {}).get("h24") if d else None
    name = (d.get("baseToken") or {}).get("name") if d else None
    return {"mint_active": mint_active, "freeze_active": freeze_active,
            "liq": liq, "vol": vol, "top10": top10, "name": name, "listed": bool(d)}


def detect_changes(old, new):
    """Liefert eine Liste beschreibender, relevanter Änderungen (oder leer)."""
    if not old:
        return []  # Baseline – kein Alarm beim ersten Sehen
    out = []
    if new["mint_active"] and not old.get("mint_active"):
        out.append("⚠️ Mint Authority wurde REAKTIVIERT – es können wieder neue Token erzeugt werden.")
    if new["freeze_active"] and not old.get("freeze_active"):
        out.append("⚠️ Freeze Authority wurde REAKTIVIERT – Wallets könnten eingefroren werden.")
    ol, nl = old.get("liq"), new.get("liq")
    if ol and ol > 1000:
        if nl is None or nl < ol * 0.5:
            out.append(f"📉 Liquidität stark gefallen: {fmt_usd(ol)} → {fmt_usd(nl)}.")
    ot, nt = old.get("top10"), new.get("top10")
    if ot is not None and nt is not None and (nt - ot) >= 15:
        out.append(f"📊 Top-10-Konzentration deutlich gestiegen: {ot}% → {nt}%.")
    return out


def send_discord(msg):
    if not DISCORD:
        return
    try:
        http(DISCORD, data=json.dumps({"content": msg}).encode(),
             headers={"Content-Type": "application/json", "User-Agent": "Klaryx-Waechter/1.0"}, method="POST")
    except Exception as e:
        print("  ! Discord", e)


def send_telegram(msg):
    if not (TG_TOKEN and TG_CHAT):
        return
    try:
        http(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
             data=json.dumps({"chat_id": TG_CHAT, "text": msg}).encode(),
             headers={"Content-Type": "application/json", "User-Agent": "Klaryx-Waechter/1.0"}, method="POST")
    except Exception as e:
        print("  ! Telegram", e)


def main():
    rows = sb("GET", "watchlist?select=id,owner_wallet,token_address,last_snapshot") or []
    tokens = {}
    for r in rows:
        tk = r["token_address"]
        tokens.setdefault(tk, {"ids": [], "prev": None})
        tokens[tk]["ids"].append(r["id"])
        if r.get("last_snapshot") and tokens[tk]["prev"] is None:
            tokens[tk]["prev"] = r["last_snapshot"]

    print(f"{len(rows)} Watchlist-Eintrag(e), {len(tokens)} eindeutige Token")
    alerts = 0
    for token, meta in tokens.items():
        new = snapshot(token)
        chg = detect_changes(meta["prev"], new)
        if chg:
            name = new.get("name") or (token[:8] + "…")
            body = ("🔔 Klaryx-Wächter\n"
                    f"Token: {name}\n{token}\n\n"
                    + "\n".join(chg)
                    + f"\n\nStand: Liquidität {fmt_usd(new.get('liq'))} · Top-10 "
                    + (f"{new.get('top10')}%" if new.get("top10") is not None else "unbekannt")
                    + "\n— Kein Finanzprodukt, keine Empfehlung. "
                    + f"Prüfen: https://klaryx.de/check.html?token={token}")
            send_discord(body)
            send_telegram(body)
            alerts += 1
            print("  ALERT", token, chg)
        for rid in meta["ids"]:
            sb("PATCH", f"watchlist?id=eq.{rid}",
               body={"last_snapshot": new, "last_checked": datetime.now(timezone.utc).isoformat()},
               prefer="return=minimal")

    print(f"Fertig: {alerts} Alert(s) verschickt.")


if __name__ == "__main__":
    if not SERVICE_KEY:
        print("FEHLER: SUPABASE_SERVICE_ROLE_KEY fehlt.")
        raise SystemExit(1)
    main()
