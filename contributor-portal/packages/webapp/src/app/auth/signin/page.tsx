"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { OAuthButtons } from "@/components/auth/oauth-buttons";
import { OtpInput } from "@/components/auth/otp-input";
import { BRAND } from "@/lib/config";
import { createClient } from "@/lib/supabase/client";
import { AUTH_COPY, mapOtpError } from "@/lib/auth/copy";
import { useResendCooldown } from "@/hooks/useResendCooldown";

type Mode = "password" | "otp";
type OtpStage = "idle" | "code_sent" | "verifying";

export default function SignInPage() {
  const [mode, setMode] = useState<Mode>("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpStage, setOtpStage] = useState<OtpStage>("idle");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { remaining, start } = useResendCooldown(60);

  async function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    window.location.href = "/contribute";
  }

  async function handleSendOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error: otpError } = await supabase.auth.signInWithOtp({
      email,
      options: { shouldCreateUser: false },
    });

    setLoading(false);
    if (otpError) {
      setError(mapOtpError(otpError.message));
      return;
    }

    setOtpStage("code_sent");
    start();
  }

  async function handleVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setOtpStage("verifying");

    const supabase = createClient();
    const { error: verifyError } = await supabase.auth.verifyOtp({
      email,
      token: otp,
      type: "email",
    });

    if (verifyError) {
      setError(mapOtpError(verifyError.message));
      setOtpStage("code_sent");
      setLoading(false);
      return;
    }

    window.location.href = "/contribute";
  }

  async function handleResend() {
    if (remaining > 0 || loading) return;
    setError(null);
    const supabase = createClient();
    const { error: otpError } = await supabase.auth.signInWithOtp({
      email,
      options: { shouldCreateUser: false },
    });
    if (otpError) {
      setError(mapOtpError(otpError.message));
      return;
    }
    start();
  }

  function switchMode(next: Mode) {
    setMode(next);
    setError(null);
    setOtp("");
    setOtpStage("idle");
  }

  const inputClass =
    "w-full px-5 py-3 border-[1.5px] border-[#1B1034] bg-white text-sm text-[#1B1034] placeholder:text-gray-400 focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10 outline-none transition";

  const primaryButtonClass =
    "w-full py-2.5 bg-[#1B1034] text-white text-[13px] font-medium hover:bg-[#2D2250] transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer";

  return (
    <>
      <Image
        src={BRAND.logo}
        alt={BRAND.name}
        width={36}
        height={36}
        className="w-9 h-9"
      />

      <h1 className="text-[22px] font-semibold text-[#1B1034] mt-6">Sign in</h1>
      <p className="text-[13px] text-gray-500 mt-1">
        Welcome back to Contributor Kitchen of Humanbased.
      </p>

      <div className="mt-7">
        <OAuthButtons mode="signin" />
      </div>

      <div className="flex items-center gap-4 my-5">
        <div className="flex-1 h-px bg-gray-300" />
        <span className="text-[11px] text-gray-400 tracking-widest font-medium">
          OR
        </span>
        <div className="flex-1 h-px bg-gray-300" />
      </div>

      {/* Mode tabs */}
      <div
        role="tablist"
        aria-label="Sign-in method"
        className="flex border-[1.5px] border-[#1B1034] mb-4"
      >
        <button
          type="button"
          role="tab"
          aria-selected={mode === "password"}
          onClick={() => switchMode("password")}
          className={`flex-1 py-2 text-[13px] font-medium transition cursor-pointer ${
            mode === "password"
              ? "bg-[#1B1034] text-white"
              : "bg-white text-[#1B1034] hover:bg-gray-50"
          }`}
        >
          Password
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "otp"}
          onClick={() => switchMode("otp")}
          className={`flex-1 py-2 text-[13px] font-medium border-l-[1.5px] border-[#1B1034] transition cursor-pointer ${
            mode === "otp"
              ? "bg-[#1B1034] text-white"
              : "bg-white text-[#1B1034] hover:bg-gray-50"
          }`}
        >
          Email code
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 p-3 mb-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {mode === "password" && (
        <form onSubmit={handlePasswordSubmit} className="space-y-3.5">
          <div>
            <label
              htmlFor="email"
              className="block text-[13px] font-medium text-[#1B1034] mb-1.5"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label
                htmlFor="password"
                className="block text-[13px] font-medium text-[#1B1034]"
              >
                Password
              </label>
              <Link
                href="/auth/reset-password"
                className="text-[12px] text-[#834DFB] hover:underline"
              >
                Forgot password?
              </Link>
            </div>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          <button type="submit" disabled={loading} className={primaryButtonClass}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      )}

      {mode === "otp" && otpStage === "idle" && (
        <form onSubmit={handleSendOtp} className="space-y-3.5">
          <div>
            <label
              htmlFor="otp-email"
              className="block text-[13px] font-medium text-[#1B1034] mb-1.5"
            >
              Email
            </label>
            <input
              id="otp-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          <button type="submit" disabled={loading || !email} className={primaryButtonClass}>
            {loading ? "Sending..." : AUTH_COPY.otpSendButton}
          </button>
        </form>
      )}

      {mode === "otp" && otpStage !== "idle" && (
        <form onSubmit={handleVerifyOtp} className="space-y-5">
          <p className="text-[13px] text-gray-500">We sent a code to {email}</p>

          <div>
            <label className="block text-[13px] font-medium text-[#1B1034] mb-3">
              Verification code
            </label>
            <OtpInput value={otp} onChange={setOtp} />
          </div>

          <button
            type="submit"
            disabled={loading || otp.length < 6}
            className={primaryButtonClass}
          >
            {loading ? "Verifying..." : "Verify code"}
          </button>

          <div className="text-center space-y-1">
            <p className="text-[13px] text-gray-500">
              Didn&apos;t receive it?{" "}
              {remaining > 0 ? (
                <span className="text-gray-400">
                  {AUTH_COPY.otpResendCooldown(remaining)}
                </span>
              ) : (
                <button
                  type="button"
                  onClick={handleResend}
                  className="text-[#834DFB] hover:underline font-medium cursor-pointer"
                >
                  {AUTH_COPY.otpResendButton}
                </button>
              )}
            </p>
            <button
              type="button"
              onClick={() => switchMode("otp")}
              className="text-[13px] text-[#834DFB] hover:underline cursor-pointer"
            >
              Wrong email? Go back
            </button>
          </div>
        </form>
      )}

      <p className="text-[13px] text-gray-500 text-center mt-5">
        Don&apos;t have an account?{" "}
        <Link
          href="/auth/signup"
          className="text-[#834DFB] hover:underline font-medium"
        >
          Sign up
        </Link>
      </p>

      <p className="text-[11px] text-gray-400 text-center mt-10">
        &copy; 2026 Codatta PTE LTD.
      </p>
    </>
  );
}
