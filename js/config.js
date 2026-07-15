/**
 * KLARYX Configuration Loader
 * Loads environment variables safely from window or environment
 * NEVER hardcode secrets!
 */

// Configuration with fallbacks for browser environment
const CONFIG = {
  // Supabase
  SUPABASE_URL: window.__ENV?.SUPABASE_URL || 'https://wpxcgducfkbozecknfdw.supabase.co',
  SUPABASE_ANON_KEY: window.__ENV?.SUPABASE_ANON_KEY || '',

  // Sentry
  SENTRY_DSN: window.__ENV?.SENTRY_DSN || '',

  // Environment
  IS_PRODUCTION: window.__ENV?.NODE_ENV === 'production',
};

// Validate required keys
function validateConfig() {
  if (!CONFIG.SUPABASE_ANON_KEY) {
    console.error('❌ SUPABASE_ANON_KEY not configured. Set in environment variables.');
    return false;
  }
  return true;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { CONFIG, validateConfig };
}
