#!/usr/bin/env node
/**
 * Capture Getting Started screenshots from the running webapp.
 * Usage: node scripts/capture-screenshots.mjs
 * Requires: webapp running at localhost:3000
 */
import puppeteer from "../packages/webapp/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js";
import { mkdir } from "fs/promises";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient } from "../packages/webapp/node_modules/@supabase/supabase-js/dist/index.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "../packages/docs/public/images/getting-started");
const BASE = "http://localhost:3000";

const SUPABASE_URL = "https://uxafdddzhgdhsabkwmgw.supabase.co";
const SUPABASE_SECRET = process.env.SUPABASE_SECRET_KEY;
const SUPABASE_PUBLISHABLE = process.env.SUPABASE_PUBLISHABLE_KEY;
const PROJECT_REF = "uxafdddzhgdhsabkwmgw";

await mkdir(OUT, { recursive: true });

// --- Generate a full Supabase session ---
console.log("Generating auth session...");
const adminClient = createClient(SUPABASE_URL, SUPABASE_SECRET, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const { data: linkData, error: linkErr } = await adminClient.auth.admin.generateLink({
  type: "magiclink",
  email: "yi@inductive.network",
});

if (linkErr || !linkData?.properties?.hashed_token) {
  console.error("Failed to generate magic link:", linkErr?.message);
  process.exit(1);
}

// Use a fresh public client to verify the OTP and get a full session
const publicClient = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const { data: verifyData, error: verifyErr } = await publicClient.auth.verifyOtp({
  type: "magiclink",
  token_hash: linkData.properties.hashed_token,
});

if (verifyErr || !verifyData?.session) {
  console.error("Failed to verify OTP:", verifyErr?.message);
  process.exit(1);
}

const session = verifyData.session;
console.log(`Got session for ${session.user.email} (expires_in: ${session.expires_in}s)`);

// Build the Supabase storage key format
const storageKey = `sb-${PROJECT_REF}-auth-token`;
const storageValue = JSON.stringify({
  access_token: session.access_token,
  refresh_token: session.refresh_token,
  expires_in: session.expires_in,
  expires_at: session.expires_at,
  token_type: session.token_type,
  user: session.user,
});

// --- Launch browser ---
const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 800, deviceScaleFactor: 2 });

async function shot(name, url, opts = {}) {
  console.log(`  capturing ${name}...`);
  await page.goto(url, { waitUntil: "networkidle2", timeout: 15000 }).catch(() => {});
  if (opts.delay) await new Promise((r) => setTimeout(r, opts.delay));
  if (opts.action) await opts.action(page);
  await page.screenshot({
    path: join(OUT, `${name}.png`),
    fullPage: opts.fullPage || false,
  });
}

// --- Unauthenticated pages ---
await shot("01-landing", BASE, { delay: 1000 });
await shot("02-signup", `${BASE}/auth/signup`, { delay: 500 });
await shot("03-signin", `${BASE}/auth/signin`, { delay: 500 });

// --- Inject auth session into localStorage ---
console.log("Injecting auth session...");
await page.goto(BASE, { waitUntil: "networkidle2" });
await page.evaluate((key, value, token) => {
  localStorage.setItem(key, value);
  localStorage.setItem("access_token", token);
}, storageKey, storageValue, session.access_token);

// Verify session is set
await page.reload({ waitUntil: "networkidle2" });
await new Promise((r) => setTimeout(r, 2000));

const currentUrl = page.url();
console.log(`  After session inject, navigated to: ${currentUrl}`);

// --- Authenticated pages ---
// Dashboard overview
await shot("05-dashboard-overview", `${BASE}/dashboard`, { delay: 3000 });

// Check if we actually got the dashboard
const dashUrl = page.url();
console.log(`  Dashboard URL: ${dashUrl}`);

if (dashUrl.includes("dashboard")) {
  // Subscriptions page
  await shot("06-subscriptions", `${BASE}/dashboard/subscriptions`, { delay: 2000 });

  // API Keys page
  await shot("07-api-keys", `${BASE}/dashboard/api-keys`, { delay: 1500 });

  // Billing page
  await shot("08-billing", `${BASE}/dashboard/billing`, { delay: 1500 });

  // Org Settings page
  await shot("09-org-settings", `${BASE}/dashboard/organization`, { delay: 1500 });

  // Account Settings page
  await shot("10-account-settings", `${BASE}/dashboard/account`, { delay: 1500 });

  // Team Members page
  await shot("11-team-members", `${BASE}/dashboard/members`, { delay: 1500 });

  // Onboarding (requires auth — capture after session inject)
  await shot("04-onboarding", `${BASE}/onboarding`, { delay: 1500 });
} else {
  console.log("  Auth failed — dashboard redirected to:", dashUrl);
}

await browser.close();
console.log(`\nDone! Screenshots saved to ${OUT}`);
