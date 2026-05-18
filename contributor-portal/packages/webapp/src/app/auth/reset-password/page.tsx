"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { StepIndicator } from "@/components/auth/step-indicator";
import { OtpInput } from "@/components/auth/otp-input";
import { PasswordInput, isPasswordValid } from "@/components/auth/password-input";
import { BRAND } from "@/lib/config";
import { createClient } from "@/lib/supabase/client";
import { AUTH_COPY, mapOtpError } from "@/lib/auth/copy";
import { useResendCooldown } from "@/hooks/useResendCooldown";

type Step = "email" | "otp" | "new_password";

export default function ResetPasswordPage() {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { remaining, start } = useResendCooldown(60);

  const stepNumber = step === "email" ? 1 : step === "otp" ? 2 : 3;

  const inputClass =
    "w-full px-5 py-3 border-[1.5px] border-[#1B1034] bg-white text-sm text-[#1B1034] placeholder:text-gray-400 focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10 outline-none transition";

  const primaryButtonClass =
    "w-full py-2.5 bg-[#1B1034] text-white text-[13px] font-medium hover:bg-[#2D2250] transition disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer";

  async function handleSendCode(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    await supabase.auth.signInWithOtp({
      email,
      options: { shouldCreateUser: false },
    });

    // Generic success regardless of whether the email exists — prevents enumeration.
    setLoading(false);
    setNotice(AUTH_COPY.otpUnknownEmail);
    setStep("otp");
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

    setLoading(false);
    if (verifyError) {
      setError(mapOtpError(verifyError.message));
      return;
    }

    setNotice(null);
    setStep("new_password");
  }

  async function handleSetPassword(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!isPasswordValid(password)) return;
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);

    const supabase = createClient();
    const { error: updateError } = await supabase.auth.updateUser({ password });

    if (updateError) {
      setError(updateError.message);
      setLoading(false);
      return;
    }

    // Full reload so server-side auth state re-reads cleanly.
    window.location.href = "/contribute";
  }

  async function handleResend() {
    if (remaining > 0 || loading) return;
    setError(null);
    const supabase = createClient();
    await supabase.auth.signInWithOtp({
      email,
      options: { shouldCreateUser: false },
    });
    start();
  }

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
        Reset password
      </h1>
      <p className="text-[13px] text-gray-500 mt-1">
        {step === "email" && "We'll send a verification code to your email."}
        {step === "otp" && `Enter the code we sent to ${email}.`}
        {step === "new_password" && "Choose a new password."}
      </p>

      <div className="mt-5 mb-6">
        <StepIndicator steps={3} current={stepNumber} />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 p-3 mb-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {notice && step === "otp" && (
        <div className="bg-gray-50 border border-gray-200 p-3 mb-4 text-[13px] text-gray-600">
          {notice}
        </div>
      )}

      {step === "email" && (
        <form onSubmit={handleSendCode} className="space-y-3.5">
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

          <button type="submit" disabled={loading || !email} className={primaryButtonClass}>
            {loading ? "Sending..." : AUTH_COPY.otpSendButton}
          </button>
        </form>
      )}

      {step === "otp" && (
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
                  onClick={handleResend}
                  className="text-[#834DFB] hover:underline font-medium cursor-pointer"
                >
                  {AUTH_COPY.otpResendButton}
                </button>
              )}
            </p>
            <button
              type="button"
              onClick={() => {
                setStep("email");
                setOtp("");
                setNotice(null);
              }}
              className="text-[13px] text-[#834DFB] hover:underline cursor-pointer"
            >
              Wrong email? Go back
            </button>
          </div>
        </form>
      )}

      {step === "new_password" && (
        <form onSubmit={handleSetPassword} className="space-y-3.5">
          <div>
            <label
              htmlFor="password"
              className="block text-[13px] font-medium text-[#1B1034] mb-1.5"
            >
              New password
            </label>
            <PasswordInput value={password} onChange={setPassword} id="password" />
          </div>

          <div>
            <label
              htmlFor="confirm"
              className="block text-[13px] font-medium text-[#1B1034] mb-1.5"
            >
              Confirm password
            </label>
            <input
              id="confirm"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !isPasswordValid(password) || password !== confirm}
            className={primaryButtonClass}
          >
            {loading ? "Updating..." : "Set new password"}
          </button>
        </form>
      )}

      <p className="text-[13px] text-gray-500 text-center mt-5">
        Remembered it?{" "}
        <Link
          href="/auth/signin"
          className="text-[#834DFB] hover:underline font-medium"
        >
          Sign in
        </Link>
      </p>

      <p className="text-[11px] text-gray-400 text-center mt-10">
        &copy; 2026 Codatta PTE LTD.
      </p>
    </>
  );
}
