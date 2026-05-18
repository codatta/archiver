import { test, expect } from "@playwright/test";

test.describe("Home Dashboard", () => {
  test("renders dashboard with all sections", async ({ page }) => {
    await page.goto("/contribute");
    // Wait for hydration
    await page.waitForSelector("text=Good morning");

    await expect(page.getByText("Good morning, Yi")).toBeVisible();

    // 4 metric cards
    await expect(page.getByRole("main").getByText("Total Earned")).toBeVisible();
    await expect(page.getByRole("main").getByText("$847.20")).toBeVisible();
    await expect(page.getByText("Active Campaigns")).toBeVisible();

    // Attention section
    await expect(page.getByText("Needs Attention")).toBeVisible();
    await expect(page.getByText(/stuck in queue/)).toBeVisible();

    // Quick actions
    await expect(page.getByText("Continue Tasks →")).toBeVisible();
    await expect(page.getByText("Discover Campaigns →")).toBeVisible();
    await expect(page.getByText("View Earnings →")).toBeVisible();
  });

  test("quick action links navigate correctly", async ({ page }) => {
    await page.goto("/contribute");

    await page.getByText("Continue Tasks →").click();
    await page.waitForURL("/contribute/tasks");
    await expect(page.getByText("My Tasks")).toBeVisible();
  });
});

test.describe("Sidebar Navigation", () => {
  test("all nav items visible and clickable", async ({ page }) => {
    await page.goto("/contribute");
    await page.waitForSelector("aside");

    // Section labels in sidebar
    const sidebar = page.locator("aside");
    await expect(sidebar.getByText("WORK")).toBeVisible();
    await expect(sidebar.getByText("EARNINGS", { exact: true })).toBeVisible();

    // Nav items — ordered: Tasks > Discover > Enrollments > Contributions > Earnings
    await expect(sidebar.getByRole("link", { name: "Tasks" })).toBeVisible();
    await expect(sidebar.getByRole("link", { name: "Discover" })).toBeVisible();
    await expect(sidebar.getByRole("link", { name: "Enrollments" })).toBeVisible();
    await expect(sidebar.getByRole("link", { name: "Contributions" })).toBeVisible();
    await expect(sidebar.getByRole("link", { name: "Earnings" })).toBeVisible();

    // Footer has Docs link
    await expect(sidebar.getByText("Docs")).toBeVisible();
  });

  test("nav items navigate to correct pages", async ({ page }) => {
    await page.goto("/contribute");
    const sidebar = page.locator("aside");

    await sidebar.getByRole("link", { name: "Tasks" }).click();
    await page.waitForURL("/contribute/tasks");
    await expect(page.getByRole("main").getByRole("heading", { name: "Tasks" })).toBeVisible();

    await sidebar.getByRole("link", { name: "Discover" }).click();
    await page.waitForURL("/contribute/discover");
    await expect(page.getByRole("main").getByRole("heading", { name: "Discover" })).toBeVisible();

    await sidebar.getByRole("link", { name: "Enrollments" }).click();
    await page.waitForURL("/contribute/enrollments");
    await expect(page.getByRole("main").getByRole("heading", { name: "Enrollments" })).toBeVisible();

    await sidebar.getByRole("link", { name: "Contributions" }).click();
    await page.waitForURL("/contribute/contributions");
    await expect(page.getByRole("main").getByRole("heading", { name: "Contributions" })).toBeVisible();

    await sidebar.getByRole("link", { name: "Earnings" }).click();
    await page.waitForURL("/contribute/earnings");
    await expect(page.getByRole("main").getByRole("heading", { name: "Earnings" })).toBeVisible();
  });

  test("sidebar collapses", async ({ page }) => {
    await page.goto("/contribute");
    await page.waitForSelector("aside");

    const sidebar = page.locator("aside");
    const boxBefore = await sidebar.boundingBox();
    expect(boxBefore?.width).toBeGreaterThan(150);

    // Click collapse toggle (last button in sidebar)
    await sidebar.locator("button").last().click();
    await page.waitForTimeout(300);

    const boxAfter = await sidebar.boundingBox();
    expect(boxAfter?.width).toBeLessThan(100);
  });
});

test.describe("Discover", () => {
  test("renders campaign grid with 4 cards", async ({ page }) => {
    await page.goto("/contribute/discover");

    await expect(page.getByRole("main").getByRole("heading", { name: "Discover" })).toBeVisible();
    await expect(page.getByText("Find campaigns and start earning")).toBeVisible();

    await expect(page.getByText("Kitchen Manipulation")).toBeVisible();
    await expect(page.getByText("RoboMIND Trajectories")).toBeVisible();
    await expect(page.getByText("Egocentric Experience")).toBeVisible();
    await expect(page.getByText("Humanoid Motion Library")).toBeVisible();

    await expect(page.getByText("4 campaigns")).toBeVisible();
  });

  test("campaign cards show correct compensation info", async ({ page }) => {
    await page.goto("/contribute/discover");

    await expect(page.getByText(/Fixed.*\$2\.50/)).toBeVisible();
    await expect(page.getByText(/Royalty.*\$1\.80/)).toBeVisible();
    await expect(page.getByText(/Hybrid.*\$1\.00/)).toBeVisible();
    await expect(page.getByText(/Bounty.*\$5,000/)).toBeVisible();
  });

  test("qualification states display correctly", async ({ page }) => {
    await page.goto("/contribute/discover");

    await expect(page.getByText("✓ You qualify").first()).toBeVisible();
    await expect(page.getByText("⚠ 1 req not met")).toBeVisible();
    await expect(page.getByText("✕ 2 reqs not met")).toBeVisible();
  });
});

test.describe("Tasks Queue", () => {
  test("renders priority pills and campaign groups", async ({ page }) => {
    await page.goto("/contribute/tasks");

    await expect(page.getByText("My Tasks")).toBeVisible();
    await expect(page.getByText("7 submitted")).toBeVisible();

    // Priority pills
    await expect(page.getByText("Priority Items")).toBeVisible();
    await expect(page.getByRole("button", { name: /Resume/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Expiring/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Dispute/ })).toBeVisible();

    // Task cards present
    await expect(page.getByText("Upload kitchen task video").first()).toBeVisible();
  });

  test("priority pills expand carousel", async ({ page }) => {
    await page.goto("/contribute/tasks");

    await page.getByRole("button", { name: /Resume/ }).click();
    await expect(page.getByText("Review 12 clips from kitchen demo")).toBeVisible({ timeout: 2000 });

    await page.getByRole("button", { name: /Resume/ }).click();
    await page.waitForTimeout(400);
  });

  test("campaign selector visible", async ({ page }) => {
    await page.goto("/contribute/tasks");
    // Horizontal campaign tabs — truncated names
    await expect(page.getByRole("button", { name: /Kitchen/ })).toBeVisible();
  });
});

test.describe("Contributions Table", () => {
  test("renders table with header and data rows", async ({ page }) => {
    await page.goto("/contribute/contributions");

    await expect(page.getByRole("heading", { name: "Contributions" })).toBeVisible();
    await expect(page.getByText("147 submissions")).toBeVisible();

    for (const col of ["Campaign", "Type", "Instance", "Chain ID", "Status", "Stage", "Pay"]) {
      await expect(page.getByRole("columnheader", { name: col })).toBeVisible();
    }

    await expect(page.getByText("Kitchen Manip.").first()).toBeVisible();
    await expect(page.getByText("RoboMIND")).toBeVisible();
    await expect(page.getByText("#inst-4f2a")).toBeVisible();

    await expect(page.getByText("✓ Accepted").first()).toBeVisible();
    await expect(page.getByText("● Working")).toBeVisible();
    await expect(page.getByText("✕ Rejected")).toBeVisible();
  });

  test("pagination and export visible", async ({ page }) => {
    await page.goto("/contribute/contributions");

    await expect(page.getByText("Showing 1–6 of 147")).toBeVisible();
    await expect(page.getByText("← Prev")).toBeVisible();
    await expect(page.getByText("Next →")).toBeVisible();
    await expect(page.getByText("Export CSV ↓")).toBeVisible();
  });
});

test.describe("Earnings", () => {
  test("renders summary cards and pipeline breakdown", async ({ page }) => {
    await page.goto("/contribute/earnings");

    await expect(page.getByRole("heading", { name: "Earnings" })).toBeVisible();

    await expect(page.getByText("$1,240.00")).toBeVisible();
    await expect(page.getByText("$420.00")).toBeVisible();
    await expect(page.getByText("$86.50")).toBeVisible();

    await expect(page.getByText("Pipeline Breakdown")).toBeVisible();
    await expect(page.getByText(/Stalled.*Egocentric/)).toBeVisible();
    await expect(page.getByText("Transaction History")).toBeVisible();
    await expect(page.getByText("Go to Payouts →")).toBeVisible();
  });
});

test.describe("Profile", () => {
  test("renders hero and overview tab", async ({ page }) => {
    await page.goto("/contribute/profile");

    const main = page.getByRole("main");

    // Hero section
    await expect(main.getByText("Yi Zhang")).toBeVisible();
    await expect(main.getByText("@yi_zhang")).toBeVisible();
    await expect(main.getByText("yi@humanbased.io")).toBeVisible();
    await expect(main.getByText("Member since Dec 2024")).toBeVisible();
    await expect(main.getByText("Edit Profile")).toBeVisible();

    // Tabs
    await expect(main.getByText("Overview")).toBeVisible();
    await expect(main.getByText("Credentials")).toBeVisible();

    // Overview metrics
    await expect(main.getByText("/ 1,000")).toBeVisible();
    await expect(main.getByText("$847.20")).toBeVisible();
    await expect(main.getByText("3 campaigns active")).toBeVisible();

    // Skills snapshot
    await expect(main.getByText("Robotics Annotation")).toBeVisible();
  });

  test("credentials tab shows tier badges", async ({ page }) => {
    await page.goto("/contribute/profile");
    await page.getByText("Credentials").click();

    await expect(page.getByText("tutorial-passed")).toBeVisible();
    await expect(page.getByText("credential-verified")).toBeVisible();
    await expect(page.getByText("unverified")).toBeVisible();
    await expect(page.getByText("Start Training →")).toBeVisible();
  });
});

test.describe("Onboarding", () => {
  test("step 1: skill selection works", async ({ page }) => {
    await page.goto("/onboarding");

    await expect(page.getByText("What are you good at?")).toBeVisible();

    await page.getByText("Robotics Annotation").click();
    await page.getByText("Data Collection").click();

    const continueBtn = page.getByRole("button", { name: "Continue" });
    await expect(continueBtn).toBeEnabled();
    await continueBtn.click();

    await expect(page.getByText("What kind of work interests you?")).toBeVisible();
  });

  test("step 2: task type and time selection", async ({ page }) => {
    await page.goto("/onboarding");
    await page.getByText("Skip for now").click();

    await expect(page.getByText("What kind of work interests you?")).toBeVisible();
    await page.getByText("Supply", { exact: false }).first().click();
    await page.getByText("5–15 hrs").click();

    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByText("You're all set!")).toBeVisible();
  });

  test("step 3: shows profile summary and CTA", async ({ page }) => {
    await page.goto("/onboarding");
    await page.getByText("Skip for now").click();
    await page.getByText("Skip for now").click();

    await expect(page.getByText("You're all set!")).toBeVisible();
    await expect(page.getByText("Yi Zhang")).toBeVisible();
    await expect(page.getByText("Discover Campaigns →")).toBeVisible();
    await expect(page.getByText("Go to Dashboard")).toBeVisible();
  });
});
