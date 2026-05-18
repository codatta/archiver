export const AUTH_COPY = {
  oauthDisabledCaption: "OAuth sign-in is temporarily unavailable. Use email below.",
  showMoreProviders: "Show more sign-in options",
  hideMoreProviders: "Show fewer options",
  otpSendButton: "Send code",
  otpResendButton: "Resend code",
  otpResendCooldown: (s: number) => `Resend code (${s}s)`,
  otpInvalidCode: "Invalid or expired code. Please try again.",
  otpRateLimited: "Too many attempts. Please wait before retrying.",
  otpUnknownEmail: "If an account exists, we sent a code.",
  otpGenericError: "Something went wrong. Please try again.",
} as const;

export function mapOtpError(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes("invalid") || lower.includes("expired") || lower.includes("token")) {
    return AUTH_COPY.otpInvalidCode;
  }
  if (lower.includes("rate") || lower.includes("too many")) {
    return AUTH_COPY.otpRateLimited;
  }
  return AUTH_COPY.otpGenericError;
}
