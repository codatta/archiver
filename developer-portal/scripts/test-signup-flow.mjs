#!/usr/bin/env node
/**
 * Test signup workflow and capture key screens:
 *   Test A: non-@inductive.network email → verify-email / onboarding
 *   Test B: @inductive.network email → auto-join → dashboard
 *
 * Usage: node scripts/test-signup-flow.mjs
 * Requires: webapp at localhost:3000, API at localhost:8001
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

const ts = Date.now();

await mkdir(OUT, { recursive: true });

const adminClient = createClient(SUPABASE_URL, SUPABASE_SECRET, {
  auth: { autoRefreshToken: false, persistSession: false },
});

async function deleteTestUser(email) {
  try {
    const { data } = await adminClient.auth.admin.listUsers();
    const u = data?.users?.find((u) => u.email === email);
    if (u) {
      // Delete public.users and org_memberships first
      const userRow = await adminClient.from("users").select("id").eq("auth_id", u.id).single();
      if (userRow.data) {
        await adminClient.from("org_memberships").delete().eq("user_id", userRow.data.id);
        await adminClient.from("users").delete().eq("id", userRow.data.id);
      }
      await adminClient.auth.admin.deleteUser(u.id);
      console.log(`  cleaned up ${email}`);
    }
  } catch (e) {
    console.log(`  cleanup skipped: ${e.message}`);
  }
}

// --- Launch browser ---
const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

async function shot(name, page, opts = {}) {
  if (opts.delay) await new Promise((r) => setTimeout(r, opts.delay));
  if (opts.action) await opts.action(page);
  const path = join(OUT, `${name}.png`);
  await page.screenshot({ path, fullPage: opts.fullPage || false });
  console.log(`  saved ${name}.png`);
}

// ═══════════════════════════════════════════════════════════════════════════════
// TEST A: Sign up with non-@inductive.network email
// ═══════════════════════════════════════════════════════════════════════════════
console.log("\n== TEST A: Non-@inductive.network signup ==");
const testEmailA = `test-ext-${ts}@gmail.com`;
console.log(`  email: ${testEmailA}`);

// Pre-clean
await deleteTestUser(testEmailA);

// Use a fresh page (clean localStorage)
const pageA = await browser.newPage();
await pageA.setViewport({ width: 1280, height: 800, deviceScaleFactor: 2 });

// Clear all storage
await pageA.goto(BASE, { waitUntil: "networkidle2" });
await pageA.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });

// Navigate to signup
await pageA.goto(`${BASE}/auth/signup`, { waitUntil: "networkidle2", timeout: 15000 });
await new Promise((r) => setTimeout(r, 500));
await shot("signup-01-blank-form", pageA);

// Fill form
await pageA.type('input[type="text"]', "External Tester");
await pageA.type('input[type="email"]', testEmailA);
await pageA.type('input[type="password"]', "TestPass123!");
await shot("signup-02-filled-form", pageA, { delay: 300 });

// Submit
await Promise.all([
  pageA.click('button[type="submit"]'),
  pageA.waitForNavigation({ waitUntil: "networkidle2", timeout: 15000 }).catch(() => {}),
]);
await new Promise((r) => setTimeout(r, 2000));

const urlA = pageA.url();
console.log(`  -> After submit: ${urlA}`);

if (urlA.includes("verify-email")) {
  await shot("signup-03-verify-email", pageA);
  console.log("  PASS: Redirected to verify-email (email confirmations enabled)");
} else if (urlA.includes("onboarding")) {
  await shot("signup-03-onboarding", pageA);
  console.log("  PASS: Went to onboarding (email confirmations disabled, no auto-join)");
} else if (urlA.includes("dashboard")) {
  await shot("signup-03-dashboard", pageA);
  console.log("  NOTE: Went to dashboard (user was auto-joined to some org)");
} else {
  await shot("signup-03-unexpected", pageA);
  console.log(`  UNEXPECTED: ${urlA}`);
}

await pageA.close();
await deleteTestUser(testEmailA);

// ═══════════════════════════════════════════════════════════════════════════════
// TEST B: Sign up with @inductive.network email -> auto-join
// ═══════════════════════════════════════════════════════════════════════════════
console.log("\n== TEST B: @inductive.network signup (auto-join) ==");
const testEmailB = `test-join-${ts}@inductive.network`;
console.log(`  email: ${testEmailB}`);

// Pre-clean
await deleteTestUser(testEmailB);

// Fresh page
const pageB = await browser.newPage();
await pageB.setViewport({ width: 1280, height: 800, deviceScaleFactor: 2 });

// Clear all storage
await pageB.goto(BASE, { waitUntil: "networkidle2" });
await pageB.evaluate(() => { localStorage.clear(); sessionStorage.clear(); });

// Navigate to signup
await pageB.goto(`${BASE}/auth/signup`, { waitUntil: "networkidle2", timeout: 15000 });
await new Promise((r) => setTimeout(r, 500));

// Capture browser console for debugging
pageB.on("console", (msg) => {
  if (msg.type() === "error" || msg.type() === "warn") {
    console.log(`  [browser ${msg.type()}] ${msg.text()}`);
  }
});
pageB.on("requestfailed", (req) => {
  console.log(`  [request failed] ${req.method()} ${req.url()} — ${req.failure()?.errorText}`);
});

// Fill form with @inductive.network email
await pageB.type('input[type="text"]', "Internal Tester");
await pageB.type('input[type="email"]', testEmailB);
await pageB.type('input[type="password"]', "TestPass123!");
await shot("signup-04-inductive-filled", pageB, { delay: 300 });

// Submit and wait longer for async operations
await pageB.click('button[type="submit"]');
// Wait up to 15s for navigation
for (let i = 0; i < 15; i++) {
  await new Promise((r) => setTimeout(r, 1000));
  const currentUrl = pageB.url();
  if (!currentUrl.includes("/auth/signup")) {
    console.log(`  navigated after ${i + 1}s`);
    break;
  }
  if (i === 14) console.log("  timed out waiting for navigation");
}

const urlB = pageB.url();
console.log(`  -> After submit: ${urlB}`);
const pageTextB = await pageB.evaluate(() => document.body.innerText);
if (pageTextB.includes("error") || pageTextB.includes("Error") || pageTextB.includes("already")) {
  console.log(`  Page text excerpt: ${pageTextB.slice(0, 300)}`);
}

if (urlB.includes("dashboard")) {
  await shot("signup-05-auto-join-dashboard", pageB);
  console.log("  PASS: Auto-joined Inductive Network, went directly to dashboard!");
} else if (urlB.includes("onboarding")) {
  await shot("signup-05-onboarding", pageB);
  console.log("  NOTE: Went to onboarding despite @inductive.network email");

  // Check if user was actually auto-joined by looking at the dashboard
  await pageB.goto(`${BASE}/dashboard`, { waitUntil: "networkidle2", timeout: 15000 });
  await new Promise((r) => setTimeout(r, 2000));
  const dashUrl = pageB.url();
  if (dashUrl.includes("dashboard")) {
    await shot("signup-06-dashboard-after-onboarding", pageB, { delay: 1000 });
    console.log("  INFO: User can access dashboard — auto-join worked, but wasn't detected in signup flow");
  }
} else if (urlB.includes("verify-email")) {
  await shot("signup-05-verify-email-inductive", pageB);
  console.log("  INFO: Email confirmations enabled — verification required first");
} else {
  await shot("signup-05-unexpected", pageB);
  console.log(`  UNEXPECTED: ${urlB}`);
}

// Capture key state as screenshots regardless
const pageText = await pageB.evaluate(() => document.body.innerText);
if (pageText.includes("You're in!")) {
  console.log("  WelcomeModal visible!");
  await shot("signup-06-welcome-modal", pageB);
}

await pageB.close();
await deleteTestUser(testEmailB);

await browser.close();
console.log(`\n=== Done! Screenshots in ${OUT} ===`);
