import React from "react";
import { supabase } from "../../lib/supabase";
import { ENV } from "../../lib/env";
import { THEME } from "../../lib/config";

const btnCls =
  "w-full py-2.5 px-4 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm font-medium flex items-center justify-center gap-2 hover:bg-gray-50 disabled:opacity-50 transition-colors";

export type OAuthButtonsProps = {
  returnTo?: string;
  onError?: (message: string) => void;
};

export async function startGitHubOAuth(returnTo: string): Promise<string | null> {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "github",
    options: { redirectTo: `${window.location.origin}${returnTo}` },
  });
  return error ? error.message : null;
}

export function startHuggingFaceOAuth(returnTo: string): void {
  const url = `${ENV.API_URL}/v1/auth/huggingface/start?return_to=${encodeURIComponent(returnTo)}`;
  window.location.href = url;
}

const GitHubIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58 0-.29-.01-1.04-.02-2.04-3.34.72-4.04-1.61-4.04-1.61-.55-1.38-1.34-1.75-1.34-1.75-1.09-.75.08-.73.08-.73 1.21.09 1.85 1.24 1.85 1.24 1.07 1.84 2.81 1.31 3.5 1 .11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.17 0 0 1.01-.32 3.3 1.23.96-.27 1.98-.4 3-.41 1.02.01 2.04.14 3 .41 2.29-1.55 3.3-1.23 3.3-1.23.66 1.65.25 2.87.12 3.17.77.84 1.24 1.91 1.24 3.22 0 4.61-2.8 5.62-5.48 5.92.43.37.81 1.1.81 2.22 0 1.61-.01 2.9-.01 3.29 0 .32.22.7.83.58C20.56 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
  </svg>
);

const HuggingFaceIcon = () => (
  <img src="/icons/huggingface.svg" alt="" width={20} height={20} aria-hidden="true" />
);

export function OAuthButtons({ returnTo = "/auth/callback", onError }: OAuthButtonsProps) {
  const [loading, setLoading] = React.useState<"github" | "huggingface" | null>(null);

  async function handleGitHub() {
    setLoading("github");
    const err = await startGitHubOAuth(returnTo);
    if (err) {
      setLoading(null);
      onError?.(err);
    }
    // On success, browser is navigating away; no state change needed.
  }

  function handleHuggingFace() {
    setLoading("huggingface");
    startHuggingFaceOAuth(returnTo);
  }

  return (
    <div className="space-y-2.5">
      <button
        type="button"
        onClick={handleGitHub}
        disabled={loading !== null}
        className={btnCls}
        style={{
          color: THEME.textPrimary,
          opacity: loading && loading !== "github" ? 0.5 : 1,
        }}
        aria-label="Continue with GitHub"
      >
        <GitHubIcon />
        <span>{loading === "github" ? "Redirecting…" : "Continue with GitHub"}</span>
      </button>
      <button
        type="button"
        onClick={handleHuggingFace}
        disabled={loading !== null}
        className={btnCls}
        style={{
          color: THEME.textPrimary,
          opacity: loading && loading !== "huggingface" ? 0.5 : 1,
        }}
        aria-label="Continue with HuggingFace"
      >
        <HuggingFaceIcon />
        <span>
          {loading === "huggingface" ? "Redirecting…" : "Continue with HuggingFace"}
        </span>
      </button>
    </div>
  );
}

export function OAuthDivider() {
  return (
    <div className="flex items-center gap-3 my-4">
      <div className="flex-1 h-px" style={{ background: THEME.border }} />
      <span className="text-xs uppercase tracking-wider" style={{ color: THEME.textMuted }}>
        or
      </span>
      <div className="flex-1 h-px" style={{ background: THEME.border }} />
    </div>
  );
}
