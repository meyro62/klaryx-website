# KLARYX – Supabase Einrichtung (Schritt für Schritt)

## Wann?
Wenn Supabase wieder stabil ist (nach 02. Juli 2026 Wartung).

## Schritt 1 – Projekt erstellen
1. supabase.com → Dashboard → "New Project"
2. Organisation: Klaryx
3. Name: `klaryx`
4. Passwort: sicheres Datenbankpasswort notieren
5. Region: **eu-central-1 (Frankfurt)** – wegen DSGVO
6. "Create new project" klicken

## Schritt 2 – Datenbank aufbauen
1. Im Dashboard links auf **"SQL Editor"**
2. Inhalt von `klaryx_supabase_setup.sql` kopieren
3. Einfügen und auf **"Run"** klicken
4. Alle Tabellen sollten grün erscheinen

## Schritt 3 – API Keys holen
1. Links auf **"Settings"** → **"API"**
2. Notieren:
   - **Project URL**: `https://XXXX.supabase.co`
   - **anon public key**: `eyJXXXX...`

## Schritt 4 – Migration ausführen
1. `klaryx_migration_sheets_to_supabase.py` öffnen
2. `SUPABASE_URL` und `SUPABASE_KEY` eintragen
3. In WSL ausführen:
```bash
python3 /mnt/c/Users/PC/Desktop/Klaryx/klaryx_migration_sheets_to_supabase.py
```

## Schritt 5 – Keep-Alive einrichten
Damit das Projekt nicht nach 1 Woche pausiert wird, 
den Batch-Script um einen Supabase-Ping erweitern.

## Tabellen-Übersicht
| Tabelle | Inhalt |
|---|---|
| wallets | Alle Holder |
| referrals | Einladungshistorie |
| badges | Badge-Status |
| market_data | CoinGecko Daten |
| reports | KI-Marktberichte |
| milestones | Community-Meilensteine |

## Nächste Schritte nach Einrichtung
1. CoinGecko API einbinden
2. Wöchentlichen Marktbericht automatisieren
3. Portal auf Supabase umstellen (statt Google Sheet)
