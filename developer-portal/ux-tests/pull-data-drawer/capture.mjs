#!/usr/bin/env node
/**
 * Capture UX screenshots for the Pull Data drawer (IN-66).
 *
 * Renders a self-contained preview.html showing all 3 key states:
 *   State 1 — No API key (full gate)
 *   State 2 — Keys exist but none scoped (warning banner + Run)
 *   State 3 — Accessible key (Run + curl snippet + result preview)
 *
 * Usage: node ux-tests/pull-data-drawer/capture.mjs
 * No running dev server required.
 */
import puppeteer from "../../packages/webapp/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js";
import { mkdir } from "fs/promises";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = __dirname;

await mkdir(OUT, { recursive: true });

const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 800, deviceScaleFactor: 2 });

const previewUrl = `file://${join(OUT, "preview.html")}`;
await page.goto(previewUrl, { waitUntil: "networkidle0", timeout: 10000 });

// Full-page overview with all 3 states
console.log("  capturing all-states...");
await page.screenshot({
  path: join(OUT, "all-states.png"),
  fullPage: true,
});
console.log("  ✓ all-states.png saved");

// Individual state screenshots
for (const id of ["state-1", "state-2", "state-3"]) {
  console.log(`  capturing ${id}...`);
  const el = await page.$(`#${id}`);
  if (el) {
    await el.screenshot({ path: join(OUT, `${id}.png`) });
    console.log(`  ✓ ${id}.png saved`);
  } else {
    console.error(`  ✗ #${id} not found`);
  }
}

await browser.close();
console.log("\nDone — screenshots saved to ux-tests/pull-data-drawer/");
