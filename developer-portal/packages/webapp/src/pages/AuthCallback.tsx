import React, { useEffect, useState } from "react";
import { navigate } from "../App";
import { supabase } from "../lib/supabase";
import { apiFetch } from "../lib/api";
import { BRAND, THEME } from "../lib/config";

type AutoJoinInfo = { orgName: string };

function WelcomeModal({ orgName, onContinue }: { orgName: string; onContinue: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4"
      style={{ background: "rgba(27, 16, 52, 0.5)" }}>
      <div
        className="w-full max-w-sm bg-white border-[1.5px] border-[#1B1034] rounded-none shadow-2xl overflow-hidden"
        style={{ animation: "fadeSlideUp 0.25s ease" }}
      >
        {/* Accent strip */}
        <div className="h-1.5 w-full" style={{ background: "linear-gradient(90deg, #834DFB, #1B1034)" }} />

        <div className="px-8 pt-8 pb-7 text-center">
          {/* Icon */}
          <div className="w-16 h-16 rounded-full mx-auto mb-5 flex items-center justify-center text-3xl"
            style={{ background: THEME.accentLight }}>
            🎉
          </div>

          <h2 className="text-xl font-semibold mb-2" style={{ color: THEME.textPrimary }}>
            You're in!
          </h2>
          <p className="text-sm leading-relaxed mb-1" style={{ color: THEME.textSecondary }}>
            Your email matched the{" "}
            <span className="font-semibold" style={{ color: THEME.accent }}>{orgName}</span>{" "}
            workspace.
          </p>
          <p className="text-sm leading-relaxed mb-7" style={{ color: THEME.textMuted }}>
            You've been added as a member — no setup required.
          </p>

          <button
            onClick={onContinue}
            className="w-full py-2.5 text-sm font-medium text-white rounded-none transition-colors"
            style={{ background: THEME.btnBg }}
            onMouseOver={e => (e.currentTarget.style.background = THEME.btnHover)}
            onMouseOut={e => (e.currentTarget.style.background = THEME.btnBg)}
          >
            Go to dashboard
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

export function AuthCallback() {
  const [error, setError] = useState("");
  const [autoJoin, setAutoJoin] = useState<AutoJoinInfo | null>(null);

  useEffect(() => {
    async function handle() {
      const { data: { session }, error: err } = await supabase.auth.getSession();
      if (err || !session) {
        setError(err?.message || "No session found. Please sign in again.");
        return;
      }
      localStorage.setItem("access_token", session.access_token);

      try {
        const res = await apiFetch<{ user: { org_id: string | null; org_name: string | null; auto_joined: boolean } }>(
          "/v1/auth/sync-profile",
          { method: "POST" }
        );
        const { org_id, org_name, auto_joined } = res.user;

        if (org_id && auto_joined && org_name) {
          // Show welcome popup — user will dismiss and navigate themselves
          setAutoJoin({ orgName: org_name });
        } else if (org_id) {
          navigate("/dashboard");
        } else {
          navigate("/onboarding");
        }
      } catch {
        // If sync-profile fails, fall through to onboarding
        navigate("/onboarding");
      }
    }
    handle();
  }, []);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4" style={{ background: THEME.bg }}>
        <div className="w-full max-w-sm text-center">
          <img src={BRAND.logo} alt={BRAND.name} className="h-8 w-auto mb-8 mx-auto" />
          <h1 className="text-xl font-semibold mb-2" style={{ color: THEME.textPrimary }}>Verification failed</h1>
          <p className="text-sm mb-4" style={{ color: THEME.textMuted }}>{error}</p>
          <button onClick={() => navigate("/auth/signin")} className="text-sm font-medium" style={{ color: THEME.accent }}>
            Back to sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: THEME.bg }}>
      <p className="text-sm" style={{ color: THEME.textMuted }}>Verifying your email...</p>
      {autoJoin && (
        <WelcomeModal
          orgName={autoJoin.orgName}
          onContinue={() => navigate("/dashboard")}
        />
      )}
    </div>
  );
}
