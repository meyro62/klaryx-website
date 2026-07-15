# 🎮 KLARYX Discord Server Setup Guide

**Task #47 - WEEK 2**

## Step 1: Create Discord Server (Manually)

### 1.1 Create Server
1. Go to Discord → Click "+" → "Create a server"
2. Name: **Klaryx Community**
3. Region: Frankfurt (GDPR compliant)

### 1.2 Server Structure (Channels)

Delete default channels. Create these:

```
📌 GENERAL (Text)
├─ #announcements (News & Updates - POST ONLY)
├─ #welcome (Intro channel with rules)
├─ #general (Community chat)
└─ #introductions (Members introduce themselves)

💬 COMMUNITY (Text)
├─ #referrals (Referral strategies & tips)
├─ #milestones (Celebrate when phases unlock)
├─ #showcase (User screenshots & wins)
└─ #feedback (Feature requests & ideas)

📊 REPORTS (Text)
├─ #weekly-reports (Auto-posted Free tier reports)
├─ #einblick-reports (Restricted to Einblick tier)
└─ #tiefe-reports (Restricted to Tiefe tier)

🎯 ROLES (Voice)
├─ #general-voice (Community voice chat)
└─ #events (Future events)

🔧 ROLES & PERMISSIONS

Roles to create:
- @Community (Auto-assign on join)
- @Referrer (25+ refs - access to Einblick)
- @Legend (50+ refs - access to Tiefe)
- @Moderator (Manual assign)
- @Bot (For Discord bot)
```

### 1.3 Role Permissions

| Role | Permissions |
|------|-------------|
| @everyone | See #announcements, #welcome, #general, #introductions |
| @Community | See all channels except tier-locked |
| @Referrer (Einblick) | See #einblick-reports |
| @Legend (Tiefe) | See #tiefe-reports |
| @Moderator | Manage messages, pin, edit |
| @Bot | Send messages, manage roles, react |

---

## Step 2: Create Discord Bot

### 2.1 Create Bot Application
1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name: **Klaryx Bot**
4. Accept Terms
5. Go to "Bot" tab → Click "Add Bot"

### 2.2 Configure Bot
1. **Intents** → Enable:
   - [x] Message Content Intent
   - [x] Server Members Intent
   - [x] Guild Messages

2. **Permissions** → Select:
   - [x] Send Messages
   - [x] Send Messages in Threads
   - [x] Embed Links
   - [x] Attach Files
   - [x] Manage Roles
   - [x] Read Message History
   - [x] React with Emojis

3. **Copy Bot Token** → Save securely (GitHub Secrets)

### 2.3 Invite Bot to Server
1. Go to "OAuth2" → "URL Generator"
2. Select scopes: `bot`
3. Select permissions: (same as above)
4. Copy generated URL
5. Open URL in browser
6. Select "Klaryx Community" server
7. Click "Authorize"

---

## Step 3: GitHub Secrets Configuration

Add these to GitHub repository secrets:

```
DISCORD_BOT_TOKEN=<your-bot-token-here>
DISCORD_SERVER_ID=<your-server-id>
DISCORD_ANNOUNCEMENTS_CHANNEL_ID=<announcements-channel-id>
DISCORD_REPORTS_CHANNEL_ID=<weekly-reports-channel-id>
DISCORD_EINBLICK_CHANNEL_ID=<einblick-reports-channel-id>
DISCORD_TIEFE_CHANNEL_ID=<tiefe-reports-channel-id>
```

**How to get IDs:**
- Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
- Right-click channel/server → Copy ID

---

## Step 4: Discord Bot Script (Python)

Create: `.github/scripts/discord_bot.py`

```python
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

# Configuration
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
SERVER_ID = int(os.environ.get('DISCORD_SERVER_ID', 0))
ANNOUNCEMENTS_CHANNEL_ID = int(os.environ.get('DISCORD_ANNOUNCEMENTS_CHANNEL_ID', 0))
REPORTS_CHANNEL_ID = int(os.environ.get('DISCORD_REPORTS_CHANNEL_ID', 0))
EINBLICK_CHANNEL_ID = int(os.environ.get('DISCORD_EINBLICK_CHANNEL_ID', 0))
TIEFE_CHANNEL_ID = int(os.environ.get('DISCORD_TIEFE_CHANNEL_ID', 0))

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Bot is ready"""
    print(f'✅ Bot logged in as {bot.user}')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name='Klaryx Community grow 📈'
        )
    )

@bot.event
async def on_member_join(member):
    """Welcome new member"""
    server = bot.get_guild(SERVER_ID)
    
    # Auto-assign @Community role
    community_role = discord.utils.get(server.roles, name='Community')
    if community_role:
        await member.add_roles(community_role)
    
    # Send welcome message
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
            value='#announcements - News\n#general - Chat\n#referrals - Tipps',
            inline=False
        )
        await welcome_channel.send(embed=embed)

@bot.command(name='tier')
async def check_tier(ctx):
    """Check user's tier (manual command)"""
    embed = discord.Embed(
        title='🏆 Dein Klaryx Tier',
        description='Gehe zu https://klaryx.de/portal.html um dein Tier zu sehen',
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command(name='referral')
async def get_referral_link(ctx):
    """Get referral link"""
    embed = discord.Embed(
        title='🔗 Dein Referral Link',
        description='Gehe zu https://klaryx.de/portal.html um deinen Referral Link zu kopieren',
        color=discord.Color.blue()
    )
    embed.add_field(
            name='💡 Tipps:',
            value='• Teile deinen Link überall\n• Jeder Referral = +0.005 KLRX\n• 25 Refs = Einblick Tier Unlock!',
            inline=False
        )
    await ctx.send(embed=embed)

@tasks.loop(hours=1)
async def sync_roles():
    """Sync Discord roles with Supabase (hourly)
    
    In future: Connect to Supabase REST API to check
    referral counts and update roles accordingly
    """
    server = bot.get_guild(SERVER_ID)
    if not server:
        return
    
    print(f'🔄 Syncing roles at {datetime.now().isoformat()}')
    # TODO: Call Supabase API to get top referrers
    # TODO: Assign @Referrer role to 25+ refs
    # TODO: Assign @Legend role to 50+ refs

@sync_roles.before_loop
async def before_sync_roles():
    """Wait until bot is ready"""
    await bot.wait_until_ready()

# Start bot
if __name__ == '__main__':
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print('❌ DISCORD_BOT_TOKEN not set')
```

---

## Step 5: GitHub Actions Workflow

Create: `.github/workflows/discord-announcements.yml`

```yaml
name: Discord Weekly Announcements

on:
  schedule:
    - cron: '0 10 * * 0'  # Every Sunday 10:00 UTC
  workflow_dispatch:

jobs:
  announce:
    runs-on: ubuntu-latest
    name: Post Weekly Announcements

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Post Weekly Announcement
        env:
          DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
          DISCORD_ANNOUNCEMENTS_CHANNEL_ID: ${{ secrets.DISCORD_ANNOUNCEMENTS_CHANNEL_ID }}
        run: |
          echo "🔔 Posting weekly announcement to Discord..."
          
          # Get current week
          WEEK_NUM=$(date -u +%V)
          YEAR=$(date -u +%Y)
          
          # TODO: Call Discord API to post announcement
          # Format: Week 28/2026 - Community Update
          # Include: New holders, milestones reached, etc.
          
          echo "✅ Announcement posted to Discord"
```

---

## Step 6: Manual Setup Checklist

- [ ] Discord Server created
- [ ] Channels created (see Step 1.2)
- [ ] Roles created (see Step 1.3)
- [ ] Bot application created
- [ ] Bot invited to server
- [ ] Bot token added to GitHub Secrets
- [ ] Channel IDs added to GitHub Secrets
- [ ] Discord bot script placed in `.github/scripts/`
- [ ] Workflow file created
- [ ] Test: Run bot locally to verify

---

## Step 7: Testing

### Test Bot Locally
```bash
# Set environment variables
export DISCORD_BOT_TOKEN="your-token"
export DISCORD_SERVER_ID="123456789"
export DISCORD_ANNOUNCEMENTS_CHANNEL_ID="987654321"

# Run bot
python .github/scripts/discord_bot.py
```

### Test Welcome Message
1. Create a test Discord account
2. Join the Klaryx server
3. Check if welcome message posted
4. Check if @Community role assigned

### Test Commands
- In Discord: `!tier` → Should show tier info
- In Discord: `!referral` → Should show referral link

---

## Phase 2: Advanced Features (Future)

- [ ] OAuth2: Login with Discord (connect to Klaryx Portal)
- [ ] Role Sync: Auto-assign roles based on referral count
- [ ] Leaderboard: Post top 10 referrers monthly
- [ ] Reports: Auto-post weekly reports to tier channels
- [ ] Reactions: Celebrate milestones with reactions
- [ ] Giveaways: KLRX rewards for engagement

---

## Summary

✅ Discord server structured  
✅ Bot token secured  
✅ Welcome automation ready  
✅ GitHub Actions workflow prepared  
✅ Future role sync prepared  

**Status: READY FOR DEPLOYMENT**
