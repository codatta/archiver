import index from "./index.html";
import { join } from "path";

const publicDir = join(import.meta.dir, "../public");

const logoFile = Bun.file(join(publicDir, "assets/company-logo.png"));
const hfIconFile = Bun.file(join(publicDir, "icons/huggingface.svg"));

// Client-safe env vars — only public/publishable values, never secrets.
// API_URL has no hardcoded fallback — it must be set via .env or process env
// to prevent staging from silently hitting production.
if (!process.env.API_URL) {
  console.warn("[server] WARNING: API_URL is not set. Defaulting to http://localhost:8000. Set API_URL in .env for staging/production.");
}
const clientEnv = {
  API_URL:                  process.env.API_URL                  ?? "http://localhost:8000",
  SUPABASE_URL:             process.env.SUPABASE_URL             ?? "https://uxafdddzhgdhsabkwmgw.supabase.co",
  SUPABASE_PUBLISHABLE_KEY: process.env.SUPABASE_PUBLISHABLE_KEY ?? "sb_publishable_OgL0DMwL6JattvbkLG1HBw_-pR9k7mJ",
};

const envJs = new Response(
  `window.__ENV__=${JSON.stringify(clientEnv)};`,
  { headers: { "Content-Type": "application/javascript", "Cache-Control": "no-cache" } },
);

Bun.serve({
  port: Number(process.env.PORT ?? 3000),
  routes: {
    "/env.js": () => envJs.clone(),
    "/assets/company-logo.png": new Response(logoFile, {
      headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=86400" },
    }),
    "/icons/huggingface.svg": new Response(hfIconFile, {
      headers: { "Content-Type": "image/svg+xml", "Cache-Control": "public, max-age=86400" },
    }),
    "/*": index,
  },
  development: {
    hmr: true,
    console: true,
  },
});

console.log(`Webapp running at http://localhost:${process.env.PORT ?? 3000}`);
console.log(`  API_URL → ${clientEnv.API_URL}`);
