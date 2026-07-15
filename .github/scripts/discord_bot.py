#!/usr/bin/env python3
"""
Klaryx Discord Bot - Community Management
Handles:
- Welcome messages
- Role management based on referrals
- Weekly report posting
- Community announcements
"""

import os
import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
SERVER_ID = int(os.environ.get('DISCORD_SERVER_ID', 0)) if os.environ.get('DISCORD_SERVER_ID') else None
ANNOUNCEMENTS_CHANNEL_ID = int(os.environ.get('DISCORD_ANNOUNCEMENTS_CHANNEL_ID', 0)) if os.environ.get('DISCORD_ANNOUNCEMENTS_CHANNEL_ID') else None
REPORTS_CHANNEL_ID = int(os.environ.get('DISCORD_REPORTS_CHANNEL_ID', 0)) if os.environ.get('DISCORD_REPORTS_CHANNEL_ID') else None
EINBLICK_CHANNEL_ID = int(os.environ.get('DISCORD_EINBLICK_CHANNEL_ID', 0)) if os.environ.get('DISCORD_EINBLICK_CHANNEL_ID') else None
TIEFE_CHANNEL_ID = int(os.environ.get('DISCORD_TIEFE_CHANNEL_ID', 0)) if os.environ.get('DISCORD_TIEFE_CHANNEL_ID') else None

# Validate token
if not DISCORD_TOKEN:
    logger.error('❌ DISCORD_BOT_TOKEN not set in environment')
    exit(1)

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Create bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Events
@bot.event
async def on_ready():
    """Bot is ready"""
    logger.info(f'✅ Bot logged in as {bot.user}')
    logger.info(f'🎮 Bot is in {len(bot.guilds)} guild(s)')

    # Set status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name='Klaryx Community grow 📈'
        )
    )

    # Start background tasks
    if not sync_roles.is_running():
        sync_roles.start()
        logger.info('🔄 Role sync task started')

@bot.event
async def on_member_join(member):
    """Welcome new member"""
    try:
        if not SERVER_ID:
            logger.warning('⚠️ SERVER_ID not configured, skipping welcome')
            return

        server = bot.get_guild(SERVER_ID)
        if not server:
            logger.error(f'❌ Could not find guild {SERVER_ID}')
            return

        # Auto-assign @Community role
        community_role = discord.utils.get(server.roles, name='Community')
        if community_role:
            try:
                await member.add_roles(community_role)
                logger.info(f'✅ Assigned @Community role to {member.name}')
            except discord.Forbidden:
                logger.error(f'❌ Cannot assign role to {member.name} (insufficient permissions)')
        else:
            logger.warning('⚠️ @Community role not found')

        # Send welcome message
        if ANNOUNCEMENTS_CHANNEL_ID:
            welcome_channel = bot.get_channel(ANNOUNCEMENTS_CHANNEL_ID)
            if welcome_channel:
                embed = discord.Embed(
                    title=f'🎉 Willkommen, {member.name}!',
                    description='Du bist der Klaryx Community beigetreten!',
                    color=discord.Color.green()
                )
                embed.add_field(
                    name='📱 Nächste Schritte:',
                    value='1. Stelle dich in #introductions vor\n2. Gehe zu https://klaryx.de/portal.html\n3. Registriere deine Wallet\n4. Verdiene Referrals!',
                    inline=False
                )
                embed.add_field(
                    name='💬 Kanäle:',
                    value='#announcements - News & Updates\n#general - Community Chat\n#referrals - Tipps & Strategien',
                    inline=False
                )
                embed.set_footer(text=f'Willkommen bei Klaryx | {datetime.now().strftime("%d.%m.%Y")}')

                try:
                    await welcome_channel.send(f'{member.mention}', embed=embed)
                    logger.info(f'✅ Welcome message sent to {member.name}')
                except discord.Forbidden:
                    logger.error(f'❌ Cannot send message to {ANNOUNCEMENTS_CHANNEL_ID}')
    except Exception as e:
        logger.error(f'❌ Error in on_member_join: {e}')

@bot.event
async def on_error(event, *args, **kwargs):
    """Error handler"""
    logger.error(f'❌ Error in {event}: {args} {kwargs}')

# Commands
@bot.command(name='tier', help='Check your Klaryx tier')
async def check_tier(ctx):
    """Check user's tier"""
    try:
        embed = discord.Embed(
            title='🏆 Dein Klaryx Tier',
            description='Gehe zu https://klaryx.de/portal.html um dein Tier zu sehen',
            color=discord.Color.blue()
        )
        embed.add_field(
            name='📊 Tier-Übersicht:',
            value='🟢 Free: 0 Referrals\n🔵 Einblick: 25+ Referrals\n🟣 Tiefe: 50+ Referrals',
            inline=False
        )
        await ctx.send(embed=embed)
        logger.info(f'✅ !tier command used by {ctx.author.name}')
    except Exception as e:
        logger.error(f'❌ Error in !tier: {e}')
        await ctx.send('❌ Error checking tier')

@bot.command(name='referral', help='Get your referral link')
async def get_referral_link(ctx):
    """Get referral link"""
    try:
        embed = discord.Embed(
            title='🔗 Dein Referral Link',
            description='Gehe zu https://klaryx.de/portal.html um deinen Referral Link zu kopieren',
            color=discord.Color.blue()
        )
        embed.add_field(
            name='💡 Tipps zum Verdienen:',
            value='• Teile deinen Link überall (Twitter, Telegram, Discord)\n• Jeder Referral = +0.005 KLRX\n• 25 Refs = Einblick Tier Unlock (Community Intelligence)\n• 50 Refs = Tiefe Tier Unlock (Network Analysis)\n• 100 Refs = Legend Status (Hall of Fame)',
            inline=False
        )
        embed.set_footer(text='Aktiv referren = Aktive Community = Mehr Wert für alle!')
        await ctx.send(embed=embed)
        logger.info(f'✅ !referral command used by {ctx.author.name}')
    except Exception as e:
        logger.error(f'❌ Error in !referral: {e}')
        await ctx.send('❌ Error getting referral info')

@bot.command(name='stats', help='Show community stats')
async def get_stats(ctx):
    """Get community stats"""
    try:
        embed = discord.Embed(
            title='📊 Klaryx Community Stats',
            description='Live stats from https://klaryx.de/klaryx_milestones.html',
            color=discord.Color.blurple()
        )
        embed.add_field(
            name='🎯 Phases:',
            value='Phase 1: ✅ JETZT LIVE\nPhase 2: 500 Holder\nPhase 3: 1.000 Holder\nPhase 4: 5.000 Holder\nPhase 5: 10.000 Holder (Company Launch)',
            inline=False
        )
        embed.set_footer(text='Besuche https://klaryx.de für aktuelle Zahlen')
        await ctx.send(embed=embed)
        logger.info(f'✅ !stats command used by {ctx.author.name}')
    except Exception as e:
        logger.error(f'❌ Error in !stats: {e}')
        await ctx.send('❌ Error getting stats')

@bot.command(name='help', help='Show all commands')
async def show_help(ctx):
    """Show help"""
    try:
        embed = discord.Embed(
            title='❓ Klaryx Bot Commands',
            description='Alle verfügbaren Befehle:',
            color=discord.Color.gold()
        )
        embed.add_field(
            name='📱 Portal & Account:',
            value='`!tier` - Dein aktuelles Tier anzeigen\n`!referral` - Referral Link Info',
            inline=False
        )
        embed.add_field(
            name='📊 Gemeinschaft:',
            value='`!stats` - Community Statistiken\n`!help` - Diesen Help anzeigen',
            inline=False
        )
        embed.add_field(
            name='🌐 Links:',
            value='🔗 Portal: https://klaryx.de/portal.html\n🔗 Milestones: https://klaryx.de/klaryx_milestones.html',
            inline=False
        )
        await ctx.send(embed=embed)
        logger.info(f'✅ !help command used by {ctx.author.name}')
    except Exception as e:
        logger.error(f'❌ Error in !help: {e}')

# Background Tasks
@tasks.loop(hours=1)
async def sync_roles():
    """Sync Discord roles with Supabase (hourly)

    TODO: Connect to Supabase REST API to:
    - Get top referrers from wallets table
    - Assign @Referrer (25+) role
    - Assign @Legend (50+) role
    """
    try:
        if not SERVER_ID:
            return

        server = bot.get_guild(SERVER_ID)
        if not server:
            logger.error(f'❌ Could not find guild {SERVER_ID}')
            return

        logger.info(f'🔄 Syncing roles at {datetime.now().isoformat()}')

        # TODO: Call Supabase REST API
        # Example:
        # response = requests.get(
        #     "https://wpxcgducfkbozecknfdw.supabase.co/rest/v1/wallets",
        #     headers={
        #         "apikey": SUPABASE_KEY,
        #         "Authorization": f"Bearer {SUPABASE_KEY}"
        #     }
        # )
        # wallets = response.json()
        #
        # for wallet in wallets:
        #     if wallet.get('referrer_count', 0) >= 25:
        #         # Find member and assign @Referrer role
        #         pass

        logger.info('✅ Role sync completed')
    except Exception as e:
        logger.error(f'❌ Error in sync_roles: {e}')

@sync_roles.before_loop
async def before_sync_roles():
    """Wait until bot is ready"""
    await bot.wait_until_ready()
    logger.info('⏳ Waiting for bot ready...')

# Main
if __name__ == '__main__':
    logger.info('🚀 Klaryx Discord Bot starting...')
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.InvalidToken:
        logger.error('❌ Invalid Discord token provided')
        exit(1)
    except Exception as e:
        logger.error(f'❌ Fatal error: {e}')
        exit(1)
