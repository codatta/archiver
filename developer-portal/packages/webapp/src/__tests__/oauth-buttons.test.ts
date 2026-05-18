import { test, expect, mock, beforeEach } from "bun:test";

/**
 * Tests for the OAuthButtons helper functions (startGitHubOAuth,
 * startHuggingFaceOAuth). We mock the supabase client and window.location
 * so these run in bun's headless test env without a DOM.
 */

// Hoisted mocks must happen before module import
const signInWithOAuth = mock(async (_opts: { provider: string; options: unknown }) => ({
  data: null,
  error: null as { message: string } | null,
}));

mock.module("../lib/supabase", () => ({
  supabase: { auth: { signInWithOAuth } },
}));

mock.module("../lib/env", () => ({
  ENV: { API_URL: "http://api.test", SUPABASE_URL: "x", SUPABASE_PUBLISHABLE_KEY: "y" },
}));

mock.module("../lib/config", () => ({
  THEME: { textPrimary: "#000", textMuted: "#999", border: "#ccc" },
  BRAND: { name: "Test", logo: "" },
}));

const { startGitHubOAuth, startHuggingFaceOAuth } = await import(
  "../components/auth/OAuthButtons"
);

beforeEach(() => {
  signInWithOAuth.mockClear();
});

test("startGitHubOAuth calls supabase.auth.signInWithOAuth with github provider", async () => {
  // Set window.location.origin
  // @ts-expect-error – test stub
  globalThis.window = { location: { origin: "http://localhost:3000", href: "" } };

  const err = await startGitHubOAuth("/auth/callback");

  expect(err).toBeNull();
  expect(signInWithOAuth).toHaveBeenCalledTimes(1);
  const call = signInWithOAuth.mock.calls[0][0];
  expect(call.provider).toBe("github");
  expect((call.options as { redirectTo: string }).redirectTo).toBe(
    "http://localhost:3000/auth/callback",
  );
});

test("startGitHubOAuth returns error message on failure", async () => {
  signInWithOAuth.mockImplementationOnce(async () => ({
    data: null,
    error: { message: "provider offline" },
  }));
  // @ts-expect-error – test stub
  globalThis.window = { location: { origin: "http://localhost:3000", href: "" } };

  const err = await startGitHubOAuth("/auth/callback");

  expect(err).toBe("provider offline");
});

test("startGitHubOAuth respects custom returnTo path", async () => {
  // @ts-expect-error – test stub
  globalThis.window = { location: { origin: "https://app.example.com", href: "" } };

  await startGitHubOAuth("/onboarding");

  const call = signInWithOAuth.mock.calls[0][0];
  expect((call.options as { redirectTo: string }).redirectTo).toBe(
    "https://app.example.com/onboarding",
  );
});

test("startHuggingFaceOAuth navigates to API /v1/auth/huggingface/start with return_to", () => {
  const location = { origin: "http://localhost:3000", href: "" };
  // @ts-expect-error – test stub
  globalThis.window = { location };

  startHuggingFaceOAuth("/auth/callback");

  expect(location.href).toBe(
    "http://api.test/v1/auth/huggingface/start?return_to=%2Fauth%2Fcallback",
  );
});

test("startHuggingFaceOAuth url-encodes the return_to param", () => {
  const location = { origin: "http://localhost:3000", href: "" };
  // @ts-expect-error – test stub
  globalThis.window = { location };

  startHuggingFaceOAuth("/dashboard?foo=bar&baz=1");

  expect(location.href).toContain("return_to=%2Fdashboard%3Ffoo%3Dbar%26baz%3D1");
});
