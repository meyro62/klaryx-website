/* Klaryx – gemeinsamer Header + Footer (eine Quelle für alle Seiten).
   Einbinden: <div id="site-header"></div> ganz oben im <body>,
              <div id="site-footer"></div> unten, dann <script src="partials.js"></script>.
   Der aktive Menüpunkt wird automatisch anhand des Dateinamens hervorgehoben. */
(function () {
  var page = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  if (page === "" ) page = "index.html";

  // Direkt sichtbare Tools (die aktiven Werkzeuge) + gruppierte Bereiche (Dropdown / mobil eingerückt).
  var NAV_DIRECT = [
    ["check.html", "Klartext-Check"],
    ["link-check.html", "Link-Check"],
    ["bookmarklet.html", "Bookmarklet"]
  ];
  var NAV_GROUPS = [
    ["Daten",   [["warnliste.html", "Warnliste"], ["analyse.html", "Analyse"], ["markt.html", "Markt"], ["watchlist.html", "Wächter"]]],
    ["Lernen",  [["news.html", "News"], ["lernpfad.html", "Lernpfad"], ["ratgeber.html", "Ratgeber"], ["faq.html", "FAQ"]]],
    ["Projekt", [["ueber-klrx.html", "Über KLRX"], ["klaryx_milestones.html", "Meilensteine"], ["klaryx_halloffame.html", "Hall of Fame"], ["klaryx_wallet_setup.html", "Wallet Setup"]]]
  ];

  function isActive(href) { return href.toLowerCase() === page; }
  function grpActive(items) { return items.some(function (n) { return isActive(n[0]); }); }

  var muted = "color:var(--muted);text-decoration:none;";
  var active = "color:var(--text);text-decoration:none;";

  // ---- Desktop-Nav: Direkt-Links + Gruppen mit Hover-Dropdown ----
  var deskDirect = NAV_DIRECT.map(function (n) {
    return '<a href="' + n[0] + '" style="' + (isActive(n[0]) ? active : muted) + 'font-size:13px;">' + n[1] + '</a>';
  }).join("");
  var deskGroups = NAV_GROUPS.map(function (g) {
    var items = g[1].map(function (n) {
      return '<a href="' + n[0] + '" style="' + (isActive(n[0]) ? active : muted) + '">' + n[1] + '</a>';
    }).join("");
    return '<div class="khdr-grp"><span class="khdr-gl" style="' + (grpActive(g[1]) ? active : muted) + 'font-size:13px;">' + g[0] + ' <span style="font-size:8px;opacity:.7;">▼</span></span>'
      + '<div class="khdr-dd">' + items + '</div></div>';
  }).join("");

  // ---- Mobile-Nav: Direkt-Links, dann Bereiche mit Überschrift + eingerückten Links ----
  var mobDirect = NAV_DIRECT.map(function (n) {
    return '<a href="' + n[0] + '" style="' + (isActive(n[0]) ? active : muted) + 'padding:12px 24px;border-bottom:1px solid var(--border);font-size:14px;">' + n[1] + '</a>';
  }).join("");
  var mobGroups = NAV_GROUPS.map(function (g) {
    var head = '<div style="padding:14px 24px 4px;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);opacity:.55;">' + g[0] + '</div>';
    var items = g[1].map(function (n) {
      return '<a href="' + n[0] + '" style="' + (isActive(n[0]) ? active : muted) + 'padding:9px 24px 9px 36px;border-bottom:1px solid var(--border);font-size:14px;">' + n[1] + '</a>';
    }).join("");
    return head + items;
  }).join("");

  var headerHTML =
    '<header style="display:flex;align-items:center;justify-content:space-between;padding:14px 24px;border-bottom:1px solid var(--border);background:var(--bg);">' +
      '<a href="index.html" style="font-family:\'Space Mono\',monospace;font-size:16px;font-weight:700;text-decoration:none;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Klaryx</a>' +
      '<div class="khdr-d" style="display:flex;align-items:center;gap:20px;">' + deskDirect + deskGroups +
        '<a href="portal.html" style="background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-radius:8px;padding:8px 18px;font-size:13px;font-weight:600;text-decoration:none;">Portal →</a>' +
      '</div>' +
      '<button class="khdr-b" onclick="var m=document.getElementById(\'khdrM\');m.style.display=m.style.display===\'flex\'?\'none\':\'flex\';" style="display:none;background:none;border:none;color:var(--text);font-size:22px;cursor:pointer;padding:0;">☰</button>' +
    '</header>' +
    '<div id="khdrM" style="display:none;flex-direction:column;background:var(--surface);border-bottom:1px solid var(--border);">' + mobDirect + mobGroups +
      '<a href="portal.html" style="color:var(--accent);text-decoration:none;padding:12px 24px;font-size:14px;">Portal →</a>' +
    '</div>' +
    '<style>' +
      '.khdr-grp{position:relative;padding:8px 0}' +
      '.khdr-gl{cursor:pointer;display:inline-flex;align-items:center;gap:3px}' +
      '.khdr-dd{position:absolute;top:100%;right:0;min-width:170px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:6px;display:none;flex-direction:column;gap:1px;z-index:60;box-shadow:0 10px 30px rgba(0,0,0,.45)}' +
      '.khdr-grp:hover .khdr-dd{display:flex}' +
      '.khdr-dd a{padding:8px 12px;border-radius:7px;font-size:13px;white-space:nowrap}' +
      '.khdr-dd a:hover{background:var(--surface2)}' +
      '@media(max-width:640px){.khdr-d{display:none!important}.khdr-b{display:block!important}}' +
    '</style>';

  // ---- Footer (eine Quelle) ----
  // Gruppierter Footer: alle Links bleiben, nur nach Zweck sortiert (aufgeräumter als eine lange Kette).
  function grp(label, links) {
    var inner = links.map(function (l) {
      var ext = l[2] ? ' target="_blank" rel="noopener"' : '';
      return '<a href="' + l[0] + '"' + ext + ' style="color:var(--muted);text-decoration:none;white-space:nowrap;">' + l[1] + '</a>';
    }).join(' <span style="opacity:.35;">·</span> ');
    return '<div style="margin:7px 0;line-height:2;">' +
      '<span style="color:var(--muted);opacity:.5;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;margin-right:10px;">' + label + '</span>' +
      inner + '</div>';
  }
  var footerHTML =
    '<footer style="text-align:center;padding:40px 24px;border-top:1px solid var(--border);font-size:12px;color:var(--muted);">' +
      '<div style="font-size:11px;opacity:.8;margin-bottom:18px;">$KLRX ist kein Finanzprodukt · Kein Gewinnversprechen · Teilnahme auf eigenes Risiko</div>' +
      grp("Werkzeuge", [["check.html", "Klartext-Check"], ["link-check.html", "Link-Check"], ["warnliste.html", "Warnliste"], ["analyse.html", "Analyse"], ["markt.html", "Markt"], ["watchlist.html", "Wächter"], ["bookmarklet.html", "Bookmarklet"]]) +
      grp("Lernen", [["news.html", "News"], ["ratgeber.html", "Ratgeber"], ["faq.html", "FAQ"], ["lernpfad.html", "Lernpfad"], ["check.html#warnzeichen", "Sicherheit"]]) +
      grp("Projekt", [["ueber-klrx.html", "Über den Token"], ["klaryx_milestones.html", "Meilensteine"], ["klaryx_halloffame.html", "Hall of Fame"], ["portal.html", "Portal"], ["klaryx_wallet_setup.html", "Wallet Setup"], ["https://solscan.io/token/2Dc81HQDDSCUWVUD1XeyUmv8nyLD46ai9VuDBsr7z2RD", "Solscan", true]]) +
      grp("Rechtliches", [["klaryx_impressum.html", "Impressum"], ["klaryx_datenschutz.html", "Datenschutz"], ["klaryx_disclaimer.html", "Disclaimer"], ["klaryx_legal.html", "Rechtliche Hinweise"], ["mailto:info@klaryx.de", "Kontakt"]]) +
      grp("Folgen", [["https://x.com/klaryxhq", "X", true], ["https://discord.gg/abyTeFaghX", "Discord", true], ["https://t.me/klaryxhq", "Telegram", true]]) +
      '<div style="margin-top:18px;font-size:11px;opacity:.7;">klaryx.de · © 2026 Klaryx</div>' +
    '</footer>';

  // ---- "Weitere Ratgeber" (nur auf Ratgeber-Seiten, interne Vernetzung/SEO) ----
  // Erscheint automatisch vor dem Footer und verlinkt die je anderen Ratgeber + Check.
  var RATGEBER = [
    ["ratgeber-solana-scam-erkennen.html", "Ist dieser Solana-Coin ein Scam?"],
    ["ratgeber-pumpfun-betrug-erkennen.html", "Betrug auf pump.fun erkennen"],
    ["ratgeber-honeypot-erkennen.html", "Honeypot erkennen"],
    ["ratgeber-krypto-phishing-erkennen.html", "Fake-Airdrop & Wallet-Drainer"]
  ];
  if (page.indexOf("ratgeber-") === 0) {
    var andere = RATGEBER.filter(function (r) { return r[0].toLowerCase() !== page; });
    var cards = andere.map(function (r) {
      return '<a href="' + r[0] + '" style="display:block;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 18px;text-decoration:none;color:var(--text);font-weight:600;font-size:14px;transition:border-color .15s;" onmouseover="this.style.borderColor=\'var(--accent)\'" onmouseout="this.style.borderColor=\'var(--border)\'">' + r[1] + ' <span style="color:var(--accent);">→</span></a>';
    }).join("");
    var relatedHTML =
      '<section style="max-width:760px;margin:0 auto;padding:40px 24px 8px;border-top:1px solid var(--border);">' +
        '<div style="font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);font-weight:600;margin-bottom:14px;">Weitere Ratgeber</div>' +
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;">' + cards + '</div>' +
        '<div style="margin-top:20px;text-align:center;">' +
          '<a href="check.html" style="display:inline-block;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-radius:10px;padding:12px 26px;text-decoration:none;font-weight:600;font-size:15px;">Jetzt einen Coin prüfen →</a>' +
        '</div>' +
      '</section>';
    var footEl = document.querySelector("footer");
    if (footEl) footEl.insertAdjacentHTML("beforebegin", relatedHTML);
  }

  // Ersetzt den vorhandenen Header/Footer jeder Seite durch die kanonische Version
  // (kein Platzhalter nötig – nur <script src="partials.js"></script> einbinden).
  // Altes Mobile-Menü zuerst entfernen, sonst gäbe es die id "khdrM" doppelt.
  var oldMenu = document.getElementById("khdrM");
  if (oldMenu && oldMenu.parentNode) oldMenu.parentNode.removeChild(oldMenu);
  var oldHeader = document.querySelector("header");
  if (oldHeader) oldHeader.outerHTML = headerHTML;
  var oldFooter = document.querySelector("footer");
  if (oldFooter) oldFooter.outerHTML = footerHTML;
})();
