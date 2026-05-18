import React, { useState } from "react";
import { navigate } from "../App";
import { supabase } from "../lib/supabase";
import { BRAND, THEME } from "../lib/config";
import { OAuthButtons, OAuthDivider } from "../components/auth/OAuthButtons";

const inputCls = "w-full px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";

export function SignIn() {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [error, setError] = useState(""); const [loading, setLoading] = useState(false);

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault(); setError(""); setLoading(true);
    const { data, error: err } = await supabase.auth.signInWithPassword({ email, password });
    if (err) { setError(err.message); setLoading(false); return; }
    if (data.session) { localStorage.setItem("access_token", data.session.access_token); navigate("/dashboard"); }
    setLoading(false);
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: THEME.bg }}>
      <div className="w-full max-w-sm">
        <img src={BRAND.logo} alt={BRAND.name} className="h-8 w-auto mb-8" />
        <h1 className="text-2xl font-semibold mb-1" style={{ color: THEME.textPrimary }}>Sign in</h1>
        <p className="text-sm mb-6" style={{ color: THEME.textMuted }}>Welcome back to {BRAND.name}</p>
        <OAuthButtons returnTo="/auth/callback" onError={setError} />
        <OAuthDivider />
        <form onSubmit={handleSubmit} className="space-y-4">
          <div><label className="block text-sm font-medium mb-1.5" style={{ color: THEME.textPrimary }}>Email</label><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className={inputCls} /></div>
          <div><label className="block text-sm font-medium mb-1.5" style={{ color: THEME.textPrimary }}>Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className={inputCls} /></div>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button type="button" onClick={() => handleSubmit()} disabled={loading} className="w-full py-2.5 text-white rounded-none text-sm font-medium disabled:opacity-50" style={{ background: THEME.btnBg }}>{loading ? "Signing in..." : "Sign in"}</button>
        </form>
        <p className="text-sm mt-6 text-center" style={{ color: THEME.textMuted }}>Don't have an account? <button onClick={() => navigate("/auth/signup")} className="font-medium" style={{ color: THEME.accent }}>Sign up</button></p>
      </div>
    </div>
  );
}
