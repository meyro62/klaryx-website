-- ============================================
-- KLARYX RLS FIX - SAUBERE LÖSUNG
-- ============================================
-- Problem: Edge Function "payout-referral-bonuses" hat keine SELECT-Berechtigung auf wallets
-- Lösung: Saubere RLS-Policies für service_role und public getrennt

-- Step 1: Lösche ALLE permissiven anon/public policies
DROP POLICY IF EXISTS "Anon can read all wallets" ON wallets;
DROP POLICY IF EXISTS "Anon can view wallet data" ON wallets;
DROP POLICY IF EXISTS "Anon can register wallet" ON wallets;

-- Step 2: Stelle sicher dass RLS auf der Tabelle enabled ist
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;

-- Step 3: Service Role Policies (für Backend/Edge Functions - voll Zugriff)
CREATE POLICY "Service role: SELECT all wallets"
  ON wallets
  FOR SELECT
  TO service_role
  USING (true);

CREATE POLICY "Service role: INSERT wallets"
  ON wallets
  FOR INSERT
  TO service_role
  WITH CHECK (true);

CREATE POLICY "Service role: UPDATE all wallets"
  ON wallets
  FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role: DELETE wallets"
  ON wallets
  FOR DELETE
  TO service_role
  USING (true);

-- Step 4: Public Policies (nur für EIGENE wallet)
-- Diese sind für normale Users, nicht für Backend
CREATE POLICY "Public: SELECT own wallet"
  ON wallets
  FOR SELECT
  TO public
  USING ((auth.uid())::text = wallet_address);

CREATE POLICY "Public: INSERT own wallet"
  ON wallets
  FOR INSERT
  TO public
  WITH CHECK ((auth.uid())::text = wallet_address);

CREATE POLICY "Public: UPDATE own wallet"
  ON wallets
  FOR UPDATE
  TO public
  USING ((auth.uid())::text = wallet_address)
  WITH CHECK ((auth.uid())::text = wallet_address);

CREATE POLICY "Public: DELETE own wallet"
  ON wallets
  FOR DELETE
  TO public
  USING ((auth.uid())::text = wallet_address);

-- Step 5: Verifiziere dass alles richtig ist
SELECT policyname, roles, cmd, qual FROM pg_policies WHERE tablename = 'wallets' ORDER BY policyname;
