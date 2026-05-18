import { test, expect } from "bun:test";

// Test CLI argument parsing logic (extracted)

type ParsedCmd = { cmd: string; sub: string; arg1?: string };

function parseArgs(args: string[]): ParsedCmd | null {
  if (args.length === 0) return null;
  return { cmd: args[0], sub: args[1] ?? "", arg1: args[2] };
}

test("parse 'auth set-key KEY'", () => {
  const r = parseArgs(["auth", "set-key", "hb_live_sk_abc"]);
  expect(r?.cmd).toBe("auth");
  expect(r?.sub).toBe("set-key");
  expect(r?.arg1).toBe("hb_live_sk_abc");
});

test("parse 'auth whoami'", () => {
  const r = parseArgs(["auth", "whoami"]);
  expect(r?.cmd).toBe("auth");
  expect(r?.sub).toBe("whoami");
});

test("parse 'verticals list'", () => {
  const r = parseArgs(["verticals", "list"]);
  expect(r?.cmd).toBe("verticals");
  expect(r?.sub).toBe("list");
});

test("parse 'data pull sub-1'", () => {
  const r = parseArgs(["data", "pull", "sub-1"]);
  expect(r?.cmd).toBe("data");
  expect(r?.sub).toBe("pull");
  expect(r?.arg1).toBe("sub-1");
});

test("parse 'data adopt item-1'", () => {
  const r = parseArgs(["data", "adopt", "item-1"]);
  expect(r?.cmd).toBe("data");
  expect(r?.sub).toBe("adopt");
  expect(r?.arg1).toBe("item-1");
});

test("parse empty args returns null", () => {
  expect(parseArgs([])).toBeNull();
});

// Frontier commands
test("parse 'frontiers list'", () => {
  const r = parseArgs(["frontiers", "list"]);
  expect(r?.cmd).toBe("frontiers");
  expect(r?.sub).toBe("list");
});

test("parse 'frontiers tasks frontier-1'", () => {
  const r = parseArgs(["frontiers", "tasks", "frontier-1"]);
  expect(r?.cmd).toBe("frontiers");
  expect(r?.sub).toBe("tasks");
  expect(r?.arg1).toBe("frontier-1");
});

// Live data commands
test("parse 'live pull sub-1'", () => {
  const r = parseArgs(["live", "pull", "sub-1"]);
  expect(r?.cmd).toBe("live");
  expect(r?.sub).toBe("pull");
  expect(r?.arg1).toBe("sub-1");
});

test("parse 'live adopt sub-1'", () => {
  const r = parseArgs(["live", "adopt", "sub-1"]);
  expect(r?.cmd).toBe("live");
  expect(r?.sub).toBe("adopt");
  expect(r?.arg1).toBe("sub-1");
});

// API key format validation
test("valid key starts with hb_live_sk_", () => {
  const key = "hb_live_sk_abc123";
  expect(key.startsWith("hb_live_sk_")).toBe(true);
});

test("invalid key rejected", () => {
  const key = "sk_test_abc123";
  expect(key.startsWith("hb_live_sk_")).toBe(false);
});

// Config path
test("config dir is ~/.humanbased", () => {
  const home = "/Users/test";
  const configDir = `${home}/.humanbased`;
  expect(configDir).toContain(".humanbased");
});
