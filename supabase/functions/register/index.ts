// KLARYX – Edge Function "register"
// =====================================================================
// Einziger erlaubter Schreibpfad für Registrierung + Referral.
// Prüft die Wallet-SIGNATUR serverseitig (Eigentumsnachweis) und schreibt
// mit service_role. anon hat KEIN Insert/Update mehr (siehe revoke-SQL).
//
// Deploy: Supabase Dashboard -> Edge Functions -> "register" -> Code einfügen
//         -> Deploy. WICHTIG: "Verify JWT" für diese Function AUSschalten
//         (sonst kann das Portal sie nicht mit dem publishable Key aufrufen).
//         SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY sind automatisch verfügbar.
//
// Anti-Sybil (Wallet-Alter/Aktivität) – standardmäßig AUS. Zum Anschalten
// (vor DEX-Listing) als Function-Secrets setzen:
//   REQUIRE_WALLET_AGE = true
//   MIN_WALLET_AGE_DAYS = 30      (optional, Default 30)
//   MIN_TX_COUNT       = 3        (optional, Default 3)
//   SOLANA_RPC         = https://...   (optional, Default mainnet-beta)
// =====================================================================
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import nacl from "https://esm.sh/tweetnacl@1.0.3";
import bs58 from "https://esm.sh/bs58@5.0.0";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const REQUIRE_AGE = (Deno.env.get("REQUIRE_WALLET_AGE") ?? "false").toLowerCase() === "true";
const MIN_AGE_DAYS = Number(Deno.env.get("MIN_WALLET_AGE_DAYS") ?? "30");
const MIN_TX = Number(Deno.env.get("MIN_TX_COUNT") ?? "3");
const RPC = Deno.env.get("SOLANA_RPC") ?? "https://api.mainnet-beta.solana.com";

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

// Anti-Sybil: prüft optional Wallet-Alter + Mindest-Transaktionen via Solana-RPC.
async function walletEligible(wallet: string): Promise<{ ok: boolean; reason?: string }> {
  if (!REQUIRE_AGE) return { ok: true };
  try {
    const res = await fetch(RPC, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0", id: 1, method: "getSignaturesForAddress",
        params: [wallet, { limit: 1000 }],
      }),
    });
    const data = await res.json();
    const sigs = data?.result ?? [];
    if (sigs.length < MIN_TX) return { ok: false, reason: `Wallet zu wenig genutzt (min. ${MIN_TX} Transaktionen).` };
    const oldest = sigs[sigs.length - 1];
    const bt = oldest?.blockTime;
    if (!bt) return { ok: false, reason: "Wallet-Alter nicht prüfbar." };
    const ageDays = (Date.now() / 1000 - bt) / 86400;
    if (ageDays < MIN_AGE_DAYS) return { ok: false, reason: `Wallet zu neu (min. ${MIN_AGE_DAYS} Tage).` };
    return { ok: true };
  } catch (_e) {
    // Fail-open: RPC-Ausfall soll die Registrierung nicht komplett kippen.
    return { ok: true };
  }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return j({ error: "method" }, 405);

  let body: any;
  try { body = await req.json(); } catch { return j({ error: "bad json" }, 400); }
  const { wallet, message, signature, referrer } = body ?? {};

  if (!validAddr(wallet)) return j({ error: "wallet ungültig" }, 400);
  if (typeof message !== "string" || !Array.isArray(signature)) return j({ error: "signatur fehlt" }, 400);

  // Nachricht muss Format + frische Zeit haben (Replay-Schutz, 5 Minuten)
  const m = /Wallet:\s*(\S+)[\s\S]*Time:\s*(\S+)/.exec(message);
  if (!m || m[1] !== wallet) return j({ error: "nachricht ungültig" }, 400);
  const t = Date.parse(m[2]);
  if (!t || Math.abs(Date.now() - t) > 5 * 60 * 1000) return j({ error: "nachricht abgelaufen" }, 400);

  // ed25519-Signatur prüfen: wurde message wirklich von <wallet> signiert?
  let ok = false;
  try {
    ok = nacl.sign.detached.verify(
      new TextEncoder().encode(message),
      Uint8Array.from(signature),
      bs58.decode(wallet),
    );
  } catch { ok = false; }
  if (!ok) return j({ error: "signatur ungültig" }, 401);

  // Optionaler Anti-Sybil-Check
  const elig = await walletEligible(wallet);
  if (!elig.ok) return j({ error: elig.reason }, 403);

  const sb = createClient(SUPABASE_URL, SERVICE_KEY);

  // Referrer validieren (muss existieren, nicht man selbst)
  let ref: string | null = null;
  if (validAddr(referrer) && referrer !== wallet) {
    const { data } = await sb.from("wallets").select("wallet_address").eq("wallet_address", referrer).maybeSingle();
    if (data) ref = referrer;
  }

  // Schon registriert? -> bestätigen, referrer NICHT überschreiben
  const { data: existing } = await sb.from("wallets").select("wallet_address").eq("wallet_address", wallet).maybeSingle();
  if (existing) return j({ status: "exists" });

  const { error } = await sb.from("wallets").insert([{
    wallet_address: wallet,
    registered_at: new Date().toISOString(),
    klrx_balance: "0.1",
    badge: "Free",
    tier: "Free",
    claim_status: "Ausstehend",
    og_status: true,
    referrer_wallet: ref,
  }]);
  if (error) return j({ error: error.message }, 500);

  if (ref) {
    await sb.from("referrals").insert([{
      referrer_wallet: ref, invited_wallet: wallet, created_at: new Date().toISOString(),
    }]);
  }

  return j({ status: "registered", referrer: ref });
});
