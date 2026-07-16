#!/usr/bin/env python3
"""
KLARYX – Idempotenter On-Chain Settlement-Sender
=================================================
Läuft in GitHub Actions (serverlos, gratis auf public repo).

Idee: Für jede Wallet wird das SOLL-Guthaben aus den Referrals berechnet
(Modell 0,1 / 1 / 2, identisch zum Portal). Davon wird abgezogen, was bereits
on-chain gesendet wurde (Spalte klrx_sent_onchain). Nur die DIFFERENZ wird
per spl-token transfer wirklich überwiesen. Dadurch:
  - kann nie doppelt gezahlt werden
  - deckt Free Claim (0,1) UND Referral-Boni in einem Lauf ab
  - selbstheilend, falls ein Lauf ausfällt

Benötigte Umgebungsvariablen (in der Action gesetzt):
  SUPABASE_URL               z.B. https://xxxx.supabase.co
  SUPABASE_SERVICE_ROLE_KEY  Service-Role-Key (nur Backend)
  KLRX_KEYPAIR_PATH          Pfad zur Distributor-Keypair-JSON (aus GitHub Secret)
  SOLANA_RPC                 optional, Default mainnet-beta
  DRY_RUN                    "1" = nichts senden, nur anzeigen (Default: aus)
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN

import urllib.request
import urllib.error

# ---------------------------------------------------------------- Konfiguration
SUPABASE_URL   = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY    = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
KEYPAIR_PATH   = os.environ.get("KLRX_KEYPAIR_PATH", "")
SOLANA_RPC     = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
DRY_RUN        = os.environ.get("DRY_RUN", "").strip() in ("1", "true", "yes")

MINT_ADDRESS   = "2Dc81HQDDSCUWVUD1XeyUmv8nyLD46ai9VuDBsr7z2RD"
SPL_TOKEN      = os.environ.get("SPL_TOKEN_BIN", "spl-token")
DUST           = Decimal("0.000001")   # kleinere Differenzen ignorieren


# ---------------------------------------------------------- Belohnungs-Modell
def owed_balance(referrals: int) -> Decimal:
    """Soll-Guthaben – EXAKT wie portal.html calculateKLRXBalance().
       0 Refs -> 0,1  |  25 Refs -> 1,0  |  50 Refs -> 2,0"""
    bal = Decimal("0.1")
    if 0 < referrals <= 25:
        bal += Decimal(referrals) * Decimal("0.036")
    elif referrals > 25:
        bal += Decimal(25) * Decimal("0.036")
        bal += Decimal(min(referrals - 25, 25)) * Decimal("0.04")
    if referrals > 50:
        bal += Decimal(referrals - 50) * Decimal("0.04")
    return bal.quantize(Decimal("0.001"), rounding=ROUND_DOWN)


def get_badge(r: int) -> str:
    if r >= 100: return "Legend"
    if r >= 50:  return "Diamond"
    if r >= 25:  return "Platinum"
    if r >= 10:  return "Gold"
    if r >= 5:   return "Silver"
    if r >= 1:   return "Bronze"
    return "Free"


def get_tier(r: int) -> str:
    if r >= 50: return "Tiefe"
    if r >= 25: return "Einblick"
    return "Free"


# ---------------------------------------------------------- Supabase-Helfer
def sb_request(method: str, path: str, body=None, prefer=None):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        print(f"  ! Supabase {method} {path} -> HTTP {e.code}: {e.read().decode()[:200]}")
        raise


def fetch_wallets():
    return sb_request("GET", "wallets?select=wallet_address,einladungen,klrx_balance,"
                             "klrx_sent_onchain,claim_status,badge,tier&order=registered_at.asc") or []


def fetch_referral_counts():
    """Zählt tatsächliche Referrals pro Einlader (verlässlicher als der Zähler)."""
    rows = sb_request("GET", "referrals?select=referrer_wallet") or []
    counts = {}
    for r in rows:
        rw = r.get("referrer_wallet")
        if rw:
            counts[rw] = counts.get(rw, 0) + 1
    return counts


def update_wallet(addr, fields):
    sb_request("PATCH", f"wallets?wallet_address=eq.{addr}", body=fields,
               prefer="return=minimal")


def log_payout(addr, amount, reason, signature):
    sb_request("POST", "referral_payouts", body=[{
        "wallet_address": addr,
        "amount": str(amount),
        "reason": reason,
        "tx_signature": signature,
    }], prefer="return=minimal")


# ---------------------------------------------------------- Solana-Transfer
def send_klrx(wallet_address: str, amount: Decimal):
    """Sendet <amount> KLRX on-chain. Gibt (status, info) zurück.
       status: 'ok' | 'no_account' | 'error'.
       Bewusst OHNE --fund-recipient: der User legt (und bezahlt) sein eigenes
       KLRX-Token-Konto selbst an (siehe Wallet-Setup-Guide, ~0,01 SOL). Hat er
       das noch nicht, schlaegt der Transfer fehl -> 'no_account' -> naechster
       Lauf zahlt automatisch nach, sobald das Konto existiert."""
    amt = format(amount.normalize(), "f")
    cmd = [
        SPL_TOKEN, "transfer", MINT_ADDRESS, amt, wallet_address,
        "--owner", KEYPAIR_PATH, "--url", SOLANA_RPC,
        "--output", "json",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            err = (res.stderr or res.stdout).strip()
            low = err.lower()
            if any(k in low for k in ("could not find", "no associated", "associated token account",
                                      "recipient", "account not found", "uninitialized",
                                      "unfunded", "no account", "not have")):
                return "no_account", err[:200]
            return "error", err[:300]
        sig = ""
        try:
            sig = json.loads(res.stdout).get("signature", "")
        except Exception:
            for line in res.stdout.splitlines():
                if "signature" in line.lower():
                    sig = line.split(":")[-1].strip()
        return "ok", sig
    except Exception as e:
        return "error", str(e)


# ---------------------------------------------------------- Hauptlauf
def main():
    if not (SUPABASE_URL and SERVICE_KEY):
        print("FEHLER: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY fehlen.")
        sys.exit(1)
    if not DRY_RUN and not (KEYPAIR_PATH and os.path.exists(KEYPAIR_PATH)):
        print("FEHLER: KLRX_KEYPAIR_PATH fehlt oder Datei nicht vorhanden.")
        sys.exit(1)

    print("=" * 60)
    print(f"KLARYX Settlement  |  {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
    print(f"Modus: {'TROCKENLAUF (kein Versand)' if DRY_RUN else 'ECHT – sendet on-chain'}")
    print("=" * 60)

    wallets = fetch_wallets()
    ref_counts = fetch_referral_counts()
    print(f"{len(wallets)} Wallet(s), {sum(ref_counts.values())} Referral(s) gesamt\n")

    sent_total = Decimal("0")
    ok = skip = fail = 0

    for w in wallets:
        addr = w["wallet_address"]
        refs = ref_counts.get(addr, 0)
        owed = owed_balance(refs)
        already = Decimal(str(w.get("klrx_sent_onchain") or 0))
        delta = (owed - already).quantize(Decimal("0.000000001"))
        badge, tier = get_badge(refs), get_tier(refs)

        short = addr[:6] + "…" + addr[-4:]
        if delta < DUST:
            print(f"  = {short}  refs={refs}  soll={owed}  gesendet={already}  -> nichts offen")
            # Badge/Tier ggf. trotzdem aktualisieren
            if w.get("badge") != badge or w.get("tier") != tier:
                if not DRY_RUN:
                    update_wallet(addr, {"badge": badge, "tier": tier, "einladungen": refs})
            skip += 1
            continue

        print(f"  → {short}  refs={refs}  soll={owed}  offen={delta}", end="  ")

        if DRY_RUN:
            print("[Trockenlauf: würde senden]")
            sent_total += delta
            ok += 1
            continue

        status, info = send_klrx(addr, delta)
        if status == "ok":
            new_sent = (already + delta)
            update_wallet(addr, {
                "klrx_sent_onchain": str(new_sent),
                "klrx_balance": str(owed),
                "badge": badge,
                "tier": tier,
                "einladungen": refs,
                "claim_status": "Gesendet",
                "claim_sent_at": datetime.now(timezone.utc).isoformat(),
            })
            reason = "free_claim" if already == 0 else "referral"
            try:
                log_payout(addr, delta, reason, info)
            except Exception as e:
                print(f"(Audit-Log übersprungen: {str(e)[:70]}) ", end="")
            print(f"✅ {info[:24]}")
            sent_total += delta
            ok += 1
        elif status == "no_account":
            print("⏳ noch kein KLRX-Konto – wird beim nächsten Lauf nachgezahlt")
            skip += 1
        else:
            print(f"❌ {info}")
            fail += 1

    print("\n" + "=" * 60)
    print(f"Fertig: {ok} gesendet, {skip} nichts offen, {fail} Fehler")
    print(f"Summe {'(simuliert) ' if DRY_RUN else ''}gesendet: {sent_total} KLRX")
    print("=" * 60)
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
