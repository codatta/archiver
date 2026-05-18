import React from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import "@flaticon/flaticon-uicons/css/solid/straight.css";
import { App } from "./App";

// Load runtime env vars before rendering.
// In Vercel builds, env.js is already in the HTML (injected post-build).
// In local dev, it's served dynamically by server.ts.
function loadEnv(): Promise<void> {
  return new Promise((resolve) => {
    if (window.__ENV__) { resolve(); return; }
    const s = document.createElement("script");
    s.src = "/env.js";
    s.onload = () => resolve();
    s.onerror = () => resolve(); // fall through to hardcoded defaults
    document.head.appendChild(s);
  });
}

loadEnv().then(() => {
  const root = createRoot(document.getElementById("root")!);
  root.render(<App />);
});
