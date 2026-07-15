-- ============================================
-- KLARYX COMMUNITY METRICS TABLES
-- ============================================
-- Task #45: Create tables for Gamification System
-- Purpose: Store weekly metrics, leaderboard data, and achievements

-- 1. COMMUNITY METRICS TABLE (Weekly Snapshots)
-- Stores aggregated data for reports (Free/Einblick/Tiefe)
CREATE TABLE IF NOT EXISTS community_metrics (
  id BIGSERIAL PRIMARY KEY,
  week_number INTEGER NOT NULL,
  year INTEGER NOT NULL,
  total_wallets INTEGER DEFAULT 0,
  new_this_week INTEGER DEFAULT 0,
  total_referrals INTEGER DEFAULT 0,
  avg_refs_per_wallet DECIMAL(10,2) DEFAULT 0,
  badge_distribution JSONB DEFAULT '{}'::jsonb,
  tier_distribution JSONB DEFAULT '{}'::jsonb,
  generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(week_number, year)
);

-- 2. LEADERBOARD CACHE TABLE
-- Pre-computed top referrers for fast loading
CREATE TABLE IF NOT EXISTS leaderboard_cache (
  id BIGSERIAL PRIMARY KEY,
  wallet_address VARCHAR(44) NOT NULL,
  referral_count INTEGER DEFAULT 0,
  badge VARCHAR(20),
  klrx_earned DECIMAL(10,3) DEFAULT 0,
  rank INTEGER,
  week_number INTEGER,
  year INTEGER,
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(wallet_address, week_number, year)
);

-- 3. ACHIEVEMENT UNLOCKS TABLE
-- Track when users unlock achievements
CREATE TABLE IF NOT EXISTS achievement_unlocks (
  id BIGSERIAL PRIMARY KEY,
  wallet_address VARCHAR(44) NOT NULL,
  achievement_name VARCHAR(50) NOT NULL,
  threshold_met INTEGER NOT NULL,
  unlocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  bonus_klrx_awarded DECIMAL(10,3) DEFAULT 0,
  UNIQUE(wallet_address, achievement_name)
);

-- 4. WEEKLY STREAKS TABLE
-- Track consecutive weeks of activity
CREATE TABLE IF NOT EXISTS weekly_streaks (
  id BIGSERIAL PRIMARY KEY,
  wallet_address VARCHAR(44) NOT NULL UNIQUE,
  current_streak INTEGER DEFAULT 0,
  longest_streak INTEGER DEFAULT 0,
  last_active_week INTEGER,
  last_active_year INTEGER,
  streak_bonus_klrx DECIMAL(10,3) DEFAULT 0,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on all new tables
ALTER TABLE community_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE achievement_unlocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_streaks ENABLE ROW LEVEL SECURITY;

-- RLS POLICIES: Service Role (Backend) - Full Access
CREATE POLICY "Service role: community_metrics full access"
  ON community_metrics
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role: leaderboard_cache full access"
  ON leaderboard_cache
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role: achievement_unlocks full access"
  ON achievement_unlocks
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role: weekly_streaks full access"
  ON weekly_streaks
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- RLS POLICIES: Public (Frontend) - Read Only
CREATE POLICY "Public: Read community_metrics"
  ON community_metrics
  FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Public: Read leaderboard_cache"
  ON leaderboard_cache
  FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Public: Read own achievements"
  ON achievement_unlocks
  FOR SELECT
  TO public
  USING (true);

CREATE POLICY "Public: Read own streak"
  ON weekly_streaks
  FOR SELECT
  TO public
  USING ((auth.uid())::text = wallet_address);

-- Grant permissions to service_role
GRANT SELECT, INSERT, UPDATE, DELETE ON community_metrics TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON leaderboard_cache TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON achievement_unlocks TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON weekly_streaks TO service_role;

-- Grant sequence access
GRANT USAGE, SELECT ON SEQUENCE community_metrics_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE leaderboard_cache_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE achievement_unlocks_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE weekly_streaks_id_seq TO service_role;

-- Verify tables created
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('community_metrics', 'leaderboard_cache', 'achievement_unlocks', 'weekly_streaks');
