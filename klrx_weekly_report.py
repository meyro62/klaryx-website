#!/usr/bin/env python3
"""
KLARYX Weekly Report Generator – Werttreppe (Free / Einblick / Tiefe)
Erzeugt 3 kumulative HTML-Reports und speichert sie in Supabase (Tabelle reports).
- Free    : Marktueberblick (BTC/ETH/SOL) + Community-Snapshot
- Einblick: alles aus Free + Top-Solana-Token nach Volumen + Community-Intelligence
- Tiefe   : alles aus Einblick + Rohdaten (JSON) zum Selber-Analysieren
Datenquellen: CoinGecko (kostenlos, kein Key) + Klaryx-Supabase.
Rein BESCHREIBEND - keine Empfehlungen, keine Prognosen. Disclaimer in jedem Report.
"""
import requests
import json
from datetime import datetime, timedelta
import os

SUPABASE_URL = os.environ.get('VITE_SUPABASE_URL', 'https://wpxcgducfkbozecknfdw.supabase.co')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_SERVICE_KEY:
    raise ValueError('SUPABASE_SERVICE_ROLE_KEY Environment Variable not set!')

CG = "https://api.coingecko.com/api/v3"


def get_week_info():
    today = datetime.now()
    return today.isocalendar()[1], today.isocalendar()[0]


def get_klaryx_community_metrics():
    try:
        headers = {"apikey": SUPABASE_SERVICE_KEY,
                   "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                   "Content-Type": "application/json"}
        url = f"{SUPABASE_URL}/rest/v1/wallets?select=wallet_address,registered_at,badge,tier,einladungen"
        wallets = requests.get(url, headers=headers, timeout=10).json()
        total = len(wallets)
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        new_this_week = sum(1 for w in wallets if w.get('registered_at') and
                            datetime.fromisoformat(w['registered_at']).date() >= week_start.date())
        top_referrers = sorted(wallets, key=lambda x: x.get('einladungen', 0) or 0, reverse=True)[:10]
        badge_counts, tier_counts = {}, {}
        for w in wallets:
            badge_counts[w.get('badge', 'Free')] = badge_counts.get(w.get('badge', 'Free'), 0) + 1
            tier_counts[w.get('tier', 'Free')] = tier_counts.get(w.get('tier', 'Free'), 0) + 1
        total_referrals = sum((w.get('einladungen', 0) or 0) for w in wallets)
        return {'total_wallets': total, 'new_this_week': new_this_week,
                'top_referrers': top_referrers, 'badge_distribution': badge_counts,
                'tier_distribution': tier_counts, 'total_referrals': total_referrals}
    except Exception as e:
        print(f'WARN Community-Daten Fehler: {e}')
        return {'total_wallets': 0, 'new_this_week': 0, 'top_referrers': [],
                'badge_distribution': {}, 'tier_distribution': {}, 'total_referrals': 0}


def fetch_market_data():
    out = {'majors': [], 'solana_top': [], 'error': None}
    try:
        r = requests.get(f"{CG}/coins/markets", params={
            "vs_currency": "usd", "ids": "bitcoin,ethereum,solana",
            "price_change_percentage": "24h,7d"}, timeout=15)
        r.raise_for_status()
        for c in r.json():
            out['majors'].append({'name': c.get('name'), 'symbol': (c.get('symbol') or '').upper(),
                                  'price': c.get('current_price'),
                                  'ch24h': c.get('price_change_percentage_24h_in_currency'),
                                  'ch7d': c.get('price_change_percentage_7d_in_currency')})
    except Exception as e:
        out['error'] = str(e)
        print(f'WARN Majors Fehler: {e}')
    try:
        r = requests.get(f"{CG}/coins/markets", params={
            "vs_currency": "usd", "category": "solana-ecosystem", "order": "volume_desc",
            "per_page": 15, "page": 1, "price_change_percentage": "7d"}, timeout=15)
        r.raise_for_status()
        for c in r.json():
            out['solana_top'].append({'name': c.get('name'), 'symbol': (c.get('symbol') or '').upper(),
                                      'price': c.get('current_price'), 'volume': c.get('total_volume'),
                                      'ch7d': c.get('price_change_percentage_7d_in_currency')})
    except Exception as e:
        print(f'WARN Solana-Top Fehler: {e}')
    return out


def _pct(v):
    if v is None:
        return '<span style="color:#4e5870;">-</span>'
    return f'<span style="color:{"#22d3a0" if v >= 0 else "#ff6b6b"};">{v:+.1f}%</span>'


def _usd(v):
    if v is None:
        return '-'
    return f"${v:,.2f}" if v >= 1 else (f"${v:,.6f}".rstrip('0').rstrip('.'))


def _vol(v):
    if not v:
        return '-'
    for unit in ['', 'K', 'M', 'B']:
        if abs(v) < 1000:
            return f"${v:,.1f}{unit}"
        v /= 1000
    return f"${v:,.1f}T"


def generate_disclaimer():
    return """
    <div style="background: rgba(34,211,160,0.05); border: 1px solid rgba(34,211,160,0.2); padding: 15px; border-radius: 8px; margin: 20px 0; font-size: 12px; color: #dde0eb;">
        <strong>Disclaimer:</strong> Alle Angaben sind oeffentlich zugaengliche Marktdaten und Community-Statistiken,
        rein zu Informationszwecken. KEINE Anlageberatung, KEINE Kauf-/Verkaufsempfehlung, KEINE Prognose.
        Klaryx ist kein Finanzdienstleister. Handeln auf eigene Verantwortung. Alle Angaben ohne Gewaehr.
    </div>
    """


def block_market(market):
    if not market['majors']:
        return '<p style="color:#4e5870;font-size:13px;">Marktdaten aktuell nicht verfuegbar.</p>'
    rows = ""
    for c in market['majors']:
        rows += (f'<tr><td style="padding:8px;"><strong>{c["symbol"]}</strong> '
                 f'<span style="color:#4e5870;">{c["name"]}</span></td>'
                 f'<td style="padding:8px;text-align:right;">{_usd(c["price"])}</td>'
                 f'<td style="padding:8px;text-align:right;">{_pct(c["ch24h"])}</td>'
                 f'<td style="padding:8px;text-align:right;">{_pct(c["ch7d"])}</td></tr>')
    return f"""
    <div style="background: rgba(91,127,255,0.05); border:1px solid rgba(91,127,255,0.2); padding:20px; border-radius:8px; margin:15px 0;">
      <h3 style="color:#5b7fff; margin-top:0;">Marktueberblick</h3>
      <table style="width:100%; border-collapse:collapse; font-size:13px; color:#dde0eb;">
        <tr style="color:#4e5870; font-size:11px; text-transform:uppercase;">
          <td style="padding:8px;">Coin</td><td style="padding:8px;text-align:right;">Preis</td>
          <td style="padding:8px;text-align:right;">24h</td><td style="padding:8px;text-align:right;">7 Tage</td></tr>
        {rows}
      </table>
    </div>"""


def block_community(metrics):
    total = metrics['total_wallets']
    new = metrics['new_this_week']
    growth = (new / total * 100) if total > 0 else 0
    return f"""
    <div style="background: rgba(34,211,160,0.05); border:1px solid rgba(34,211,160,0.2); padding:20px; border-radius:8px; margin:15px 0;">
      <h3 style="color:#22d3a0; margin-top:0;">Klaryx Community</h3>
      <ul style="color:#dde0eb; line-height:2; font-size:14px; margin:0; padding-left:18px;">
        <li><strong>{total}</strong> Holder insgesamt</li>
        <li><strong>{new}</strong> neue Wallets diese Woche ({growth:.1f}% Wachstum)</li>
        <li><strong>{metrics['total_referrals']}</strong> Einladungen insgesamt</li>
      </ul>
    </div>"""


def block_solana(market):
    if not market['solana_top']:
        return '<p style="color:#4e5870;font-size:13px;">Solana-Token-Daten aktuell nicht verfuegbar.</p>'
    rows = ""
    for c in market['solana_top']:
        rows += (f'<tr><td style="padding:6px;"><strong>{c["symbol"]}</strong></td>'
                 f'<td style="padding:6px;text-align:right;">{_usd(c["price"])}</td>'
                 f'<td style="padding:6px;text-align:right;">{_vol(c["volume"])}</td>'
                 f'<td style="padding:6px;text-align:right;">{_pct(c["ch7d"])}</td></tr>')
    return f"""
    <div style="background: rgba(162,155,254,0.05); border:1px solid rgba(162,155,254,0.2); padding:20px; border-radius:8px; margin:15px 0;">
      <h3 style="color:#a78bfa; margin-top:0;">Top Solana-Token nach Volumen (7 Tage)</h3>
      <table style="width:100%; border-collapse:collapse; font-size:12px; color:#dde0eb;">
        <tr style="color:#4e5870; font-size:11px; text-transform:uppercase;">
          <td style="padding:6px;">Token</td><td style="padding:6px;text-align:right;">Preis</td>
          <td style="padding:6px;text-align:right;">Volumen 24h</td><td style="padding:6px;text-align:right;">7 Tage</td></tr>
        {rows}
      </table>
    </div>"""


def block_intel(metrics):
    badge_rows = ""
    for badge, count in sorted(metrics['badge_distribution'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / metrics['total_wallets'] * 100) if metrics['total_wallets'] > 0 else 0
        badge_rows += f'<li>{badge}: <strong>{count}</strong> ({pct:.1f}%)</li>'
    ref_rows = ""
    for w in [x for x in metrics['top_referrers'] if (x.get('einladungen', 0) or 0) > 0][:5]:
        addr = w.get('wallet_address', '')
        short = (addr[:4] + '..' + addr[-4:]) if len(addr) > 8 else addr
        ref_rows += f'<li><span style="font-family:monospace;">{short}</span>: <strong>{w.get("einladungen",0)}</strong> Einladungen</li>'
    if not ref_rows:
        ref_rows = '<li style="color:#4e5870;">Noch keine aktiven Einlader.</li>'
    return f"""
    <div style="background: rgba(245,197,66,0.05); border:1px solid rgba(245,197,66,0.2); padding:20px; border-radius:8px; margin:15px 0;">
      <h3 style="color:#f5c542; margin-top:0;">Community-Intelligence</h3>
      <p style="color:#dde0eb; font-size:13px; margin:0 0 6px;"><strong>Badge-Verteilung:</strong></p>
      <ul style="color:#dde0eb; line-height:1.8; font-size:13px; margin:0 0 12px; padding-left:18px;">{badge_rows}</ul>
      <p style="color:#dde0eb; font-size:13px; margin:0 0 6px;"><strong>Aktivste Einlader:</strong></p>
      <ul style="color:#dde0eb; line-height:1.8; font-size:13px; margin:0; padding-left:18px;">{ref_rows}</ul>
    </div>"""


def block_raw(metrics, market):
    raw = {'community': {k: metrics[k] for k in ('total_wallets', 'new_this_week', 'total_referrals',
                                                 'badge_distribution', 'tier_distribution')},
           'market_majors': market['majors'], 'solana_top': market['solana_top'],
           'generated_at': datetime.now().isoformat()}
    dump = json.dumps(raw, indent=2, ensure_ascii=False)
    return f"""
    <div style="background: rgba(255,255,255,0.02); border:1px solid #1a2236; padding:20px; border-radius:8px; margin:15px 0;">
      <h3 style="color:#dde0eb; margin-top:0;">Rohdaten (zum Selber-Analysieren)</h3>
      <pre style="background:#141926; padding:15px; border-radius:6px; overflow-x:auto; font-size:11px; color:#dde0eb; white-space:pre-wrap;">{dump}</pre>
    </div>"""


def generate_free_tier_report(metrics, market):
    return f"""
    <h2>Klaryx Weekly Snapshot (Free)</h2>
    {block_market(market)}
    {block_community(metrics)}
    {generate_disclaimer()}
    """


def generate_einblick_tier_report(metrics, market):
    return f"""
    <h2>Klaryx Community Intelligence (Einblick)</h2>
    {block_market(market)}
    {block_community(metrics)}
    {block_solana(market)}
    {block_intel(metrics)}
    {generate_disclaimer()}
    """


def generate_tiefe_tier_report(metrics, market):
    return f"""
    <h2>Klaryx Network Analysis (Tiefe)</h2>
    {block_market(market)}
    {block_community(metrics)}
    {block_solana(market)}
    {block_intel(metrics)}
    {block_raw(metrics, market)}
    {generate_disclaimer()}
    """


def save_reports_to_supabase(week_num, year, free_html, einblick_html, tiefe_html):
    url = f"{SUPABASE_URL}/rest/v1/reports"
    headers = {"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
               "Content-Type": "application/json"}
    reports = [
        {"week_number": week_num, "year": year, "tier": "free",
         "title": f"Klaryx Weekly Snapshot - KW {week_num}", "content_html": free_html,
         "content_json": json.dumps({}), "generated_at": datetime.now().isoformat()},
        {"week_number": week_num, "year": year, "tier": "einblick",
         "title": f"Klaryx Community Intelligence - KW {week_num}", "content_html": einblick_html,
         "content_json": json.dumps({}), "generated_at": datetime.now().isoformat()},
        {"week_number": week_num, "year": year, "tier": "tiefe",
         "title": f"Klaryx Network Analysis - KW {week_num}", "content_html": tiefe_html,
         "content_json": json.dumps({}), "generated_at": datetime.now().isoformat()},
    ]
    for report in reports:
        try:
            resp = requests.post(url, headers=headers, json=report, timeout=10)
            resp.raise_for_status()
            print(f"OK {report['tier'].upper()} report gespeichert")
        except Exception as e:
            print(f"FEHLER beim Speichern {report['tier']}: {e}")


def run():
    print("KLARYX Weekly Report Generator (Werttreppe)")
    week_num, year = get_week_info()
    print(f"Reports fuer KW {week_num}/{year}")
    metrics = get_klaryx_community_metrics()
    print(f"{metrics['total_wallets']} Wallets, {metrics['total_referrals']} Einladungen")
    market = fetch_market_data()
    print(f"{len(market['majors'])} Majors, {len(market['solana_top'])} Solana-Token")
    free_report = generate_free_tier_report(metrics, market)
    einblick_report = generate_einblick_tier_report(metrics, market)
    tiefe_report = generate_tiefe_tier_report(metrics, market)
    save_reports_to_supabase(week_num, year, free_report, einblick_report, tiefe_report)
    print("Fertig!")


if __name__ == "__main__":
    run()
