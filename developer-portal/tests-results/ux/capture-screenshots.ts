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

// 1. Sign-in page
console.log("1. Sign-in page...");
await page.goto(`${BASE}/auth/signin`, { waitUntil: "networkidle2", timeout: 15000 });
await snap("01-sign-in-page", 1000);

// 2. Login
console.log("2. Logging in...");
await page.type('input[type="email"]', EMAIL);
await page.type('input[type="password"]', PASSWORD);
await page.click('button[type="submit"]');
await page.waitForFunction(
  () => window.location.pathname.includes("dashboard") || window.location.pathname.includes("onboarding"),
  { timeout: 15000 }
);
await new Promise((r) => setTimeout(r, 2500));

// Handle onboarding if needed
const currentPath = await page.evaluate(() => window.location.pathname);
if (currentPath.includes("onboarding")) {
  console.log("   Completing onboarding...");
  const orgInput = await page.$('input[type="text"]');
  if (orgInput) {
    await orgInput.type("UX Test Org");
    const btn = await page.evaluateHandle(() => {
      const btns = Array.from(document.querySelectorAll("button"));
      return btns.find(b => /create|next|continue/i.test(b.textContent || "")) || btns[btns.length - 1];
    });
    if (btn.asElement()) await (btn.asElement() as any).click();
    await new Promise((r) => setTimeout(r, 3000));
  }
}

// 3. Dashboard overview
console.log("3. Dashboard overview...");
await snap("02-dashboard-overview", 1000);

// 4. Sidebar close-up
console.log("4. Sidebar close-up...");
const sidebar = await page.$("aside");
if (sidebar) {
  await sidebar.screenshot({ path: join(OUTPUT, "03-sidebar-borders.png") });
  console.log("  ✓ 03-sidebar-borders.png");
}

// 5. Navigate to Subscriptions
console.log("5. Subscriptions page...");
await page.evaluate(() => {
  const btns = Array.from(document.querySelectorAll("button"));
  const sub = btns.find(b => b.textContent?.includes("Subscriptions"));
  if (sub) (sub as HTMLButtonElement).click();
});
await new Promise((r) => setTimeout(r, 2500));
await snap("04-subscriptions-page", 500);

// 6. Open category dropdown — find button containing "categories" text
console.log("6. Category dropdown...");
const catClicked = await page.evaluate(() => {
  const btns = Array.from(document.querySelectorAll("button"));
  const cat = btns.find(b => b.textContent?.includes("categories"));
  if (cat) { (cat as HTMLButtonElement).click(); return true; }
  return false;
});
if (catClicked) {
  await snap("05-category-dropdown-open", 600);
  // Close by clicking outside
  await page.evaluate(() => document.body.click());
  await new Promise((r) => setTimeout(r, 400));
} else {
  console.log("   (not found)");
}

// 7. Open sort dropdown — find button containing "Most data" or "Most tasks"
console.log("7. Sort dropdown...");
const sortClicked = await page.evaluate(() => {
  const btns = Array.from(document.querySelectorAll("button"));
  const sort = btns.find(b => /Most data|Most tasks/.test(b.textContent || ""));
  if (sort) { (sort as HTMLButtonElement).click(); return true; }
  return false;
});
if (sortClicked) {
  await snap("06-sort-dropdown-open", 600);
  await page.evaluate(() => document.body.click());
  await new Promise((r) => setTimeout(r, 400));
} else {
  console.log("   (not found)");
}

// 8. Full page
console.log("8. Full page...");
await page.screenshot({ path: join(OUTPUT, "07-full-page.png"), fullPage: true });
console.log("  ✓ 07-full-page.png");

await browser.close();
console.log("\nDone! All screenshots in tests-results/ux/minor-fix/");
