#!/usr/bin/env node
/**
 * Capture UX screenshots for the OAuth sign-in feature.
 *
 * Captures the Sign In and Sign Up pages showing the new GitHub +
 * HuggingFace OAuth buttons above the email form.
 *
 * Usage: node ux-tests/oauth-signin/capture.mjs
 * Requires: webapp running at localhost:3000
 */
import puppeteer from "../../packages/webapp/node_modules/puppeteer/lib/esm/puppeteer/puppeteer.js";
import { mkdir } from "fs/promises";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = __dirname; // ux-tests/oauth-signin/
const BASE = "http://localhost:3000";

await mkdir(OUT, { recursive: true });

const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 800, deviceScaleFactor: 2 });

async function shot(name, url, opts = {}) {
  console.log(`  capturing ${name}...`);
  await page.goto(url, { waitUntil: "networkidle2", timeout: 15000 }).catch(() => {});
  if (opts.delay) await new Promise((r) => setTimeout(r, opts.delay));
  await page.screenshot({
    path: join(OUT, `${name}.png`),
    fullPage: opts.fullPage || false,
  });
  console.log(`  ✓ ${name}.png saved`);
}

// Sign-in page — shows GitHub + HuggingFace buttons + "or" divider + email form
await shot("signin-page", `${BASE}/auth/signin`, { delay: 800 });

// Sign-up page (step 1: email) — shows GitHub + HuggingFace buttons + "or" divider + email form
await shot("signup-page", `${BASE}/auth/signup`, { delay: 800 });

await browser.close();
console.log("\nDone — screenshots saved to ux-tests/oauth-signin/");
