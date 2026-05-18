import { test, expect } from "@playwright/test";

// ---------------------------------------------------------------------------
// Sign In — UI state (no Supabase required)
// ---------------------------------------------------------------------------

test.describe("Sign In — UI", () => {
  test("renders logo, heading, and footer", async ({ page }) => {
    await page.goto("/auth/signin");
    await expect(page.locator("img[alt='Humanbased']")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expect(page.getByText("Welcome back to Contributor Kitchen of Humanbased.")).toBeVisible();
    await expect(page.getByText("Codatta PTE LTD.")).toBeVisible();
  });

  test("primary OAuth buttons (Google, LinkedIn) are visible by default", async ({ page }) => {
    await page.goto("/auth/signin");
    await expect(page.getByText("Continue with Google")).toBeVisible();
    await expect(page.getByText("Continue with LinkedIn")).toBeVisible();
  });

  test("secondary providers hidden until 'Show more' is clicked", async ({ page }) => {
    await page.goto("/auth/signin");
    await expect(page.getByText("Continue with GitHub")).not.toBeVisible();
    await expect(page.getByText("Continue with Hugging Face")).not.toBeVisible();

    await page.getByRole("button", { name: /show more/i }).click();

    await expect(page.getByText("Continue with GitHub")).toBeVisible();
    await expect(page.getByText("Continue with Hugging Face")).toBeVisible();
  });

  test("'Show more' toggles back to 'Show fewer'", async ({ page }) => {
    await page.goto("/auth/signin");
    const toggle = page.getByRole("button", { name: /show more/i });
    await toggle.click();
    await expect(page.getByRole("button", { name: /show fewer/i })).toBeVisible();
    await page.getByRole("button", { name: /show fewer/i }).click();
    await expect(page.getByText("Continue with GitHub")).not.toBeVisible();
  });

  test("OAuth buttons are aria-disabled and show caption when OAUTH_ENABLED is off", async ({ page }) => {
    await page.goto("/auth/signin");
    // In test env NEXT_PUBLIC_OAUTH_ENABLED defaults to false
    const googleBtn = page.getByRole("button", { name: /Continue with Google/i });
    await expect(googleBtn).toHaveAttribute("aria-disabled", "true");
    await expect(page.getByText("OAuth sign-in is temporarily unavailable.")).toBeVisible();
  });

  test("defaults to Password tab", async ({ page }) => {
    await page.goto("/auth/signin");
    const passwordTab = page.getByRole("tab", { name: "Password" });
    await expect(passwordTab).toHaveAttribute("aria-selected", "true");
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
  });

  test("switching to Email code tab shows OTP email form", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.getByRole("tab", { name: "Email code" }).click();
    await expect(page.getByRole("tab", { name: "Email code" })).toHaveAttribute("aria-selected", "true");
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByRole("button", { name: "Send code" })).toBeVisible();
    await expect(page.getByLabel("Password")).not.toBeVisible();
  });

  test("'Forgot password?' link navigates to reset-password page", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.getByRole("link", { name: "Forgot password?" }).click();
    await page.waitForURL("/auth/reset-password");
    await expect(page.getByRole("heading", { name: "Reset password" })).toBeVisible();
  });

  test("sign-up link navigates to signup page", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.getByRole("link", { name: "Sign up" }).click();
    await page.waitForURL("/auth/signup");
    await expect(page.getByRole("heading", { name: "Create your account" })).toBeVisible();
  });

  test("OTP tab: Send code button disabled until email entered", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.getByRole("tab", { name: "Email code" }).click();
    const sendBtn = page.getByRole("button", { name: "Send code" });
    await expect(sendBtn).toBeDisabled();
    await page.getByLabel("Email").fill("test@example.com");
    await expect(sendBtn).not.toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// Sign In — Auth flows (require Supabase; expected to fail without credentials)
// ---------------------------------------------------------------------------

test.describe("Sign In — Auth flows", () => {
  test("password sign-in navigates to /contribute on success", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.getByLabel("Email").fill("test@example.com");
    await page.getByLabel("Password").fill("password123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL("/contribute", { timeout: 5000 });
  });

  test("invalid credentials surface an error message", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.getByLabel("Email").fill("bad@example.com");
    await page.getByLabel("Password").fill("wrongpassword");
    await page.getByRole("button", { name: "Sign in" }).click();
    // Supabase returns an error; we just check that a message appears
    await expect(page.locator(".bg-red-50")).toBeVisible({ timeout: 5000 });
  });
});

// ---------------------------------------------------------------------------
// Sign Up — UI state (no Supabase required)
// ---------------------------------------------------------------------------

test.describe("Sign Up — UI", () => {
  test("defaults to Password tab with full form", async ({ page }) => {
    await page.goto("/auth/signup");
    await expect(page.getByRole("heading", { name: "Create your account" })).toBeVisible();
    const passwordTab = page.getByRole("tab", { name: "Password" });
    await expect(passwordTab).toHaveAttribute("aria-selected", "true");
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Full name")).toBeVisible();
    await expect(page.getByLabel("Username")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Create account" })).toBeVisible();
  });

  test("switching to Email code tab shows OTP step 1", async ({ page }) => {
    await page.goto("/auth/signup");
    await page.getByRole("tab", { name: "Email code" }).click();
    await expect(page.getByRole("tab", { name: "Email code" })).toHaveAttribute("aria-selected", "true");
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByRole("button", { name: "Send verification code" })).toBeVisible();
    await expect(page.getByLabel("Full name")).not.toBeVisible();
  });

  test("OAuth buttons visible on step 1 of Email code tab", async ({ page }) => {
    await page.goto("/auth/signup");
    await page.getByRole("tab", { name: "Email code" }).click();
    await expect(page.getByText("Sign up with Google")).toBeVisible();
  });

  test("sign-in link navigates to signin page", async ({ page }) => {
    await page.goto("/auth/signup");
    await page.getByRole("link", { name: "Sign in" }).click();
    await page.waitForURL("/auth/signin");
  });
});

// ---------------------------------------------------------------------------
// Sign Up — Auth flows (OTP, existing)
// ---------------------------------------------------------------------------

test.describe("Sign Up — OTP flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/auth/signup");
    await page.getByRole("tab", { name: "Email code" }).click();
  });

  test("step 1 → step 2: sends OTP and shows code input", async ({ page }) => {
    await page.getByLabel("Email").fill("test@example.com");
    await page.getByRole("button", { name: "Send verification code" }).click();
    await expect(page.getByText("Check your email")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("test@example.com")).toBeVisible();
    await expect(page.getByText("Verification code")).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Reset Password — UI state
// ---------------------------------------------------------------------------

test.describe("Reset Password — UI", () => {
  test("renders step 1 with step indicator and email form", async ({ page }) => {
    await page.goto("/auth/reset-password");
    await expect(page.getByRole("heading", { name: "Reset password" })).toBeVisible();
    await expect(page.getByText("We'll send a verification code to your email.")).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByRole("button", { name: "Send code" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Sign in" })).toBeVisible();
  });

  test("Send code button disabled until email entered", async ({ page }) => {
    await page.goto("/auth/reset-password");
    await expect(page.getByRole("button", { name: "Send code" })).toBeDisabled();
    await page.getByLabel("Email").fill("test@example.com");
    await expect(page.getByRole("button", { name: "Send code" })).not.toBeDisabled();
  });

  test("step 1 submit shows generic copy (anti-enumeration)", async ({ page }) => {
    await page.goto("/auth/reset-password");
    await page.getByLabel("Email").fill("unknown@example.com");
    await page.getByRole("button", { name: "Send code" }).click();
    // Generic copy shown regardless of whether email exists
    await expect(page.getByText("If an account exists, we sent a code.")).toBeVisible({ timeout: 5000 });
    // Step 2 OTP form should appear
    await expect(page.getByText("Verification code")).toBeVisible({ timeout: 5000 });
  });

  test("'Remembered it?' link navigates back to sign in", async ({ page }) => {
    await page.goto("/auth/reset-password");
    await page.getByRole("link", { name: "Sign in" }).click();
    await page.waitForURL("/auth/signin");
  });
});

// ---------------------------------------------------------------------------
// OTP resend cooldown — UI state
// ---------------------------------------------------------------------------

test.describe("Resend cooldown", () => {
  test("resend button shows countdown after send on signin OTP tab", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.getByRole("tab", { name: "Email code" }).click();
    await page.getByLabel("Email").fill("test@example.com");
    await page.getByRole("button", { name: "Send code" }).click();

    // After send, resend appears in cooldown state
    await expect(page.getByText(/Resend code \(\d+s\)/)).toBeVisible({ timeout: 5000 });
  });
});

// ---------------------------------------------------------------------------
// Accessibility
// ---------------------------------------------------------------------------

test.describe("Accessibility", () => {
  test("signin form labels are associated with inputs", async ({ page }) => {
    await page.goto("/auth/signin");
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
  });

  test("mode tabs have correct ARIA roles and aria-selected", async ({ page }) => {
    await page.goto("/auth/signin");
    const tablist = page.getByRole("tablist");
    await expect(tablist).toBeVisible();
    const passwordTab = page.getByRole("tab", { name: "Password" });
    const otpTab = page.getByRole("tab", { name: "Email code" });
    await expect(passwordTab).toHaveAttribute("aria-selected", "true");
    await expect(otpTab).toHaveAttribute("aria-selected", "false");
    await otpTab.click();
    await expect(otpTab).toHaveAttribute("aria-selected", "true");
    await expect(passwordTab).toHaveAttribute("aria-selected", "false");
  });

  test("disabled OAuth buttons have aria-disabled=true", async ({ page }) => {
    await page.goto("/auth/signin");
    const google = page.getByRole("button", { name: /Continue with Google/i });
    await expect(google).toHaveAttribute("aria-disabled", "true");
    const linkedin = page.getByRole("button", { name: /Continue with LinkedIn/i });
    await expect(linkedin).toHaveAttribute("aria-disabled", "true");
  });
});
