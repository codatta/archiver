#!/usr/bin/env node
/**
 * Capture tutorial screenshots from staging.developer.humanbased.ai
 * Injects Supabase auth token to access authenticated pages.
 *
 * Usage:
 *   STAGING_TOKEN="eyJ..." STAGING_USER_ID="<uuid>" STAGING_USER_EMAIL="<email>" \
 *     node ux-tests/docs-tutorial/capture.mjs
 *
 * To get a fresh token: open staging.developer.humanbased.ai in Chrome,
 * log in, then run in DevTools console:
 *   JSON.parse(localStorage.getItem('sb-jbugexmhyxggatppgfcv-auth-token')).access_token
 */
import puppeteer from "../../packages/webapp/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { mkdirSync } from "fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "../../packages/docs/public/images/getting-started");
mkdirSync(OUT, { recursive: true });

const BASE = "https://staging.developer.humanbased.ai";
const SUPABASE_KEY = "sb-jbugexmhyxggatppgfcv-auth-token";

// ── Auth token — pass via env var STAGING_TOKEN ───────────────────────────────
const ACCESS_TOKEN = process.env.STAGING_TOKEN;
if (!ACCESS_TOKEN) {
  console.error("\nERROR: Set STAGING_TOKEN env var before running.\n");
  console.error("Get a fresh token from DevTools console (after logging in to staging):");
  console.error(`  JSON.parse(localStorage.getItem('${SUPABASE_KEY}')).access_token\n`);
  process.exit(1);
}

// Decode exp from JWT to warn if already expired
try {
  const payload = JSON.parse(Buffer.from(ACCESS_TOKEN.split(".")[1], "base64").toString());
  const expiresAt = new Date(payload.exp * 1000);
  if (Date.now() > payload.exp * 1000) {
    console.error(`\nERROR: Token expired at ${expiresAt.toISOString()}. Get a fresh one.\n`);
    process.exit(1);
  }
  console.log(`Token valid until ${expiresAt.toISOString()}`);
} catch {
  console.warn("Could not decode token — proceeding anyway.");
}

const STAGING_USER_ID = process.env.STAGING_USER_ID || "";
const STAGING_USER_EMAIL = process.env.STAGING_USER_EMAIL || "";

const SESSION = JSON.stringify({
  access_token: ACCESS_TOKEN,
  token_type: "bearer",
  expires_in: 3600,
  expires_at: Math.floor(Date.now() / 1000) + 3600,
  refresh_token: "",
  user: {
    id: STAGING_USER_ID,
    email: STAGING_USER_EMAIL,
    role: "authenticated",
    app_metadata: { provider: "github", providers: ["github"] },
    user_metadata: {},
  },
});

// ── Helpers ───────────────────────────────────────────────────────────────────

// Click the Sandbox/Production toggle button (a BUTTON between two SPANs in the header)
async function clickProductionToggle(page) {
  await page.evaluate(() => {
    const spans = [...document.querySelectorAll("span")];
    const prod = spans.find((s) => s.textContent.trim() === "Production");
    if (!prod) return;
    const btn = [...prod.parentElement.children].find((el) => el.tagName === "BUTTON");
    if (btn) btn.click();
  });
}

// Click a sidebar nav item by its exact button text (sidebar uses BUTTONs, not links)
async function clickSidebarItem(page, label) {
  await page.evaluate((text) => {
    const btn = [...document.querySelectorAll("button")].find((b) => b.textContent.trim() === text);
    if (btn) btn.click();
  }, label);
  await new Promise((r) => setTimeout(r, 2000));
}

async function injectAuth(page) {
  await page.evaluateOnNewDocument((key, session) => {
    localStorage.setItem(key, session);
  }, SUPABASE_KEY, SESSION);
}

async function shot(page, filename, { fullPage = false } = {}) {
  const path = join(OUT, filename);
  await page.screenshot({ path, fullPage });
  console.log(`  ✓ ${filename}`);
}

async function goto(page, path, { waitFor, settle = 2500 } = {}) {
  await page.goto(`${BASE}${path}`, { waitUntil: "networkidle2", timeout: 30000 });

  // Wait for "Loading..." spinner to disappear
  await page
    .waitForFunction(() => !document.body.innerText.includes("Loading..."), { timeout: 10000 })
    .catch(() => {});

  if (waitFor) {
    await page.waitForSelector(waitFor, { timeout: 10000 }).catch(() => {});
  }

  // Extra settle time for animations and data rendering
  await new Promise((r) => setTimeout(r, settle));
}

// ── Main ──────────────────────────────────────────────────────────────────────
const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 800, deviceScaleFactor: 2 });

console.log("\n── Public pages ─────────────────────────────────────────────");

// 01 Landing / sign-in page (correct route: /auth/signin)
await goto(page, "/auth/signin", { waitFor: "button", settle: 1500 });
await shot(page, "01-landing.png");

// 02 Sign-up page (correct route: /auth/signup)
await goto(page, "/auth/signup", { waitFor: "input", settle: 1500 });
await shot(page, "02-signup.png");

console.log("\n── Authenticated pages ──────────────────────────────────────");

// Inject auth for all subsequent pages
await injectAuth(page);

// 03 Dashboard overview
await goto(page, "/dashboard", { settle: 3000 });
await shot(page, "03-dashboard-overview.png");

// 05 Subscriptions (sandbox mode — shows active subscriptions + simulated verticals)
await goto(page, "/dashboard/subscriptions", { settle: 2500 });
await shot(page, "05-subscriptions.png");

// 06 Browse datasets — Subscriptions in Production mode
// The Sandbox/Production toggle is a BUTTON between two SPANs in the header.
// Sidebar items are BUTTONs (not <a> links). After clicking Production toggle,
// navigate to API Keys via sidebar button to keep the Production React state.
await goto(page, "/dashboard/subscriptions", { settle: 2000 });
await clickProductionToggle(page);
await new Promise((r) => setTimeout(r, 4000));
await shot(page, "06-browse-datasets.png");

// 04 API Keys — capture in Production mode via sidebar nav (preserves toggle state)
await clickSidebarItem(page, "API Keys");
await new Promise((r) => setTimeout(r, 3000));
await shot(page, "04-api-keys.png");

// 07 Billing
await goto(page, "/dashboard/billing", { settle: 2500 });
await shot(page, "07-billing.png");

// 08 Org settings (correct route: /dashboard/organization)
await goto(page, "/dashboard/organization", { waitFor: "form, input", settle: 2000 });
await shot(page, "08-org-settings.png");

// 09 Team members (correct route: /dashboard/members)
await goto(page, "/dashboard/members", { settle: 2500 });
await shot(page, "09-team-members.png");

// 10 Account settings (correct route: /dashboard/account)
await goto(page, "/dashboard/account", { waitFor: "form, input", settle: 2000 });
await shot(page, "10-account-settings.png");

await browser.close();
console.log(`\nDone — screenshots saved to:\n  ${OUT}\n`);
