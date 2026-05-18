import { test } from "@playwright/test";

// User journey screenshots for the contribution pipeline (I1-0 delivery).
// Captures four flows:
//   1. Campaign signup / enroll page
//   2. Task list — entry to the pipeline
//   3. Supply task (T1) — file upload + detection presets
//   4. Labeling task (T3a) — cull review with FramePlayer
//   5. Workspace instance switching — drawer open, then confirm dialog
//
// Output: tests/v1/ux-tests/pipeline-*.png
// Run: bun x playwright test e2e/contribution-pipeline-journey.spec.ts

const SCREENSHOT_DIR = "tests/v1/ux-tests";
const CAMPAIGN_ID = "camp-k1m";
const SUPPLY_TASK_ID = "t1-supply-55";
const LABELING_TASK_ID = "t3-label-48";
const OTHER_LABELING_TASK_ID = "t3-label-49";

test.describe("Contribution Pipeline — User Journey", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("01 campaign detail — enroll entry point", async ({ page }) => {
    await page.goto(`/contribute/campaigns/${CAMPAIGN_ID}`);
    await page.waitForSelector("text=Kitchen Manipulation");
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-01-campaign-signup.png`,
      fullPage: true,
    });
  });

  test("02 tasks list — pick an instance to work on", async ({ page }) => {
    await page.goto("/contribute/tasks");
    await page.waitForSelector("text=My Tasks");
    // Let priority pills and campaign tabs hydrate.
    await page.waitForTimeout(400);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-02-tasks-list.png`,
      fullPage: true,
    });
  });

  test("03 supply step — upload + detection presets", async ({ page }) => {
    await page.goto(`/workspace/${CAMPAIGN_ID}/${SUPPLY_TASK_ID}/supply`);
    await page.waitForSelector("text=Upload your capture");
    await page.waitForTimeout(200);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-03-supply.png`,
      fullPage: false,
    });

    // Expand Advanced parameters for a second shot.
    await page.getByRole("button", { name: /Advanced parameters/ }).click();
    await page.waitForTimeout(150);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-03b-supply-advanced-open.png`,
      fullPage: false,
    });
  });

  test("04 review step — cull review, frame player, timeline", async ({ page }) => {
    await page.goto(`/workspace/${CAMPAIGN_ID}/${LABELING_TASK_ID}/review`);
    await page.waitForSelector("text=Segment info");
    // Wait for Konva canvas to finish drawing.
    await page.waitForTimeout(600);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-04-review-cull.png`,
      fullPage: false,
    });

    // Press Y to mark the first segment valid, then capture progress.
    await page.keyboard.press("y");
    await page.waitForTimeout(300);
    await page.keyboard.press("n");
    await page.waitForTimeout(300);
    await page.keyboard.press("y");
    await page.waitForTimeout(400);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-04b-review-with-decisions.png`,
      fullPage: false,
    });
  });

  test("05 annotate step — action label palette, filmstrip, language", async ({ page }) => {
    await page.goto(`/workspace/${CAMPAIGN_ID}/${LABELING_TASK_ID}/annotate`);
    await page.waitForSelector("text=Action segments");
    await page.waitForTimeout(600);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-05-annotate.png`,
      fullPage: false,
    });

    // Assign a label via keyboard shortcut and write a language instruction.
    await page.keyboard.press("1");
    await page.waitForTimeout(150);
    await page
      .getByPlaceholder("Describe what the person is doing in this segment…")
      .fill("Person picks up a box and folds it onto the work surface.");
    await page.waitForTimeout(200);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-05b-annotate-with-label.png`,
      fullPage: false,
    });
  });

  test("06 export step — submit checklist", async ({ page }) => {
    await page.goto(`/workspace/${CAMPAIGN_ID}/${LABELING_TASK_ID}/export`);
    await page.waitForSelector("text=Submit Contribution");
    await page.waitForTimeout(200);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-06-export.png`,
      fullPage: true,
    });
  });

  test("07 instance switcher — open drawer from workspace", async ({ page }) => {
    // Start fresh (no dirty state yet)
    await page.goto(`/workspace/${CAMPAIGN_ID}/${LABELING_TASK_ID}/review`);
    await page.waitForSelector("text=Segment info");
    await page.waitForTimeout(600);

    // Open switcher by clicking the Instance #xxx label in the top-right
    await page.getByRole("button", { name: /Instance #/ }).click();
    await page.waitForSelector("text=Switch instance");
    await page.waitForTimeout(200);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-07a-switcher-open.png`,
      fullPage: false,
    });

    // Click "All enrolled" to show campaigns beyond the current one.
    await page.getByRole("button", { name: "All enrolled" }).click();
    await page.waitForTimeout(200);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-07b-switcher-all.png`,
      fullPage: false,
    });
  });

  test("08 confirm dialog — dirty work + cacheable draft", async ({ page }) => {
    await page.goto(`/workspace/${CAMPAIGN_ID}/${LABELING_TASK_ID}/review`);
    await page.waitForSelector("text=Segment info");
    await page.waitForTimeout(600);

    // Make review "dirty" by marking one segment
    await page.keyboard.press("y");
    await page.waitForTimeout(200);
    await page.keyboard.press("n");
    await page.waitForTimeout(200);

    // Now try to switch instance — should pop the confirmation dialog
    await page.getByRole("button", { name: /Instance #/ }).click();
    await page.waitForSelector("text=Switch instance");
    await page.getByRole("button", { name: /Review \d+ clips from kitchen demo/ }).first().click();

    await page.waitForSelector("text=Unsaved contribution");
    await page.waitForTimeout(200);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-08a-confirm-dialog-cacheable.png`,
      fullPage: false,
    });
  });

  test("09 confirm dialog — dirty work + non-cacheable (supply)", async ({ page }) => {
    await page.goto(`/workspace/${CAMPAIGN_ID}/${SUPPLY_TASK_ID}/supply`);
    await page.waitForSelector("text=Upload your capture");
    await page.waitForTimeout(300);

    // Fill task name — marks supply dirty
    await page.getByLabel("Task name").fill("kitchen_fold_demo_02");
    await page.waitForTimeout(200);

    // Try to navigate to review step via sub-task bar — but review is pending
    // (not yet visited), so we instead click Skip which goes to /contribute/tasks
    // and is always guarded.
    await page.getByRole("button", { name: /Skip/ }).click();
    await page.waitForSelector("text=Unsaved contribution");
    await page.waitForTimeout(200);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-08b-confirm-dialog-noncacheable.png`,
      fullPage: false,
    });
  });

  test("10 workspace chrome — full layout with all steps visible", async ({ page }) => {
    await page.goto(`/workspace/${CAMPAIGN_ID}/${LABELING_TASK_ID}/annotate`);
    await page.waitForSelector("text=Action segments");
    await page.waitForTimeout(600);
    // Viewport-height shot to emphasise the shell chrome (pipeline + sub-task + action bars)
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-09-workspace-chrome.png`,
      fullPage: false,
    });
  });
});

// Also capture an "up and down" navigation sequence — the user demoing
// instance switching through the drawer. Kept as a separate test so failures
// in earlier shots don't block this.
test.describe("Contribution Pipeline — Instance navigation sequence", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("sequence: review A → switcher → review B", async ({ page }) => {
    await page.goto(`/workspace/${CAMPAIGN_ID}/${LABELING_TASK_ID}/review`);
    await page.waitForSelector("text=Segment info");
    await page.waitForTimeout(500);

    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-10a-sequence-instance-a.png`,
      fullPage: false,
    });

    // Open switcher (no dirty state — no dialog)
    await page.getByRole("button", { name: /Instance #/ }).click();
    await page.waitForSelector("text=Switch instance");
    await page.waitForTimeout(200);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-10b-sequence-switcher.png`,
      fullPage: false,
    });

    // Click a different instance card
    await page.getByRole("button", { name: /Review bounding boxes/ }).first().click();
    await page.waitForURL(new RegExp(`/workspace/.*${OTHER_LABELING_TASK_ID}/review`), {
      timeout: 5000,
    });
    await page.waitForSelector("text=Segment info");
    await page.waitForTimeout(500);
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/pipeline-10c-sequence-instance-b.png`,
      fullPage: false,
    });
  });
});
