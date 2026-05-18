// Runtime env override — set by server injection (env.js) or devtools for local API switching.
// Uses hostname-based detection to resolve staging vs production when not explicitly set.
declare global {
  interface Window {
    __ENV__?: Record<string, string>;
  }
}

function isStaging(): boolean {
  return typeof window !== "undefined" && window.location.hostname.includes("staging.");
}

function defaultApiUrl(): string {
  return isStaging() ? "https://staging.api.humanbased.ai" : "https://api.humanbased.ai";
}

function get(key: string, fallback: string): string {
  return (typeof window !== "undefined" && window.__ENV__?.[key]) || fallback;
}

export const ENV = {
  SUPABASE_URL:            get("SUPABASE_URL",            "https://uxafdddzhgdhsabkwmgw.supabase.co"),
  SUPABASE_PUBLISHABLE_KEY:get("SUPABASE_PUBLISHABLE_KEY","sb_publishable_OgL0DMwL6JattvbkLG1HBw_-pR9k7mJ"),
  API_URL:                 get("API_URL",                 defaultApiUrl()),
};
