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

# python-telegram-bot
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    print("⚠️ python-telegram-bot not installed. Install with: pip install python-telegram-bot")
    exit(1)

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

# Validate
if not TELEGRAM_TOKEN:
    logger.error('❌ TELEGRAM_BOT_TOKEN not set')
    exit(1)

if not SUPABASE_KEY:
    logger.warning('⚠️ SUPABASE_SERVICE_ROLE_KEY not set (some commands may not work)')

# Supabase headers
SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY or "anon-key",
    "Authorization": f"Bearer {SUPABASE_KEY or 'anon-key'}",
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
    try:
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
        logger.info(f'✅ /start from {user.first_name} ({user.id})')
    except Exception as e:
        logger.error(f'❌ Error in /start: {e}')

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

💡 **Wie aufstufen?**
Teile deinen Referral Link! Jeder neue Holder erhöht deine Referral-Count.
"""
    try:
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
        logger.info(f'✅ /tier from {update.effective_user.first_name}')
    except Exception as e:
        logger.error(f'❌ Error in /tier: {e}')

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
1. Erkläre was Klaryx ist
2. Zeige deine Tier-Level
3. Erwähne die exklusiven Reports
4. Sei authentisch
5. Hilf anderen, ihre Links zu teilen

🤝 Je mehr Holder, desto wertvoller wird Klaryx!
"""
    try:
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
        logger.info(f'✅ /referral from {update.effective_user.first_name}')
    except Exception as e:
        logger.error(f'❌ Error in /referral: {e}')

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get leaderboard"""
    try:
        # Fetch wallets
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/wallets?select=wallet_address&limit=100",
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
                f"{SUPABASE_URL}/rest/v1/wallets?select=count()&referrer_wallet=eq.{wallet['wallet_address']}",
                headers=SUPABASE_HEADERS,
                timeout=10
            )
            if ref_response.ok:
                try:
                    count = ref_response.json()[0]['count']
                    if count > 0:
                        referral_counts[wallet['wallet_address']] = count
                except:
                    pass

        # Sort and get top 10
        sorted_wallets = sorted(referral_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        if not sorted_wallets:
            message = "📊 Leaderboard wird noch aufgebaut...\n\nSei der erste! Teile deinen Referral Link!"
            await update.message.reply_text(message, parse_mode='Markdown')
            return

        # Format message
        message = "🏆 **Top Referrer**\n\n"
        medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        for idx, (wallet, count) in enumerate(sorted_wallets):
            medal = medals[idx] if idx < len(medals) else f"{idx+1}️⃣"
            bonus = count * 0.005
            message += f"{medal} `{wallet[:8]}...{wallet[-4:]}` • {count} Refs (+{bonus:.3f} KLRX)\n"

        message += "\n💡 Kannst du es in die Top 10 schaffen? Teile deinen Link!"

        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f'✅ /leaderboard executed')
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

        total_wallets = 0
        if count_response.ok:
            try:
                total_wallets = count_response.json()[0]['count']
            except:
                pass

        message = f"""
📊 **Klaryx Community Stats**

👥 **Holder:** {total_wallets}

🎯 **Phases:**
✅ Phase 1: LIVE
📍 Phase 2: 500 Holder
📍 Phase 3: 1.000 Holder
📍 Phase 4: 5.000 Holder
📍 Phase 5: 10.000 Holder (Company Launch)

**Status:**
✅ Community Intelligence Reports
✅ Referral System
✅ Gamification aktiv
✅ Security geprüft

🔗 Dashboard: https://klaryx.de/klaryx_milestones.html
"""
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
        logger.info(f'✅ /stats executed')
    except Exception as e:
        logger.error(f'❌ Error in /stats: {e}')
        await update.message.reply_text('❌ Error fetching stats')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    message = """
❓ **Klaryx Bot Commands**

/start - Willkommensnachricht
/tier - Dein aktuelles Tier
/referral - Referral Info
/leaderboard - Top Referrer
/stats - Community Stats
/help - Diese Hilfe

🔗 **Links:**
🌐 Portal: https://klaryx.de/portal.html
📈 Milestones: https://klaryx.de/klaryx_milestones.html
🏆 Hall of Fame: https://klaryx.de/klaryx_halloffame.html

💬 **Gruppen:**
- Klaryx Community (Chat)
- Klaryx Referrals (Tipps)

🚀 Let's grow Klaryx!
"""
    try:
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
        logger.info(f'✅ /help from {update.effective_user.first_name}')
    except Exception as e:
        logger.error(f'❌ Error in /help: {e}')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f'Update {update} caused error {context.error}')

# Main
def main():
    """Start bot"""
    if not TELEGRAM_TOKEN:
        logger.error('❌ TELEGRAM_BOT_TOKEN not set')
        return

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
    logger.info(f'📱 Bot ready to receive commands')

    try:
        app.run_polling()
    except KeyboardInterrupt:
        logger.info('🛑 Bot stopped')

if __name__ == '__main__':
    main()
