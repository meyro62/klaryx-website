# Klaryx – Edge Function Setup
**Kompletter Guide zum Selbst-Deployment**

---

## 🚀 SCHRITT 1: Edge Function erstellen

1. Geh zu: https://app.supabase.com
2. Wähle dein Klaryx-Projekt
3. Geh zu: **Edge Functions** (linkes Menü)
4. Klick: **Create a new function**
5. Name: `register-wallet`
6. Language: **TypeScript**
7. Klick: **Create function**

---

## 📝 SCHRITT 2: Code kopieren

Kopiere **ALLES** von hier in die Edge Function:

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { wallet_address, referrer_wallet } = await req.json();

    // Validierung
    if (!wallet_address || wallet_address.length !== 44) {
      return new Response(
        JSON.stringify({ error: "Invalid wallet address" }),
        { status: 400, headers: corsHeaders }
      );
    }

    // Supabase Client mit Service Role Key
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") || "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || ""
    );

    // 1. Wallet registrieren
    const { error: walletError } = await supabase
      .from("wallets")
      .insert([
        {
          wallet_address: wallet_address,
          registered_at: new Date().toISOString(),
          klrx_balance: 0.01,
          badge: "Free",
          tier: "Free",
          claim_status: "Pending",
          og_status: true,
          referrer_wallet: referrer_wallet || null,
        },
      ])
      .select();

    if (walletError && walletError.code !== "23505") {
      // 23505 = duplicate key (wallet existiert schon)
      return new Response(JSON.stringify({ error: walletError.message }), {
        status: 400,
        headers: corsHeaders,
      });
    }

    // 2. Referral tracken (wenn referrer vorhanden)
    if (referrer_wallet && referrer_wallet.length === 44) {
      await supabase.from("referrals").insert([
        {
          referrer_wallet: referrer_wallet,
          referred_wallet: wallet_address,
          created_at: new Date().toISOString(),
        },
      ]);
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: "Wallet registered. KLRX will be sent within 24 hours.",
      }),
      { status: 200, headers: corsHeaders }
    );
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: corsHeaders,
    });
  }
});
```

---

## 🔑 SCHRITT 3: Secrets hinzufügen

1. In der Edge Function: **Secrets** Tab
2. Füge diese zwei hinzu:

| Name | Wert |
|------|------|
| `SUPABASE_URL` | Deine Supabase Project URL (z.B. `https://wpxcgducfkbozecknfdw.supabase.co`) |
| `SUPABASE_SERVICE_ROLE_KEY` | Dein Service Role Key (Settings → API → service_role) |

**Wichtig:** 
- URL findest du in Supabase Settings → API → Project URL
- Service Role Key in derselben Stelle unter "Project API keys"
- ⚠️ **NIEMALS öffentlich teilen!**

3. Klick: **Deploy**

---

## ✅ SCHRITT 4: Testen

1. Nach Deploy: Function URL kopieren (steht oben in der Edge Function)
2. In `portal.html` suchen nach: `handleWallet()` Funktion
3. Die URL dort einfügen (siehe nächste Sektion)

---

## 📋 URL-Format

Deine Edge Function URL sieht so aus:
```
https://YOUR_PROJECT_ID.functions.supabase.co/register-wallet
```

Die brauchst du für portal.html!

---

## 🚨 Troubleshooting

**Error: "Invalid wallet address"**
- Wallet muss genau 44 Zeichen lang sein
- Nur alphanumerische Zeichen

**Error: "Duplicate key"**
- Wallet ist schon registriert (normal, nicht schlimm)

**Error: Service Role Key undefined**
- Secrets nicht richtig gespeichert?
- Redeploy nach dem Hinzufügen der Secrets

---

**Nächster Schritt:** Portal.html aktualisieren mit der Edge Function URL
