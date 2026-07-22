// KLARYX Wächter – Edge Function "watchlist" (Phase 1)
// =====================================================================
// Fügt Token zur Watchlist hinzu / entfernt sie. Nur signaturgeprüft
// (der Besitzer muss unterschreiben) und mit Tier-Limit (Free 1 /
// Einblick 5 / Tiefe 20). Schreibt mit service_role. anon kann NICHT
// direkt schreiben (siehe watchlist-SQL).
//
// Deploy: Supabase Dashboard -> Edge Functions -> "watchlist" -> Code
//         einfügen -> Deploy. "Verify JWT" AUS (wie bei "register").
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

// Tier + Limit aus der Zahl der geworbenen Wallets (wie im Sender)
function limitForRefs(refs: number): { tier: string; limit: number } {
  if (refs >= 50) return { tier: "Tiefe", limit: 20 };
  if (refs >= 25) return { tier: "Einblick", limit: 5 };
  return { tier: "Free", limit: 1 };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return j({ error: "method" }, 405);

  let body: any;
  try { body = await req.json(); } catch { return j({ error: "bad json" }, 400); }
  const { action, owner, message, signature, token, label } = body ?? {};

  if (!validAddr(owner)) return j({ error: "owner ungültig" }, 400);
  if (typeof message !== "string" || !Array.isArray(signature)) return j({ error: "signatur fehlt" }, 400);

  // Nachricht: Format + frische Zeit (Replay-Schutz, 5 Min)
  const m = /Wallet:\s*(\S+)[\s\S]*Zeit:\s*(\S+)/.exec(message);
  if (!m || m[1] !== owner) return j({ error: "nachricht ungültig" }, 400);
  const t = Date.parse(m[2]);
  if (!t || Math.abs(Date.now() - t) > 5 * 60 * 1000) return j({ error: "nachricht abgelaufen" }, 400);

  // Signatur prüfen
  let ok = false;
  try {
    ok = nacl.sign.detached.verify(new TextEncoder().encode(message), Uint8Array.from(signature), bs58.decode(owner));
  } catch { ok = false; }
  if (!ok) return j({ error: "signatur ungültig" }, 401);

  const sb = createClient(SUPABASE_URL, SERVICE_KEY);

  if (action === "remove") {
    if (!validAddr(token)) return j({ error: "token ungültig" }, 400);
    await sb.from("watchlist").delete().eq("owner_wallet", owner).eq("token_address", token);
    return j({ status: "removed" });
  }

  if (action === "add") {
    if (!validAddr(token)) return j({ error: "token ungültig" }, 400);
    if (token === owner) return j({ error: "token = eigene Wallet" }, 400);

    // Tier ermitteln (geworbene Wallets zählen)
    const { data: refRows } = await sb.from("wallets").select("wallet_address").eq("referrer_wallet", owner);
    const refs = (refRows || []).length;
    const { tier, limit } = limitForRefs(refs);

    // Bereits vorhanden? (idempotent)
    const { data: existing } = await sb.from("watchlist").select("id").eq("owner_wallet", owner).eq("token_address", token).maybeSingle();
    if (existing) return j({ status: "exists", tier, limit });

    // Aktuelle Anzahl gegen Limit
    const { count } = await sb.from("watchlist").select("id", { count: "exact", head: true }).eq("owner_wallet", owner);
    const current = count || 0;
    if (current >= limit) {
      return j({ error: `Watch-Limit erreicht (${current}/${limit}, Tier ${tier}). Lade mehr Freunde ein, um mehr zu beobachten.`, tier, limit }, 403);
    }

    const { error } = await sb.from("watchlist").insert([{
      owner_wallet: owner, token_address: token, label: typeof label === "string" ? label.slice(0, 40) : null,
    }]);
    if (error) return j({ error: error.message }, 500);
    return j({ status: "added", tier, limit, count: current + 1 });
  }

  return j({ error: "unbekannte action" }, 400);
});
