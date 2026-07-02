#!/usr/bin/env python3
"""
KLRX Batch-Script – wöchentliche Versendung
Liest Wallet-Adressen aus Google Sheet (Tab: Ausstehend)
Sendet 0.01 KLRX und verschiebt ins Archiv
"""

import subprocess
import urllib.request
import urllib.parse
from datetime import datetime

# ============================================================
# KONFIGURATION
# ============================================================
SHEET_ID = "1dMt9nLGLgg6AszsltiaPKJH612LIFSvF7VZJTg8GX5Q"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyeOLlf31LBv0puUKF2rM0MgAU3nn8rroj6JO-5e0rXjc_zufcnPm2Fz4kXkYOM-Ucc/exec"
MINT_ADDRESS = "2Dc81HQDDSCUWVUD1XeyUmv8nyLD46ai9VuDBsr7z2RD"
KLRX_AMOUNT = "0.01"
DISTRIBUTOR_KEYPAIR = "/home/mahir/klrx-distributor.json"
# ============================================================

def get_pending_wallets():
    """Liest ausstehende Wallets aus Tab 'Ausstehend'"""
    # GID 0 = erster Tab
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
        
        wallets = []
        lines = content.strip().split('\n')
        for i, line in enumerate(lines[1:], 2):
            parts = line.split(',')
            if len(parts) >= 5:
                datum = parts[0].strip().strip('"')
                uhrzeit = parts[1].strip().strip('"')
                wallet = parts[2].strip().strip('"')
                status = parts[4].strip().strip('"')
                if status == "Ausstehend" and wallet and len(wallet) > 20:
                    wallets.append({
                        'zeile': i,
                        'datum': datum,
                        'uhrzeit': uhrzeit,
                        'wallet': wallet
                    })
        return wallets
    except Exception as e:
        print(f"Fehler beim Lesen des Sheets: {e}")
        return []

def send_klrx(wallet_address):
    """Sendet 0.01 KLRX an eine Wallet"""
    try:
        cmd = [
            "/home/mahir/solana-release/bin/spl-token", "transfer",
            MINT_ADDRESS,
            KLRX_AMOUNT,
            wallet_address,
            "--fund-recipient",
            "--allow-unfunded-recipient",
            "--owner", DISTRIBUTOR_KEYPAIR
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)

def archivieren(wallet, gesendet_am):
    """Verschiebt Wallet-Eintrag ins Archiv via Apps Script"""
    try:
        params = urllib.parse.urlencode({
            'archivieren': '1',
            'wallet': wallet,
            'gesendet': gesendet_am
        })
        urllib.request.urlopen(WEBHOOK_URL + "?" + params, timeout=10)
    except Exception as e:
        print(f"  Archivierung Fehler: {e}")

def main():
    print("=" * 60)
    print("KLRX Batch-Script")
    print(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("=" * 60)
    
    wallets = get_pending_wallets()
    
    if not wallets:
        print("\nKeine ausstehenden Wallets gefunden.")
        return
    
    print(f"\n{len(wallets)} ausstehende Wallet(s) gefunden:\n")
    for w in wallets:
        print(f"  - {w['wallet'][:30]}... (registriert: {w['datum']} {w['uhrzeit']})")
    
    print(f"\nSende {KLRX_AMOUNT} KLRX an jede Wallet...\n")
    
    erfolg = 0
    fehler = 0
    
    for w in wallets:
        wallet = w['wallet']
        print(f"Sende an {wallet[:20]}...", end=" ", flush=True)
        success, msg = send_klrx(wallet)
        if success:
            gesendet_am = datetime.now().strftime("%d.%m.%Y %H:%M")
            archivieren(wallet, gesendet_am)
            print("✅ → Archiviert")
            erfolg += 1
        else:
            print(f"❌ ({msg[:50]})")
            fehler += 1
    
    print(f"\n{'='*60}")
    print(f"Ergebnis: {erfolg} erfolgreich, {fehler} fehlgeschlagen")
    print("=" * 60)

if __name__ == "__main__":
    main()
