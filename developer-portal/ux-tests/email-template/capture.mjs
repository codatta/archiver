#!/usr/bin/env node
/**
 * Capture UX screenshots for all branded email templates.
 *
 * Renders each HTML email sample and saves a PNG screenshot.
 * Usage: node ux-tests/email-template/capture.mjs
 */
import puppeteer from "../../packages/webapp/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js";
import { readdir } from "fs/promises";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = __dirname;

const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

const page = await browser.newPage();
await page.setViewport({ width: 680, height: 900, deviceScaleFactor: 2 });

const files = (await readdir(OUT)).filter((f) => f.endsWith(".html") && f !== "capture.mjs");
files.sort();

for (const file of files) {
  const name = file.replace(".html", "");
  console.log(`  capturing ${name}...`);
  await page.goto(`file://${join(OUT, file)}`, { waitUntil: "networkidle0", timeout: 10000 }).catch(() => {});
  await new Promise((r) => setTimeout(r, 500));
  await page.screenshot({
    path: join(OUT, `${name}.png`),
    fullPage: true,
  });
  console.log(`  \u2713 ${name}.png`);
}

await browser.close();
console.log(`\nDone — ${files.length} screenshots saved to ux-tests/email-template/`);
