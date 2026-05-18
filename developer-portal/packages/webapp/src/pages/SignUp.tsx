import React, { useEffect, useState } from "react";
import { navigate } from "../App";
import { supabase } from "../lib/supabase";
import { apiFetch } from "../lib/api";
import { BRAND, THEME } from "../lib/config";
import { OAuthButtons, OAuthDivider } from "../components/auth/OAuthButtons";
import { usePasswordRules } from "../lib/password/usePasswordRules";
import { PasswordRules } from "../lib/password/PasswordRules";
import { StrengthMeter } from "../lib/password/StrengthMeter";

const inputCls = "w-full px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";

const RESEND_COOLDOWN = 60;

type Step = "email" | "otp" | "password";
type AutoJoinInfo = { orgName: string };

function WelcomeModal({ orgName, onContinue }: { orgName: string; onContinue: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4"
      style={{ background: "rgba(27, 16, 52, 0.5)" }}>
      <div className="w-full max-w-sm bg-white border-[1.5px] border-[#1B1034] rounded-none shadow-2xl overflow-hidden"
        style={{ animation: "fadeSlideUp 0.25s ease" }}>
        <div className="h-1.5 w-full" style={{ background: `linear-gradient(90deg, ${THEME.accent}, #1B1034)` }} />
        <div className="px-8 pt-8 pb-7 text-center">
          <div className="w-16 h-16 rounded-full mx-auto mb-5 flex items-center justify-center text-3xl"
            style={{ background: "#F0EBFF" }}>
            <i className="fi fi-ss-party-horn" style={{ color: THEME.accent }} />
          </div>
          <h2 className="text-xl font-semibold mb-2" style={{ color: THEME.textPrimary }}>Welcome aboard!</h2>
          <p className="text-sm leading-relaxed mb-1" style={{ color: THEME.textSecondary }}>
            Your email matched the{" "}
            <span className="font-semibold" style={{ color: THEME.accent }}>{orgName}</span>{" "}
            workspace.
          </p>
          <p className="text-sm leading-relaxed mb-7" style={{ color: THEME.textMuted }}>
            You've been added as a member — no setup required.
          </p>
          <button onClick={onContinue}
            className="w-full py-2.5 text-sm font-medium text-white rounded-none"
            style={{ background: THEME.btnBg }}>
            Go to dashboard
          </button>
        </div>
      </div>
      <style>{`@keyframes fadeSlideUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }`}</style>
    </div>
  );
}

export function SignUp() {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [autoJoin, setAutoJoin] = useState<AutoJoinInfo | null>(null);
  const [otpCode, setOtpCode] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [confirmTouched, setConfirmTouched] = useState(false);
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [confirmVisible, setConfirmVisible] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  const passwordValidation = usePasswordRules(password);
  const passwordsMatch =
    password.length > 0 && password === confirmPassword;
  const confirmShowError =
    confirmPassword.length > 0 &&
    !passwordsMatch &&
    (confirmTouched || confirmPassword.length >= password.length);
  const canSubmitPassword =
    !!fullName.trim() && passwordValidation.valid && passwordsMatch;

  useEffect(() => {
    if (cooldown <= 0) return;
    const id = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(id);
  }, [cooldown]);

  // Parse rate-limit wait time from Supabase error and set real-time countdown
  function handleRateLimit(msg: string) {
    const match = msg.match(/after (\d+) second/);
    if (match) {
      setCooldown(parseInt(match[1], 10));
      setError("");
    } else {
      setError(msg);
    }
  }

  // Step 1: Send OTP to email
  async function handleSendOtp(e?: React.FormEvent) {
    e?.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { error: err } = await supabase.auth.signInWithOtp({ email });
      if (err) {
        handleRateLimit(err.message);
      } else {
        setCooldown(RESEND_COOLDOWN);
        setStep("otp");
      }
    } catch {
      // Even if the request errored, the OTP was likely sent — advance to OTP step
      setCooldown(RESEND_COOLDOWN);
      setStep("otp");
      setError("Sending took longer than expected. Check your email — the code may have arrived.");
    } finally {
      setLoading(false);
    }
  }

  // Resend OTP
  async function handleResend() {
    if (cooldown > 0) return;
    setError("");
    try {
      const { error: err } = await supabase.auth.signInWithOtp({ email });
      if (err) {
        handleRateLimit(err.message);
      } else {
        setCooldown(RESEND_COOLDOWN);
      }
    } catch {
      setCooldown(RESEND_COOLDOWN);
      setError("Resend may have been slow. Check your email.");
    }
  }

  // Step 2: Verify OTP
  async function handleVerifyOtp(e?: React.FormEvent) {
    e?.preventDefault();
    setError("");
    setLoading(true);
    try {
      const timeout = new Promise<{ data: { session: null }; error: { message: string } }>((resolve) =>
        setTimeout(() => resolve({ data: { session: null }, error: { message: "Verification timed out. Please try again." } }), 20000),
      );
      const code = otpCode.trim();
      // Try 'signup' type first (new user), fall back to 'email' (existing user sign-in)
      const signupReq = supabase.auth.verifyOtp({ email, token: code, type: "signup" });
      let result = await Promise.race([signupReq, timeout]);
      if (result.error) {
        const emailReq = supabase.auth.verifyOtp({ email, token: code, type: "email" });
        result = await Promise.race([emailReq, timeout]);
      }
      const { data, error: err } = result;
      if (err) {
        const msg = err.message;
        if (msg.toLowerCase().includes("expired") || msg.toLowerCase().includes("invalid")) {
          setError("Code expired or invalid. Click \"Resend code\" to get a new one.");
          setOtpCode("");
          setCooldown(0);
        } else {
          setError(msg);
        }
        return;
      }
      if (data.session) {
        localStorage.setItem("access_token", data.session.access_token);
      }
      setStep("password");
    } catch (err: unknown) {
      setError((err as Error).message ?? "Verification failed");
    } finally {
      setLoading(false);
    }
  }

  // Step 3: Set password and complete signup
  async function handleSetPassword(e?: React.FormEvent) {
    e?.preventDefault();
    setError("");
    // Defensive guard — real gating happens via disabled button.
    if (!passwordValidation.valid || !passwordsMatch) {
      setError("Password does not meet all requirements");
      setPasswordTouched(true);
      setConfirmTouched(true);
      return;
    }
    setLoading(true);
    try {
      const { error: err } = await supabase.auth.updateUser({
        password,
        data: { full_name: fullName },
      });
      if (err) {
        setError(err.message);
        setLoading(false);
        return;
      }
      // Sync profile — check for auto-join
      try {
        const res = await apiFetch<{
          user: { org_id: string | null; org_name: string | null; auto_joined: boolean };
        }>("/v1/auth/sync-profile", { method: "POST" });
        if (res.user?.org_id && res.user?.auto_joined && res.user?.org_name) {
          setLoading(false);
          setAutoJoin({ orgName: res.user.org_name });
          return; // Show welcome modal — user clicks to go to dashboard
        }
      } catch {}
      navigate("/onboarding");
    } catch (err: unknown) {
      setError((err as Error).message ?? "Failed to create account");
      setLoading(false);
    }
  }

  const stepLabels = ["Verify email", "Set up profile", "Start building"];
  const activeStep = step === "email" ? 0 : step === "otp" ? 0 : 1;

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ background: THEME.bg }}
    >
      <div className="w-full max-w-sm">
        <img src={BRAND.logo} alt={BRAND.name} className="h-8 w-auto mb-8" />

        {/* Step 1: Email */}
        {step === "email" && (
          <>
            <h1
              className="text-2xl font-semibold mb-1"
              style={{ color: THEME.textPrimary }}
            >
              Create your account
            </h1>
            <p className="text-sm mb-6" style={{ color: THEME.textMuted }}>
              Enter your email to get started
            </p>
            <OAuthButtons returnTo="/auth/callback" onError={setError} />
            <OAuthDivider />
            <form onSubmit={handleSendOtp} className="space-y-4">
              <div>
                <label
                  className="block text-sm font-medium mb-1.5"
                  style={{ color: THEME.textPrimary }}
                >
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                  className={inputCls}
                  placeholder="you@company.com"
                />
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <button
                type="button"
                onClick={() => handleSendOtp()}
                disabled={loading || cooldown > 0}
                className="w-full py-2.5 text-white rounded-none text-sm font-medium disabled:opacity-50"
                style={{ background: THEME.btnBg }}
              >
                {loading
                  ? "Sending..."
                  : cooldown > 0
                  ? `Wait ${cooldown}s`
                  : "Send verification code"}
              </button>
            </form>
          </>
        )}

        {/* Step 2: OTP Verification */}
        {step === "otp" && (
          <>
            <h1
              className="text-2xl font-semibold mb-1"
              style={{ color: THEME.textPrimary }}
            >
              Check your email
            </h1>
            <p className="text-sm mb-1" style={{ color: THEME.textMuted }}>
              We sent a 6-digit code to{" "}
              <strong style={{ color: THEME.textPrimary }}>{email}</strong>
            </p>
            <p className="text-xs mb-6" style={{ color: THEME.textMuted }}>
              Sent from{" "}
              <span style={{ color: THEME.textSecondary }}>
                noreply@humanbased.ai
              </span>{" "}
              — check spam if it doesn't arrive within 2 minutes.
            </p>
            <form onSubmit={handleVerifyOtp} className="space-y-4">
              <div>
                <label
                  className="block text-sm font-medium mb-1.5"
                  style={{ color: THEME.textPrimary }}
                >
                  Verification code
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) =>
                    setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))
                  }
                  required
                  autoFocus
                  className={`${inputCls} text-center text-lg font-mono tracking-[0.3em]`}
                  placeholder="000000"
                />
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <button
                type="button"
                onClick={() => handleVerifyOtp()}
                disabled={loading || otpCode.length < 6}
                className="w-full py-2.5 text-white rounded-none text-sm font-medium disabled:opacity-50"
                style={{ background: THEME.btnBg }}
              >
                {loading ? "Verifying..." : "Verify"}
              </button>
            </form>

            <div className="flex items-center justify-between mt-4">
              <button
                type="button"
                onClick={handleResend}
                disabled={cooldown > 0}
                className="text-sm disabled:opacity-40 cursor-pointer disabled:cursor-default underline decoration-1 underline-offset-2"
                style={{ color: cooldown > 0 ? THEME.textMuted : THEME.accent }}
              >
                {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend code"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setStep("email");
                  setOtpCode("");
                  setError("");
                }}
                className="text-sm cursor-pointer underline decoration-1 underline-offset-2"
                style={{ color: THEME.textSecondary }}
              >
                Wrong email?
              </button>
            </div>
          </>
        )}

        {/* Step 3: Set Password */}
        {step === "password" && (
          <>
            <h1
              className="text-2xl font-semibold mb-1"
              style={{ color: THEME.textPrimary }}
            >
              Set up your profile
            </h1>
            <p className="text-sm mb-1" style={{ color: THEME.textMuted }}>
              Email verified:{" "}
              <strong style={{ color: THEME.accent }}>{email}</strong>
            </p>
            <p className="text-sm mb-6" style={{ color: THEME.textMuted }}>
              Choose a password to secure your account
            </p>
            <form onSubmit={handleSetPassword} className="space-y-4">
              <div>
                <label
                  className="block text-sm font-medium mb-1.5"
                  style={{ color: THEME.textPrimary }}
                >
                  Full name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  autoFocus
                  className={inputCls}
                />
              </div>
              <div>
                <label
                  className="block text-sm font-medium mb-1.5"
                  style={{ color: THEME.textPrimary }}
                >
                  Password
                </label>
                <div className="relative">
                  <input
                    type={passwordVisible ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onBlur={() => setPasswordTouched(true)}
                    required
                    className={inputCls + " pr-14"}
                    placeholder="At least 10 characters"
                  />
                  <button
                    type="button"
                    aria-pressed={passwordVisible}
                    aria-label={passwordVisible ? "Hide password" : "Show password"}
                    onClick={() => setPasswordVisible((v) => !v)}
                    className="absolute inset-y-0 right-3 flex items-center text-xs font-medium text-gray-500 hover:text-[#1B1034]"
                  >
                    {passwordVisible ? "Hide" : "Show"}
                  </button>
                </div>
                <StrengthMeter score={passwordValidation.score} />
                <PasswordRules
                  validation={passwordValidation}
                  isDirty={passwordTouched || password.length > 0}
                />
              </div>
              <div>
                <label
                  className="block text-sm font-medium mb-1.5"
                  style={{ color: THEME.textPrimary }}
                >
                  Confirm password
                </label>
                <div className="relative">
                  <input
                    type={confirmVisible ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    onBlur={() => setConfirmTouched(true)}
                    required
                    className={inputCls + " pr-14"}
                  />
                  <button
                    type="button"
                    aria-pressed={confirmVisible}
                    aria-label={confirmVisible ? "Hide password" : "Show password"}
                    onClick={() => setConfirmVisible((v) => !v)}
                    className="absolute inset-y-0 right-3 flex items-center text-xs font-medium text-gray-500 hover:text-[#1B1034]"
                  >
                    {confirmVisible ? "Hide" : "Show"}
                  </button>
                </div>
                {confirmPassword.length > 0 && (
                  <p
                    data-match-state={
                      passwordsMatch ? "match" : confirmShowError ? "mismatch" : "typing"
                    }
                    className={
                      "mt-1.5 text-xs " +
                      (passwordsMatch
                        ? "text-emerald-600"
                        : confirmShowError
                          ? "text-red-500"
                          : "text-gray-400")
                    }
                  >
                    {passwordsMatch ? "Passwords match" : "Passwords do not match"}
                  </p>
                )}
              </div>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <button
                type="button"
                onClick={() => handleSetPassword()}
                disabled={loading || !canSubmitPassword}
                className="w-full py-2.5 text-white rounded-none text-sm font-medium disabled:opacity-50"
                style={{ background: THEME.btnBg }}
              >
                {loading ? "Creating account..." : "Create account"}
              </button>
            </form>
          </>
        )}

        {/* Step indicator */}
        <div className="flex items-center gap-2 mt-6 mb-4">
          {stepLabels.map((label, i) => (
            <React.Fragment key={label}>
              <div className="flex items-center gap-1.5">
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium"
                  style={
                    i <= activeStep
                      ? { background: THEME.accent, color: "#fff" }
                      : {
                          border: `1.5px solid ${THEME.border}`,
                          color: THEME.textMuted,
                        }
                  }
                >
                  {i < activeStep ? "✓" : i + 1}
                </div>
                <span
                  className="text-xs"
                  style={{
                    color:
                      i <= activeStep ? THEME.textPrimary : THEME.textMuted,
                  }}
                >
                  {label}
                </span>
              </div>
              {i < stepLabels.length - 1 && (
                <div
                  className="flex-1 h-px"
                  style={{
                    background:
                      i < activeStep ? THEME.accent : THEME.border,
                  }}
                />
              )}
            </React.Fragment>
          ))}
        </div>

        <p
          className="text-sm text-center"
          style={{ color: THEME.textMuted }}
        >
          Already have an account?{" "}
          <button
            onClick={() => navigate("/auth/signin")}
            className="font-medium"
            style={{ color: THEME.accent }}
          >
            Sign in
          </button>
        </p>
      </div>
      {autoJoin && (
        <WelcomeModal
          orgName={autoJoin.orgName}
          onContinue={() => navigate("/dashboard")}
        />
      )}
    </div>
  );
}
