import puppeteer from "puppeteer";
import { mkdir } from "fs/promises";
import { join } from "path";

const OUTPUT = join(import.meta.dir, "minor-fix");
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

// Login
console.log("1. Logging in...");
await page.goto(`${BASE}/auth/signin`, { waitUntil: "networkidle2", timeout: 15000 });
await page.type('input[type="email"]', EMAIL);
await page.type('input[type="password"]', PASSWORD);
await page.click('button[type="submit"]');
await page.waitForFunction(
  () => window.location.pathname.includes("dashboard"),
  { timeout: 15000 }
);
await new Promise((r) => setTimeout(r, 2000));

// Navigate to Subscriptions
console.log("2. Navigating to Subscriptions...");
await page.evaluate(() => {
  const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent?.includes("Subscriptions"));
  if (btn) btn.click();
});
await new Promise((r) => setTimeout(r, 2500));

// Check if cards exist
const cardCount = await page.evaluate(() => {
  return document.querySelectorAll('[class*="border-[1.5px]"][class*="border-\\[\\#1B1034\\]"]').length;
});
console.log(`   Found ${cardCount} frontier cards`);

// Capture collapsed state (2-col grid)
await snap("10-cards-collapsed-grid", 500);

// Click on a card to expand it
console.log("3. Expanding a card...");
const clicked = await page.evaluate(() => {
  // Find "Explore" buttons
  const btns = Array.from(document.querySelectorAll("button"));
  const explore = btns.find(b => b.textContent?.trim() === "Explore");
  if (explore) { explore.click(); return true; }
  return false;
});

if (clicked) {
  // Capture mid-animation (100ms)
  await snap("11-card-expanding", 150);
  // Capture fully expanded (after 300ms animation)
  await snap("12-card-expanded-full-width", 400);

  // Scroll to see the close button
  console.log("4. Checking close button...");
  await snap("13-card-expanded-with-close-btn", 200);

  // Click close button to collapse
  console.log("5. Collapsing via close button...");
  const closed = await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label="Close detail view"]');
    if (btn) { (btn as HTMLButtonElement).click(); return true; }
    return false;
  });
  if (closed) {
    await snap("14-card-collapsing", 150);
    await snap("15-cards-collapsed-restored", 400);
  } else {
    console.log("   Close button not found, trying Collapse button...");
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll("button"));
      const collapse = btns.find(b => b.textContent?.trim() === "Collapse");
      if (collapse) collapse.click();
    });
    await snap("15-cards-collapsed-restored", 400);
  }
} else {
  console.log("   No Explore button found");
  await snap("10-no-cards-available", 500);
}

// Full page final state
await page.screenshot({ path: join(OUTPUT, "16-final-state.png"), fullPage: true });
console.log("  ✓ 16-final-state.png");

await browser.close();
console.log("\nDone!");
