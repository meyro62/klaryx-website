#!/usr/bin/env python3
"""
KLARYX Weekly Report Generator (NEW - Community Intelligence Edition)
Generates 3 HTML-Reports with Klaryx Community Data instead of CoinGecko copy
- Free Tier: Weekly Snapshot (new wallets, top referrers, badges, growth)
- Einblick Tier: Community Intelligence (referral growth, holder distribution, activity)
- Tiefe Tier: Network Analysis (raw data, whale movements, trends)
Stores in Supabase reports table via REST API
"""

import requests
import json
from datetime import datetime, timedelta
import os

# Supabase Credentials
SUPABASE_URL = os.environ.get('VITE_SUPABASE_URL', 'https://wpxcgducfkbozecknfdw.supabase.co')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_SERVICE_KEY:
    raise ValueError('SUPABASE_SERVICE_ROLE_KEY Environment Variable not set!')

def get_week_info():
    """Get current week and year"""
    today = datetime.now()
    week_num = today.isocalendar()[1]
    year = today.isocalendar()[0]
    return week_num, year

def get_klaryx_community_metrics():
    """Fetch Klaryx community data from Supabase"""
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }

        # Get all wallets
        wallets_url = f"{SUPABASE_URL}/rest/v1/wallets?select=wallet_address,registered_at,badge,tier,einladungen"
        wallets_response = requests.get(wallets_url, headers=headers, timeout=10)
        wallets_response.raise_for_status()
        wallets = wallets_response.json() if wallets_response.status_code == 200 else []

        # Get all referrals
        referrals_url = f"{SUPABASE_URL}/rest/v1/wallets?select=referrer_wallet"
        referrals_response = requests.get(referrals_url, headers=headers, timeout=10)
        referrals_response.raise_for_status()
        referrals = referrals_response.json() if referrals_response.status_code == 200 else []

        # Calculate metrics
        total_wallets = len(wallets)

        # This week's new wallets
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        new_this_week = sum(1 for w in wallets if w.get('registered_at') and
                           datetime.fromisoformat(w['registered_at']).date() >= week_start.date())

        # Top referrers (by einladungen count)
        top_referrers = sorted(wallets, key=lambda x: x.get('einladungen', 0), reverse=True)[:10]

        # Badge distribution
        badge_counts = {}
        for w in wallets:
            badge = w.get('badge', 'Unknown')
            badge_counts[badge] = badge_counts.get(badge, 0) + 1

        # Tier distribution
        tier_counts = {}
        for w in wallets:
            tier = w.get('tier', 'Free')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        return {
            'total_wallets': total_wallets,
            'new_this_week': new_this_week,
            'top_referrers': top_referrers,
            'badge_distribution': badge_counts,
            'tier_distribution': tier_counts,
            'total_referrals': len(referrals),
        }
    except Exception as e:
        print(f'Error fetching community metrics: {e}')
        return {
            'total_wallets': 0,
            'new_this_week': 0,
            'top_referrers': [],
            'badge_distribution': {},
            'tier_distribution': {},
            'total_referrals': 0,
        }

def generate_disclaimer():
    """Standard disclaimer for all reports"""
    return """
    <div style="background: rgba(34,211,160,0.05); border: 1px solid rgba(34,211,160,0.2); padding: 15px; border-radius: 8px; margin: 20px 0; font-size: 12px; color: #dde0eb;">
        <strong>⚠️ WICHTIG - DISCLAIMER:</strong><br>
        Diese Daten sind reine Informationen über die Klaryx Community. KEINE Finanzberatung.<br>
        Wir machen KEINE Vorhersagen oder Kaufempfehlungen. Du bist allein verantwortlich für deine Entscheidungen.<br>
        Alle Angaben ohne Gewähr.
    </div>
    """

def generate_free_tier_report(metrics):
    """Generate Free Tier Report: Weekly Snapshot"""
    new_wallets = metrics['new_this_week']
    total = metrics['total_wallets']
    growth_pct = ((new_wallets / total) * 100) if total > 0 else 0

    html = f"""
    <h2>📊 Klaryx Weekly Snapshot</h2>

    <div style="background: rgba(91,127,255,0.05); border: 1px solid rgba(91,127,255,0.2); padding: 20px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #5b7fff; margin-top: 0;">Diese Woche's Highlights</h3>
        <ul style="color: #dde0eb; line-height: 2;">
            <li>🆕 <strong>{new_wallets} neue Wallets</strong> registriert ({growth_pct:.1f}% Wachstum)</li>
            <li>👥 <strong>{total} Holder</strong> insgesamt in der Klaryx Community</li>
            <li>🏆 Siehe Top Referrer in der Hall of Fame</li>
            <li>📈 Community wächst organisch durch Referrals</li>
        </ul>
    </div>

    <p style="color: #4e5870; font-size: 13px;">
        Klaryx ist ein Community-Projekt. Diese Daten zeigen wie aktiv unsere Community ist.
        Je aktiver die Community, desto wertvoller wird das Projekt.
    </p>

    {generate_disclaimer()}
    """
    return html

def generate_einblick_tier_report(metrics):
    """Generate Einblick Tier Report: Community Intelligence"""
    html = f"""
    <h2>🧠 Klaryx Community Intelligence (Einblick)</h2>

    <div style="background: rgba(91,127,255,0.05); border: 1px solid rgba(91,127,255,0.2); padding: 20px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #5b7fff; margin-top: 0;">📈 Growth Metrics</h3>
        <ul style="color: #dde0eb; line-height: 2; font-size: 14px;">
            <li>Total Holder: <strong>{metrics['total_wallets']}</strong></li>
            <li>New This Week: <strong>{metrics['new_this_week']}</strong></li>
            <li>Total Referrals: <strong>{metrics['total_referrals']}</strong></li>
        </ul>
    </div>

    <div style="background: rgba(162,155,254,0.05); border: 1px solid rgba(162,155,254,0.2); padding: 20px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #a78bfa; margin-top: 0;">🎖️ Badge Distribution</h3>
        <ul style="color: #dde0eb; line-height: 2; font-size: 13px;">
    """

    for badge, count in sorted(metrics['badge_distribution'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / metrics['total_wallets'] * 100) if metrics['total_wallets'] > 0 else 0
        html += f"            <li>{badge}: <strong>{count}</strong> ({pct:.1f}%)</li>\n"

    html += f"""
        </ul>
    </div>

    <div style="background: rgba(34,211,160,0.05); border: 1px solid rgba(34,211,160,0.2); padding: 20px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #22d3a0; margin-top: 0;">🏅 Tier Distribution</h3>
        <ul style="color: #dde0eb; line-height: 2; font-size: 13px;">
    """

    for tier, count in sorted(metrics['tier_distribution'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / metrics['total_wallets'] * 100) if metrics['total_wallets'] > 0 else 0
        html += f"            <li>{tier}: <strong>{count}</strong> ({pct:.1f}%)</li>\n"

    html += f"""
        </ul>
    </div>

    <p style="color: #4e5870; font-size: 13px; margin-top: 20px;">
        <strong>Was bedeutet das?</strong> Diese Daten zeigen wie sich Klaryx entwickelt.
        Mehr Holder = mehr Community = mehr Wert für das Projekt.
        Diese exklusiven Daten siehst nur DU als Einblick-Tier Member.
    </p>

    {generate_disclaimer()}
    """
    return html

def generate_tiefe_tier_report(metrics):
    """Generate Tiefe Tier Report: Network Analysis"""
    html = f"""
    <h2>🔬 Klaryx Network Analysis (Tiefe)</h2>

    <div style="background: rgba(245,197,66,0.05); border: 1px solid rgba(245,197,66,0.2); padding: 20px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #f5c542; margin-top: 0;">📊 Full Network Data</h3>

        <h4 style="color: #dde0eb; font-size: 14px; margin-top: 15px;">Absolute Metriken:</h4>
        <pre style="background: #141926; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; color: #dde0eb;">
Total Wallets:        {metrics['total_wallets']}
New This Week:        {metrics['new_this_week']}
Total Referrals:      {metrics['total_referrals']}
Avg Refs per Wallet:  {(metrics['total_referrals'] / max(metrics['total_wallets'], 1)):.2f}
        </pre>

        <h4 style="color: #dde0eb; font-size: 14px; margin-top: 15px;">Badge Distribution (Raw):</h4>
        <pre style="background: #141926; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; color: #dde0eb;">
{json.dumps(metrics['badge_distribution'], indent=2)}
        </pre>

        <h4 style="color: #dde0eb; font-size: 14px; margin-top: 15px;">Tier Distribution (Raw):</h4>
        <pre style="background: #141926; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; color: #dde0eb;">
{json.dumps(metrics['tier_distribution'], indent=2)}
        </pre>
    </div>

    <div style="background: rgba(162,155,254,0.05); border: 1px solid rgba(162,155,254,0.2); padding: 20px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #a78bfa; margin-top: 0;">📈 Trend Analysis</h3>
        <p style="color: #dde0eb; font-size: 13px;">
            <strong>Was bedeuten diese Daten?</strong><br>
            - Holder Growth: Wie schnell wächst die Community<br>
            - Referral Ratio: Wie aktiv sind User (mehr Refs = aktiver)<br>
            - Badge Progression: Wie viele User bleiben aktiv
        </p>
        <p style="color: #4e5870; font-size: 12px;">
            Historisch: Projekte mit steigendem Holder Growth und hohem Referral Ratio
            zeigen starkes organisches Wachstum.
        </p>
    </div>

    {generate_disclaimer()}
    """
    return html

def save_reports_to_supabase(week_num, year, free_html, einblick_html, tiefe_html):
    """Save reports to Supabase via REST API"""
    url = f"{SUPABASE_URL}/rest/v1/reports"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    reports = [
        {
            "week_number": week_num,
            "year": year,
            "tier": "free",
            "title": f"Klaryx Weekly Snapshot - Week {week_num}",
            "content_html": free_html,
            "content_json": json.dumps({}),
            "generated_at": datetime.now().isoformat()
        },
        {
            "week_number": week_num,
            "year": year,
            "tier": "einblick",
            "title": f"Klaryx Community Intelligence - Week {week_num}",
            "content_html": einblick_html,
            "content_json": json.dumps({}),
            "generated_at": datetime.now().isoformat()
        },
        {
            "week_number": week_num,
            "year": year,
            "tier": "tiefe",
            "title": f"Klaryx Network Analysis - Week {week_num}",
            "content_html": tiefe_html,
            "content_json": json.dumps({}),
            "generated_at": datetime.now().isoformat()
        }
    ]

    for report in reports:
        try:
            response = requests.post(
                url,
                headers=headers,
                json=report,
                timeout=10
            )
            response.raise_for_status()
            print(f"✅ {report['tier'].upper()} report saved")
        except Exception as e:
            print(f"❌ Error saving {report['tier']} report: {e}")

print("🚀 KLARYX Weekly Report Generator (Community Intelligence Edition)")
print("=" * 60)

# Get week info
week_num, year = get_week_info()
print(f"📅 Generating reports for week {week_num}/{year}")

# Fetch community metrics
print("📊 Fetching Klaryx community metrics...")
metrics = get_klaryx_community_metrics()
print(f"✅ Loaded {metrics['total_wallets']} wallets, {metrics['total_referrals']} referrals")

# Generate reports
print("📝 Generating reports...")
free_report = generate_free_tier_report(metrics)
einblick_report = generate_einblick_tier_report(metrics)
tiefe_report = generate_tiefe_tier_report(metrics)

# Save to Supabase
print("💾 Saving reports to Supabase...")
save_reports_to_supabase(week_num, year, free_report, einblick_report, tiefe_report)

print("✅ Report generation complete!")
