#!/usr/bin/env node
/**
 * KLARYX – Batch-Check (füllt die Analyse-Datenbank)
 * Holt frische Solana-Adressen von Dexscreener und jagt sie durch den
 * Klaryx-Check-Endpunkt. Jeder Check schreibt automatisch in check_analytics.
 * Läuft als GitHub Action (Node ist dort vorinstalliert) – kein npm install.
 *
 * Anzahl per Umgebungsvariable ANZAHL (Default 300).
 */
const WORKER = "https://klaryx-bot.mahirgulabi.workers.dev/check";
const ZIEL = parseInt(process.env.ANZAHL || "300", 10);
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

async function sammlePumpFun(addrs) {
  for (const [sort, limit] of [["created_timestamp", PF_NEUESTE], ["market_cap", PF_TOP]]) {
    try {
      const url = "https://frontend-api-v3.pump.fun/coins?offset=0&limit=" + limit +
                  "&sort=" + sort + "&order=DESC&includeNsfw=true";
      const d = await (await fetch(url, { headers: { accept: "application/json" } })).json();
      if (Array.isArray(d)) d.forEach((c) => {
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
      console.log(`pump.fun (${sort}): ${Array.isArray(d) ? d.length : 0} Coins geholt.`);
    } catch (e) { console.log(`pump.fun-Quelle (${sort}) nicht erreichbar: ${e.message}`); }
    await sleep(400);
  }
}

// Schreibt die erfassten pump.fun-Metadaten als Zeitpunkt-Snapshot in pumpfun_meta.
async function schreibePumpMeta() {
  if (!SB_KEY) { console.log("Kein SUPABASE_SERVICE_ROLE_KEY gesetzt – pump.fun-Meta wird NICHT gespeichert."); return; }
  if (!pumpMeta.length) { console.log("Keine pump.fun-Meta zu speichern."); return; }
  const seen = new Map();
  pumpMeta.forEach((m) => seen.set(m.token_address, m)); // Duplikate im selben Lauf zusammenfassen
  const rows = [...seen.values()];
  try {
    const r = await fetch(SB_URL + "/rest/v1/pumpfun_meta", {
      method: "POST",
      headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY, "Content-Type": "application/json", Prefer: "return=minimal" },
      body: JSON.stringify(rows),
    });
    console.log(r.ok ? `pump.fun-Meta gespeichert: ${rows.length} Coins.` : `pump.fun-Meta Fehler: ${r.status} ${await r.text()}`);
  } catch (e) { console.log(`pump.fun-Meta Schreibfehler: ${e.message}`); }
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

async function sammleAdressen(mindestens) {
  const addrs = new Set();
  ETABLIERT.forEach((a) => addrs.add(a));   // Balance: bekannte Coins mit rein
  await sammlePumpFun(addrs);               // frische + fast graduierte pump.fun-Coins (+ Meta erfassen)
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
  return [...addrs];
}

async function checkeOne(addr) {
  for (let v = 0; v < 3; v++) {
    try {
      const r = await fetch(WORKER + "?token=" + encodeURIComponent(addr));
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
  console.log(`\nFertig: ${ok} ok, ${fail} fehlgeschlagen | 🟢 ${z.gruen}  🟡 ${z.gelb}  🔴 ${z.rot}`);
}
main();
