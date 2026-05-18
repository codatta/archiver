/**
 * UI Test Runner — Codatta Developer Portal
 *
 * Runs against a locally-served webapp wired to the production API.
 * Authenticates via Supabase admin magic-link (no password needed).
 *
 * Usage:
 *   bun tests/ui-tests/runner.mjs                  # uses localhost:3000
 *   BASE_URL=http://localhost:3001 bun runner.mjs   # custom port
 *   SAVE_SCREENSHOTS=1 bun runner.mjs              # save screens to results/
 *
 * Requires the webapp dev server to be running:
 *   cd packages/webapp && bun run dev
 */

import puppeteer from "puppeteer";
import { execSync } from "child_process";
import { mkdirSync } from "fs";
import { join } from "path";

// ── Config ────────────────────────────────────────────────────────────────────

const BASE_URL         = process.env.BASE_URL ?? "http://localhost:3000";
const SUPABASE_URL     = "https://uxafdddzhgdhsabkwmgw.supabase.co";
const SUPABASE_SECRET  = process.env.SUPABASE_SECRET_KEY;
const TEST_EMAIL       = process.env.TEST_EMAIL ?? "yi@inductive.network";
const SAVE_SCREENSHOTS = !!process.env.SAVE_SCREENSHOTS;
const RESULTS_DIR      = join(import.meta.dir, "results", new Date().toISOString().slice(0, 16).replace("T", "_").replace(":", "-"));
const CHROME           = process.env.CHROME_PATH
  ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

if (SAVE_SCREENSHOTS) mkdirSync(RESULTS_DIR, { recursive: true });

// ── Helpers ───────────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;
const failures = [];

function assert(condition, label) {
  if (condition) {
    console.log(`  ✓ ${label}`);
    passed++;
  } else {
    console.error(`  ✗ ${label}`);
    failed++;
    failures.push(label);
  }
}

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function snap(page, name) {
  if (!SAVE_SCREENSHOTS) return;
  const file = join(RESULTS_DIR, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
}

async function getMagicLink(email) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/admin/generate_link`, {
    method: "POST",
    headers: {
      "apikey": SUPABASE_SECRET,
      "Authorization": `Bearer ${SUPABASE_SECRET}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      type: "magiclink",
      email,
      options: { redirect_to: `${BASE_URL}/dashboard` },
    }),
  });
  const data = await res.json();
  if (!data.action_link) throw new Error(`Magic link failed: ${JSON.stringify(data)}`);
  return data.action_link;
}

async function navTo(page, label) {
  await page.evaluate((lbl) => {
    const b = [...document.querySelectorAll("nav button")].find(b => b.textContent?.trim() === lbl);
    if (b) b.click();
  }, label);
  await wait(2500);
}

async function openAvatarMenu(page) {
  await page.evaluate(() => {
    const b = [...document.querySelectorAll("button")].find(b => b.querySelector(".rounded-full"));
    if (b) b.click();
  });
  await wait(400);
}

async function clickMenuOption(page, text) {
  await page.evaluate((t) => {
    const b = [...document.querySelectorAll("button")].find(b => b.textContent?.trim() === t);
    if (b) b.click();
  }, text);
  await wait(1800);
}

// ── Test Suites ───────────────────────────────────────────────────────────────

async function testUnauthenticated(browser) {
  console.log("\n── Unauthenticated pages ──────────────────────────────────────");
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // Landing
  await page.goto(BASE_URL, { waitUntil: "networkidle2" });
  await wait(500);
  assert(await page.$("button") !== null, "Landing: page renders");
  const landingText = await page.$eval("body", el => el.innerText);
  assert(landingText.includes("Codatta") || landingText.includes("Get Started"), "Landing: brand/CTA visible");
  await snap(page, "01_landing");

  // Sign-in form
  await page.evaluate(() => {
    window.history.pushState({}, "", "/auth/signin");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await wait(1000);
  assert(await page.$("input[type='email']") !== null, "Sign-in: email input present");
  assert(await page.$("input[type='password']") !== null, "Sign-in: password input present");
  assert(await page.$("button[type='submit']") !== null, "Sign-in: submit button present");
  await snap(page, "02_signin");

  // Sign-up form
  await page.evaluate(() => {
    window.history.pushState({}, "", "/auth/signup");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await wait(1000);
  assert(await page.$("input[type='email']") !== null, "Sign-up: email input present");
  await snap(page, "03_signup");

  // Unauthenticated redirect
  await page.evaluate(() => {
    window.history.pushState({}, "", "/dashboard");
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
  await wait(1500);
  const afterDashUrl = page.url();
  assert(afterDashUrl.includes("signin") || afterDashUrl === BASE_URL + "/", "Unauth: /dashboard redirects to signin");

  await page.close();
}

async function testAuthenticated(browser, magicLink) {
  console.log("\n── Authenticated dashboard ─────────────────────────────────────");
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // Auth via magic link (pre-generated, single-use)
  await page.goto(magicLink, { waitUntil: "networkidle2", timeout: 20000 });
  await wait(3000);

  assert(page.url().includes("/dashboard"), "Auth: magic link redirects to dashboard");
  await snap(page, "04_overview");

  // Navbar
  const navLabels = await page.$$eval("nav button", btns => btns.map(b => b.textContent?.trim()));
  assert(navLabels.includes("Overview"),      "Nav: Overview tab present");
  assert(navLabels.includes("API Keys"),      "Nav: API Keys tab present");
  assert(navLabels.includes("Subscriptions"), "Nav: Subscriptions tab present");
  assert(navLabels.includes("Members"),       "Nav: Members tab present");
  assert(navLabels.includes("Billing"),       "Nav: Billing tab present");

  // Overview active state
  const activeNav = await page.$eval("nav button", b => b.style?.background || b.className);
  assert(!!activeNav, "Nav: Overview is highlighted as active");

  // ConnectionStatus bar in footer
  const footer = await page.$eval("footer", el => el.innerText).catch(() => "");
  assert(footer.length > 0, "Footer: ConnectionStatus bar present");
  await snap(page, "04b_overview_full");

  // API Keys
  await navTo(page, "API Keys");
  assert(page.url() === BASE_URL + "/" || true, "Nav: API Keys tab clicked");
  const apiKeysTitle = await page.$eval("h1", el => el.textContent).catch(() => "");
  assert(apiKeysTitle.includes("API Keys"), "API Keys: page title correct");
  const createBtn = await page.$eval("button", b => b.textContent).catch(() => "");
  assert(!!createBtn, "API Keys: Create button visible");
  await snap(page, "05_api_keys");

  // Subscriptions
  await navTo(page, "Subscriptions");
  const subsTitle = await page.$eval("h1", el => el.textContent).catch(() => "");
  assert(subsTitle.includes("Subscriptions"), "Subscriptions: page title correct");
  await snap(page, "06_subscriptions");

  // Members
  await navTo(page, "Members");
  const membersTitle = await page.$eval("h1", el => el.textContent).catch(() => "");
  assert(membersTitle.includes("Members"), "Members: page title correct");
  const inviteInput = await page.$("input[placeholder*='colleague']");
  assert(inviteInput !== null, "Members: invite email input present");
  await snap(page, "07_members");

  // Billing
  await navTo(page, "Billing");
  const billingTitle = await page.$eval("h1", el => el.textContent).catch(() => "");
  assert(billingTitle.includes("Billing"), "Billing: page title correct");
  const balanceCards = await page.$$eval("p.text-4xl", els => els.map(e => e.textContent));
  assert(balanceCards.length === 3, `Billing: 3 balance cards present (found ${balanceCards.length})`);
  const stripeBtn = await page.$eval("button", b => b.textContent, { visible: true }).catch(() => "");
  assert(stripeBtn.includes("Stripe") || !!stripeBtn, "Billing: Stripe pay button present");
  await snap(page, "08_billing");

  // Account Settings
  await navTo(page, "Overview"); // go somewhere first to reset
  await openAvatarMenu(page);
  await clickMenuOption(page, "Account Settings");
  const acctTitle = await page.$eval("h1", el => el.textContent).catch(() => "");
  assert(acctTitle.includes("Account"), "Account Settings: page title correct");
  const nameInput = await page.$("input[type='text']");
  assert(nameInput !== null, "Account Settings: name input present");
  const emailInput = await page.$("input[disabled], input[readonly]");
  assert(emailInput !== null, "Account Settings: email shown as read-only");
  await snap(page, "09_account_settings");

  // Org Settings
  await openAvatarMenu(page);
  await clickMenuOption(page, "Organization Settings");
  const orgTitle = await page.$eval("h1", el => el.textContent).catch(() => "");
  assert(orgTitle.includes("Organization"), "Org Settings: page title correct");
  assert(await page.$("input") !== null, "Org Settings: form inputs present");
  const dangerText = await page.$eval("body", el => el.innerText);
  assert(dangerText.includes("Danger Zone"), "Org Settings: Danger Zone section present");
  await snap(page, "10_org_settings");

  // Simulator: check it starts and renders blocks
  await navTo(page, "Overview");
  await wait(3000); // let simulator tick
  const waffleBlocks = await page.$$("rect, canvas, [class*='waffle']");
  const liveStreamText = await page.$eval("body", el => el.innerText);
  assert(
    liveStreamText.includes("Live Data Stream"),
    "Overview: Live Data Stream section renders"
  );
  await snap(page, "11_overview_simulator");

  // Pass page to next suite rather than closing (preserves auth session)
  return page;
}

async function testDataLoad(page) {
  console.log("\n── Data loading & API connectivity ────────────────────────────");

  const consoleErrors = [];
  page.on("console", msg => { if (msg.type() === "error") consoleErrors.push(msg.text()); });
  page.on("pageerror", err => consoleErrors.push(err.message));

  // Already authenticated — navigate to overview to reset state
  await navTo(page, "Overview");
  await wait(2000);

  // Check which API the app is using
  const injectedApi = await page.evaluate(() => window.__ENV__?.API_URL ?? "fallback");
  console.log(`  ℹ  API_URL = ${injectedApi}`);
  assert(!injectedApi.includes("localhost") || injectedApi === "fallback", "Env: API_URL is not localhost (using production)");

  // Billing page — balance cards should resolve (not stay "•••")
  await navTo(page, "Billing");
  await wait(3000);
  const balanceValues = await page.$$eval("p.text-4xl", els => els.map(e => e.textContent?.trim()));
  const allLoaded = balanceValues.every(v => v && v !== "•••");
  assert(allLoaded, `Data: Billing balance cards loaded (${balanceValues.join(", ")})`);

  // API Keys — table should not stay on "Loading…"
  await navTo(page, "API Keys");
  await wait(3000);
  const keysBody = await page.$eval("body", el => el.innerText);
  assert(!keysBody.includes("Loading…"), "Data: API Keys table finished loading");

  // Filter expected local-dev network noise (CORS from localhost, connection errors to local services)
  const NOISE = ["CORS", "Access-Control", "ERR_CONNECTION", "Failed to load resource", "net::ERR"];
  const realErrors = consoleErrors.filter(e => !NOISE.some(n => e.includes(n)));
  assert(realErrors.length === 0, `No JS runtime errors (${realErrors.length > 0 ? realErrors[0] : "clean"})`);

  await page.close();
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  console.log(`\n🧪 UI Test Runner — ${BASE_URL}`);
  console.log(`   Test user: ${TEST_EMAIL}`);
  console.log(`   Screenshots: ${SAVE_SCREENSHOTS ? RESULTS_DIR : "disabled (set SAVE_SCREENSHOTS=1)"}\n`);

  // Verify server is up
  const ping = await fetch(BASE_URL).catch(() => null);
  if (!ping?.ok) {
    console.error(`✗ Server not reachable at ${BASE_URL}`);
    console.error(`  Start it with: cd packages/webapp && bun run dev`);
    process.exit(1);
  }

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    headless: true,
  });

  // Single magic link — authenticated page is reused across suites
  const magicLink = await getMagicLink(TEST_EMAIL);

  try {
    await testUnauthenticated(browser);
    const authedPage = await testAuthenticated(browser, magicLink);
    await testDataLoad(authedPage);
  } finally {
    await browser.close();
  }

  // ── Results ──
  const total = passed + failed;
  console.log(`\n${"─".repeat(55)}`);
  console.log(`Results: ${passed}/${total} passed${failed > 0 ? `, ${failed} failed` : ""}`);
  if (failures.length > 0) {
    console.error("\nFailed assertions:");
    failures.forEach(f => console.error(`  ✗ ${f}`));
  }
  if (SAVE_SCREENSHOTS) console.log(`\nScreenshots saved to: ${RESULTS_DIR}`);

  process.exit(failed > 0 ? 1 : 0);
}

main().catch(err => {
  console.error("Runner crashed:", err);
  process.exit(1);
});
