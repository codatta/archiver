import { test, expect } from "bun:test";
import {
  DEFAULT_RULES,
  validatePassword,
  type Rule,
} from "../lib/password/rules";

test("empty string fails all rules and has score 0", () => {
  const v = validatePassword("");
  expect(v.valid).toBe(false);
  expect(v.passedCount).toBe(0);
  expect(v.score).toBe(0);
  expect(v.totalCount).toBe(DEFAULT_RULES.length);
  for (const r of v.rules) expect(r.passed).toBe(false);
});

test("strong password passes all rules", () => {
  const v = validatePassword("Abcdef1!X0");
  expect(v.valid).toBe(true);
  expect(v.passedCount).toBe(6);
  expect(v.score).toBe(4);
});

test("short password fails length rule only", () => {
  const v = validatePassword("Sh0rt!A");
  const length = v.rules.find((r) => r.id === "length");
  expect(length?.passed).toBe(false);
  // All other rules should pass for this input
  const others = v.rules.filter((r) => r.id !== "length");
  for (const r of others) expect(r.passed).toBe(true);
  expect(v.valid).toBe(false);
});

test("all-lowercase password fails uppercase rule", () => {
  const v = validatePassword("alllowercase123!");
  expect(v.rules.find((r) => r.id === "uppercase")?.passed).toBe(false);
  expect(v.valid).toBe(false);
});

test("all-uppercase password fails lowercase rule", () => {
  const v = validatePassword("ALLUPPERCASE123!");
  expect(v.rules.find((r) => r.id === "lowercase")?.passed).toBe(false);
  expect(v.valid).toBe(false);
});

test("no-digits password fails digit rule", () => {
  const v = validatePassword("NoDigitsHere!!");
  expect(v.rules.find((r) => r.id === "digit")?.passed).toBe(false);
  expect(v.valid).toBe(false);
});

test("no-special password fails special rule", () => {
  const v = validatePassword("NoSpecial123ABC");
  expect(v.rules.find((r) => r.id === "special")?.passed).toBe(false);
  expect(v.valid).toBe(false);
});

test("password with space fails whitespace rule", () => {
  const v = validatePassword("Has space123!A");
  expect(v.rules.find((r) => r.id === "no-whitespace")?.passed).toBe(false);
  expect(v.valid).toBe(false);
});

test("password with tab fails whitespace rule", () => {
  const v = validatePassword("Has\tTab123!A");
  expect(v.rules.find((r) => r.id === "no-whitespace")?.passed).toBe(false);
  expect(v.valid).toBe(false);
});

test("custom rules array only evaluates provided rules", () => {
  const custom: Rule[] = [
    { id: "length", label: "10 chars", test: (v) => v.length >= 10 },
    { id: "digit", label: "has digit", test: (v) => /[0-9]/.test(v) },
  ];
  const v = validatePassword("abcdefghij", custom);
  expect(v.totalCount).toBe(2);
  expect(v.rules.find((r) => r.id === "length")?.passed).toBe(true);
  expect(v.rules.find((r) => r.id === "digit")?.passed).toBe(false);
  expect(v.valid).toBe(false);
});

test("score maps from passedCount: 0-2 rules = 0, 3 = 1, 4 = 2, 5 = 3, 6 = 4", () => {
  // 0 rules met
  expect(validatePassword("").score).toBe(0);
  // 3 rules met: lowercase + digit + no-whitespace (too short, no upper, no special)
  expect(validatePassword("abc123").score).toBe(1);
  // 4 rules met: lowercase + uppercase + digit + no-whitespace (short, no special)
  expect(validatePassword("Abc123").score).toBe(2);
  // 5 rules met: length + lowercase + uppercase + digit + no-whitespace (no special)
  expect(validatePassword("Abcdefghij123").score).toBe(3);
  // 6 rules met: all
  expect(validatePassword("Abcdef1!X0").score).toBe(4);
});

test("DEFAULT_RULES exports 6 rules with expected ids", () => {
  const ids = DEFAULT_RULES.map((r) => r.id).sort();
  expect(ids).toEqual([
    "digit",
    "length",
    "lowercase",
    "no-whitespace",
    "special",
    "uppercase",
  ]);
});
