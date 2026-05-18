"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { OAuthButtons } from "@/components/auth/oauth-buttons";
import { StepIndicator } from "@/components/auth/step-indicator";
import { OtpInput } from "@/components/auth/otp-input";
import { createClient } from "@/lib/supabase/client";
import { PasswordInput, isPasswordValid } from "@/components/auth/password-input";
import { BRAND } from "@/lib/config";
import { AUTH_COPY, mapOtpError } from "@/lib/auth/copy";
import { useResendCooldown } from "@/hooks/useResendCooldown";

type Mode = "password" | "otp";
type OtpStep = 1 | 2 | 3;

export default function SignUpPage() {
  const [mode, setMode] = useState<Mode>("password");
  const [step, setStep] = useState<OtpStep>(1);
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [usernameAvailable, setUsernameAvailable] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { remaining, start } = useResendCooldown(60);

  useEffect(() => {
    if (username.length < 3) return;
    const t = setTimeout(() => {
      setUsernameAvailable(username !== "taken");
    }, 400);
    return () => clearTimeout(t);
  }, [username]);

  function switchMode(next: Mode) {
    setMode(next);
    setError(null);
    setStep(1);
    setOtp("");
  }

  // ── Password mode (direct signUp) ─────────────────────────────────────────
  async function handlePasswordSignUp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!isPasswordValid(password)) return;
    if (usernameAvailable === false) return;
    setLoading(true);

    const supabase = createClient();
    const { error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: name, username } },
    });

    if (signUpError) {
      setError(signUpError.message);
      setLoading(false);
      return;
    }

    window.location.href = "/onboarding";
  }

  // ── OTP mode (existing 3-step flow) ───────────────────────────────────────
  async function handleSendOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();
    const { error: otpError } = await supabase.auth.signInWithOtp({ email });
    if (otpError) {
      setError(mapOtpError(otpError.message));
      setLoading(false);
      return;
    }
    setLoading(false);
    setStep(2);
    start();
  }

  async function handleVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();
    const { error: verifyError } = await supabase.auth.verifyOtp({
      email,
      token: otp,
      type: "email",
    });
    if (verifyError) {
      setError(mapOtpError(verifyError.message));
      setLoading(false);
      return;
    }
    setLoading(false);
    setStep(3);
  }

  async function handleCreateAccount(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!isPasswordValid(password)) return;
    setLoading(true);
    const supabase = createClient();
    const { error: updateError } = await supabase.auth.updateUser({
      password,
      data: { full_name: name, username },
    });
    if (updateError) {
      setError(updateError.message);
      setLoading(false);
      return;
    }
    window.location.href = "/onboarding";
  }

  async function handleResendOtp() {
    if (remaining > 0 || loading) return;
    setError(null);
    const supabase = createClient();
    const { error: otpError } = await supabase.auth.signInWithOtp({ email });
    if (otpError) {
      setError(mapOtpError(otpError.message));
      return;
    }
    start();
  }

  const inputClass =
    "w-full px-5 py-3 border-[1.5px] border-[#1B1034] bg-white text-sm text-[#1B1034] placeholder:text-gray-400 focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10 outline-none transition";

  const primaryButtonClass =
    "w-full py-2.5 bg-[#1B1034] text-white text-[13px] font-medium hover:bg-[#2D2250] transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer";

  const showProfileFields = mode === "password" || (mode === "otp" && step === 3);

  return (
    <>
      <Image
        src={BRAND.logo}
        alt={BRAND.name}
        width={36}
        height={36}
        className="w-9 h-9"
      />

      <h1 className="text-[22px] font-semibold text-[#1B1034] mt-6">
        {mode === "otp" && step === 2
          ? "Check your email"
          : mode === "otp" && step === 3
            ? "Set up your profile"
            : "Create your account"}
      </h1>
      <p className="text-[13px] text-gray-500 mt-1">
        {mode === "otp" && step === 2
          ? `We sent a code to ${email}`
          : mode === "otp" && step === 3
            ? "Almost there — just a few details"
            : "Join the Contributor Kitchen of Humanbased."}
      </p>

      {mode === "otp" && (
        <div className="mt-5 mb-6">
          <StepIndicator steps={3} current={step} />
        </div>
      )}

      {/* OAuth + mode toggle only on step 1 */}
      {(mode === "password" || step === 1) && (
        <>
          <div className={mode === "otp" ? "" : "mt-7"}>
            <OAuthButtons mode="signup" />
          </div>

          <div className="flex items-center gap-4 my-5">
            <div className="flex-1 h-px bg-gray-300" />
            <span className="text-[11px] text-gray-400 tracking-widest font-medium">
              OR
            </span>
            <div className="flex-1 h-px bg-gray-300" />
          </div>

          <div
            role="tablist"
            aria-label="Sign-up method"
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
        </>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 p-3 mb-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Password mode: single-form signup */}
      {mode === "password" && (
        <form onSubmit={handlePasswordSignUp} className="space-y-3.5">
          <div>
            <label htmlFor="email" className="block text-[13px] font-medium text-[#1B1034] mb-1.5">
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

          {showProfileFields && (
            <>
              <div>
                <label htmlFor="name" className="block text-[13px] font-medium text-[#1B1034] mb-1.5">
                  Full name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className={inputClass}
                />
              </div>

              <div>
                <label htmlFor="username" className="block text-[13px] font-medium text-[#1B1034] mb-1.5">
                  Username
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-gray-400">
                    @
                  </span>
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => {
                      const next = e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "");
                      setUsername(next);
                      if (next.length < 3) setUsernameAvailable(null);
                    }}
                    required
                    className="w-full pl-7 pr-4 py-2.5 border-[1.5px] border-[#1B1034] bg-white text-sm text-[#1B1034] focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10 outline-none transition"
                  />
                </div>
                {usernameAvailable !== null && username.length >= 3 && (
                  <p className={`text-[11px] mt-1 ${usernameAvailable ? "text-green-600" : "text-red-500"}`}>
                    {usernameAvailable ? "✓ Available" : "✕ Username taken"}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-[13px] font-medium text-[#1B1034] mb-1.5">
                  Password
                </label>
                <PasswordInput value={password} onChange={setPassword} />
              </div>
            </>
          )}

          <button
            type="submit"
            disabled={
              loading ||
              !email ||
              !name ||
              !username ||
              !isPasswordValid(password) ||
              usernameAvailable === false
            }
            className={primaryButtonClass}
          >
            {loading ? "Creating..." : "Create account"}
          </button>
        </form>
      )}

      {/* OTP mode step 1 — email + send code */}
      {mode === "otp" && step === 1 && (
        <form onSubmit={handleSendOtp} className="space-y-3.5">
          <div>
            <label htmlFor="otp-email" className="block text-[13px] font-medium text-[#1B1034] mb-1.5">
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
            {loading ? "Sending..." : "Send verification code"}
          </button>
        </form>
      )}

      {/* OTP mode step 2 — verify code */}
      {mode === "otp" && step === 2 && (
        <form onSubmit={handleVerifyOtp} className="space-y-5">
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
                  onClick={handleResendOtp}
                  className="text-[#834DFB] hover:underline font-medium cursor-pointer"
                >
                  {AUTH_COPY.otpResendButton}
                </button>
              )}
            </p>
            <button
              type="button"
              onClick={() => {
                setStep(1);
                setOtp("");
              }}
              className="text-[13px] text-[#834DFB] hover:underline cursor-pointer"
            >
              Wrong email? Go back
            </button>
          </div>
        </form>
      )}

      {/* OTP mode step 3 — profile + password */}
      {mode === "otp" && step === 3 && (
        <form onSubmit={handleCreateAccount} className="space-y-3.5">
          <div>
            <label htmlFor="name" className="block text-[13px] font-medium text-[#1B1034] mb-1.5">
              Full name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          <div>
            <label htmlFor="username" className="block text-[13px] font-medium text-[#1B1034] mb-1.5">
              Username
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-gray-400">
                @
              </span>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => {
                  const next = e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "");
                  setUsername(next);
                  if (next.length < 3) setUsernameAvailable(null);
                }}
                required
                className="w-full pl-7 pr-4 py-2.5 border-[1.5px] border-[#1B1034] bg-white text-sm text-[#1B1034] focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10 outline-none transition"
              />
            </div>
            {usernameAvailable !== null && username.length >= 3 && (
              <p className={`text-[11px] mt-1 ${usernameAvailable ? "text-green-600" : "text-red-500"}`}>
                {usernameAvailable ? "✓ Available" : "✕ Username taken"}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-[13px] font-medium text-[#1B1034] mb-1.5">
              Password
            </label>
            <PasswordInput value={password} onChange={setPassword} />
          </div>

          <button
            type="submit"
            disabled={
              loading ||
              !name ||
              !username ||
              !isPasswordValid(password) ||
              usernameAvailable === false
            }
            className={primaryButtonClass}
          >
            {loading ? "Creating..." : "Create account"}
          </button>
        </form>
      )}

      {(mode === "password" || step === 1) && (
        <p className="text-[13px] text-gray-500 text-center mt-5">
          Already have an account?{" "}
          <Link
            href="/auth/signin"
            className="text-[#834DFB] hover:underline font-medium"
          >
            Sign in
          </Link>
        </p>
      )}

      <p className="text-[11px] text-gray-400 text-center mt-10">
        &copy; 2026 Codatta PTE LTD.
      </p>
    </>
  );
}
