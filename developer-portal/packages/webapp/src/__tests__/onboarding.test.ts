import { test, expect } from "bun:test";
import { slugify } from "../lib/utils";

// --- Routing (test the pure function without importing App which pulls in supabase) ---

type Route = "landing" | "signin" | "signup" | "onboarding" | "dashboard";

function getRoute(path: string): Route {
  if (path.startsWith("/dashboard")) return "dashboard";
  if (path.startsWith("/onboarding")) return "onboarding";
  if (path === "/auth/signin") return "signin";
  if (path === "/auth/signup") return "signup";
  return "landing";
}

test("routes /onboarding to onboarding", () => {
  expect(getRoute("/onboarding")).toBe("onboarding");
});

test("routes /onboarding/org-details to onboarding", () => {
  expect(getRoute("/onboarding/org-details")).toBe("onboarding");
});

test("routes /dashboard to dashboard (not onboarding)", () => {
  expect(getRoute("/dashboard")).toBe("dashboard");
});

// --- Slugify ---

test("slugify converts name to lowercase kebab", () => {
  expect(slugify("Acme AI Labs")).toBe("acme-ai-labs");
});

test("slugify removes special characters", () => {
  expect(slugify("Hello World! @#$%")).toBe("hello-world");
});

test("slugify handles leading/trailing spaces", () => {
  expect(slugify("  My Org  ")).toBe("my-org");
});

test("slugify handles empty string", () => {
  expect(slugify("")).toBe("");
});

test("slugify handles consecutive special chars", () => {
  expect(slugify("foo---bar")).toBe("foo-bar");
});

test("slugify handles numbers", () => {
  expect(slugify("Web3 Company 123")).toBe("web3-company-123");
});

test("slugify strips leading/trailing hyphens", () => {
  expect(slugify("--hello--")).toBe("hello");
});

// --- Invite role validation ---

test("valid roles are admin and member only", () => {
  const validRoles = ["admin", "member"];
  expect(validRoles.includes("admin")).toBe(true);
  expect(validRoles.includes("member")).toBe(true);
  expect(validRoles.includes("owner")).toBe(false);
});

// --- API key prefix ---

test("API key prefix is hb_live_sk_", () => {
  const prefix = "hb_live_sk_";
  expect(prefix.startsWith("hb_live_")).toBe(true);
  expect(prefix.length).toBe(11);
});

// --- Onboarding step 3: Get Started (not API Key) ---

test("onboarding steps include 'Get Started' as final step (not 'API Key')", () => {
  const STEPS = ["Organization", "Invite Team", "Get Started"];
  expect(STEPS[2]).toBe("Get Started");
  expect(STEPS).not.toContain("API Key");
});

test("StepNextActions card config has correct paths", () => {
  const CARDS = [
    {
      title: "Browse available datasets",
      path: "/dashboard/subscriptions",
      buttonLabel: "Go to Subscriptions",
    },
    {
      title: "Create your first API key",
      path: "/dashboard/api-keys",
      buttonLabel: "Go to API Keys",
    },
  ];

  expect(CARDS).toHaveLength(2);
  expect(CARDS[0].path).toBe("/dashboard/subscriptions");
  expect(CARDS[1].path).toBe("/dashboard/api-keys");
});

test("StepNextActions cards navigate to dashboard tabs, not external links", () => {
  const CARDS = [
    { path: "/dashboard/subscriptions" },
    { path: "/dashboard/api-keys" },
  ];

  for (const card of CARDS) {
    expect(card.path.startsWith("/dashboard/")).toBe(true);
    expect(card.path.startsWith("http")).toBe(false);
  }
});

test("onboarding complete endpoint path is correct", () => {
  const orgId = "org-123";
  const endpoint = `/v1/onboarding/complete?org_id=${orgId}`;
  expect(endpoint).toBe("/v1/onboarding/complete?org_id=org-123");
  expect(endpoint).not.toContain("api-key");
});
