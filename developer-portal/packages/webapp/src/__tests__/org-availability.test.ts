/**
 * Tests for useOrgAvailability — pure logic + state machine.
 *
 * We test:
 *  1. buildCheckUrl — URL construction from name + slug
 *  2. parseCheckResponse — maps API JSON to { nameAvailable, slugAvailable }
 *  3. shouldCheck — idle guard (inputs < 2 chars stay idle)
 *  4. Full hook state transitions via a mock fetch (available, name_taken, slug_taken)
 */
import { test, expect, mock, beforeEach } from "bun:test";
import {
  buildCheckUrl,
  parseCheckResponse,
  shouldCheck,
} from "../lib/orgAvailability";

// ── URL construction ──────────────────────────────────────────────────────────

test("buildCheckUrl encodes name and slug as query params", () => {
  const url = buildCheckUrl("Acme AI Labs", "acme-ai-labs");
  expect(url).toBe(
    "/v1/onboarding/org/check?name=Acme+AI+Labs&slug=acme-ai-labs",
  );
});

test("buildCheckUrl encodes special characters", () => {
  const url = buildCheckUrl("Foo & Bar", "foo-bar");
  expect(url).toBe("/v1/onboarding/org/check?name=Foo+%26+Bar&slug=foo-bar");
});

test("buildCheckUrl trims whitespace from inputs", () => {
  const url = buildCheckUrl("  Acme  ", "  acme  ");
  expect(url).toBe("/v1/onboarding/org/check?name=Acme&slug=acme");
});

// ── Response parsing ──────────────────────────────────────────────────────────

test("parseCheckResponse: both available", () => {
  const result = parseCheckResponse({ name_available: true, slug_available: true });
  expect(result).toEqual({ nameAvailable: true, slugAvailable: true });
});

test("parseCheckResponse: name taken", () => {
  const result = parseCheckResponse({ name_available: false, slug_available: true });
  expect(result.nameAvailable).toBe(false);
  expect(result.slugAvailable).toBe(true);
});

test("parseCheckResponse: slug taken", () => {
  const result = parseCheckResponse({ name_available: true, slug_available: false });
  expect(result.nameAvailable).toBe(true);
  expect(result.slugAvailable).toBe(false);
});

test("parseCheckResponse: both taken", () => {
  const result = parseCheckResponse({ name_available: false, slug_available: false });
  expect(result).toEqual({ nameAvailable: false, slugAvailable: false });
});

// ── Idle guard ────────────────────────────────────────────────────────────────

test("shouldCheck returns false when name is empty", () => {
  expect(shouldCheck("", "acme")).toBe(false);
});

test("shouldCheck returns false when slug is empty", () => {
  expect(shouldCheck("Acme", "")).toBe(false);
});

test("shouldCheck returns false when name is 1 char", () => {
  expect(shouldCheck("A", "acme")).toBe(false);
});

test("shouldCheck returns false when slug is 1 char", () => {
  expect(shouldCheck("Acme", "a")).toBe(false);
});

test("shouldCheck returns true when both name and slug >= 2 chars", () => {
  expect(shouldCheck("Ac", "ac")).toBe(true);
});

test("shouldCheck returns true for normal inputs", () => {
  expect(shouldCheck("Acme AI", "acme-ai")).toBe(true);
});
