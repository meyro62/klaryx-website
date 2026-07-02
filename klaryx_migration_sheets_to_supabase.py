#!/usr/bin/env python3
"""
KLARYX – Migration von Google Sheets zu Supabase
Einmalig ausführen wenn Supabase eingerichtet ist.

Voraussetzungen:
1. Supabase Projekt erstellt
2. SQL Setup (klaryx_supabase_setup.sql) ausgeführt
3. Supabase URL und API Key eingetragen
"""

import urllib.request
import urllib.parse
import json
import csv
import io

# ============================================================
# KONFIGURATION – nach Supabase-Einrichtung ausfüllen
# ============================================================
SUPABASE_URL = "https://wpxcgducfkbozecknfdw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndweGNnZHVjZmtib3plY2tuZmR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI5Mjc4ODUsImV4cCI6MjA5ODUwMzg4NX0.y72FT56n_vQzjNRpvFRdx31Cz2LHbFkgfRaMU54Qoyg"
SHEET_ID = "1dMt9nLGLgg6AszsltiaPKJH612LIFSvF7VZJTg8GX5Q"
# ============================================================

def get_sheet_data(gid="0"):
    """Liest Daten aus Google Sheet"""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        print(f"  Fehler beim Lesen von Tab {gid}: HTTP {e.code} {e.reason}")
        return None

def supabase_insert(table, data):
    """Fügt Daten in Supabase ein"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        'Content-Type': 'application/json',
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Prefer': 'return=minimal'
    }
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            return True
    except Exception as e:
        print(f"Fehler: {e}")
        return False

def migrate_ausstehend():
    """Migriert Tab 'Ausstehend'"""
    print("Migriere 'Ausstehend'...")
    csv_data = get_sheet_data("0")
    if not csv_data:
        print("  Fehler: Keine Daten erhalten")
        return
    reader = csv.reader(io.StringIO(csv_data))
    header = next(reader, None)
    if not header:
        print("  Fehler: Keine Header gefunden")
        return
    print(f"  Header: {header}")
    count = 0
    for i, row in enumerate(reader, 2):
        if not row or not row[0]:
            continue
        if len(row) >= 5 and row[2] and len(row[2]) > 20:
            data = {
                'wallet_address': row[2].strip(),
                'registered_at': f"2026-{row[0].strip()}" if row[0] else None,
                'referrer_wallet': row[3].strip() if row[3] and row[3] != '–' else None,
                'claim_status': row[4].strip() if row[4] else 'Ausstehend'
            }
            if supabase_insert('wallets', data):
                count += 1
    print(f"  {count} Wallets migriert")

def migrate_archiv():
    """Migriert Tab 'Archiv'"""
    print("Migriere 'Archiv'...")
    csv_data = get_sheet_data("1")
    if not csv_data:
        print("  Fehler: Keine Daten erhalten")
        return
    reader = csv.reader(io.StringIO(csv_data))
    header = next(reader, None)
    if not header:
        print("  Fehler: Keine Header gefunden")
        return
    print(f"  Header: {header}")
    count = 0
    for i, row in enumerate(reader, 2):
        if not row or not row[0]:
            continue
        if len(row) >= 5 and row[2] and len(row[2]) > 20:
            data = {
                'wallet_address': row[2].strip(),
                'referrer_wallet': row[3].strip() if row[3] and row[3] != '–' else None,
                'claim_status': 'Gesendet',
                'klrx_balance': 0.01
            }
            if supabase_insert('wallets', data):
                count += 1
    print(f"  {count} Wallets aus Archiv migriert")

def main():
    print("=" * 50)
    print("KLARYX – Google Sheets → Supabase Migration")
    print("=" * 50)
    print()
    print("ACHTUNG: Supabase URL und API Key eintragen!")
    print(f"URL: {SUPABASE_URL}")
    print()
    
    if "DEINE-PROJECT-ID" in SUPABASE_URL:
        print("FEHLER: Bitte zuerst SUPABASE_URL und SUPABASE_KEY eintragen!")
        return
    
    migrate_ausstehend()
    migrate_archiv()
    
    print()
    print("Migration abgeschlossen!")

if __name__ == "__main__":
    main()
