#!/usr/bin/env python3
"""
KLARYX Weekly Report Generator
Holt Daten von CoinGecko, generiert 3 HTML-Reports (Free/Einblick/Tiefe)
Speichert in Supabase reports Tabelle via REST API
"""

import requests
import json
from datetime import datetime, timedelta
import os

# Supabase Credentials (aus Umgebungsvariablen)
SUPABASE_URL = os.environ.get('VITE_SUPABASE_URL', 'https://wpxcgducfkbozecknfdw.supabase.co')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_SERVICE_KEY:
    raise ValueError('SUPABASE_SERVICE_ROLE_KEY Environment Variable not set!')

# CoinGecko API (kostenlos, kein Key)
COINGECKO_API = 'https://api.coingecko.com/api/v3'

def get_week_info():
    """Aktuelle Woche und Jahr berechnen"""
    today = datetime.now()
    week_num = today.isocalendar()[1]
    year = today.isocalendar()[0]
    return week_num, year

def get_top_cryptocurrencies():
    """Hole Top 10 Kryptowährungen von CoinGecko"""
    try:
        url = f'{COINGECKO_API}/coins/markets'
        params = {
            'vs_currency': 'eur',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '7d'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f'Error fetching cryptocurrencies: {e}')
        return []

def get_solana_tokens():
    """Hole Top 10 Solana Tokens"""
    try:
        url = f'{COINGECKO_API}/coins/markets'
        params = {
            'vs_currency': 'eur',
            'category': 'solana-ecosystem',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '7d'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f'Error fetching Solana tokens: {e}')
        return []

def generate_disclaimer():
    """Standard Disclaimer für alle Reports"""
    return """
    <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 20px 0; font-size: 12px;">
        <strong>⚠️ DISCLAIMER:</strong> Dies ist ein reiner Daten-Aggregator. KEINE Finanzberatung.
        Informationszwecke only. Du bist allein verantwortlich für deine Entscheidungen.
    </div>
    """

def generate_free_tier_report(crypto_data, solana_data):
    """Generiere Report für Free Tier (nur Info)"""
    html = f"""
    <h2>📊 Solana Ecosystem Overview</h2>
    <p>Diese Woche werden {len(solana_data)} Top Solana Tokens verfolgt.</p>
    {generate_disclaimer()}
    <p><em>Premium-Features (Einblick/Tiefe) werden zu einem späteren Zeitpunkt freigeschaltet.</em></p>
    """
    return html

def generate_einblick_report(crypto_data, solana_data):
    """Generiere Report für Einblick Tier (Top 10 + Daten)"""
    html = "<h2>📊 Top 10 Solana Tokens (Einblick)</h2><table border='1' cellpadding='10'>"
    html += "<tr><th>Token</th><th>Price (EUR)</th><th>7d Change</th><th>Volume</th></tr>"

    for token in solana_data[:10]:
        symbol = token.get('symbol', 'N/A').upper()
        price = token.get('current_price', 0)
        change = token.get('price_change_percentage_7d_in_currency', 0)
        volume = token.get('total_volume', 0)
        html += f"<tr><td>{symbol}</td><td>€{price:.2f}</td><td>{change:.2f}%</td><td>€{volume:,.0f}</td></tr>"

    html += "</table>"
    html += generate_disclaimer()
    return html

def generate_tiefe_report(crypto_data, solana_data):
    """Generiere Report für Tiefe Tier (Raw JSON + Analysis)"""
    html = "<h2>📊 Tiefe Analysis (Raw JSON Data)</h2>"
    html += f"<pre>{json.dumps(solana_data[:10], indent=2)}</pre>"
    html += generate_disclaimer()
    return html

def save_reports_to_supabase(week_num, year, free_html, einblick_html, tiefe_html):
    """Speichere Reports via Supabase REST API"""
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
            "title": f"Free Tier Report - Week {week_num}",
            "content_html": free_html,
            "content_json": json.dumps({}),
            "generated_at": datetime.now().isoformat()
        },
        {
            "week_number": week_num,
            "year": year,
            "tier": "einblick",
            "title": f"Einblick Tier Report - Week {week_num}",
            "content_html": einblick_html,
            "content_json": json.dumps({}),
            "generated_at": datetime.now().isoformat()
        },
        {
            "week_number": week_num,
            "year": year,
            "tier": "tiefe",
            "title": f"Tiefe Tier Report - Week {week_num}",
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

print("🚀 KLARYX Weekly Report Generator")
print("=" * 50)

# Hole Daten
print("📊 Hole CoinGecko Daten...")
crypto_data = get_top_cryptocurrencies()
print(f"✅ {len(crypto_data)} Kryptowährungen geladen")

solana_data = get_solana_tokens()
print(f"✅ {len(solana_data)} Solana Tokens geladen")

# Generiere Reports
print("📝 Generiere Reports...")
week_num, year = get_week_info()

free_report = generate_free_tier_report(crypto_data, solana_data)
einblick_report = generate_einblick_report(crypto_data, solana_data)
tiefe_report = generate_tiefe_report(crypto_data, solana_data)

# Speichere in Supabase
print("💾 Speichere in Supabase...")
save_reports_to_supabase(week_num, year, free_report, einblick_report, tiefe_report)

print("✅ Report generation complete")
