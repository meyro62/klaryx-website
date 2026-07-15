# 🤖 KLARYX Telegram Bot Setup Guide

**Task #48 - WEEK 2**

## Step 1: Create Telegram Bot (via BotFather)

### 1.1 Create Bot with BotFather
1. Open Telegram
2. Search: `@BotFather`
3. Send: `/newbot`
4. Choose name: **Klaryx Bot**
5. Choose username: `@KlaryxBot` (must be unique)
6. Copy the **Bot Token** → Save securely (GitHub Secrets)

### 1.2 Configure Bot Settings
1. In BotFather: `/mybots` → select **Klaryx Bot**
2. Click **"Bot Settings"**
3. Set:
   - Commands → Add:
     - `/start` - Start bot & info
     - `/tier` - Check your tier
     - `/referral` - Get referral link
     - `/leaderboard` - Top referrers
     - `/stats` - Community stats
     - `/help` - Show commands

### 1.3 Enable Group Permissions (Optional)
- Allow in groups: YES
- Allow in channels: YES

---

## Step 2: Create Telegram Groups/Channels

### 2.1 Create Groups

**Main Groups:**
```
📢 Klaryx Announcements (Channel - read-only)
💬 Klaryx Community (Group)
🔗 Klaryx Referrals (Group)
📊 Klaryx Reports (Private - for Tiefe tier)
```

### 2.2 Group Descriptions

**Announcements Channel:**
```
🚀 Klaryx Community Updates

Offizielle Neuigkeiten über Klaryx

📱 Portal: https://klaryx.de/portal.html
🔗 Milestones: https://klaryx.de/klaryx_milestones.html

Abonniere für Benachrichtigungen!
```

**Community Group:**
```
💬 Klaryx Community Chat

Ort für Community-Diskussionen:
- Fragen stellen
- Erfahrungen austauschen
- Tipps für Referrals
- Community-Events

🤖 Bot Commands: /help
```

**Referrals Group:**
```
🔗 Klaryx Referral Community

Strategien zum Verdienen:
- Referral-Tipps teilen
- Erfolgsgeschichten
- Marketing-Ideen

💰 Jeder Referral = +0.005 KLRX
📈 25 Refs = Einblick Tier
👑 50 Refs = Tiefe Tier
```

---

## Step 3: GitHub Secrets Configuration

Add to GitHub repository secrets:

```
TELEGRAM_BOT_TOKEN=<your-bot-token-here>
TELEGRAM_ANNOUNCEMENTS_CHANNEL_ID=<channel-id>
TELEGRAM_COMMUNITY_GROUP_ID=<group-id>
TELEGRAM_REFERRALS_GROUP_ID=<group-id>
TELEGRAM_REPORTS_CHANNEL_ID=<channel-id>
SUPABASE_URL=https://wpxcgducfkbozecknfdw.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
```

**How to get IDs:**
1. Add bot to group/channel
2. Send a message
3. Open: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Find `chat.id` in response

---

## Step 4: Telegram Bot Script (Python)

Create: `.github/scripts/telegram_bot.py`

```python
#!/usr/bin/env python3
"""
Klaryx Telegram Bot - Community Management
Handles:
- Welcome messages
- Referral info
- Community stats
- Weekly announcements
"""

import os
import logging
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://wpxcgducfkbozecknfdw.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
ANNOUNCEMENTS_CHANNEL = os.environ.get('TELEGRAM_ANNOUNCEMENTS_CHANNEL_ID')

# Validate
if not TELEGRAM_TOKEN:
    logger.error('❌ TELEGRAM_BOT_TOKEN not set')
    exit(1)

# Supabase headers
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    message = f"""
🚀 Willkommen zu Klaryx, {user.first_name}!

Klaryx ist ein Community-Projekt auf Solana mit Rewards für aktive Mitglieder.

📱 **Deine Optionen:**
/tier - Dein aktuelles Tier
/referral - Referral Link & Tipps
/leaderboard - Top Referrer
/stats - Community Statistiken
/help - Alle Commands

🔗 **Links:**
Portal: https://klaryx.de/portal.html
Milestones: https://klaryx.de/klaryx_milestones.html

💡 **Wie funktioniert's?**
1. Registriere deine Wallet im Portal
2. Teile deinen Referral Link
3. Verdiene KLRX für jeden Referral
4. Erreiche höhere Tiers (Einblick, Tiefe)
5. Erhalte exklusive Community Intelligence Reports

👥 Tritt unseren Gruppen bei:
- Klaryx Community (Chat & Support)
- Klaryx Referrals (Tipps & Strategien)

Los geht's! 🚀
"""
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f'✅ /start command from {user.first_name} ({user.id})')

async def tier_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check tier command"""
    message = """
🏆 **Dein Klaryx Tier**

Gehe zu https://klaryx.de/portal.html um dein Tier zu sehen.

**Tier-Übersicht:**
🟢 **Free**: 0 Referrals
   • Basis-Features
   • Free Tier Reports
   
🔵 **Einblick**: 25+ Referrals
   • +0.90 KLRX Bonus gesamt
   • Community Intelligence Reports
   • Hall of Fame Eintrag
   
🟣 **Tiefe**: 50+ Referrals
   • +2.0 KLRX Bonus gesamt
   • Network Analysis Reports
   • Premium Hall of Fame

👑 **Legend**: 100+ Referrals
   • +2.0+ KLRX Bonus
   • Alle Premium Features
   • VIP Status
   • Eintrag in Hall of Fame

💡 **Wie aufstufen?**
Teile deinen Referral Link! Jeder neue Holder erhöht deine Referral-Count.
"""
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f'✅ /tier command from {update.effective_user.first_name}')

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get referral info"""
    message = """
🔗 **Dein Referral Link**

Gehe zu https://klaryx.de/portal.html um deinen persönlichen Referral Link zu kopieren.

**💰 Verdiene mit Referrals:**
• Jeder Referral = +0.005 KLRX
• Jeder Referral = +1 zur Referral Count
• 25 Refs = Einblick Tier Unlock 🔵
• 50 Refs = Tiefe Tier Unlock 🟣
• 100 Refs = Legend Status 👑

**📤 Wo teilen?**
✅ Twitter / X
✅ Discord Communities
✅ Telegram Groups
✅ Reddit
✅ WhatsApp Friends
✅ Persönlich

**🎯 Tipps zum Erfolg:**
1. Erkläre was Klaryx ist (Community Project, Rewards)
2. Zeige deine Tier-Level
3. Erwähne die exklusiven Reports
4. Sei authentisch (nicht spammy)
5. Hilf anderen, ihre Links zu teilen

🤝 Je mehr aktive Community-Member, desto wertvoller wird Klaryx für alle!
"""
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f'✅ /referral command from {update.effective_user.first_name}')

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get leaderboard"""
    try:
        # Fetch from Supabase
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/wallets?select=wallet_address,registered_at&order=registered_at.desc&limit=100",
            headers=SUPABASE_HEADERS,
            timeout=10
        )

        if not response.ok:
            await update.message.reply_text('❌ Could not fetch leaderboard')
            return

        wallets = response.json()

        # Calculate referral counts
        referral_counts = {}
        for wallet in wallets:
            ref_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/wallets?select=wallet_address&referrer_wallet=eq.{wallet['wallet_address']}",
                headers=SUPABASE_HEADERS,
                timeout=10
            )
            if ref_response.ok:
                referral_counts[wallet['wallet_address']] = len(ref_response.json())

        # Sort and get top 10
        sorted_wallets = sorted(referral_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Format message
        message = "🏆 **Top 10 Referrer dieser Woche**\n\n"
        for idx, (wallet, count) in enumerate(sorted_wallets, 1):
            badge = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][idx-1]
            bonus = count * 0.005
            message += f"{badge} `{wallet[:8]}...{wallet[-4:]}` - {count} Refs (+{bonus:.3f} KLRX)\n"

        message += "\n💡 Kannst du es in die Top 10 schaffen? Teile deinen Referral Link!"

        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f'✅ /leaderboard command executed')
    except Exception as e:
        logger.error(f'❌ Error in /leaderboard: {e}')
        await update.message.reply_text('❌ Error fetching leaderboard')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get community stats"""
    try:
        # Fetch wallet count
        count_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/wallets?select=count()",
            headers=SUPABASE_HEADERS,
            timeout=10
        )

        total_wallets = count_response.json()[0]['count'] if count_response.ok else 0

        message = f"""
📊 **Klaryx Community Stats**

👥 **Holder:** {total_wallets}
🎯 **Phase 1:** ✅ LIVE
📈 **Phase 2 Target:** 500 Holder
🚀 **Phase 5 Target:** 10.000 Holder (Company Launch)

**Aktueller Status:**
✅ Community Intelligence Reports aktiv
✅ Referral System läuft
✅ Gamification aktiv
✅ Sicherheit geprüft

🔗 Live Dashboard: https://klaryx.de/klaryx_milestones.html
"""
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f'✅ /stats command executed')
    except Exception as e:
        logger.error(f'❌ Error in /stats: {e}')
        await update.message.reply_text('❌ Error fetching stats')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    message = """
❓ **Klaryx Bot Commands**

/start - Willkommensnachricht
/tier - Dein aktuelles Tier anzeigen
/referral - Referral Link Info
/leaderboard - Top 10 Referrer
/stats - Community Statistiken
/help - Diese Hilfe

🔗 **Wichtige Links:**
🌐 Portal: https://klaryx.de/portal.html
📈 Milestones: https://klaryx.de/klaryx_milestones.html
🏆 Hall of Fame: https://klaryx.de/klaryx_halloffame.html

📱 **Unsere Gruppen:**
💬 Klaryx Community - Chat & Support
🔗 Klaryx Referrals - Tipps & Strategien

💡 **Haben wir Fragen?**
Schreib in der Community Group oder kontaktiere einen Moderator!

🚀 Let's grow Klaryx together!
"""
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f'✅ /help command from {update.effective_user.first_name}')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f'Update {update} caused error {context.error}')

# Main
def main():
    """Start bot"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('tier', tier_command))
    app.add_handler(CommandHandler('referral', referral_command))
    app.add_handler(CommandHandler('leaderboard', leaderboard_command))
    app.add_handler(CommandHandler('stats', stats_command))
    app.add_handler(CommandHandler('help', help_command))

    # Error handler
    app.add_error_handler(error_handler)

    logger.info('🤖 Klaryx Telegram Bot starting...')
    app.run_polling()

if __name__ == '__main__':
    main()
```

---

## Step 5: Telegram Weekly Announcements Workflow

Create: `.github/workflows/telegram-announcements.yml`

```yaml
name: Telegram Weekly Announcements

on:
  schedule:
    - cron: '45 10 * * 0'  # Every Sunday 10:45 UTC
  workflow_dispatch:

jobs:
  announce:
    runs-on: ubuntu-latest
    name: Post Weekly Telegram Announcement

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install requests
        run: pip install requests --break-system-packages

      - name: Send Telegram Announcement
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_ANNOUNCEMENTS_CHANNEL: ${{ secrets.TELEGRAM_ANNOUNCEMENTS_CHANNEL_ID }}
          SUPABASE_URL: https://wpxcgducfkbozecknfdw.supabase.co
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
        run: |
          python << 'EOF'
          import requests
          import json
          from datetime import datetime

          bot_token = "${{ env.TELEGRAM_BOT_TOKEN }}"
          chat_id = "${{ env.TELEGRAM_ANNOUNCEMENTS_CHANNEL }}"
          supabase_url = "${{ env.SUPABASE_URL }}"
          supabase_key = "${{ env.SUPABASE_SERVICE_ROLE_KEY }}"

          if not all([bot_token, chat_id]):
              print("⚠️ Telegram credentials not configured")
              exit(0)

          headers = {
              "apikey": supabase_key,
              "Authorization": f"Bearer {supabase_key}"
          }

          # Get stats
          try:
              response = requests.get(
                  f"{supabase_url}/rest/v1/wallets?select=count()",
                  headers=headers,
                  timeout=10
              )
              total_wallets = response.json()[0]['count'] if response.ok else 0
          except:
              total_wallets = 0

          # Create message
          week = datetime.now().isocalendar()[1]
          message = f"""
📊 **Klaryx Weekly Update - Week {week}/2026**

👥 **Community Size:** {total_wallets} Holder

🎯 **This Week:**
✨ Community Intelligence Reports published
📈 Referral activity tracking
🏆 Leaderboard updated

📱 **Check Your Progress:**
🔗 Portal: https://klaryx.de/portal.html
👑 Hall of Fame: https://klaryx.de/klaryx_halloffame.html

💡 **Next Phase Target:** Phase 2 @ 500 Holder

🚀 Keep sharing your referral link!

---
*Klaryx Community Bot | Every Sunday 10:45 UTC*
"""

          # Send via Telegram API
          url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
          data = {
              "chat_id": chat_id,
              "text": message,
              "parse_mode": "Markdown",
              "disable_web_page_preview": True
          }

          try:
              response = requests.post(url, json=data, timeout=10)
              if response.status_code == 200:
                  print("✅ Telegram announcement sent successfully")
              else:
                  print(f"⚠️ Telegram API returned {response.status_code}: {response.text}")
          except Exception as e:
              print(f"❌ Error sending Telegram message: {e}")

          EOF

      - name: Log completion
        run: |
          echo "✅ Telegram announcements workflow completed"
```

---

## Step 6: Testing

### Test Bot Locally
```bash
export TELEGRAM_BOT_TOKEN="your-token"
python .github/scripts/telegram_bot.py
```

### Test Commands
1. Start bot: `/start`
2. Check tier: `/tier`
3. Get referral: `/referral`
4. See leaderboard: `/leaderboard`
5. Get stats: `/stats`

---

## Step 7: Add Bot to Groups

1. Create test group
2. Add @KlaryxBot
3. Test commands
4. Invite real users

---

## Summary

✅ Telegram Bot with 6 commands
✅ Group/Channel structure ready
✅ Weekly announcements automated
✅ Leaderboard integration
✅ Community stats fetching

**Status: READY FOR DEPLOYMENT** 🚀
