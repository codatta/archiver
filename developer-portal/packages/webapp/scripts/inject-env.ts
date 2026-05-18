/**
 * Post-build script: generates dist/env.js from environment variables
 * and injects <script src="/env.js"> into dist/index.html.
 *
 * Only public/publishable values — never secrets.
 *
 * NOTE: API_URL intentionally has no hardcoded fallback. When not set,
 * env.js omits it and the client-side env.ts uses hostname-based detection
 * (staging.* → staging API, otherwise → production API). This prevents
 * staging deployments from silently hitting the production API.
 */
const clientEnv: Record<string, string> = {
  SUPABASE_URL:             process.env.SUPABASE_URL             ?? "https://uxafdddzhgdhsabkwmgw.supabase.co",
  SUPABASE_PUBLISHABLE_KEY: process.env.SUPABASE_PUBLISHABLE_KEY ?? "sb_publishable_OgL0DMwL6JattvbkLG1HBw_-pR9k7mJ",
};
// Only include API_URL in env.js if explicitly set — otherwise let client-side hostname detection handle it
if (process.env.API_URL) {
  clientEnv.API_URL = process.env.API_URL;
}

import { fileURLToPath } from "node:url";
const distDir = fileURLToPath(new URL("../dist/", import.meta.url)) + "/";

// 1. Write dist/env.js
await Bun.write(`${distDir}env.js`, `window.__ENV__=${JSON.stringify(clientEnv)};`);

// 2. Inject <script src="/env.js"> into dist/index.html before the first <script>
const htmlPath = `${distDir}index.html`;
const html = await Bun.file(htmlPath).text();
const patched = html.replace(
  /<script /,
  '<script src="/env.js"></script>\n  <script ',
);
await Bun.write(htmlPath, patched);

console.log(`[inject-env] Generated dist/env.js with API_URL=${clientEnv.API_URL ?? "(not set — client will use hostname detection)"}`);

