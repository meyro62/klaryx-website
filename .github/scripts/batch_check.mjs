#!/usr/bin/env node
/**
 * KLARYX – Batch-Check (füllt die Analyse-Datenbank)
 * Holt frische Solana-Adressen von Dexscreener und jagt sie durch den
 * Klaryx-Check-Endpunkt. Jeder Check schreibt automatisch in check_analytics.
 * Läuft als GitHub Action (Node ist dort vorinstalliert) – kein npm install.
 *
 * Anzahl per Umgebungsvariable ANZAHL (Default 5000). Der Adress-Harvest skaliert mit:
 * Re-Check bekannter Coins (fuer Verlaeufe) + pump.fun (frisch) + Jupiter (Auffueller).
 */
const WORKER = "https://klaryx-bot.mahirgulabi.workers.dev/check";
const ZIEL = parseInt(process.env.ANZAHL || "5000", 10);
const PAUSE_MS = 1500;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// --- pump.fun-Erfassung: Datengenerator für die spätere Graduation-/Creator-Korrelation ---
// Läuft NUR hier im Batch (GitHub Actions), nicht im nutzerseitigen Worker. Die pump.fun-API
// ist inoffiziell; alles ist in try/catch – fällt sie aus, läuft der Batch normal weiter.
const SB_URL = process.env.SUPABASE_URL || "https://wpxcgducfkbozecknfdw.supabase.co";
const SB_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
const PF_NEUESTE = 100;                       // frischeste Launches (created_timestamp)
const PF_TOP = 40;                            // nahe Graduation / bereits migriert (market_cap)
const PF_INITIAL_RESERVES = 793100000000000; // Start-Reserve der Bonding Curve (= 0 % verkauft)
const pumpMeta = [];                          // {token_address, creator, complete, graduation_pct, market_cap_usd}

// Graduation-Fortschritt aus den Bonding-Curve-Reserven (0 % = frisch, 100 % = migriert).
function gradPct(c) {
  if (c.complete) return 100;
  const r = Number(c.real_token_reserves);
  if (!isFinite(r) || r <= 0) return null;
  return +Math.max(0, Math.min(100, (1 - r / PF_INITIAL_RESERVES) * 100)).toFixed(1);
}

// Holt EINE Seite pump.fun-Coins, fuegt Mints + Metadaten hinzu, gibt die Anzahl zurueck.
async function pumpSeite(addrs, sort, offset, limit) {
  try {
    const url = "https://frontend-api-v3.pump.fun/coins?offset=" + offset + "&limit=" + limit +
                "&sort=" + sort + "&order=DESC&includeNsfw=true";
    const d = await (await fetch(url, { headers: { accept: "application/json" } })).json();
    if (!Array.isArray(d)) return 0;
    d.forEach((c) => {
      if (!c || !c.mint) return;
      addrs.add(c.mint);
      pumpMeta.push({
        token_address: c.mint,
        creator: c.creator || null,
        complete: !!c.complete,
        graduation_pct: gradPct(c),
        market_cap_usd: c.usd_market_cap != null ? +Number(c.usd_market_cap).toFixed(2) : null,
      });
    });
    return d.length;
  } catch (e) { console.log(`pump.fun (${sort}@${offset}) nicht erreichbar: ${e.message}`); return 0; }
}

// Sammelt pump.fun-Coins, bis ~ziel Adressen zusammen sind: ein paar nahe der Graduation
// (market_cap) plus so viele der NEUESTEN, wie fuer die Zielzahl noetig sind (seitenweise).
async function sammlePumpFun(addrs, ziel) {
  // Jede pump.fun-Liste ist per Offset bei ~1000-1500 gedeckelt, liefert aber ANDERE Coins:
  // created_timestamp = neueste, market_cap = groesste, last_trade_timestamp = zuletzt gehandelt.
  // Nacheinander angezapft holt das maximal viele einzigartige Adressen aus der kostenlosen API.
  for (const sort of ["created_timestamp", "market_cap", "last_trade_timestamp"]) {
    if (addrs.size >= ziel) break;
    let off = 0, geholt = 0;
    const MAX_OFF = 5000;   // pump.fun kappt ohnehin frueher; Deckel gegen Endlosschleife
    while (addrs.size < ziel && off < MAX_OFF) {
      const n = await pumpSeite(addrs, sort, off, PF_NEUESTE);
      geholt += n;
      if (n === 0) break;   // Ende der Liste (pump.fun kappt die Offset-Tiefe)
      off += PF_NEUESTE;
      await sleep(300);     // freundlich zur inoffiziellen API
    }
    console.log(`pump.fun (${sort}): ${geholt} geholt / Adressen gesamt jetzt ${addrs.size}.`);
  }
}

// Schreibt die erfassten pump.fun-Metadaten als Zeitpunkt-Snapshot in pumpfun_meta.
async function schreibePumpMeta() {
  if (!SB_KEY) { console.log("Kein SUPABASE_SERVICE_ROLE_KEY gesetzt – pump.fun-Meta wird NICHT gespeichert."); return; }
  if (!pumpMeta.length) { console.log("Keine pump.fun-Meta zu speichern."); return; }
  const seen = new Map();
  pumpMeta.forEach((m) => seen.set(m.token_address, m)); // Duplikate im selben Lauf zusammenfassen
  const rows = [...seen.values()];
  let ok = 0;
  // In Bloecken schreiben, damit auch grosse Laeufe (9999) nicht an einer Riesen-Anfrage scheitern.
  for (let i = 0; i < rows.length; i += 1000) {
    const chunk = rows.slice(i, i + 1000);
    try {
      const r = await fetch(SB_URL + "/rest/v1/pumpfun_meta", {
        method: "POST",
        headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY, "Content-Type": "application/json", Prefer: "return=minimal" },
        body: JSON.stringify(chunk),
      });
      if (r.ok) ok += chunk.length; else console.log(`pump.fun-Meta Fehler: ${r.status} ${await r.text()}`);
    } catch (e) { console.log(`pump.fun-Meta Schreibfehler: ${e.message}`); }
  }
  console.log(`pump.fun-Meta gespeichert: ${ok}/${rows.length} Coins.`);
}

// Berechnet die Sammel-/Börsen-Wallet-Liste (infra_wallets) neu – Wallets, die in >=5
// verschiedenen etablierten Token als Top-Halter auftauchen. Läuft NACH den heutigen Checks,
// damit die frischen Halter-Daten einfließen.
async function refreshInfra() {
  if (!SB_KEY) { console.log("Kein SUPABASE_SERVICE_ROLE_KEY – infra_wallets wird nicht aktualisiert."); return; }
  try {
    const r = await fetch(SB_URL + "/rest/v1/rpc/refresh_infra_wallets", {
      method: "POST",
      headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ min_tokens: 5 }),
    });
    console.log(r.ok ? `infra_wallets aktualisiert: ${(await r.text()).trim()} Wallets.` : `infra_wallets Fehler: ${r.status} ${await r.text()}`);
  } catch (e) { console.log(`infra_wallets Fehler: ${e.message}`); }
}

// Etablierte, bekannte Solana-Coins – für Balance in den Daten (werden eher grün/gelb).
const ETABLIERT = [
  "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", // BONK
  "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm", // WIF
  "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",  // JUP
  "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr", // POPCAT
  "9Qq3cwZkScM2TUXLHaMWJHxaJYaPEeG1uP1UmuFCCh7R", // PENGU
  "CcSttKajAXQbY4mU7vMhpSP6YFunzn7cBc59o5oDebbo", // MOODENG
  "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3", // PYTH
  "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",  // JITO
  "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R", // RAY
  "MEW1gQWJ3nEXg2qgERiKu7FAFj79PHvQVREQUzScPP5",  // MEW
  "8x5VqbHA8D7NkD52uNuS5nnt3PwA8pLD34ymskeSo2Wn", // ZEUS
  "AZsHEMXd36Bj1EMNXhowJajpUXzrKcK57wW4ZGXVa7yR", // GUAC
  "2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump", // PNUT
  "CzLSujWBLFssjncfkh59rUFqvafWcY5tzedWJSuypump", // GOAT
  "5z3EqYQo9HiCEs3R84RCDMu2n7anpDMxRhdK8PSWmrRC", // FWOG
  "63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9", // BOME
];

// Jupiter-Token-Universum: grosse freie Quelle handelbarer Solana-Token (Feld "id" = Mint).
// Fuellt bei GROSSEN Zielzahlen auf, wenn pump.fun (per Offset gedeckelt) nicht reicht.
// Bei normalen Laeufen (~1000) meist ungenutzt, weil pump.fun das Ziel schon erreicht.
async function sammleJupiter(addrs, ziel) {
  if (addrs.size >= ziel) return;
  const urls = [
    "https://lite-api.jup.ag/tokens/v2/tag?query=verified",
    "https://lite-api.jup.ag/tokens/v2/toptraded/24h?limit=100",
    "https://lite-api.jup.ag/tokens/v2/toporganicscore/24h?limit=100",
  ];
  for (const url of urls) {
    if (addrs.size >= ziel) break;
    try {
      const d = await (await fetch(url, { headers: { accept: "application/json" } })).json();
      const arr = Array.isArray(d) ? d : (Array.isArray(d?.tokens) ? d.tokens : []);
      const vor = addrs.size;
      arr.forEach((t) => { const m = t && (t.id || t.address || t.mint); if (m) addrs.add(m); });
      console.log(`Jupiter (${url.replace("https://lite-api.jup.ag/tokens/v2/", "")}): +${addrs.size - vor} / gesamt ${addrs.size}.`);
    } catch (e) { console.log(`Jupiter-Quelle nicht erreichbar: ${e.message}`); }
    await sleep(300);
  }
}

// Re-Check: zuletzt gesehene Coins erneut pruefen, damit VERLAEUFE entstehen (Liquiditaet ueber
// Zeit -> Rug-Erkennung, Graduation-Fortschritt). Das ist der eigentliche Wert der Daten, nicht
// die reine Menge. Zieht die zuletzt geprueften Coins der letzten 4 Tage aus check_analytics.
async function sammleRecheck(addrs, maxCoins) {
  if (!SB_KEY) { console.log("Kein SUPABASE_SERVICE_ROLE_KEY – Re-Check uebersprungen."); return; }
  try {
    const seit = new Date(Date.now() - 4 * 86400000).toISOString();  // letzte 4 Tage
    const distinct = new Set();
    for (let page = 0; page < 3 && distinct.size < maxCoins; page++) {
      const url = SB_URL + "/rest/v1/check_analytics?select=token_address&checked_at=gte." +
                  encodeURIComponent(seit) + "&order=checked_at.desc&limit=1000&offset=" + (page * 1000);
      const rows = await (await fetch(url, { headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY } })).json();
      if (!Array.isArray(rows) || !rows.length) break;
      rows.forEach((r) => { if (r.token_address && distinct.size < maxCoins) distinct.add(r.token_address); });
      if (rows.length < 1000) break;
    }
    const vor = addrs.size;
    distinct.forEach((a) => addrs.add(a));
    console.log(`Re-Check: +${addrs.size - vor} bekannte Coins (letzte 4 Tage) fuer Verlaeufe.`);
  } catch (e) { console.log(`Re-Check-Quelle nicht erreichbar: ${e.message}`); }
}

async function sammleAdressen(mindestens) {
  const addrs = new Set();
  ETABLIERT.forEach((a) => addrs.add(a));   // Balance: bekannte Coins mit rein
  await sammleRecheck(addrs, Math.min(2000, Math.floor(mindestens * 0.4)));  // Verlaeufe: bekannte Coins erneut pruefen
  await sammlePumpFun(addrs, mindestens);   // frische pump.fun-Coins seitenweise bis zur Zielzahl (+ Meta)
  const terms = [
    "cat","dog","pepe","moon","ai","baby","frog","bull","gem","doge","meme","gold",
    "trump","elon","inu","shib","floki","wojak","chad","turbo","mog","brett","andy",
    "sigma","based","degen","apu","banana","chill","goat","fwog","giga","ponke","michi",
    "king","queen","dragon","tiger","bear","ape","monkey","panda","fox","wolf","duck",
    "toad","rat","bird","fish","snake","lion","cash","rich","lambo","rocket","star",
    "space","alien","robot","ghost","skull","fire","ice","water","sun","dark","light",
    "wif","bonk","sol","usd","pump","fun","degods","mad","boys","girls","pump2","new",
  ];
  for (const url of [
    "https://api.dexscreener.com/token-profiles/latest/v1",
    "https://api.dexscreener.com/token-boosts/latest/v1",
    "https://api.dexscreener.com/token-boosts/top/v1",
  ]) {
    try {
      const d = await (await fetch(url)).json();
      if (Array.isArray(d)) d.forEach((p) => { if (p.chainId === "solana" && p.tokenAddress) addrs.add(p.tokenAddress); });
    } catch {}
    await sleep(300);
  }
  for (const q of terms) {
    if (addrs.size >= mindestens) break;
    try {
      const d = await (await fetch("https://api.dexscreener.com/latest/dex/search?q=" + encodeURIComponent(q))).json();
      (d.pairs || []).filter((x) => x.chainId === "solana" && x.baseToken?.address).slice(0, 10)
        .forEach((p) => addrs.add(p.baseToken.address));
    } catch {}
    await sleep(400);
  }
  await sammleJupiter(addrs, mindestens);   // grosse Zusatzquelle handelbarer Token (fuellt bei hohen Zielzahlen auf)
  return [...addrs];
}

async function checkeOne(addr) {
  for (let v = 0; v < 3; v++) {
    try {
      const r = await fetch(WORKER + "?nosummary=1&token=" + encodeURIComponent(addr));
      if (r.status === 429) { await sleep(4000); continue; }
      return await r.json();
    } catch { await sleep(1500); }
  }
  return null;
}

async function main() {
  console.log(`Klaryx Batch-Check – Ziel ~${ZIEL} Coins`);
  const addrs = await sammleAdressen(ZIEL);
  console.log(`${addrs.length} Adressen gefunden.`);
  let ok = 0, fail = 0; const z = { gruen: 0, gelb: 0, rot: 0 };
  const limit = Math.min(addrs.length, ZIEL);
  for (let i = 0; i < limit; i++) {
    const d = await checkeOne(addrs[i]);
    if (d && d.ampel) { ok++; z[d.ampel] = (z[d.ampel] || 0) + 1;
      const top = (d.facts || []).find((f) => /Top-10/.test(f.label));
      console.log(`[${i + 1}/${limit}] ${(d.name || addrs[i].slice(0,6)).slice(0,18)} ${(d.ampel||"?").toUpperCase()} ${top?top.wert:"-"}`);
    } else { fail++; }
    await sleep(PAUSE_MS);
  }
  await schreibePumpMeta();   // pump.fun-Metadaten sichern (für spätere Korrelation)
  await refreshInfra();       // Sammel-/Börsen-Wallet-Liste neu berechnen (aus frischen Halter-Daten)
  console.log(`\nFertig: ${ok} ok, ${fail} fehlgeschlagen | 🟢 ${z.gruen}  🟡 ${z.gelb}  🔴 ${z.rot}`);
}
main();
