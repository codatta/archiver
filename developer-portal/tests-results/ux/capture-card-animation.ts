import puppeteer from "puppeteer";
import { mkdir } from "fs/promises";
import { join } from "path";

const OUTPUT = join(import.meta.dir, "card-animation");
const BASE = "http://localhost:3000";
const EMAIL = "ux-test-bot@humanbased.ai";
const PASSWORD = "UxTest2026!secure";

await mkdir(OUTPUT, { recursive: true });

const browser = await puppeteer.launch({
  headless: true,
  defaultViewport: { width: 1440, height: 900 },
});

const page = await browser.newPage();

async function snap(name: string, waitMs = 500) {
  await new Promise((r) => setTimeout(r, waitMs));
  await page.screenshot({ path: join(OUTPUT, `${name}.png`), fullPage: false });
  console.log(`  ✓ ${name}.png`);
}

// ── Login ──────────────────────────────────────────────────────────
console.log("1. Logging in...");
await page.goto(`${BASE}/auth/signin`, { waitUntil: "networkidle2", timeout: 15000 });
await page.type('input[type="email"]', EMAIL);
await page.type('input[type="password"]', PASSWORD);
await page.click('button[type="submit"]');
await page.waitForFunction(
  () => window.location.pathname.includes("dashboard"),
  { timeout: 15000 }
);
await new Promise((r) => setTimeout(r, 2500));

// ── Navigate to Subscriptions ──────────────────────────────────────
console.log("2. Navigating to Subscriptions...");
await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent?.includes("Subscriptions"));
  if (btn) btn.click();
});
await new Promise((r) => setTimeout(r, 3000));

// ── 01: Collapsed grid (2-col) ─────────────────────────────────────
console.log("3. Capturing collapsed 2-col grid...");
await snap("01-collapsed-2col-grid", 500);

// Count cards and Explore buttons
const exploreCount = await page.evaluate(() => {
  return Array.from(document.querySelectorAll("button")).filter(b => b.textContent?.trim() === "Explore").length;
});
console.log(`   Found ${exploreCount} Explore buttons`);

if (exploreCount === 0) {
  console.log("   No Explore buttons — cards may not have loaded. Taking final screenshot.");
  await page.screenshot({ path: join(OUTPUT, "01-no-cards.png"), fullPage: true });
  await browser.close();
  process.exit(0);
}

// ── 02: Click first card "Explore" → expanding ─────────────────────
console.log("4. Expanding first card...");
await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent?.trim() === "Explore");
  if (btn) btn.click();
});
await snap("02-first-card-expanding", 100);
await snap("03-first-card-expanded", 400);

// ── 03: Scroll to see full expanded card + reflow ──────────────────
console.log("5. Capturing expanded card detail + reflow...");
await page.screenshot({ path: join(OUTPUT, "04-expanded-full-page.png"), fullPage: true });
console.log("  ✓ 04-expanded-full-page.png");

// ── 04: Verify close button exists ─────────────────────────────────
console.log("6. Verifying close button...");
const hasCloseBtn = await page.evaluate(() => {
  return !!document.querySelector('button[aria-label="Close detail view"]');
});
console.log(`   Close button present: ${hasCloseBtn}`);

// ── 05: Click close button → collapsing ────────────────────────────
console.log("7. Clicking close button to collapse...");
if (hasCloseBtn) {
  await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label="Close detail view"]') as HTMLButtonElement;
    if (btn) btn.click();
  });
} else {
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent?.trim() === "Collapse");
    if (btn) btn.click();
  });
}
await snap("05-collapsing", 100);
await snap("06-collapsed-restored", 400);

// ── 06: Expand a middle card (test reflow with cards above & below) ─
console.log("8. Expanding a middle card for reflow test...");
const middleClicked = await page.evaluate(() => {
  const btns = Array.from(document.querySelectorAll("button")).filter(b => b.textContent?.trim() === "Explore");
  // Click the 2nd or 3rd Explore button (a middle card)
  const target = btns[Math.min(2, btns.length - 1)];
  if (target) { target.click(); return true; }
  return false;
});
if (middleClicked) {
  await snap("07-middle-card-expanded", 500);
  await page.screenshot({ path: join(OUTPUT, "08-middle-reflow-full.png"), fullPage: true });
  console.log("  ✓ 08-middle-reflow-full.png");
}

// ── 07: Sidebar close-up ───────────────────────────────────────────
console.log("9. Sidebar close-up...");
const sidebar = await page.$("aside");
if (sidebar) {
  await sidebar.screenshot({ path: join(OUTPUT, "09-sidebar.png") });
  console.log("  ✓ 09-sidebar.png");
}

// ── 08: Open dropdowns ─────────────────────────────────────────────
// Collapse any expanded card first
await page.evaluate(() => {
  const btn = document.querySelector('button[aria-label="Close detail view"]') as HTMLButtonElement;
  if (btn) btn.click();
  else {
    const collapse = Array.from(document.querySelectorAll("button")).find(b => b.textContent?.trim() === "Collapse");
    if (collapse) collapse.click();
  }
});
await new Promise((r) => setTimeout(r, 400));

console.log("10. Opening category dropdown...");
const catClicked = await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent?.includes("categories"));
  if (btn) { btn.click(); return true; }
  return false;
});
if (catClicked) {
  await snap("10-category-dropdown", 500);
  await page.evaluate(() => document.body.click());
  await new Promise((r) => setTimeout(r, 300));
}

console.log("11. Opening sort dropdown...");
const sortClicked = await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll("button")).find(b => /Most data|Most tasks/.test(b.textContent || ""));
  if (btn) { btn.click(); return true; }
  return false;
});
if (sortClicked) {
  await snap("11-sort-dropdown", 500);
  await page.evaluate(() => document.body.click());
  await new Promise((r) => setTimeout(r, 300));
}

await browser.close();
console.log("\nDone! Screenshots saved to tests-results/ux/card-animation/");
