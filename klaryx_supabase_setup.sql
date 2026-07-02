-- ============================================================
-- KLARYX – Supabase Datenbankstruktur
-- Einmal ausführen im Supabase SQL Editor
-- ============================================================

-- 1. WALLETS – alle registrierten Holder
CREATE TABLE IF NOT EXISTS wallets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  wallet_address TEXT UNIQUE NOT NULL,
  registered_at TIMESTAMPTZ DEFAULT NOW(),
  referrer_wallet TEXT DEFAULT NULL,
  klrx_balance NUMERIC(18,9) DEFAULT 0.01,
  badge TEXT DEFAULT 'Free',
  tier TEXT DEFAULT 'Free',
  einladungen INTEGER DEFAULT 0,
  claim_status TEXT DEFAULT 'Ausstehend',
  claim_sent_at TIMESTAMPTZ DEFAULT NULL,
  og_status BOOLEAN DEFAULT TRUE
);

-- 2. REFERRALS – Einladungshistorie
CREATE TABLE IF NOT EXISTS referrals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  referrer_wallet TEXT NOT NULL,
  invited_wallet TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  referral_bonus_sent BOOLEAN DEFAULT FALSE,
  referral_bonus_amount NUMERIC(18,9) DEFAULT 0.005
);

-- 3. BADGES – Badge-Verlauf
CREATE TABLE IF NOT EXISTS badges (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  wallet_address TEXT NOT NULL,
  badge_level TEXT NOT NULL,
  einladungen INTEGER NOT NULL,
  stufen_bonus NUMERIC(18,9) DEFAULT 0,
  bonus_status TEXT DEFAULT 'Ausstehend',
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. MARKET_DATA – Marktdaten (CoinGecko/Birdeye)
CREATE TABLE IF NOT EXISTS market_data (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  token_symbol TEXT NOT NULL,
  token_name TEXT NOT NULL,
  price_usd NUMERIC(18,8),
  volume_24h NUMERIC(18,2),
  price_change_24h NUMERIC(8,4),
  market_cap NUMERIC(18,2),
  sentiment TEXT DEFAULT NULL,
  source TEXT DEFAULT 'coingecko',
  recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. REPORTS – Wöchentliche KI-Marktberichte
CREATE TABLE IF NOT EXISTS reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  week_number INTEGER NOT NULL,
  year INTEGER NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  tier_required TEXT DEFAULT 'Einblick',
  published_at TIMESTAMPTZ DEFAULT NOW(),
  created_by TEXT DEFAULT 'AI'
);

-- 6. MEILENSTEINE – Tracking
CREATE TABLE IF NOT EXISTS milestones (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  phase INTEGER NOT NULL,
  name TEXT NOT NULL,
  target_holders INTEGER NOT NULL,
  reached_at TIMESTAMPTZ DEFAULT NULL,
  is_reached BOOLEAN DEFAULT FALSE
);

-- Meilensteine eintragen
INSERT INTO milestones (phase, name, target_holders) VALUES
  (1, 'Start – Free Claim aktiv', 1),
  (2, 'Wachstum – Social Media Push', 500),
  (3, 'Etabliert – Whitepaper & Investor', 1000),
  (4, 'Launch – DEX-Vorbereitung', 5000);

-- ============================================================
-- VIEWS – nützliche Abfragen
-- ============================================================

-- Aktuelle Holder-Anzahl
CREATE OR REPLACE VIEW holder_count AS
SELECT COUNT(*) as total_holders FROM wallets;

-- Badge-Übersicht
CREATE OR REPLACE VIEW badge_overview AS
SELECT badge, COUNT(*) as count
FROM wallets
GROUP BY badge
ORDER BY count DESC;

-- Top Referrer
CREATE OR REPLACE VIEW top_referrer AS
SELECT referrer_wallet, COUNT(*) as einladungen
FROM referrals
GROUP BY referrer_wallet
ORDER BY einladungen DESC
LIMIT 100;

-- ============================================================
-- ROW LEVEL SECURITY (RLS) – Datenschutz
-- ============================================================

-- Wallets: nur lesen (kein Schreiben von außen)
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read wallets" ON wallets FOR SELECT USING (true);

-- Reports: nur lesen
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read reports" ON reports FOR SELECT USING (true);

-- Market data: nur lesen
ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read market_data" ON market_data FOR SELECT USING (true);

-- Meilensteine: nur lesen
ALTER TABLE milestones ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read milestones" ON milestones FOR SELECT USING (true);

COMMENT ON TABLE wallets IS 'Alle registrierten KLRX Holder';
COMMENT ON TABLE referrals IS 'Einladungshistorie – wer hat wen eingeladen';
COMMENT ON TABLE badges IS 'Badge-Verlauf und Bonus-Status';
COMMENT ON TABLE market_data IS 'Historische Marktdaten von CoinGecko/Birdeye';
COMMENT ON TABLE reports IS 'Woechentliche KI-Marktberichte fuer Einblick/Tiefe Tier';
COMMENT ON TABLE milestones IS 'Community-Meilensteine';
