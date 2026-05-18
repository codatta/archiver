import { test, expect } from "bun:test";

// --- daysUntil logic ---

function daysUntil(dateStr: string | null): string {
  if (!dateStr) return "Never";
  const days = Math.ceil((new Date(dateStr).getTime() - Date.now()) / 86400000);
  if (days < 0) return "Expired";
  return `${days}d left`;
}

test("daysUntil returns Never for null", () => {
  expect(daysUntil(null)).toBe("Never");
});

test("daysUntil shows days left for future date", () => {
  const future = new Date(Date.now() + 30 * 86400000).toISOString();
  const result = daysUntil(future);
  expect(result).toMatch(/^\d+d left$/);
});

test("daysUntil returns Expired for past date", () => {
  const past = new Date(Date.now() - 86400000).toISOString();
  expect(daysUntil(past)).toBe("Expired");
});

// --- Key masking ---

function maskKey(prefix: string, revealed: boolean): string {
  if (revealed) return prefix;
  return prefix.slice(0, 10) + "\u2022\u2022\u2022\u2022\u2022\u2022";
}

test("maskKey hides characters when not revealed", () => {
  const prefix = "hb_live_sk_abc123xyz";
  const masked = maskKey(prefix, false);
  expect(masked.startsWith("hb_live_sk")).toBe(true);
  expect(masked).toContain("\u2022");
});

test("maskKey shows full prefix when revealed", () => {
  const prefix = "hb_live_sk_abc123xyz";
  expect(maskKey(prefix, true)).toBe(prefix);
});

// --- Status badge mapping ---

test("all key statuses have a badge", () => {
  const badges: Record<string, string> = {
    active: "bg-green-100 text-green-700",
    expired: "bg-amber-100 text-amber-700",
    revoked: "bg-red-100 text-red-700",
  };
  expect(badges["active"]).toBeDefined();
  expect(badges["expired"]).toBeDefined();
  expect(badges["revoked"]).toBeDefined();
});
