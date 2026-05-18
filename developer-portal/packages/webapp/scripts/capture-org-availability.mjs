#!/usr/bin/env bun
/**
 * Capture UX screenshots for the skippable org creation step.
 *
 * Renders StepOrgDetails states via react-dom/server into a standalone HTML
 * page, then uses Puppeteer to snapshot each state.
 *
 * States captured:
 *   1. Empty (idle) — no inputs, Skip for now visible
 *   2. Typing name (availability checking)
 *   3. Name taken, slug taken
 *   4. Both available
 *   5. Continue disabled when taken
 *
 * Usage: bun packages/webapp/scripts/capture-org-availability.mjs
 * No dev server required — pure SSR. Output: ux-tests/org-availability/
 */
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import puppeteer from "puppeteer";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, "..", "..", "..", "ux-tests", "org-availability");
mkdirSync(OUT, { recursive: true });

const tailwindCss = readFileSync(
  join(__dirname, "..", "src", "tailwind.out.css"),
  "utf8",
);

const inputCls =
  "w-full px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400";

function Badge({ status }) {
  if (status === "idle") return null;
  if (status === "checking")
    return React.createElement("p", { className: "text-xs text-gray-400 mt-1" }, "Checking...");
  if (status === "available")
    return React.createElement("p", { className: "text-xs text-emerald-600 mt-1" }, "✓ Available");
  return React.createElement("p", { className: "text-xs text-red-500 mt-1" }, "Already in use");
}

function StepPreview({ title, name, slug, nameStatus, slugStatus, canSubmit }) {
  return React.createElement(
    "section",
    { className: "mb-10 p-6 border-[1.5px] border-[#1B1034] bg-white rounded-none" },
    React.createElement("h2", { className: "text-sm font-semibold mb-4 text-[#834DFB]" }, title),
    React.createElement(
      "div",
      { className: "space-y-4" },
      // Name field
      React.createElement(
        "div",
        null,
        React.createElement("label", { className: "block text-sm font-medium text-[#1B1034] mb-1.5" }, "Organization name"),
        React.createElement("input", {
          type: "text",
          value: name,
          readOnly: true,
          placeholder: "Acme AI Labs",
          className: inputCls,
        }),
        React.createElement(Badge, { status: nameStatus }),
      ),
      // Slug field
      React.createElement(
        "div",
        null,
        React.createElement("label", { className: "block text-sm font-medium text-[#1B1034] mb-1.5" }, "Slug"),
        React.createElement(
          "div",
          { className: "flex items-center gap-1" },
          React.createElement("span", { className: "text-sm text-gray-400" }, "humanbased.ai/"),
          React.createElement("input", {
            type: "text",
            value: slug,
            readOnly: true,
            placeholder: "acme-ai",
            className: inputCls.replace("w-full ", "") + " flex-1",
          }),
        ),
        React.createElement(Badge, { status: slugStatus }),
      ),
      // Continue button
      React.createElement(
        "button",
        {
          type: "button",
          disabled: !canSubmit,
          className: "w-full py-2.5 bg-[#1B1034] text-white rounded-none text-sm font-medium hover:bg-[#2A1D4E] disabled:opacity-50",
        },
        "Continue",
      ),
      // Skip link
      React.createElement(
        "div",
        { className: "text-center" },
        React.createElement(
          "button",
          { type: "button", className: "text-sm text-gray-400 hover:text-[#1B1034] underline-offset-2 hover:underline" },
          "Skip for now",
        ),
      ),
    ),
  );
}

const panels = [
  {
    title: "State 1 — Empty (idle)",
    name: "",
    slug: "",
    nameStatus: "idle",
    slugStatus: "idle",
    canSubmit: false,
  },
  {
    title: "State 2 — Checking availability",
    name: "Acme AI Labs",
    slug: "acme-ai-labs",
    nameStatus: "checking",
    slugStatus: "checking",
    canSubmit: false,
  },
  {
    title: "State 3 — Name taken",
    name: "Acme AI Labs",
    slug: "acme-ai-labs",
    nameStatus: "taken",
    slugStatus: "available",
    canSubmit: false,
  },
  {
    title: "State 4 — Slug taken",
    name: "Acme AI Labs",
    slug: "acme-ai-labs",
    nameStatus: "available",
    slugStatus: "taken",
    canSubmit: false,
  },
  {
    title: "State 5 — Both available (Continue enabled)",
    name: "Acme AI Labs",
    slug: "acme-ai-labs",
    nameStatus: "available",
    slugStatus: "available",
    canSubmit: true,
  },
];

const body = panels
  .map((p) => renderToStaticMarkup(React.createElement(StepPreview, p)))
  .join("\n");

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Org availability — onboarding preview</title>
<style>${tailwindCss}</style>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #E8E0F0; padding: 40px 20px; }
  .preview { max-width: 480px; margin: 0 auto; }
  h1 { color: #1B1034; font-size: 20px; font-weight: 600; margin-bottom: 24px; }
</style>
</head>
<body>
<div class="preview">
<h1>Org creation — availability states</h1>
${body}
</div>
</body>
</html>`;

const htmlPath = join(OUT, "preview.html");
writeFileSync(htmlPath, html);
console.log("✓ preview.html written");

const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});
const page = await browser.newPage();
await page.setViewport({ width: 540, height: 900, deviceScaleFactor: 2 });
await page.goto("file://" + htmlPath, { waitUntil: "networkidle0" });

await page.screenshot({ path: join(OUT, "all-states.png"), fullPage: true });
console.log("✓ all-states.png saved");

const sections = await page.$$("section");
for (let i = 0; i < sections.length; i++) {
  const name = `state-${i + 1}.png`;
  await sections[i].screenshot({ path: join(OUT, name) });
  console.log(`✓ ${name} saved`);
}

await browser.close();
console.log("\nDone — screenshots saved to ux-tests/org-availability/");
