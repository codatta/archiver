#!/usr/bin/env node
/**
 * Capture UX screenshot for the onboarding "Get Started" step (IN-47).
 *
 * Renders the standalone preview.html which shows onboarding step 3
 * with two illustrated action cards (Browse datasets, Create API key).
 *
 * Usage: node ux-tests/onboarding-get-started/capture.mjs
 * No running webapp needed — uses the self-contained preview.html.
 */
import puppeteer from "../../packages/webapp/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = __dirname;
const PREVIEW = join(__dirname, "preview.html");

const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 800, deviceScaleFactor: 2 });

console.log("  capturing get-started step...");
await page.goto(`file://${PREVIEW}`, { waitUntil: "networkidle0", timeout: 10000 });
// Wait for images to load
await page.waitForFunction(() => {
  const imgs = document.querySelectorAll("img");
  return Array.from(imgs).every((img) => img.complete && img.naturalHeight > 0);
}, { timeout: 5000 }).catch(() => {});

await page.screenshot({
  path: join(OUT, "get-started.png"),
  fullPage: true,
});
console.log("  \u2713 get-started.png saved");

await browser.close();
console.log("\nDone \u2014 screenshot saved to ux-tests/onboarding-get-started/");
