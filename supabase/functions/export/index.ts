// KLARYX – Edge Function "export"
// =====================================================================
// Liefert den Klaryx-Prüfdatensatz als CSV – EXKLUSIV für registrierte
// KLRX-Halter (jedes Tier). Prüft die Wallet-SIGNATUR serverseitig
// (Eigentumsnachweis, Replay-Schutz 5 Min) und dass die Wallet in der
// `wallets`-Tabelle steht (= registriert / Free Claim erhalten).
// Holt die Daten über die RPC analytics_export() (nur service_role).
//
// Deploy: Supabase Dashboard -> Edge Functions -> "export" -> Code einfügen
//         -> Deploy. WICHTIG: "Verify JWT" AUS (wie register/watchlist),
//         sonst kann das Portal die Funktion nicht aufrufen.
//         SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY sind automatisch da.
// =====================================================================
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import nacl from "https://esm.sh/tweetnacl@1.0.3";
import bs58 from "https://esm.sh/bs58@5.0.0";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const j = (o: unknown, s = 200) =>
  new Response(JSON.stringify(o), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

function validAddr(a: unknown): a is string {
  try { return typeof a === "string" && bs58.decode(a).length === 32; } catch { return false; }
}

// Ein CSV-Feld sicher escapen (Anführungszeichen verdoppeln, bei Sonderzeichen quoten).
function cell(v: unknown): string {
  if (v === null || v === undefined) return "";
  const s = String(v);
  return /[",\n;]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}
const jaNein = (b: unknown): string => (b === true ? "ja" : b === false ? "nein" : "");
// Zahlen mit KOMMA als Dezimaltrenner (deutsches Excel). Trennzeichen ist Semikolon.
const num = (v: unknown, d = 0): string =>
  v === null || v === undefined ? "" : Number(v).toFixed(d).replace(".", ",");
// ISO-Zeitstempel auf "YYYY-MM-DD HH:MM" kürzen (Excel-freundlich).
const dt = (v: unknown): string => (v ? String(v).slice(0, 16).replace("T", " ") : "");

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return j({ error: "method" }, 405);

  let body: any;
  try { body = await req.json(); } catch { return j({ error: "bad json" }, 400); }
  const { wallet, message, signature } = body ?? {};

  if (!validAddr(wallet)) return j({ error: "wallet ungültig" }, 400);
  if (typeof message !== "string" || !Array.isArray(signature)) return j({ error: "signatur fehlt" }, 400);

  // Nachricht: Format + frische Zeit (Replay-Schutz, 5 Min). Portal-Format nutzt "Time:".
  const m = /Wallet:\s*(\S+)[\s\S]*Time:\s*(\S+)/.exec(message);
  if (!m || m[1] !== wallet) return j({ error: "nachricht ungültig" }, 400);
  const t = Date.parse(m[2]);
  if (!t || Math.abs(Date.now() - t) > 5 * 60 * 1000) return j({ error: "nachricht abgelaufen" }, 400);

  // ed25519-Signatur prüfen
  let ok = false;
  try {
    ok = nacl.sign.detached.verify(new TextEncoder().encode(message), Uint8Array.from(signature), bs58.decode(wallet));
  } catch { ok = false; }
  if (!ok) return j({ error: "signatur ungültig" }, 401);

  const sb = createClient(SUPABASE_URL, SERVICE_KEY);

  // Halter-Gate: Wallet muss registriert sein (= in `wallets`, jedes Tier).
  const { data: holder } = await sb.from("wallets").select("wallet_address").eq("wallet_address", wallet).maybeSingle();
  if (!holder) return j({ error: "Nur für registrierte KLRX-Halter. Bitte zuerst im Portal registrieren." }, 403);

  // Datensatz holen (RPC gibt dedupliziertes JSON-Array; kein 1000-Zeilen-Limit)
  const { data: rows, error } = await sb.rpc("analytics_export");
  if (error) return j({ error: "Datensatz nicht verfügbar." }, 500);
  const list: any[] = Array.isArray(rows) ? rows : [];

  const stand = new Date().toISOString().slice(0, 10);

  // Format: CSV (Default) oder JSON (?format=json oder body.format="json").
  // JSON gibt die rohen Feldnamen zurück – praktischer zum Weiterverarbeiten.
  const url = new URL(req.url);
  const wantJson = String(url.searchParams.get("format") || body?.format || "").toLowerCase() === "json";
  if (wantJson) {
    const payload = {
      stand,
      hinweis: "Beschreibende On-Chain-Fakten, keine Anlageberatung.",
      anzahl: list.length,
      coins: list,
    };
    return new Response(JSON.stringify(payload), {
      status: 200,
      headers: { ...cors, "Content-Type": "application/json; charset=utf-8" },
    });
  }

  // CSV bauen
  const head = [
    "Adresse", "Name", "Symbol", "Ampel",
    "Mint aktiv", "Freeze aktiv", "Metadaten veraenderbar", "Gelistet",
    "Liquiditaet USD", "Volumen 24h USD", "Alter Tage", "Top10 Prozent", "Geprueft am",
  ];
  const lines: string[] = [];
  lines.push(cell("Klaryx Scan-Datensatz – beschreibende On-Chain-Fakten, keine Anlageberatung. Stand: " + stand));
  lines.push(head.map(cell).join(";"));
  for (const r of list) {
    lines.push([
      cell(r.token_address), cell(r.name), cell(r.symbol), cell(r.ampel),
      jaNein(r.mint_active), jaNein(r.freeze_active), jaNein(r.metadata_mutable), jaNein(r.listed),
      num(r.liquidity_usd, 0), num(r.volume_24h_usd, 0), num(r.age_days, 1), num(r.top10_pct, 2),
      dt(r.checked_at),
    ].join(";"));
  }
  // BOM voranstellen, damit Excel Umlaute korrekt öffnet.
  const csv = "﻿" + lines.join("\r\n");

  return new Response(csv, {
    status: 200,
    headers: {
      ...cors,
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="klaryx-scancheck-${stand}.csv"`,
    },
  });
});
