#!/usr/bin/env bun
/**
 * Capture UX screenshots for the password strength module.
 *
 * Renders the module's components (StrengthMeter + PasswordRules + match
 * indicator) via react-dom/server into a standalone preview HTML page,
 * then uses Puppeteer to snapshot each state.
 *
 * Usage: bun packages/webapp/scripts/capture-password-strength.mjs
 * No dev server required — pure SSR. Output lands in ux-tests/password-strength/.
 */
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import puppeteer from "puppeteer";

import { validatePassword } from "../src/lib/password/rules.ts";
import { PasswordRules } from "../src/lib/password/PasswordRules.tsx";
import { StrengthMeter } from "../src/lib/password/StrengthMeter.tsx";

const __dirname = dirname(fileURLToPath(import.meta.url));
// __dirname = packages/webapp/scripts — output to <repo>/ux-tests/password-strength
const OUT = join(__dirname, "..", "..", "..", "ux-tests", "password-strength");
mkdirSync(OUT, { recursive: true });

const tailwindCss = readFileSync(
  join(__dirname, "..", "src", "tailwind.out.css"),
  "utf8",
);

const inputCls =
  "w-full px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400";

function Field({
  label,
  value,
  type = "password",
  showToggle = true,
  toggleState = "Show",
  match,
}) {
  return React.createElement(
    "div",
    null,
    React.createElement(
      "label",
      { className: "block text-sm font-medium mb-1.5 text-[#1B1034]" },
      label,
    ),
    React.createElement(
      "div",
      { className: "relative" },
      React.createElement("input", {
        type,
        value,
        readOnly: true,
        className: inputCls + " pr-14",
      }),
      showToggle &&
        React.createElement(
          "button",
          {
            type: "button",
            className:
              "absolute inset-y-0 right-3 flex items-center text-xs font-medium text-gray-500",
          },
          toggleState,
        ),
    ),
    match &&
      React.createElement(
        "p",
        {
          className:
            "mt-1.5 text-xs " +
            (match.state === "match"
              ? "text-emerald-600"
              : match.state === "mismatch"
                ? "text-red-500"
                : "text-gray-400"),
        },
        match.text,
      ),
  );
}

function Panel({ title, password, confirm, matchState, matchText, isDirty }) {
  const v = validatePassword(password);
  return React.createElement(
    "section",
    {
      className:
        "mb-10 p-6 border-[1.5px] border-[#1B1034] bg-white rounded-none",
    },
    React.createElement(
      "h2",
      { className: "text-sm font-semibold mb-4 text-[#834DFB]" },
      title,
    ),
    React.createElement(
      "div",
      { className: "space-y-4" },
      React.createElement(
        "div",
        null,
        React.createElement(Field, {
          label: "Password",
          value: password,
          toggleState: "Show",
        }),
        React.createElement(StrengthMeter, { score: v.score }),
        React.createElement(PasswordRules, { validation: v, isDirty }),
      ),
      confirm !== undefined &&
        React.createElement(Field, {
          label: "Confirm password",
          value: confirm,
          match: matchState
            ? { state: matchState, text: matchText }
            : undefined,
        }),
    ),
  );
}

const panels = [
  {
    title: "State 1 — Empty (idle)",
    password: "",
    confirm: undefined,
    isDirty: false,
  },
  {
    title: "State 2 — Weak (typing, 2 rules pass)",
    password: "abc",
    confirm: undefined,
    isDirty: true,
  },
  {
    title: "State 3 — Fair (4 rules pass)",
    password: "Abc12345",
    confirm: undefined,
    isDirty: true,
  },
  {
    title: "State 4 — Strong (all rules pass, confirm mismatch)",
    password: "Abcdef1!X0",
    confirm: "Abcdef1!XX",
    matchState: "mismatch",
    matchText: "Passwords do not match",
    isDirty: true,
  },
  {
    title: "State 5 — Strong, matching (submit enabled)",
    password: "Abcdef1!X0",
    confirm: "Abcdef1!X0",
    matchState: "match",
    matchText: "Passwords match",
    isDirty: true,
  },
];

const body = panels
  .map((p) => renderToStaticMarkup(React.createElement(Panel, p)))
  .join("\n");

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Password strength module — preview</title>
<style>${tailwindCss}</style>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #F5F1EA; padding: 40px 20px; }
  .preview { max-width: 440px; margin: 0 auto; }
  h1 { color: #1B1034; font-size: 20px; font-weight: 600; margin-bottom: 24px; }
</style>
</head>
<body>
<div class="preview">
<h1>Password strength module — states</h1>
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
await page.setViewport({ width: 520, height: 900, deviceScaleFactor: 2 });
await page.goto("file://" + htmlPath, { waitUntil: "networkidle0" });

// Full-page screenshot of all states
await page.screenshot({
  path: join(OUT, "all-states.png"),
  fullPage: true,
});
console.log("✓ all-states.png saved");

// Per-state crops via element screenshots
const sections = await page.$$("section");
for (let i = 0; i < sections.length; i++) {
  const name = `state-${i + 1}.png`;
  await sections[i].screenshot({ path: join(OUT, name) });
  console.log(`✓ ${name} saved`);
}

await browser.close();
console.log("\nDone — screenshots saved to ux-tests/password-strength/");
