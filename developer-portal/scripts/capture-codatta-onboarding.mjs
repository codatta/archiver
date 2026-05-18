#!/usr/bin/env node
/**
 * Capture Codatta onboarding flow screenshots from staging.
 *
 * Captures the full user journey: landing → signup → onboarding wizard →
 * dashboard → subscriptions → pull data.
 *
 * Usage:
 *   node scripts/capture-codatta-onboarding.mjs
 *
 * Environment:
 *   STAGING_BASE_URL       — defaults to https://staging.developer.humanbased.ai
 *   TEST_EMAIL             — defaults to auto-generated test-onboarding-{ts}@inductive.network
 *   SUPABASE_URL           — required, Supabase project URL
 *   SUPABASE_SECRET_KEY    — required, Supabase service_role / admin secret
 *   SUPABASE_PUBLISHABLE_KEY — required, Supabase anon / publishable key
 *
 * Requires: puppeteer and @supabase/supabase-js as devDependencies
 */
import puppeteer from "puppeteer";
import { mkdir } from "fs/promises";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createClient } from "@supabase/supabase-js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "../screenshots/codatta-onboarding");
const BASE = process.env.STAGING_BASE_URL || "https://staging.developer.humanbased.ai";

function requireEnv(name) {
  const val = process.env[name];
  if (!val) {
    console.error(`Missing required environment variable: ${name}`);
    process.exit(1);
  }
  return val;
}

const SUPABASE_URL = requireEnv("SUPABASE_URL");
const SUPABASE_SECRET = requireEnv("SUPABASE_SECRET_KEY");
const SUPABASE_PUBLISHABLE = requireEnv("SUPABASE_PUBLISHABLE_KEY");
const PROJECT_REF = new URL(SUPABASE_URL).hostname.split(".")[0];

const TEST_EMAIL =
  process.env.TEST_EMAIL ||
  `test-onboarding-${Date.now()}@inductive.network`;

await mkdir(OUT, { recursive: true });

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// ── Supabase admin: create test user + session ──────────────────────
console.log(`Creating test user: ${TEST_EMAIL}`);
const adminClient = createClient(SUPABASE_URL, SUPABASE_SECRET, {
  auth: { autoRefreshToken: false, persistSession: false },
});

// Create a fresh user via admin API (auto-confirms email)
const { data: newUser, error: createErr } =
  await adminClient.auth.admin.createUser({
    email: TEST_EMAIL,
    password: "Test@Onboarding2026!",
    email_confirm: true,
  });

if (createErr) {
  console.error("Failed to create test user:", createErr.message);
  process.exit(1);
}
console.log(`  User created: ${newUser.user.id}`);

// Generate magic link to get a real session
const { data: linkData, error: linkErr } =
  await adminClient.auth.admin.generateLink({
    type: "magiclink",
    email: TEST_EMAIL,
  });

if (linkErr || !linkData?.properties?.hashed_token) {
  console.error("Failed to generate magic link:", linkErr?.message);
  process.exit(1);
}

const publicClient = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE, {
  auth: { autoRefreshToken: false, persistSession: false },
});

const { data: verifyData, error: verifyErr } =
  await publicClient.auth.verifyOtp({
    type: "magiclink",
    token_hash: linkData.properties.hashed_token,
  });

if (verifyErr || !verifyData?.session) {
  console.error("Failed to verify OTP:", verifyErr?.message);
  process.exit(1);
}

const session = verifyData.session;
console.log(
  `  Session acquired for ${session.user.email} (expires_in: ${session.expires_in}s)`
);

const storageKey = `sb-${PROJECT_REF}-auth-token`;
const storageValue = JSON.stringify({
  access_token: session.access_token,
  refresh_token: session.refresh_token,
  expires_in: session.expires_in,
  expires_at: session.expires_at,
  token_type: session.token_type,
  user: session.user,
});

// ── Launch browser ──────────────────────────────────────────────────
const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 800, deviceScaleFactor: 2 });

async function shot(name, opts = {}) {
  console.log(`  capturing ${name}...`);
  if (opts.delay) await wait(opts.delay);
  if (opts.action) await opts.action(page);
  await page.screenshot({
    path: join(OUT, `${name}.png`),
    fullPage: !!opts.fullPage,
  });
  console.log(`  ✓ ${name}.png`);
}

// ── Section 1: Unauthenticated pages ────────────────────────────────
console.log("\n── Unauthenticated Pages ──");

// Landing page
await page.goto(BASE, { waitUntil: "networkidle2", timeout: 30000 });
await shot("01-landing", { delay: 1500 });

// Signup page
await page.goto(`${BASE}/auth/signup`, {
  waitUntil: "networkidle2",
  timeout: 15000,
});
await shot("02-signup-email", { delay: 800 });

// Type a sample email to show the form in action
const emailInput = await page.$('input[type="email"]');
if (emailInput) {
  await emailInput.type("you@company.com", { delay: 40 });
  await shot("03-signup-email-filled", { delay: 300 });
}

// Signin page (for reference)
await page.goto(`${BASE}/auth/signin`, {
  waitUntil: "networkidle2",
  timeout: 15000,
});
await shot("04-signin", { delay: 800 });

// ── Section 2: Onboarding wizard (authenticated, fresh user) ────────
console.log("\n── Onboarding Wizard ──");

// Inject auth session
await page.goto(BASE, { waitUntil: "networkidle2" });
await page.evaluate(
  (key, value, token) => {
    localStorage.setItem(key, value);
    localStorage.setItem("access_token", token);
  },
  storageKey,
  storageValue,
  session.access_token
);

await page.reload({ waitUntil: "networkidle2" });
await wait(2000);

// Fresh user should redirect to onboarding — navigate explicitly if not
const currentUrl = page.url();
console.log(`  After auth inject: ${currentUrl}`);

if (!currentUrl.includes("onboarding")) {
  await page.goto(`${BASE}/onboarding`, {
    waitUntil: "networkidle2",
    timeout: 15000,
  });
  await wait(1500);
}

// Helper: find and click a button by text match
async function clickButton(textMatches) {
  const clicked = await page.evaluate((texts) => {
    const buttons = [...document.querySelectorAll("button, a")];
    const btn = buttons.find((b) =>
      texts.some((t) => b.textContent?.includes(t))
    );
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  }, textMatches);
  if (clicked) await wait(2000);
  return clicked;
}

// Step 1: Organization setup
await shot("05-onboarding-org-setup", { delay: 500 });

// Fill in org details using React-compatible value setter
const orgFilled = await page.evaluate(() => {
  // React ignores direct .value assignment — must use native setter
  const nativeSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, "value"
  ).set;
  const selectSetter = Object.getOwnPropertyDescriptor(
    window.HTMLSelectElement.prototype, "value"
  ).set;

  const inputs = [...document.querySelectorAll('input[type="text"], input:not([type])')];
  if (inputs.length >= 1) {
    nativeSetter.call(inputs[0], "Codatta");
    inputs[0].dispatchEvent(new Event("input", { bubbles: true }));
    inputs[0].dispatchEvent(new Event("change", { bubbles: true }));
  }
  if (inputs.length >= 2) {
    nativeSetter.call(inputs[1], "codatta-test");
    inputs[1].dispatchEvent(new Event("input", { bubbles: true }));
    inputs[1].dispatchEvent(new Event("change", { bubbles: true }));
  }

  const selects = [...document.querySelectorAll("select")];
  selects.forEach((sel) => {
    if (sel.options.length > 1) {
      selectSetter.call(sel, sel.options[1].value);
      sel.dispatchEvent(new Event("change", { bubbles: true }));
    }
  });
  return inputs.length;
});
console.log(`  Filled ${orgFilled} input fields (React-compatible)`);
await wait(500);
await shot("06-onboarding-org-filled", { delay: 500 });

// Click Continue / submit org step
const orgSubmitted = await clickButton(["Continue", "Create organization"]);
console.log(`  Org form submitted: ${orgSubmitted}`);
await wait(1000);

// Check if we advanced — look for step indicator or new content
const onStep2 = await page.evaluate(() => {
  const text = document.body.innerText;
  return text.includes("Invite") || text.includes("team") || text.includes("colleague");
});

if (onStep2) {
  // Step 2: Invite team
  await shot("07-onboarding-invite-team", { delay: 500 });
  // Skip invite step
  await clickButton(["later", "Skip", "Send invites & continue", "Continue"]);
} else {
  console.log("  Did not advance to invite step — capturing current state");
  await shot("07-onboarding-invite-team", { delay: 500 });
  // Try clicking any available navigation
  await clickButton(["later", "Skip", "Continue", "Next"]);
}

// Check if we're on API key step
const onStep3 = await page.evaluate(() => {
  const text = document.body.innerText;
  return text.includes("API Key") || text.includes("hb_live_") || text.includes("key");
});

if (onStep3) {
  await shot("08-onboarding-api-key", { delay: 500 });
} else {
  console.log("  Did not advance to API key step — capturing current state");
  await shot("08-onboarding-api-key", { delay: 500 });
}

// Navigate to dashboard
await clickButton(["Dashboard", "Start building", "Done", "Go to"]);

// ── Section 3: Dashboard pages ──────────────────────────────────────
console.log("\n── Dashboard Pages ──");

await page.goto(`${BASE}/dashboard`, {
  waitUntil: "networkidle2",
  timeout: 15000,
});
await shot("09-dashboard-overview", { delay: 2000 });

// API Keys page
await page.goto(`${BASE}/dashboard/api-keys`, {
  waitUntil: "networkidle2",
  timeout: 15000,
});
await shot("10-api-keys", { delay: 1500 });

// ── Section 4: Subscription flow ────────────────────────────────────
console.log("\n── Subscription Flow ──");

await page.goto(`${BASE}/dashboard/subscriptions`, {
  waitUntil: "networkidle2",
  timeout: 15000,
});
await shot("11-subscriptions-page", { delay: 2000 });

// Switch to Production mode — the toggle is a Sandbox/Production switch
const prodClicked = await page.evaluate(() => {
  // Look for clickable element containing "Production" text
  const allEls = [...document.querySelectorAll("*")];
  // Try: label, button, span, div with exact "Production" text
  const el = allEls.find(
    (e) =>
      e.textContent?.trim() === "Production" &&
      e.children.length === 0 && // leaf node
      e.offsetParent !== null // visible
  );
  if (el) {
    el.click();
    return "text-match";
  }
  // Fallback: look for a toggle/switch near "Production" text
  const toggle = document.querySelector('[role="switch"], .toggle, .switch');
  if (toggle) {
    toggle.click();
    return "toggle";
  }
  return false;
});
console.log(`  Production toggle: ${prodClicked}`);
if (prodClicked) {
  await wait(2500);
  await shot("12-subscriptions-production", { delay: 500 });
}

// Look for either "Explore" (production) or "Subscribe" (sandbox) on data source cards
const cardClicked = await clickButton(["Explore", "Preview"]);
if (cardClicked) {
  await wait(3000);
  await shot("13-explore-data-source", { delay: 500 });

  // Click "Subscribe to All" or "Subscribe"
  const subClicked = await clickButton(["Subscribe to All", "Subscribe"]);
  if (subClicked) {
    await wait(1000);
    await shot("14-subscribe-modal", { delay: 500 });

    // Accept terms checkbox if present
    const checkbox = await page.$('input[type="checkbox"]');
    if (checkbox) {
      await checkbox.click();
      await wait(300);
    }

    // Click final "Subscribe" confirm button
    const confirmClicked = await page.evaluate(() => {
      const buttons = [...document.querySelectorAll("button")];
      const btn = buttons.find(
        (b) =>
          b.textContent?.trim() === "Subscribe" &&
          !b.textContent?.includes("All")
      );
      if (btn) { btn.click(); return true; }
      return false;
    });
    if (confirmClicked) {
      await wait(2000);
      await shot("15-subscription-active", { delay: 1000 });
    }
  }
} else {
  // If no Explore/Preview, try clicking the first card's Subscribe button directly
  const directSub = await page.evaluate(() => {
    const buttons = [...document.querySelectorAll("button")];
    const btn = buttons.find((b) => b.textContent?.trim() === "Subscribe");
    if (btn) { btn.click(); return true; }
    return false;
  });
  if (directSub) {
    await wait(2000);
    await shot("13-subscribe-flow", { delay: 500 });
  }
}

// Pull Data button
if (await clickButton(["Pull Data"])) {
  await shot("16-pull-data-panel", { delay: 500 });
}

// ── Cleanup ─────────────────────────────────────────────────────────
await browser.close();

// Clean up test user (optional — keeps staging clean)
console.log(`\nCleaning up test user: ${TEST_EMAIL}`);
const { error: deleteErr } = await adminClient.auth.admin.deleteUser(
  newUser.user.id
);
if (deleteErr) {
  console.warn(`  Warning: could not delete test user: ${deleteErr.message}`);
} else {
  console.log("  Test user deleted.");
}

console.log(`\nDone! Screenshots saved to ${OUT}`);
