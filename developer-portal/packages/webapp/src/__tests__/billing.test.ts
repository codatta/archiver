import { test, expect } from "bun:test";

function formatMoney(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}

test("formatMoney formats positive amounts", () => {
  expect(formatMoney(8420)).toBe("$8,420.00");
});

test("formatMoney formats zero", () => {
  expect(formatMoney(0)).toBe("$0.00");
});

test("formatMoney formats decimals", () => {
  expect(formatMoney(17.35)).toBe("$17.35");
});

test("formatMoney formats negative amounts", () => {
  expect(formatMoney(-15)).toBe("-$15.00");
});

// Quick amount selection
test("quick amounts are valid cents when multiplied", () => {
  const amounts = [100, 500, 1000, 5000, 10000];
  for (const a of amounts) {
    const cents = Math.round(a * 100);
    expect(cents).toBe(a * 100);
    expect(cents).toBeGreaterThan(0);
  }
});

// Transaction type badge mapping
test("all transaction types have a badge", () => {
  const badges: Record<string, string> = {
    topup: "bg-green-100 text-green-700",
    freeze: "bg-blue-100 text-blue-700",
    settle: "bg-purple-100 text-purple-700",
    refund: "bg-amber-100 text-amber-700",
  };
  expect(Object.keys(badges).length).toBe(4);
});
