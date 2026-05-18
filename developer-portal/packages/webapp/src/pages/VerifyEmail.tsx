import React, { useEffect, useState } from "react";
import { navigate } from "../App";
import { supabase } from "../lib/supabase";
import { BRAND, THEME } from "../lib/config";

const RESEND_COOLDOWN = 60; // seconds

export function VerifyEmail() {
  const params = new URLSearchParams(window.location.search);
  const email = params.get("email") || "";
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const id = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(id);
  }, [cooldown]);

  async function handleResend() {
    if (!email || cooldown > 0) return;
    setResending(true);
    await supabase.auth.resend({ type: "signup", email });
    setResending(false);
    setResent(true);
    setCooldown(RESEND_COOLDOWN);
    setTimeout(() => setResent(false), 5000);
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: THEME.bg }}>
      <div className="w-full max-w-sm text-center">
        <img src={BRAND.logo} alt={BRAND.name} className="h-8 w-auto mb-8 mx-auto" />
        <div className="text-4xl mb-4">&#9993;</div>
        <h1 className="text-2xl font-semibold mb-2" style={{ color: THEME.textPrimary }}>Check your email</h1>
        <p className="text-sm mb-1" style={{ color: THEME.textMuted }}>
          We sent a verification link to{" "}
          {email ? <strong style={{ color: THEME.textPrimary }}>{email}</strong> : "your email"}.
          Click the link to continue.
        </p>
        <p className="text-xs mb-6" style={{ color: THEME.textMuted }}>
          Sent from <span style={{ color: THEME.textSecondary }}>noreply@humanbased.ai</span>
          {" "}— check your spam folder if it doesn't arrive within 2 minutes.
        </p>

        <div className="text-left border rounded-none p-4 mb-6 space-y-2" style={{ borderColor: THEME.border }}>
          <p className="text-xs font-medium mb-1" style={{ color: THEME.textSecondary }}>What happens next</p>
          {[
            "Verify your email",
            "Set up your organization",
            "Get your API key",
          ].map((step, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-medium shrink-0 ${i === 0 ? "text-white" : "border"}`}
                style={i === 0 ? { background: THEME.accent } : { borderColor: THEME.border, color: THEME.textMuted }}>
                {i + 1}
              </div>
              <span className="text-xs" style={{ color: i === 0 ? THEME.textPrimary : THEME.textMuted }}>{step}</span>
            </div>
          ))}
        </div>

        <button
          onClick={handleResend}
          disabled={resending || cooldown > 0}
          className="w-full py-2.5 text-sm font-medium rounded-none border-[1.5px] disabled:opacity-50 mb-3"
          style={{ borderColor: THEME.textPrimary, color: THEME.textPrimary }}
        >
          {resent
            ? "Email resent!"
            : resending
            ? "Resending..."
            : cooldown > 0
            ? `Resend in ${cooldown}s`
            : "Resend verification email"}
        </button>

        <div className="flex justify-center gap-4 text-sm">
          <button onClick={() => navigate("/auth/signup")} style={{ color: THEME.textMuted }}>
            Wrong email?
          </button>
          <span style={{ color: THEME.border }}>·</span>
          <button onClick={() => navigate("/auth/signin")} style={{ color: THEME.accent }}>
            Back to sign in
          </button>
        </div>
      </div>
    </div>
  );
}
