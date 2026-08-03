/* Klaryx – gemeinsamer Header + Footer (eine Quelle für alle Seiten).
   Einbinden: <div id="site-header"></div> ganz oben im <body>,
              <div id="site-footer"></div> unten, dann <script src="partials.js"></script>.
   Der aktive Menüpunkt wird automatisch anhand des Dateinamens hervorgehoben. */
(function () {
  var page = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  if (page === "" ) page = "index.html";

  // Menüpunkte (href, Label). Reihenfolge = Reihenfolge im Menü.
  var NAV = [
    ["check.html", "Klartext-Check"],
    ["link-check.html", "Link-Check"],
    ["warnliste.html", "Warnliste"],
    ["markt.html", "Markt"],
    ["watchlist.html", "Wächter"],
    ["lernpfad.html", "Lernpfad"],
    ["faq.html", "FAQ"],
    ["klaryx_milestones.html", "Meilensteine"]
  ];

  function isActive(href) {
    return href.toLowerCase() === page;
  }

  var muted = "color:var(--muted);text-decoration:none;";
  var active = "color:var(--text);text-decoration:none;";

  // ---- Desktop-Nav ----
  var deskLinks = NAV.map(function (n) {
    return '<a href="' + n[0] + '" style="' + (isActive(n[0]) ? active : muted) + 'font-size:13px;">' + n[1] + '</a>';
  }).join("");

  // ---- Mobile-Nav ----
  var mobLinks = NAV.map(function (n) {
    return '<a href="' + n[0] + '" style="' + (isActive(n[0]) ? active : muted) + 'padding:12px 24px;border-bottom:1px solid var(--border);font-size:14px;">' + n[1] + '</a>';
  }).join("");

  var headerHTML =
    '<header style="display:flex;align-items:center;justify-content:space-between;padding:14px 24px;border-bottom:1px solid var(--border);background:var(--bg);">' +
      '<a href="index.html" style="font-family:\'Space Mono\',monospace;font-size:16px;font-weight:700;text-decoration:none;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Klaryx</a>' +
      '<div class="khdr-d" style="display:flex;align-items:center;gap:22px;">' + deskLinks +
        '<a href="portal.html" style="background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-radius:8px;padding:8px 18px;font-size:13px;font-weight:600;text-decoration:none;">Portal →</a>' +
      '</div>' +
      '<button class="khdr-b" onclick="var m=document.getElementById(\'khdrM\');m.style.display=m.style.display===\'flex\'?\'none\':\'flex\';" style="display:none;background:none;border:none;color:var(--text);font-size:22px;cursor:pointer;padding:0;">☰</button>' +
    '</header>' +
    '<div id="khdrM" style="display:none;flex-direction:column;background:var(--surface);border-bottom:1px solid var(--border);">' + mobLinks +
      '<a href="portal.html" style="color:var(--accent);text-decoration:none;padding:12px 24px;font-size:14px;">Portal →</a>' +
    '</div>' +
    '<style>@media(max-width:640px){.khdr-d{display:none!important}.khdr-b{display:block!important}}</style>';

  // ---- Footer (eine Quelle) ----
  var f = 'style="color:var(--muted);text-decoration:none;"';
  var footerHTML =
    '<footer style="text-align:center;padding:36px 24px;border-top:1px solid var(--border);font-size:11px;color:var(--muted);line-height:2;">' +
      '$KLRX ist kein Finanzprodukt · Kein Gewinnversprechen · Teilnahme auf eigenes Risiko<br><br>' +
      '<a href="index.html" ' + f + '>Startseite</a> · ' +
      '<a href="check.html" ' + f + '>Klartext-Check</a> · ' +
      '<a href="link-check.html" ' + f + '>Link-Check</a> · ' +
      '<a href="warnliste.html" ' + f + '>Warnliste</a> · ' +
      '<a href="markt.html" ' + f + '>Markt</a> · ' +
      '<a href="check.html#warnzeichen" ' + f + '>Sicherheit</a> · ' +
      '<a href="faq.html" ' + f + '>FAQ</a> · ' +
      '<a href="ratgeber.html" ' + f + '>Ratgeber</a> · ' +
      '<a href="lernpfad.html" ' + f + '>Lernpfad</a> · ' +
      '<a href="watchlist.html" ' + f + '>Wächter</a> · ' +
      '<a href="ueber-klrx.html" ' + f + '>Über den Token</a> · ' +
      '<a href="portal.html" ' + f + '>Portal</a> · ' +
      '<a href="klaryx_wallet_setup.html" ' + f + '>Wallet Setup</a> · ' +
      '<a href="klaryx_halloffame.html" ' + f + '>Hall of Fame</a> · ' +
      '<a href="klaryx_milestones.html" ' + f + '>Meilensteine</a> · ' +
      '<a href="https://solscan.io/token/2Dc81HQDDSCUWVUD1XeyUmv8nyLD46ai9VuDBsr7z2RD" target="_blank" ' + f + '>Solscan</a><br>' +
      '<a href="klaryx_legal.html" ' + f + '>Rechtliche Hinweise</a> · ' +
      '<a href="klaryx_impressum.html" ' + f + '>Impressum</a> · ' +
      '<a href="klaryx_datenschutz.html" ' + f + '>Datenschutz</a> · ' +
      '<a href="klaryx_disclaimer.html" ' + f + '>Disclaimer</a> · ' +
      '<a href="mailto:info@klaryx.de" ' + f + '>Kontakt</a> · ' +
      '<a href="https://x.com/klaryxhq" target="_blank" ' + f + '>X</a> · ' +
      '<a href="https://discord.gg/abyTeFaghX" target="_blank" ' + f + '>Discord</a> · ' +
      '<a href="https://t.me/klaryxhq" target="_blank" ' + f + '>Telegram</a><br><br>' +
      'klaryx.de · © 2026 Meyro' +
    '</footer>';

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
