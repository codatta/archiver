import { test, expect } from "@playwright/test";

const screenshotDir = "tests/v1/ux-tests";

test.describe("Journey 1: New Contributor", () => {
  test("01 sign-in page — password tab (default)", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.waitForSelector("text=Sign in");
    await page.screenshot({ path: `${screenshotDir}/01-signin.png`, fullPage: true });
  });

  test("01b sign-in page — email code tab", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.waitForSelector("text=Sign in");
    await page.getByRole("tab", { name: "Email code" }).click();
    await page.waitForSelector("text=Send code");
    await page.screenshot({ path: `${screenshotDir}/01b-signin-emailcode-tab.png`, fullPage: true });
  });

  test("01c sign-in — oauth show-more expanded", async ({ page }) => {
    await page.goto("/auth/signin");
    await page.waitForSelector("text=Sign in");
    await page.getByRole("button", { name: /show more/i }).click();
    await page.waitForTimeout(200);
    await page.screenshot({ path: `${screenshotDir}/01c-signin-oauth-expanded.png`, fullPage: true });
  });

  test("02 sign-up — password tab (default)", async ({ page }) => {
    await page.goto("/auth/signup");
    await page.waitForSelector("text=Create your account");
    await page.screenshot({ path: `${screenshotDir}/02-signup-step1.png`, fullPage: true });
  });

  test("02b sign-up — email code tab (step 1)", async ({ page }) => {
    await page.goto("/auth/signup");
    await page.waitForSelector("text=Create your account");
    await page.getByRole("tab", { name: "Email code" }).click();
    await page.waitForSelector("text=Send verification code");
    await page.screenshot({ path: `${screenshotDir}/02b-signup-emailcode-tab.png`, fullPage: true });
  });

  test("03 sign-up step 2 OTP (email code tab)", async ({ page }) => {
    await page.goto("/auth/signup");
    await page.getByRole("tab", { name: "Email code" }).click();
    await page.getByLabel("Email").fill("test@example.com");
    await page.getByRole("button", { name: "Send verification code" }).click();
    // Capture whatever Supabase returns — OTP step if real account, error otherwise
    await page.waitForTimeout(2000);
    await page.screenshot({ path: `${screenshotDir}/03-signup-step2-otp.png`, fullPage: true });
  });

  test("04 sign-up step 3 profile (email code tab)", async ({ page }) => {
    await page.goto("/auth/signup");
    await page.getByRole("tab", { name: "Email code" }).click();
    await page.getByLabel("Email").fill("test@example.com");
    await page.getByRole("button", { name: "Send verification code" }).click();
    await page.waitForTimeout(2000);
    const inputs = page.locator("input[inputmode='numeric']");
    if (await inputs.count() > 0) {
      for (let i = 0; i < 6; i++) await inputs.nth(i).fill(String(i + 1));
      await page.getByRole("button", { name: "Verify code" }).click();
      await page.waitForTimeout(2000);
    }
    await page.screenshot({ path: `${screenshotDir}/04-signup-step3-profile.png`, fullPage: true });
  });

  test("04b reset-password — step 1 email", async ({ page }) => {
    await page.goto("/auth/reset-password");
    await page.waitForSelector("text=Reset password");
    await page.screenshot({ path: `${screenshotDir}/04b-reset-password-step1.png`, fullPage: true });
  });

  test("04c reset-password — step 2 OTP", async ({ page }) => {
    await page.goto("/auth/reset-password");
    await page.getByLabel("Email").fill("test@example.com");
    await page.getByRole("button", { name: "Send code" }).click();
    await expect(page.getByText("Verification code")).toBeVisible({ timeout: 5000 });
    await page.screenshot({ path: `${screenshotDir}/04c-reset-password-step2.png`, fullPage: true });
  });

  test("05 onboarding step 1 skills", async ({ page }) => {
    await page.goto("/onboarding");
    await page.waitForSelector("text=What are you good at");
    await page.getByText("Robotics Annotation").click();
    await page.getByText("Data Collection").click();
    await page.screenshot({ path: `${screenshotDir}/05-onboarding-skills.png`, fullPage: true });
  });

  test("06 onboarding step 2 interests", async ({ page }) => {
    await page.goto("/onboarding");
    await page.getByText("Skip for now").click();
    await page.waitForSelector("text=What kind of work");
    await page.screenshot({ path: `${screenshotDir}/06-onboarding-interests.png`, fullPage: true });
  });

  test("07 onboarding step 3 ready", async ({ page }) => {
    await page.goto("/onboarding");
    await page.getByText("Skip for now").click();
    await page.getByText("Skip for now").click();
    await page.waitForSelector("text=all set");
    await page.screenshot({ path: `${screenshotDir}/07-onboarding-ready.png`, fullPage: true });
  });
});

test.describe("Journey 2: Returning Contributor (daily work)", () => {
  test("08 dashboard home", async ({ page }) => {
    await page.goto("/contribute");
    await page.waitForSelector("text=Good morning");
    await page.screenshot({ path: `${screenshotDir}/08-dashboard.png`, fullPage: true });
  });

  test("09 tasks page default", async ({ page }) => {
    await page.goto("/contribute/tasks");
    await page.waitForSelector("text=My Tasks");
    await page.screenshot({ path: `${screenshotDir}/09-tasks-default.png`, fullPage: true });
  });

  test("10 tasks priority expanded", async ({ page }) => {
    await page.goto("/contribute/tasks");
    await page.waitForSelector("text=My Tasks");
    await page.getByRole("button", { name: /Resume/ }).click();
    await page.waitForTimeout(400);
    await page.screenshot({ path: `${screenshotDir}/10-tasks-priority-expanded.png`, fullPage: true });
  });

  test("11 task workspace", async ({ page }) => {
    await page.goto("/workspace/camp-k1m/t3-label-47");
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${screenshotDir}/11-task-workspace.png`, fullPage: true });
  });
});

test.describe("Journey 3: Discovery & Enrollment", () => {
  test("12 discover campaigns", async ({ page }) => {
    await page.goto("/contribute/discover");
    await page.waitForSelector("text=Discover");
    await page.screenshot({ path: `${screenshotDir}/12-discover.png`, fullPage: true });
  });

  test("13 campaign detail", async ({ page }) => {
    await page.goto("/contribute/campaigns/camp-k1m");
    await page.waitForTimeout(2000);
    // Campaign detail may show the title or Back link
    const hasContent = await page.getByText("Back to Campaigns").isVisible().catch(() => false);
    if (!hasContent) {
      // Navigate via discover page click
      await page.goto("/contribute/discover");
      await page.getByText("Kitchen Manipulation").first().click();
      await page.waitForTimeout(1000);
    }
    await page.screenshot({ path: `${screenshotDir}/13-campaign-detail.png`, fullPage: true });
  });

  test("14 enrollments", async ({ page }) => {
    await page.goto("/contribute/enrollments");
    await page.waitForSelector("text=Enrollments");
    await page.screenshot({ path: `${screenshotDir}/14-enrollments.png`, fullPage: true });
  });

  test("15 enrollments unenroll modal", async ({ page }) => {
    await page.goto("/contribute/enrollments");
    await page.waitForSelector("text=Enrollments");
    await page.getByRole("button", { name: "Unenroll" }).first().click();
    await page.waitForSelector("text=Unenroll from");
    await page.screenshot({ path: `${screenshotDir}/15-unenroll-modal.png`, fullPage: true });
  });
});

test.describe("Journey 4: Earnings & Review", () => {
  test("16 contributions table", async ({ page }) => {
    await page.goto("/contribute/contributions");
    await page.waitForSelector("text=Contributions");
    await page.screenshot({ path: `${screenshotDir}/16-contributions.png`, fullPage: true });
  });

  test("17 contributions detail drawer", async ({ page }) => {
    await page.goto("/contribute/contributions");
    await page.waitForSelector("text=Contributions");
    await page.getByText("Kitchen Manip.").first().click();
    await page.waitForSelector("text=Instance #inst");
    await page.screenshot({ path: `${screenshotDir}/17-contribution-detail.png`, fullPage: true });
  });

  test("18 earnings", async ({ page }) => {
    await page.goto("/contribute/earnings");
    await page.waitForSelector("text=Earnings");
    await page.screenshot({ path: `${screenshotDir}/18-earnings.png`, fullPage: true });
  });

  test("19 payouts", async ({ page }) => {
    await page.goto("/contribute/payouts");
    await page.waitForSelector("text=Payouts");
    await page.screenshot({ path: `${screenshotDir}/19-payouts.png`, fullPage: true });
  });
});

test.describe("Journey 5: Profile & Settings", () => {
  test("20 profile overview", async ({ page }) => {
    await page.goto("/contribute/profile");
    await page.waitForSelector("text=Yi Zhang");
    await page.screenshot({ path: `${screenshotDir}/20-profile-overview.png`, fullPage: true });
  });

  test("21 profile credentials tab", async ({ page }) => {
    await page.goto("/contribute/profile");
    await page.waitForSelector("text=Yi Zhang");
    await page.getByText("Credentials").first().click();
    await page.waitForSelector("text=tutorial-passed");
    await page.screenshot({ path: `${screenshotDir}/21-profile-credentials.png`, fullPage: true });
  });

  test("22 settings", async ({ page }) => {
    await page.goto("/contribute/settings");
    await page.waitForSelector("text=Settings");
    await page.screenshot({ path: `${screenshotDir}/22-settings.png`, fullPage: true });
  });
});
