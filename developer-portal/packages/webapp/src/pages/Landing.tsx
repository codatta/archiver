import React from "react";
import { navigate } from "../App";
import { BRAND, THEME } from "../lib/config";

export function Landing() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: THEME.bg }}>
      <header className="flex items-center justify-between px-8 py-4" style={{ background: THEME.surface, borderBottom: `1.5px solid ${THEME.border}` }}>
        <img src={BRAND.logo} alt={BRAND.name} className="h-8 w-auto" />
        <div className="flex gap-3">
          <button onClick={() => navigate("/auth/signin")} className="px-4 py-2 text-sm" style={{ color: THEME.textSecondary }}>Sign In</button>
          <button onClick={() => navigate("/auth/signup")} className="px-5 py-2.5 text-sm text-white rounded-none font-medium" style={{ background: THEME.btnBg }}>Get Started</button>
        </div>
      </header>
      <main className="flex-1 flex flex-col items-center justify-center text-center px-4">
        <img src={BRAND.logo} alt={BRAND.name} className="h-16 mb-6" />
        <h1 className="text-5xl font-bold tracking-tight mb-4" style={{ color: THEME.textPrimary }}>{BRAND.name}</h1>
        <p className="text-lg max-w-md mb-8" style={{ color: THEME.textSecondary }}>Data API for crowd-sourced, quality-controlled data</p>
        <div className="flex gap-4">
          <button onClick={() => navigate("/auth/signup")} className="px-6 py-3 text-white rounded-none text-sm font-medium" style={{ background: THEME.btnBg }}>Get Started</button>
          <button onClick={() => window.open("https://docs.humanbased.ai", "_blank")} className="px-6 py-3 border rounded-none text-sm font-medium" style={{ borderColor: THEME.border, color: THEME.textSecondary }}>Documentation</button>
        </div>
      </main>
      <footer className="text-center py-4 text-xs" style={{ color: THEME.textMuted, borderTop: `1.5px solid ${THEME.border}` }}>
        All rights reserved by Codatta PTE LTD
      </footer>
    </div>
  );
}
