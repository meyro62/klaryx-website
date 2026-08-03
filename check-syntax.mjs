// Klaryx – Syntax-Check für Inline-Scripts in HTML.
// Fängt kaputte JS-Strings (z. B. gerades " statt typografisch „ …") und andere Syntaxfehler,
// BEVOR sie live gehen. Vor jedem Push ausführen:  node check-syntax.mjs
//
// Prüft alle *.html im selben Ordner + separat partials.js.
// Exit-Code 1 bei Fehler (praktisch für einen git pre-push-Hook).

import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const dir = dirname(fileURLToPath(import.meta.url));
let problems = 0;
let checked = 0;

function checkCode(code, where) {
  checked++;
  try {
    new vm.Script(code, { filename: where }); // nur PARSEN, nicht ausführen
  } catch (e) {
    problems++;
    console.log("\n  \x1b[31m✗ SYNTAXFEHLER\x1b[0m in " + where);
    console.log("    " + e.message);
    if (/regular expression|Unexpected|Invalid or unexpected token/i.test(e.message)) {
      console.log("    \x1b[33m→ Häufige Ursache: gerades \" in einem JS-String (z. B. „…\" statt „…“).");
      console.log("      Innere Anführungszeichen typografisch setzen („…“) oder ganz weglassen.\x1b[0m");
    }
  }
}

// 1) Inline-<script> ohne src aus jeder HTML-Datei ziehen und prüfen
const htmlFiles = readdirSync(dir).filter((f) => f.endsWith(".html"));
for (const file of htmlFiles) {
  const html = readFileSync(join(dir, file), "utf8");
  const re = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi;
  let m, i = 0;
  while ((m = re.exec(html))) {
    i++;
    // JSON-LD (application/ld+json) ist kein JS -> überspringen
    const openTag = m[0].slice(0, m[0].indexOf(">") + 1);
    if (/type\s*=\s*["']application\/(ld\+json|json)["']/i.test(openTag)) continue;
    checkCode(m[1], file + " (Script-Block " + i + ")");
  }
}

// 2) Externe JS-Dateien direkt prüfen
for (const js of ["partials.js"]) {
  try {
    checkCode(readFileSync(join(dir, js), "utf8"), js);
  } catch { /* Datei fehlt -> egal */ }
}

console.log("");
if (problems === 0) {
  console.log("\x1b[32m✓ Alles sauber\x1b[0m – " + checked + " Script-Blöcke geprüft, keine Syntaxfehler.");
  process.exit(0);
} else {
  console.log("\x1b[31m✗ " + problems + " Problem(e) gefunden\x1b[0m (von " + checked + " geprüften Blöcken). Bitte fixen, dann pushen.");
  process.exit(1);
}
