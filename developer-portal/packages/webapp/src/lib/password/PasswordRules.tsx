import React from "react";
import type { PasswordValidation } from "./rules";

interface Props {
  validation: PasswordValidation;
  isDirty: boolean;
}

type RowState = "idle" | "passing" | "failing";

function getRowState(passed: boolean, isDirty: boolean): RowState {
  if (passed) return "passing";
  if (!isDirty) return "idle";
  return "failing";
}

const STATE_ICON: Record<RowState, string> = {
  idle: "○",
  passing: "✓",
  failing: "✕",
};

const STATE_CLASS: Record<RowState, string> = {
  idle: "text-gray-400",
  passing: "text-emerald-600",
  failing: "text-red-500",
};

export function PasswordRules({ validation, isDirty }: Props) {
  return (
    <ul aria-live="polite" className="mt-2 space-y-1">
      {validation.rules.map((r) => {
        const state = getRowState(r.passed, isDirty);
        const ariaLabel = `${r.label} — ${r.passed ? "met" : "not met"}`;
        return (
          <li
            key={r.id}
            data-rule-row={r.id}
            data-rule-state={state}
            aria-label={ariaLabel}
            className={`flex items-center gap-2 text-xs ${STATE_CLASS[state]}`}
          >
            <span aria-hidden="true" className="inline-block w-3 text-center">
              {STATE_ICON[state]}
            </span>
            <span>{r.label}</span>
          </li>
        );
      })}
    </ul>
  );
}
