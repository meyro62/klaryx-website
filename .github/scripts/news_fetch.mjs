#!/usr/bin/env node
/**
 * KLARYX – News-Fetch
 * Holt Solana-Sicherheits-News per RSS (Cointelegraph-Tags, keyfrei), filtert auf
 * Solana + Sicherheit, laesst den Worker eine deutsche KI-Kurzzusammenfassung machen und
 * speichert Titel + Zusammenfassung + Stichpunkte + Quell-Link in Supabase (Tabelle news).
 * NIE Volltext speichern – nur eigene Zusammenfassung + Link (urheberrechtssicher).
 * Laeuft als GitHub Action. Alles in try/catch – faellt eine Quelle aus, laeuft der Rest weiter.
 */
const WORKER = "https://klaryx-bot.mahirgulabi.workers.dev";
const SB_URL = process.env.SUPABASE_URL || "https://wpxcgducfkbozecknfdw.supabase.co";
const SB_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const FEEDS = [
  ["BTC-Echo", "https://www.btc-echo.de/feed/"],                  // deutsch
  ["BeInCrypto", "https://de.beincrypto.com/feed/"],             // deutsch
  ["Cointelegraph DE", "https://de.cointelegraph.com/rss"],      // deutsch
  ["Cointelegraph", "https://cointelegraph.com/rss/tag/solana"], // englisch, Solana-Abdeckung (KI uebersetzt, wenn frei)
];
const SOLANA_RE   = /\bsolana\b|\bSOL\b|pump\.?fun|\bSPL\b/i;
const SECURITY_RE = /hack|scam|exploit|drain|phish|rug|stolen|steal|betrug|malware|vulnerab|sicherheit|angriff|attack|breach|fraud|drainer|honeypot|wallet/i;
const MAX_NEU = 10;   // pro Lauf hoechstens so viele neue News zusammenfassen (schont AI/Zeit)

function decode(s) {
  return String(s || "")
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&#0?39;|&apos;/g, "'").replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ").trim();
}
function tag(item, name) {
  const m = item.match(new RegExp("<" + name + "[^>]*>([\\s\\S]*?)</" + name + ">", "i"));
  return m ? decode(m[1]) : "";
}
async function holeFeed(name, url) {
  try {
    const xml = await (await fetch(url, { headers: { "User-Agent": "Klaryx-News/1.0", accept: "application/rss+xml, application/xml, text/xml" } })).text();
    const parts = xml.split(/<item[ >]/i).slice(1);
    return parts.map((p) => "<item " + p.split(/<\/item>/i)[0] + "</item>").map((it) => {
      const d = tag(it, "pubDate"); const t = d ? new Date(d) : null;
      return {
        source_name: name,
        title: tag(it, "title"),
        source_url: tag(it, "link"),
        desc: tag(it, "description"),
        published_at: t && !isNaN(t) ? t.toISOString() : null,
        source_id: tag(it, "guid") || tag(it, "link"),
      };
    }).filter((n) => n.title && n.source_url);
  } catch (e) { console.log("Feed-Fehler " + url + ": " + e.message); return []; }
}

// Reichert News, die frueher OHNE KI gespeichert wurden (summary=null), bei freier Quote nach.
async function reichereAn() {
  if (!SB_KEY) return;
  try {
    const r = await fetch(SB_URL + "/rest/v1/news?select=source_id,title&summary=is.null&order=created_at.desc&limit=8",
      { headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY } });
    const bare = await r.json();
    if (!Array.isArray(bare) || !bare.length) return;
    let ok = 0;
    for (const n of bare) {
      try {
        const s = await (await fetch(WORKER + "/summarize", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: n.title, desc: "" }),
        })).json();
        if (!s || !s.summary) break;   // Quote noch nicht frei -> beim naechsten Lauf erneut
        await fetch(SB_URL + "/rest/v1/news?source_id=eq." + encodeURIComponent(n.source_id), {
          method: "PATCH",
          headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY, "Content-Type": "application/json", Prefer: "return=minimal" },
          body: JSON.stringify({ summary: s.summary, bullets: s.bullets || [] }),
        });
        ok++;
      } catch (_e) {}
      await sleep(800);
    }
    if (ok) console.log(`${ok} aeltere News nachtraeglich zusammengefasst.`);
  } catch (e) { console.log("Anreichern fehlgeschlagen: " + e.message); }
}

async function main() {
  let all = [];
  for (const [name, url] of FEEDS) { all = all.concat(await holeFeed(name, url)); await sleep(300); }
  const seen = new Map();
  all.forEach((n) => { if (n.source_id && !seen.has(n.source_id)) seen.set(n.source_id, n); });
  let items = [...seen.values()].filter((n) => SOLANA_RE.test(n.title + " " + n.desc));   // Solana-bezogen
  items.sort((a, b) => String(b.published_at || "").localeCompare(String(a.published_at || "")));
  console.log(`${all.length} Roh-Items, ${items.length} gefilterte Solana-News.`);

  if (!SB_KEY) { console.log("Kein SUPABASE_SERVICE_ROLE_KEY – Abbruch."); return; }
  const vorhanden = new Set();
  try {
    const r = await fetch(SB_URL + "/rest/v1/news?select=source_id&order=created_at.desc&limit=500",
      { headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY } });
    (await r.json() || []).forEach((x) => x && x.source_id && vorhanden.add(x.source_id));
  } catch (e) { console.log("Vorhandene News lesen fehlgeschlagen: " + e.message); }

  const neu = items.filter((n) => !vorhanden.has(n.source_id)).slice(0, MAX_NEU);
  console.log(`${neu.length} neue News zu verarbeiten.`);
  let ok = 0;
  for (const n of neu) {
    try {
      let s = {};
      try {
        s = await (await fetch(WORKER + "/summarize", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: n.title, desc: n.desc }),
        })).json();
      } catch (_e) {}
      // Fallback: auch OHNE KI speichern (nur Titel + Quelle + Datum). So bleibt die Seite immer
      // gefuellt, unabhaengig vom Workers-AI-Kontingent – die KI reichert nur an, wenn verfuegbar.
      if (!s || !s.summary) { console.log("(ohne KI) " + n.title.slice(0, 60)); s = { summary: null, bullets: [] }; }
      const row = {
        source_id: n.source_id, title: n.title, summary: s.summary || null, bullets: s.bullets || [],
        source_name: n.source_name, source_url: n.source_url, published_at: n.published_at,
      };
      const w = await fetch(SB_URL + "/rest/v1/news?on_conflict=source_id", {
        method: "POST",
        headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY, "Content-Type": "application/json", Prefer: "resolution=merge-duplicates,return=minimal" },
        body: JSON.stringify(row),
      });
      if (w.ok) { ok++; console.log("gespeichert: " + n.title.slice(0, 60)); }
      else console.log(`Speicher-Fehler ${w.status}: ${await w.text()}`);

      // Klaryx-relevanter Fund? -> in internen Speicher (klaryx_findings) zur Kontrolle/Task.
      if (s.klaryx_relevant) {
        try {
          const f = await fetch(SB_URL + "/rest/v1/klaryx_findings?on_conflict=source_id", {
            method: "POST",
            headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY, "Content-Type": "application/json", Prefer: "resolution=merge-duplicates,return=minimal" },
            body: JSON.stringify({
              source_id: n.source_id, title: n.title, source_url: n.source_url,
              kategorie: s.kategorie || null, handlung: s.handlung || null, schwere: s.schwere || null,
            }),
          });
          console.log(f.ok ? "  🔒 Klaryx-relevanter Fund: " + n.title.slice(0, 50) : `  Fund-Fehler ${f.status}`);
        } catch (e) { console.log("  Fund-Schreibfehler: " + e.message); }
      }
    } catch (e) { console.log("Verarbeitungsfehler: " + e.message); }
    await sleep(1000);
  }
  await reichereAn();   // frueher ohne KI gespeicherte News nachtraeglich zusammenfassen (wenn Quote frei)
  console.log(`Fertig: ${ok} News gespeichert.`);
}
main();
