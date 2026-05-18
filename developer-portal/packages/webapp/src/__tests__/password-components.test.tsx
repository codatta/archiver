import { test, expect } from "bun:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { PasswordRules } from "../lib/password/PasswordRules";
import { StrengthMeter } from "../lib/password/StrengthMeter";
import { validatePassword } from "../lib/password/rules";

test("PasswordRules renders one row per rule", () => {
  const validation = validatePassword("");
  const html = renderToStaticMarkup(
    <PasswordRules validation={validation} isDirty={false} />,
  );
  const rowCount = (html.match(/data-rule-row=/g) || []).length;
  expect(rowCount).toBe(validation.rules.length);
  expect(rowCount).toBe(6);
});

test("PasswordRules suppresses red state when isDirty=false", () => {
  const validation = validatePassword(""); // all failing
  const html = renderToStaticMarkup(
    <PasswordRules validation={validation} isDirty={false} />,
  );
  // No red styling applied when not dirty
  expect(html).not.toContain("text-red-500");
  // Muted state should be present
  expect(html).toContain("data-rule-state=\"idle\"");
});

test("PasswordRules shows red state for failing rules when isDirty=true", () => {
  const validation = validatePassword("abc"); // multiple failures
  const html = renderToStaticMarkup(
    <PasswordRules validation={validation} isDirty={true} />,
  );
  expect(html).toContain("data-rule-state=\"failing\"");
  expect(html).toContain("text-red-500");
});

test("PasswordRules shows green state for passing rules", () => {
  const validation = validatePassword("Abcdef1!X0"); // all passing
  const html = renderToStaticMarkup(
    <PasswordRules validation={validation} isDirty={true} />,
  );
  expect(html).toContain("data-rule-state=\"passing\"");
  expect(html).toContain("text-emerald-600");
});

test("PasswordRules sets aria-label describing met/not met per rule", () => {
  const validation = validatePassword("abc");
  const html = renderToStaticMarkup(
    <PasswordRules validation={validation} isDirty={true} />,
  );
  expect(html).toContain("aria-label");
  expect(html).toMatch(/— (met|not met)/);
});

test("StrengthMeter renders 4 segments", () => {
  const html = renderToStaticMarkup(<StrengthMeter score={0} />);
  const segmentCount = (html.match(/data-segment=/g) || []).length;
  expect(segmentCount).toBe(4);
});

test("StrengthMeter activates N segments based on score", () => {
  const score0 = renderToStaticMarkup(<StrengthMeter score={0} />);
  const score2 = renderToStaticMarkup(<StrengthMeter score={2} />);
  const score4 = renderToStaticMarkup(<StrengthMeter score={4} />);

  expect((score0.match(/data-active="true"/g) || []).length).toBe(0);
  expect((score2.match(/data-active="true"/g) || []).length).toBe(2);
  expect((score4.match(/data-active="true"/g) || []).length).toBe(4);
});

test("StrengthMeter has role=progressbar with aria-valuenow", () => {
  const html = renderToStaticMarkup(<StrengthMeter score={2} />);
  expect(html).toContain('role="progressbar"');
  expect(html).toContain('aria-valuenow="2"');
  expect(html).toContain('aria-valuemin="0"');
  expect(html).toContain('aria-valuemax="4"');
});
