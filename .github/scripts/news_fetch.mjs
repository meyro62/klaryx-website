#!/usr/bin/env node
/**
 * KLARYX – News-Fetch
 * Holt Solana-News per RSS (deutsche Quellen + Cointelegraph), filtert auf Solana, laesst
 * Groq (kostenlos, zuverlaessig) eine deutsche KI-Kurzzusammenfassung + Relevanz-Bewertung machen
 * und speichert Titel + Zusammenfassung + Stichpunkte + Quell-Link in Supabase (Tabelle news).
 * NIE Volltext speichern – nur eigene Zusammenfassung + Link (urheberrechtssicher).
 * OHNE KI-Key wird trotzdem gespeichert (Titel + Link). Alles in try/catch.
 */
const SB_URL = process.env.SUPABASE_URL || "https://wpxcgducfkbozecknfdw.supabase.co";
const SB_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
const GROQ_KEY = process.env.GROQ_API_KEY || "";
const GROQ_MODEL = "openai/gpt-oss-120b";   // llama-3.3-70b-versatile wurde 2026-08-16 von Groq abgeschaltet
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const FEEDS = [
  ["BTC-Echo", "https://www.btc-echo.de/feed/"],                  // deutsch
  ["BeInCrypto", "https://de.beincrypto.com/feed/"],             // deutsch
  ["Cointelegraph DE", "https://de.cointelegraph.com/rss"],      // deutsch
  ["Cointelegraph", "https://cointelegraph.com/rss/tag/solana"], // englisch, Solana-Abdeckung (KI uebersetzt, wenn frei)
];
const SOLANA_RE   = /\bsolana\b|pump\.?fun/i;   // echtes "Solana"-Wort, nicht der SOL-Ticker (sonst matchen Multi-Coin-Listen)
const NOISE_RE    = /price prediction|preisprognose|kursanalyse|price analysis/i;   // Preis-Roundups raus
const SECURITY_RE = /hack|scam|exploit|drain|phish|rug|stolen|steal|betrug|malware|vulnerab|sicherheit|angriff|attack|breach|fraud|drainer|honeypot|wallet/i;
const MAX_NEU = 10;   // pro Lauf hoechstens so viele neue News zusammenfassen (schont AI/Zeit)

// Deutsche KI-Zusammenfassung + Klaryx-Relevanz via Groq (OpenAI-kompatibel, kostenloser Tier).
// Gibt {summary,bullets,klaryx_relevant,kategorie,handlung,schwere} oder null (kein Key/Fehler).
async function summarize(title, desc) {
  if (!GROQ_KEY || !title) return null;
  const sys = "Du bist ein deutschsprachiger Krypto-Sicherheits-Redakteur fuer Klaryx (ein Solana-Scam-Check). AUFGABE 1: Fasse die Nachricht KURZ auf Deutsch zusammen (uebersetze bei Bedarf) - nutze AUSSCHLIESSLICH Titel + Kurzbeschreibung, erfinde nichts, keine Anlageberatung, keine Preisprognose. AUFGABE 2: Bewerte, ob die Nachricht fuer Klaryx HANDLUNGSRELEVANT ist - z.B. eine neue Betrugs-/Angriffsmasche, die unser Check erkennen sollte, ein Token-2022-Trick, eine Phishing-/Drainer-Methode, oder eine Schwachstelle in Krypto-Infrastruktur (Supabase/Cloudflare/RPC/GitHub). Reine Preis-/Markt-/Firmen-News ist NICHT relevant. Antworte NUR als JSON: {\"summary\":\"1-2 Saetze\",\"bullets\":[\"...\",\"...\"],\"klaryx_relevant\":false,\"kategorie\":\"\",\"handlung\":\"\",\"schwere\":\"hoch/mittel/niedrig\"}. WICHTIG: \"summary\" ist EIN deutscher Fliesstext als String, NIEMALS ein Objekt; \"bullets\" ist ein Array aus Strings. Hoechstens 3 Stichpunkte.";
  const usr = "Titel: " + title + "\nKurzbeschreibung: " + (desc || "(keine)");
  try {
    const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: "Bearer " + GROQ_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: GROQ_MODEL,
        messages: [{ role: "system", content: sys }, { role: "user", content: usr }],
        temperature: 0.2, max_tokens: 500, response_format: { type: "json_object" },
      }),
    });
    if (!r.ok) { console.log(`Groq-Fehler ${r.status}: ${(await r.text()).slice(0, 140)}`); return null; }
    const j = await r.json();
    const out = (j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || "";
    const p = JSON.parse(out);
    return {
      summary: typeof p.summary === "string" ? p.summary.trim() : "",
      bullets: Array.isArray(p.bullets) ? p.bullets.map((b) => String(b).trim()).filter(Boolean).slice(0, 3) : [],
      klaryx_relevant: p.klaryx_relevant === true || p.klaryx_relevant === "true",
      kategorie: String(p.kategorie || "").trim().slice(0, 60),
      handlung: String(p.handlung || "").trim().slice(0, 300),
      schwere: String(p.schwere || "").trim().toLowerCase().slice(0, 12),
    };
  } catch (e) { console.log("Groq-Fehler: " + e.message); return null; }
}

function decode(s) {
  return String(s || "")
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => { try { return String.fromCodePoint(parseInt(h, 16)); } catch { return " "; } })   // Hex-Entities (&#x201C;)
    .replace(/&#(\d+);/g, (_, n) => { try { return String.fromCodePoint(parseInt(n, 10)); } catch { return " "; } })          // numerische Entities (&#8220; -> „)
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&nbsp;/g, " ")
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

// Reichert News, die frueher OHNE KI gespeichert wurden (summary=null), nach.
// Reihenfolge = Anzeige-Reihenfolge (published_at desc), damit die sichtbare Liste von oben
// aufgefuellt wird – keine englischen Luecken mehr in der Mitte. Ein Lauf schafft die ganze
// sichtbare Seite (60). Groq-Ratelimit wird mit 2,5 s Pause pro Call respektiert.
async function reichereAn() {
  if (!SB_KEY || !GROQ_KEY) return;
  try {
    const r = await fetch(SB_URL + "/rest/v1/news?select=source_id,title&summary=is.null&order=published_at.desc.nullslast&limit=60",
      { headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY } });
    const bare = await r.json();
    if (!Array.isArray(bare) || !bare.length) return;
    console.log(`${bare.length} leere News zum Nachfuellen.`);
    let ok = 0, fails = 0;
    for (const n of bare) {
      try {
        const s = await summarize(n.title, "");
        if (!s || !s.summary) { if (++fails >= 4) { console.log("KI 4x hintereinander leer -> Abbruch, Rest naechster Lauf."); break; } continue; }
        fails = 0;
        await fetch(SB_URL + "/rest/v1/news?source_id=eq." + encodeURIComponent(n.source_id), {
          method: "PATCH",
          headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY, "Content-Type": "application/json", Prefer: "return=minimal" },
          body: JSON.stringify({ summary: s.summary, bullets: s.bullets || [] }),
        });
        ok++;
      } catch (_e) {}
      await sleep(2500);
    }
    if (ok) console.log(`${ok} aeltere News nachtraeglich zusammengefasst.`);
  } catch (e) { console.log("Anreichern fehlgeschlagen: " + e.message); }
}

// Repariert bereits gespeicherte Titel mit rohen HTML-Entities (&#8220; etc.), die der
// alte Decoder nicht umgewandelt hat. Idempotent: saubere Titel bleiben unveraendert.
async function repariereTitel() {
  if (!SB_KEY) return;
  try {
    const r = await fetch(SB_URL + "/rest/v1/news?select=source_id,title&order=published_at.desc.nullslast&limit=200",
      { headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY } });
    const rows = await r.json();
    if (!Array.isArray(rows)) return;
    let fixed = 0;
    for (const n of rows) {
      const clean = decode(n.title);
      if (clean && clean !== n.title) {
        await fetch(SB_URL + "/rest/v1/news?source_id=eq." + encodeURIComponent(n.source_id), {
          method: "PATCH",
          headers: { apikey: SB_KEY, Authorization: "Bearer " + SB_KEY, "Content-Type": "application/json", Prefer: "return=minimal" },
          body: JSON.stringify({ title: clean }),
        });
        fixed++;
      }
    }
    if (fixed) console.log(`${fixed} Titel mit HTML-Entities korrigiert.`);
  } catch (e) { console.log("Titel-Reparatur fehlgeschlagen: " + e.message); }
}

async function main() {
  let all = [];
  for (const [name, url] of FEEDS) { all = all.concat(await holeFeed(name, url)); await sleep(300); }
  const seen = new Map();
  all.forEach((n) => { if (n.source_id && !seen.has(n.source_id)) seen.set(n.source_id, n); });
  let items = [...seen.values()].filter((n) => SOLANA_RE.test(n.title + " " + n.desc) && !NOISE_RE.test(n.title));   // echt Solana, kein Preis-Rauschen
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
      let s = await summarize(n.title, n.desc);
      // Fallback: auch OHNE KI speichern (nur Titel + Quelle + Datum). So bleibt die Seite immer
      // gefuellt, unabhaengig vom KI-Dienst – die KI reichert nur an, wenn verfuegbar.
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
  await repariereTitel();   // schon gespeicherte Titel mit rohen Entities (&#8220;) korrigieren
  await reichereAn();   // frueher ohne KI gespeicherte News nachtraeglich zusammenfassen (wenn Quote frei)
  console.log(`Fertig: ${ok} News gespeichert.`);
}
main();
