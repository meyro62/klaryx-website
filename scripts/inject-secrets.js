#!/usr/bin/env node

/**
 * Secret Injection Script
 * Runs during build to inject environment secrets into portal.html
 * Only for production builds with GitHub Secrets
 */

const fs = require('fs');
const path = require('path');

const portalFile = path.join(__dirname, '../portal.html');

// Get secrets from environment (GitHub Actions sets these)
const secrets = {
  SUPABASE_URL: process.env.SUPABASE_URL || 'https://wpxcgducfkbozecknfdw.supabase.co',
  SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY || '',
  SENTRY_DSN: process.env.SENTRY_DSN || '',
};

// Validate
if (!secrets.SUPABASE_ANON_KEY) {
  console.error('❌ ERROR: SUPABASE_ANON_KEY not set in environment');
  process.exit(1);
}

// Read portal.html
let html = fs.readFileSync(portalFile, 'utf-8');

// Inject secrets as window object (before any script runs)
const secretsScript = `
<script>
// Environment secrets injected at build time
window.__ENV = {
  SUPABASE_URL: '${secrets.SUPABASE_URL}',
  SUPABASE_ANON_KEY: '${secrets.SUPABASE_ANON_KEY}',
  SENTRY_DSN: '${secrets.SENTRY_DSN}',
  NODE_ENV: '${process.env.NODE_ENV || 'production'}'
};
</script>
`;

// Insert after <head> tag
if (html.includes('</head>')) {
  html = html.replace('</head>', secretsScript + '</head>');
  fs.writeFileSync(portalFile, html, 'utf-8');
  console.log('✅ Secrets injected into portal.html');
} else {
  console.error('❌ Could not find </head> tag in portal.html');
  process.exit(1);
}
