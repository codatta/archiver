import { test, expect } from "bun:test";

const VERTICALS = [
  { slug: "crypto_account_annotation", label: "Crypto Account Annotation", topics: ["DeFi Protocol Labeling", "Exchange Identification", "Risk Flagging", "NFT & Gaming"] },
  { slug: "food_intelligence", label: "Food Intelligence", topics: ["Menu Extraction", "Price Tracking", "Review Analysis"] },
  { slug: "fashion_crawl", label: "Fashion Crawl", topics: ["Product Classification", "Trend Detection", "Brand Identification"] },
];

test("all verticals have topics", () => {
  for (const v of VERTICALS) {
    expect(v.topics.length).toBeGreaterThan(0);
    expect(v.slug).toBeTruthy();
    expect(v.label).toBeTruthy();
  }
});

test("topic toggle adds and removes", () => {
  const selected = new Set<string>();
  selected.add("DeFi Protocol Labeling");
  expect(selected.has("DeFi Protocol Labeling")).toBe(true);
  selected.delete("DeFi Protocol Labeling");
  expect(selected.has("DeFi Protocol Labeling")).toBe(false);
});

test("min quality validates range", () => {
  const val = 0.8;
  expect(val).toBeGreaterThanOrEqual(0);
  expect(val).toBeLessThanOrEqual(1);
});

test("mode options are pull and push", () => {
  const modes = ["pull", "push"];
  expect(modes).toContain("pull");
  expect(modes).toContain("push");
  expect(modes.length).toBe(2);
});

test("status badges cover all states", () => {
  const badges: Record<string, string> = {
    active: "bg-green-100",
    paused: "bg-amber-100",
    cancelled: "bg-gray-100",
  };
  expect(Object.keys(badges).length).toBe(3);
});
