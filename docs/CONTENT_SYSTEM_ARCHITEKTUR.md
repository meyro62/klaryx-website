# KLARYX – Content System Architektur
**Phase 1: Data-Aggregator (Vereinfacht, Kostenlos)**

---

## 🎯 ÜBERBLICK

Ein wöchentliches automatisches Content-System das:
- ✅ Öffentliche Marktdaten aggregiert (CoinGecko)
- ✅ Einfache HTML-Berichte generiert
- ✅ In Supabase speichert
- ✅ Automatisiert via Cron Job läuft
- ✅ 100% rechtlich sauber (Daten-Aggregator, kein Finanzberater)
- ✅ Kostenlos (€0/Monat)

---

## 📊 TIER-STRUKTUR

### FREE TIER (0.01 KLRX)
**Inhalt:**
- Top 3 Kryptowährungen: Preis + 7-Tage % Veränderung
- Top 10 nach Marktcap (Liste, keine Bewertung)
- Kurze Zusammenfassung (3-5 Sätze, nur Fakten)

**Datenquellen:**
- CoinGecko API (kostenlos, kein Key)

**Format:** HTML-Block, eingebettet im Portal

---

### EINBLICK TIER (25+ Einladungen)
**Inhalt:**
- ✅ Alles aus FREE TIER
- Top 10 Solana Token nach Marktcap
- Volumen-Daten und Preisveränderungen

**Datenquellen:**
- CoinGecko API

**Format:** HTML-Bericht im Portal

---

### TIEFE TIER (50+ Einladungen)
**Inhalt:**
- ✅ Alles aus EINBLICK TIER
- Raw JSON Daten zum Selbst-Analysieren
- Historische Vergleiche

**Format:** JSON API + HTML-Dashboard

---

## 🔒 RECHTLICHE SICHERHEIT

**Klassifizierung:** Daten-Aggregator (nicht Finanzdienstleister)

**Disclaimer auf JEDEM Report:**
```
⚠️ KLARYX – INFORMATIONSZWECKE ONLY

Diese Daten sind öffentlich zugängliche Marktinformationen.
NICHT: Finanzberatung, Anlageempfehlung, Handelssignal
NUR: Öffentliche Daten zu Informationszwecken

Klaryx ist kein lizenzierter Finanzdienstleister.
Nutzer sind allein verantwortlich für ihre Handlungen.
Handeln auf Basis dieser Daten erfolgt auf eigene Verantwortung.
```

**VERBOTEN:**
- ❌ "Kaufe X" (Empfehlung)
- ❌ "X wird steigen" (Prognose)
- ❌ "Smart Money kauft, daher..." (implizite Empfehlung)

**ERLAUBT:**
- ✅ "Token X hatte höchstes Volumen"
- ✅ "Volumen stieg um 45%"
- ✅ "Dies zeigt Aktivität, nicht Empfehlung"

---

## 💻 TECHNISCHE IMPLEMENTIERUNG

### Script: `klrx_weekly_report_phase1_simple.py`

**Was es macht:**
```python
1. CoinGecko API aufrufen
2. Top 10 Daten abrufen
3. 3 HTML-Reports generieren (Free/Einblick/Tiefe)
4. In Supabase speichern (reports Tabelle)
5. Lokal exportieren (HTML-Files)
```

**Abhängigkeiten:**
- urllib (Standard Python)
- json (Standard Python)
- requests (pip install requests)

**Keine externen APIs nötig!**

---

## 🔄 AUTOMATISIERUNG: SUPABASE CRON JOB

**Schedule:** Jeden Sonntag 10:00 UTC

```sql
select cron.schedule(
  'klrx-weekly-report',
  '0 10 * * 0',
  'select http_post(
    url => ''https://YOUR_EDGE_FUNCTION_URL'',
    headers => json_object_agg(
      ''Authorization'', 
      ''Bearer ''||current_setting(''app.supabase_service_key'')
    ),
    body => json_build_object(
      ''action'', ''generate_weekly_report''
    )
  )'
);
```

**Result:** Neue Reports automatisch alle 7 Tage

---

## 📈 INFRASTRUKTUR-KOMPONENTEN

```
CoinGecko API (kostenlos)
    ↓
klrx_weekly_report_phase1_simple.py (lokal/Edge Function)
    ↓
Supabase (PostgreSQL: reports tabelle)
    ↓
Portal.html (Anzeige je nach Tier)
    ↓
User sieht Report im Browser
```

---

## 💡 BEISPIEL: REPORT-STRUKTUR

```html
<!-- FREE TIER REPORT -->
<div class="report-container">
  <h3>📊 Marktübersicht KW 27 (2026)</h3>
  
  <div class="top-3">
    <strong>Top 3 Assets:</strong>
    <ul>
      <li>Bitcoin: $29.500 (+5.2%)</li>
      <li>Ethereum: $1.850 (+3.1%)</li>
      <li>Solana: $142 (+12.4%)</li>
    </ul>
  </div>
  
  <div class="disclaimer">
    ⚠️ Informationszwecke. Keine Finanzberatung.
  </div>
</div>
```

---

## ✅ QUALITY ASSURANCE

- **Datengenauigkeit:** ±5 Minuten (CoinGecko cache)
- **Verfügbarkeit:** 99.9% (Supabase SLA)
- **Performance:** <1 Sekunde Ladezeit
- **Security:** RLS disabled für Free Tier, Data nur öffentlich

---

## 🚀 NÄCHSTE SCHRITTE

1. Script testen lokal
2. Edge Function deployen
3. Cron Job konfigurieren
4. Reports im Portal anzeigen
5. User-Test durchführen

---

**Phase 1 Goal: MVP-Quality in 2 Tagen implementieren**
