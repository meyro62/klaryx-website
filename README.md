# ⚡ Klaryx – KI-gestützte Marktintelligenz auf Solana

Klaryx ist ein **kostenloses, token-basiertes Community-Projekt** auf Solana. Verdiene KLRX durch Einladungen und steige in Badges auf. 

⚠️ **Wichtig:** Dies ist ein privates Projekt, **kein Finanzprodukt** und kein Investment. Siehe [Rechtliche Hinweise](klaryx_legal.html).

## 🎯 Features

- **Free Claim**: Kostenlos 0.01 KLRX erhalten
- **Referral-System**: Verdiene 0.005 KLRX pro Einladung
- **Badge-Programm**: Bronze → Silver → Gold → Platinum → Diamond → Legend
- **Tier-System**: 
  - Free: OG-Status + Einladungslinks (kostenlos)
  - Einblick: Premium Features (25+ Einladungen) – **Coming Soon**
  - Tiefe: Advanced Features (50+ Einladungen) – **Coming Soon**
- **On-Chain Verified**: 100M KLRX fixed supply, Mint Authority disabled

## 🚀 Tech Stack

- **Frontend**: HTML5 + Vanilla JavaScript
- **Backend**: Supabase (PostgreSQL)
- **Automation**: Supabase Edge Functions + pg_cron
- **Blockchain**: Solana (SPL Token)
- **Hosting**: Serverless (kostenlos)

## 📋 Komponenten

### Portal (`portal.html`)
Benutzer-Dashboard zum Verwalten von:
- Wallet-Registrierung
- Badge & Tier-Status
- Referral-Counter mit Live-Progress
- Persönlichem Einladungslink

### Website (`index.html`)
Marketing-Seite mit:
- Hero-Section
- Wie es funktioniert (4 Steps)
- Tier-Übersicht
- Tokenomics
- Trust-Section

### Backend-Automation
**Edge Functions** (täglich 10:00 Uhr):
- Liest alle "Ausstehend" Wallets
- Updated Status zu "Gesendet"
- Serverlos, kostenlos

**Cron Jobs**:
- **Mo + Fr 9:00 Uhr**: Keep-Alive Ping (verhindert Supabase-Pause)
- **Täglich 10:00 Uhr**: KLRX-Versand

## 📊 Datenbank-Schema

```
wallets (Haupt-Tabelle)
├─ wallet_address (unique)
├─ claim_status (Ausstehend/Gesendet)
├─ klrx_balance
├─ badge (Free/Bronze/Silver/Gold/Platinum/Diamond/Legend)
├─ tier (Free/Einblick/Tiefe)
├─ einladungen (count)
└─ og_status (boolean)

referrals (Einladungshistorie)
├─ referrer_wallet
├─ invited_wallet
└─ referral_bonus_sent

badges (Badge-Tracking)
├─ wallet_address
├─ badge_level
├─ einladungen
└─ stufen_bonus

milestones (Community-Phasen)
├─ phase
├─ name
├─ target_holders
└─ reached_at
```

## 🔧 Konfiguration

### Supabase Setup
```sql
-- Edge Function Secret
SERVICE_ROLE_KEY = [Dein Service Role Key]

-- Cron Jobs
-- Keep-Alive (Mo+Fr 9:00)
select cron.schedule('supabase-keep-alive', '0 9 * * 1,5', 
  'select net.http_get(url:=...)'
);

-- KLRX Versand (täglich 10:00)
select cron.schedule('send-klrx-daily', '0 10 * * *',
  'select net.http_post(url:=...)'
);
```

## 📈 Meilensteine

| Phase | Holder | Status |
|-------|--------|--------|
| 🌱 Start | 1+ | Live |
| 🌿 Wachstum | 500+ | Geplant |
| 🌳 Etabliert | 1.000+ | Geplant |
| 🚀 Launch | 5.000+ | Geplant |

## 💰 Tokenomics

- **Total Supply**: 100,000,000 KLRX (fixed)
- **Mint Authority**: Disabled (on-chain verified)
- **Distribution**:
  - 40% Community
  - 35% Liquidity
  - 25% Founder (6M cliff, 18M vesting)
- **Blockchain**: Solana (SPL Token)
- **Mint Address**: `2Dc81HQDDSCUWVUD1XeyUmv8nyLD46ai9VuDBsr7z2RD`

## 🎬 Getting Started

### Für User
1. Öffne `portal.html`
2. Gib deine Solana Wallet ein
3. Registriere dich (Free Claim 0.01 KLRX)
4. Teile deinen Einladungslink
5. Verdiene KLRX durch Einladungen

### Für Entwickler
1. Clone das Repo
2. Supabase Projekt erstellen
3. Edge Function deployen
4. Cron Jobs einrichten
5. Lokal testen mit `python3 -m http.server 8000`

## 📝 Dateien

```
├── portal.html                # User-Portal mit Badges & Referrals
├── index.html                 # Marketing-Website
├── klaryx_onboarding.html     # Onboarding-Guide
├── klaryx_legal.html          # Rechtliche Hinweise (WICHTIG!)
├── klaryx_datenschutz.html    # Datenschutzerklärung
├── klaryx_disclaimer.html     # Disclaimer
├── klaryx_impressum.html      # Impressum
├── klaryx_halloffame.html     # Hall of Fame (Top Referrer)
└── README.md                  # Diese Datei
```

## ⚖️ Rechtliches & Disclaimer

**Klaryx ist ein privates Community-Projekt – KEIN Finanzprodukt!**

- ❌ Kein Gewinn- oder Renditeversprechen
- ❌ Kein Investmentprodukt
- ❌ Keine regulatorische Lizenz
- ✅ Siehe [klaryx_legal.html](klaryx_legal.html) für vollständige Hinweise

**Nutzer sind verantwortlich für:**
- Wallet-Sicherheit
- Transaktionsverifizierung
- Verstehen, dass Blockchain-Transaktionen unveränderbar sind

## 🔐 Security

- **RLS disabled** (für vereinfachten Zugang)
- `.gitignore` schützt Secrets (*.json, .env)
- Supabase Service Role Key verschlüsselt gespeichert
- Keine privaten Keys im Repo

## 📞 Support

- Website: https://klaryx.de (Coming Soon)
- Email: info@klaryx.de
- Twitter: [@klaryx](https://twitter.com/klaryx)

## 📜 License

MIT License – Frei nutzbar und modifizierbar.

---

**Made with ❤️ for the Solana Community** ⚡
