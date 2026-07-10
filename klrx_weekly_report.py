#!/usr/bin/env python3
"""
KLARYX Weekly Report Generator
Holt Daten von CoinGecko, generiert 3 HTML-Reports (Free/Einblick/Tiefe)
Speichert in Supabase reports Tabelle
"""

import requests
import json
from datetime import datetime, timedelta
from supabase import create_client
import os

# Supabase Credentials (aus Umgebungsvariablen)
SUPABASE_URL = os.environ.get('VITE_SUPABASE_URL', 'https://wpxcgducfkbozecknfdw.supabase.co')
# SECURITY: Service Role Key muss in Environment Variablen gespeichert sein!
# NIEMALS hardcoded in Python/YAML Dateien!
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_SERVICE_KEY:
    raise ValueError('SUPABASE_SERVICE_ROLE_KEY Environment Variable not set!')

# CoinGecko API (kostenlos, kein Key)
COINGECKO_API = 'https://api.coingecko.com/api/v3'

# Supabase Client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

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
    """Disclaimer für alle Reports"""
    return '''
    <div style="background: rgba(245, 90, 90, 0.05); border: 1px solid rgba(245, 90, 90, 0.2); padding: 16px; border-radius: 8px; margin-top: 20px; font-size: 12px; color: #e88a8a;">
        <strong>⚠️ KLARYX – INFORMATIONSZWECKE ONLY</strong><br>
        Diese Daten sind öffentlich zugängliche Marktinformationen.<br>
        <strong>NICHT:</strong> Finanzberatung, Anlageempfehlung, Handelssignal<br>
        <strong>NUR:</strong> Öffentliche Daten zu Informationszwecken<br>
        Klaryx ist kein lizenzierter Finanzdienstleister. Nutzer sind allein verantwortlich für ihre Handlungen.
    </div>
    '''

def generate_free_report(top_cryptos):
    """Generiere FREE TIER Report (Top 3 + Top 10 Marktcap)"""
    html = '''
    <div class="report-container">
        <h3 style="color: #5b7fff; margin-bottom: 16px;">📊 Marktübersicht – Woche {}</h3>

        <div style="background: #0f1420; border: 1px solid #1a2236; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
            <h4 style="color: #a78bfa; margin-bottom: 12px;">🏆 Top 3 Assets</h4>
            <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #1a2236;">
                    <th style="text-align: left; padding: 8px; color: #4e5870;">Asset</th>
                    <th style="text-align: right; padding: 8px; color: #4e5870;">Preis (EUR)</th>
                    <th style="text-align: right; padding: 8px; color: #4e5870;">7-Tage Änderung</th>
                </tr>
    '''

    for i, crypto in enumerate(top_cryptos[:3]):
        name = crypto.get('name', 'Unknown')
        symbol = crypto.get('symbol', '').upper()
        price = crypto.get('current_price', 0)
        change_7d = crypto.get('price_change_percentage_7d_in_currency', 0) or 0
        change_color = '#22d3a0' if change_7d >= 0 else '#f55a5a'

        html += f'''
                <tr style="border-bottom: 1px solid #1a2236;">
                    <td style="padding: 8px; color: #dde0eb;">{name} ({symbol})</td>
                    <td style="text-align: right; padding: 8px; color: #dde0eb;">€{price:,.2f}</td>
                    <td style="text-align: right; padding: 8px; color: {change_color};">{change_7d:+.2f}%</td>
                </tr>
        '''

    html += '''
            </table>
        </div>

        <div style="background: #0f1420; border: 1px solid #1a2236; padding: 16px; border-radius: 8px;">
            <h4 style="color: #a78bfa; margin-bottom: 12px;">📈 Top 10 nach Marktcap</h4>
            <ul style="list-style: none; padding: 0; font-size: 13px;">
    '''

    for crypto in top_cryptos[:10]:
        name = crypto.get('name', 'Unknown')
        symbol = crypto.get('symbol', '').upper()
        market_cap = crypto.get('market_cap', 0)
        if market_cap:
            html += f'<li style="padding: 6px 0; color: #dde0eb;">• {name} ({symbol}) – Marktcap: €{market_cap:,.0f}</li>'

    html += '''
            </ul>
        </div>
    '''

    html += generate_disclaimer()
    html += '</div>'

    week_num, year = get_week_info()
    return html.format(f'KW {week_num} / {year}')

def generate_einblick_report(top_cryptos, solana_tokens):
    """Generiere EINBLICK TIER Report (Top 10 + Solana Tokens + Volumen)"""
    html = '''
    <div class="report-container">
        <h3 style="color: #5b7fff; margin-bottom: 16px;">📊 Marktübersicht – Woche {} (Einblick)</h3>

        <div style="background: #0f1420; border: 1px solid #1a2236; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
            <h4 style="color: #a78bfa; margin-bottom: 12px;">🏆 Top 10 Kryptowährungen</h4>
            <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #1a2236;">
                    <th style="text-align: left; padding: 8px; color: #4e5870;">Rank</th>
                    <th style="text-align: left; padding: 8px; color: #4e5870;">Name</th>
                    <th style="text-align: right; padding: 8px; color: #4e5870;">Preis</th>
                    <th style="text-align: right; padding: 8px; color: #4e5870;">Volumen (24h)</th>
                    <th style="text-align: right; padding: 8px; color: #4e5870;">7-Tage</th>
                </tr>
    '''

    for i, crypto in enumerate(top_cryptos[:10], 1):
        name = crypto.get('name', 'Unknown')
        symbol = crypto.get('symbol', '').upper()
        price = crypto.get('current_price', 0)
        volume = crypto.get('total_volume', 0)
        change_7d = crypto.get('price_change_percentage_7d_in_currency', 0) or 0
        change_color = '#22d3a0' if change_7d >= 0 else '#f55a5a'

        html += f'''
                <tr style="border-bottom: 1px solid #1a2236;">
                    <td style="padding: 8px; color: #dde0eb;">#{i}</td>
                    <td style="padding: 8px; color: #dde0eb;">{name} ({symbol})</td>
                    <td style="text-align: right; padding: 8px; color: #dde0eb;">€{price:,.2f}</td>
                    <td style="text-align: right; padding: 8px; color: #dde0eb;">€{volume:,.0f}</td>
                    <td style="text-align: right; padding: 8px; color: {change_color};">{change_7d:+.2f}%</td>
                </tr>
        '''

    html += '''
            </table>
        </div>

        <div style="background: #0f1420; border: 1px solid #1a2236; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
            <h4 style="color: #a78bfa; margin-bottom: 12px;">🌊 Top 10 Solana Tokens</h4>
            <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #1a2236;">
                    <th style="text-align: left; padding: 8px; color: #4e5870;">Token</th>
                    <th style="text-align: right; padding: 8px; color: #4e5870;">Preis</th>
                    <th style="text-align: right; padding: 8px; color: #4e5870;">Marktcap</th>
                </tr>
    '''

    for token in solana_tokens[:10]:
        name = token.get('name', 'Unknown')
        symbol = token.get('symbol', '').upper()
        price = token.get('current_price', 0)
        market_cap = token.get('market_cap', 0)

        html += f'''
                <tr style="border-bottom: 1px solid #1a2236;">
                    <td style="padding: 8px; color: #dde0eb;">{name} ({symbol})</td>
                    <td style="text-align: right; padding: 8px; color: #dde0eb;">€{price:,.4f}</td>
                    <td style="text-align: right; padding: 8px; color: #dde0eb;">€{market_cap:,.0f}</td>
                </tr>
        '''

    html += '''
            </table>
        </div>
    '''

    html += generate_disclaimer()
    html += '</div>'

    week_num, year = get_week_info()
    return html.format(f'KW {week_num} / {year}')

def generate_tiefe_report(top_cryptos, solana_tokens):
    """Generiere TIEFE TIER Report (alles + JSON Export)"""
    html = generate_einblick_report(top_cryptos, solana_tokens)

    json_data = {
        'timestamp': datetime.now().isoformat(),
        'top_cryptos': [
            {
                'rank': i+1,
                'name': c.get('name'),
                'symbol': c.get('symbol'),
                'price_eur': c.get('current_price'),
                'volume_24h': c.get('total_volume'),
                'market_cap': c.get('market_cap'),
                'change_7d': c.get('price_change_percentage_7d_in_currency')
            }
            for i, c in enumerate(top_cryptos[:10])
        ],
        'solana_tokens': [
            {
                'name': t.get('name'),
                'symbol': t.get('symbol'),
                'price_eur': t.get('current_price'),
                'market_cap': t.get('market_cap')
            }
            for t in solana_tokens[:10]
        ]
    }

    html += f'''
    <div style="background: #0f1420; border: 1px solid #1a2236; padding: 16px; border-radius: 8px; margin-top: 16px;">
        <h4 style="color: #a78bfa; margin-bottom: 12px;">📥 Raw JSON Data (für Analysen)</h4>
        <pre style="background: #080b12; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 11px; color: #4e5870;">
{json.dumps(json_data, indent=2)}
        </pre>
    </div>
    '''

    return html

def save_reports_to_supabase(free_html, einblick_html, tiefe_html, json_data):
    """Speichere alle 3 Reports in Supabase"""
    week_num, year = get_week_info()

    try:
        # Free Report - Use upsert to handle re-runs (update if already exists)
        supabase.table('reports').upsert({
            'week_number': week_num,
            'year': year,
            'tier': 'free',
            'title': f'Marktübersicht KW {week_num}/{year}',
            'content_html': free_html,
            'content_json': json_data,
            'disclaimer': 'Informationszwecke only'
        }).execute()
        print('✅ Free Report gespeichert')

        # Einblick Report - Use upsert to handle re-runs (update if already exists)
        supabase.table('reports').upsert({
            'week_number': week_num,
            'year': year,
            'tier': 'einblick',
            'title': f'Detaillierte Marktanalyse KW {week_num}/{year}',
            'content_html': einblick_html,
            'content_json': json_data,
            'disclaimer': 'Informationszwecke only'
        }).execute()
        print('✅ Einblick Report gespeichert')

        # Tiefe Report - Use upsert to handle re-runs (update if already exists)
        supabase.table('reports').upsert({
            'week_number': week_num,
            'year': year,
            'tier': 'tiefe',
            'title': f'Vollständige Analyse mit JSON Export KW {week_num}/{year}',
            'content_html': tiefe_html,
            'content_json': json_data,
            'disclaimer': 'Informationszwecke only'
        }).execute()
        print('✅ Tiefe Report gespeichert')

        return True
    except Exception as e:
        print(f'❌ Error saving reports: {e}')
        return False

def main():
    """Hauptfunktion: Hole Daten und generiere Reports"""
    print('🚀 KLARYX Weekly Report Generator')
    print('=' * 50)

    # Daten abrufen
    print('📊 Hole CoinGecko Daten...')
    top_cryptos = get_top_cryptocurrencies()
    solana_tokens = get_solana_tokens()

    if not top_cryptos or not solana_tokens:
        print('❌ Fehler beim Abrufen der Daten')
        return

    print(f'✅ {len(top_cryptos)} Kryptowährungen geladen')
    print(f'✅ {len(solana_tokens)} Solana Tokens geladen')

    # Reports generieren
    print('\n📝 Generiere Reports...')
    free_html = generate_free_report(top_cryptos)
    einblick_html = generate_einblick_report(top_cryptos, solana_tokens)
    tiefe_html = generate_tiefe_report(top_cryptos, solana_tokens)

    json_data = {
        'timestamp': datetime.now().isoformat(),
        'top_cryptos': [
            {
                'name': c.get('name'),
                'symbol': c.get('symbol'),
                'price_eur': c.get('current_price'),
                'market_cap': c.get('market_cap')
            }
            for c in top_cryptos[:10]
        ],
        'solana_tokens': [
            {
                'name': t.get('name'),
                'symbol': t.get('symbol'),
                'price_eur': t.get('current_price')
            }
            for t in solana_tokens[:10]
        ]
    }

    # In Supabase speichern
    print('💾 Speichere in Supabase...')
    if save_reports_to_supabase(free_html, einblick_html, tiefe_html, json_data):
        print('✅ Reports erfolgreich gespeichert!')
    else:
        print('❌ Fehler beim Speichern')

if __name__ == '__main__':
    main()
