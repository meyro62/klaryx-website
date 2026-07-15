# Task #45: Community Metrics Database Tables

## Status: COMPLETE ✅

SQL-Datei wurde erstellt: `create_community_metrics_tables.sql`

## Ausführung in Supabase

1. Öffne Supabase Dashboard
2. Gehe zu: **SQL Editor**
3. Klicke: **New Query**
4. Kopiere den kompletten Inhalt von `create_community_metrics_tables.sql`
5. Klicke: **RUN**

## Tabellen erstellt:

### 1. `community_metrics` (Weekly Snapshots)
- Stores aggregated data für Free/Einblick/Tiefe Reports
- Fields: total_wallets, new_this_week, badge_distribution, tier_distribution
- Unique: (week_number, year)

### 2. `leaderboard_cache` (Top Referrer)
- Pre-computed rankings für schnelle Leaderboard-Anzeige
- Fields: wallet_address, referral_count, badge, rank
- Updated weekly by GitHub Actions

### 3. `achievement_unlocks` (Gamification)
- Tracks wann User welche Achievement freischalten
- Fields: wallet_address, achievement_name, threshold_met, bonus_klrx_awarded
- Unique: (wallet_address, achievement_name)

### 4. `weekly_streaks` (Consistency Rewards)
- Für zukünftige Streak-Bonuses
- Fields: current_streak, longest_streak, streak_bonus_klrx
- Updated after jeder Woche mit Aktivität

## RLS Security:
✅ Service Role: Full CRUD (für Backend/GitHub Actions)
✅ Public: Read-Only (für Frontend/Leaderboard)
✅ All GRANT permissions set up

## Next Steps:
- Task #46: Update index.html - Remove "später" Messages
- Task #47+: Discord/Telegram Integration
