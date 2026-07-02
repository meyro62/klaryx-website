# Klaryx Cron Job Setup – KLRX Versendung

## Übersicht
Automatische tägliche Versendung von KLRX an ausstehende Wallets mit UTC-Timezone.

## Option 1: Supabase Edge Function + Cron (EMPFOHLEN)

### 1. Edge Function aktivieren
```bash
# Deploy the edge function
supabase functions deploy send_klrx --no-verify

# List deployed functions
supabase functions list
```

### 2. Cron Trigger einrichten

Gehe zu **Supabase Dashboard** → **Edge Functions** → `send_klrx` → **Integrations** → **Cron**

**Konfiguration:**
```
Cron Expression: 0 8 * * * UTC
Description: Daily KLRX distribution - runs at 8 AM UTC
```

**UTC Schedule:**
- `0 8 * * *` = jeden Tag um 8:00 UTC (= 10:00 CEST / 9:00 CET)
- `0 6 * * *` = jeden Tag um 6:00 UTC (= 8:00 CEST / 7:00 CET)
- `0 0 * * *` = jeden Tag um 0:00 UTC (= 2:00 CEST / 1:00 CET)

**Cron Syntax (mit UTC):**
```
MIN HOUR DAY MONTH DAYOFWEEK [TIMEZONE]
0   8    *   *     *          UTC
```

### 3. Webhook für Batch-Versendung

**URL:** `https://your-project.supabase.co/functions/v1/send_klrx`

**Headers:**
```json
{
  "Authorization": "Bearer YOUR_ANON_KEY",
  "Content-Type": "application/json"
}
```

**Body (wird automatisch mit Cron gefüllt):**
```json
{
  "action": "send_pending_klrx",
  "timestamp": "2026-01-15T08:00:00Z"
}
```

---

## Option 2: Google Apps Script + Cron (LEGACY)

Falls ihr noch das alte Google Sheets System nutzt:

### 1. Apps Script Editor öffnen
1. Google Sheet öffnen
2. **Erweiterungen** → **Apps Script**
3. Bestehenden Code ersetzen mit:

```javascript
function sendKlrxDaily() {
  // Webhook zur Solana-Versendung
  var webhookUrl = "https://your-backend.com/send-klrx";
  var options = {
    method: "post",
    payload: JSON.stringify({
      action: "send_pending",
      timestamp: new Date().toISOString()
    }),
    contentType: "application/json"
  };
  
  var response = UrlFetchApp.fetch(webhookUrl, options);
  Logger.log("KLRX Batch Response: " + response.getContentText());
}

// Trigger manuell testen
// sendKlrxDaily();
```

### 2. Cron/Trigger einrichten
1. **Trigger** (Uhr-Icon auf der linken Seite)
2. **Neuen Trigger erstellen**
3. Konfiguration:
   - **Funktion:** `sendKlrxDaily`
   - **Ereignisquelle:** Zeitgesteuert
   - **Zeittyp:** Tag
   - **Uhrzeit:** 8:00 – 9:00 UTC

⚠️ **Wichtig:** Google Apps Script verwendet die Timezone des Nutzers! 
Für UTC, muss die Funktion die Systemzeit berücksichtigen:

```javascript
function sendKlrxDailyUTC() {
  var now = new Date();
  var utcHour = now.getUTCHours();
  
  // Nur um 8 UTC ausführen
  if (utcHour !== 8) {
    Logger.log("Skipping - not UTC 8:00");
    return;
  }
  
  // Versendung starten...
  sendKlrxBatch();
}
```

---

## Option 3: Python + Systemcron (SERVER)

Für Production auf eigenem Server/VPS:

### 1. Python-Script aktualisieren
```python
#!/usr/bin/env python3
"""
KLRX Batch Versendung – täglich um 8 UTC
"""

import subprocess
from datetime import datetime, timezone
from supabase import create_client

SUPABASE_URL = "https://wpxcgducfkbozecknfdw.supabase.co"
SUPABASE_KEY = "your_service_key"
KLRX_MINT = "2Dc81HQDDSCUWVUD1XeyUmv8nyLD46ai9VuDBsr7z2RD"

def send_klrx_batch():
    """Sendung aller ausstehenden Wallets"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Hole ausstehende Wallets
    response = supabase.table("wallets")\
        .select("wallet_address")\
        .eq("claim_status", "Ausstehend")\
        .execute()
    
    wallets = response.data
    print(f"Versende KLRX an {len(wallets)} Wallets...")
    
    erfolg = 0
    for wallet in wallets:
        address = wallet["wallet_address"]
        try:
            # Solana CLI Befehl ausführen
            cmd = [
                "spl-token", "transfer",
                KLRX_MINT,
                "0.01",
                address,
                "--fund-recipient",
                "--allow-unfunded-recipient",
                "--owner", "/path/to/keypair.json"
            ]
            subprocess.run(cmd, check=True, timeout=30)
            
            # Update DB
            supabase.table("wallets").update({
                "claim_status": "Gesendet",
                "claim_sent_at": datetime.now(timezone.utc).isoformat()
            }).eq("wallet_address", address).execute()
            
            erfolg += 1
            print(f"✓ {address[:20]}... gesendet")
        except Exception as e:
            print(f"✗ {address[:20]}... FEHLER: {e}")
    
    print(f"\nErgebnis: {erfolg}/{len(wallets)} erfolgreich")
    return erfolg == len(wallets)

if __name__ == "__main__":
    send_klrx_batch()
```

### 2. Systemcron einrichten (Linux/Mac)
```bash
crontab -e
```

```cron
# KLRX Versendung täglich um 8:00 UTC
0 8 * * * /usr/bin/python3 /home/mahir/klrx_batch.py >> /var/log/klrx_batch.log 2>&1
```

**Cron Zeitformat (UTC):**
```
MIN  HOUR  DAY  MONTH  DAYOFWEEK
0    8     *    *      *          # jeden Tag 8:00 UTC
```

### 3. Log-Monitoring
```bash
tail -f /var/log/klrx_batch.log
```

---

## Timezone-Referenz

| Uhrzeit | UTC Offset |
|---------|------------|
| 8:00 UTC | 8 UTC |
| 10:00 CET | 9 UTC (Winter) |
| 10:00 CEST | 8 UTC (Sommer) |
| 9:00 Berlin | 7-8 UTC je nach DST |

**Für Europa (Berlin/CEST) → 8 UTC = 10:00 Uhr Ortszeit**

---

## Fehlerbehandlung

### Wallet nicht gefunden
```
error: "Wallet not found in database"
→ Prüfe: wallet_address ist gültig? In DB vorhanden?
```

### Solana CLI nicht verfügbar
```
error: "spl-token: command not found"
→ Solution: `which spl-token` / PATH konfigurieren
```

### KLRX Balance zu niedrig
```
error: "Insufficient funds"
→ Distributor Wallet auffüllen!
```

### Doppelte Versendung
```
error: "claim_status is already 'Gesendet'"
→ Wallet-Status wird vor Versendung geprüft
```

---

## Monitoring & Alerts

### Alert bei Fehler in Supabase
```javascript
// In der Edge Function
if (!sendResult.success) {
  // Slack/Discord Webhook
  await notifyAdmins({
    error: sendResult.error,
    wallet: wallet_address
  });
}
```

### Database Trigger (automatisch)
```sql
CREATE TRIGGER notify_klrx_sent
AFTER UPDATE ON wallets
FOR EACH ROW
WHEN NEW.claim_status = 'Gesendet' AND OLD.claim_status != 'Gesendet'
EXECUTE FUNCTION send_notification();
```

---

## Checkliste

- [x] Supabase Edge Function deployed
- [x] Cron Job mit UTC Timezone konfiguriert
- [x] Distributor Wallet hat ausreichend KLRX
- [x] claim_sent_at wird korrekt gespeichert
- [x] claim_status wird auf "Gesendet" aktualisiert
- [x] referrals Tabelle wird gepflegt
- [x] Fehlerbehandlung & Logging aktiv
- [x] Timezone-Einstellung: UTC (nicht lokal!)

---

**Letzte Aktualisierung:** 2026-07-02
**Status:** Production Ready
