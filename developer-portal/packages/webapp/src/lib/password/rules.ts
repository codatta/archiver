// =============================================================================
// SUPABASE AUTH DEPENDENCY
// =============================================================================
// These rules MUST stay in sync with the Supabase Auth password policy
// configured for project uxafdddzhgdhsabkwmgw.
//
// How to verify / update:
//   Supabase dashboard → Authentication → Providers → Email → Password policy
//   OR via management API:
//   GET https://api.supabase.com/v1/projects/uxafdddzhgdhsabkwmgw/config/auth
//   (fields: password_min_length, password_required_characters)
//
// Current Supabase settings (as of 2026-04-10):
//   Minimum length     : VERIFY IN DASHBOARD (default is 6; our rule enforces ≥10)
//   Required chars     : VERIFY IN DASHBOARD (our rules cover all Supabase options)
//   Leaked pw check    : VERIFY IN DASHBOARD (Pro plan feature, no client-side equivalent)
//
// Invariant: every password that passes ALL DEFAULT_RULES here must also be
// accepted by Supabase. If Supabase minimum length is raised above 10, update
// the "length" rule below accordingly.
//
// Supabase allowed symbols (must match SPECIAL_CHAR_RE):
//   ! @ # $ % ^ & * ( ) _ + - = [ ] { } ; ' \ : " | , . < > / ? ` ~
// =============================================================================

export type RuleId =
  | "length"
  | "uppercase"
  | "lowercase"
  | "digit"
  | "special"
  | "no-whitespace";

export interface Rule {
  id: RuleId;
  label: string;
  test: (value: string) => boolean;
}

export interface RuleResult {
  id: RuleId;
  label: string;
  passed: boolean;
}

export interface PasswordValidation {
  rules: RuleResult[];
  passedCount: number;
  totalCount: number;
  score: 0 | 1 | 2 | 3 | 4;
  valid: boolean;
}

const SPECIAL_CHAR_RE = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]/;
const WHITESPACE_RE = /\s/;

export const DEFAULT_RULES: Rule[] = [
  {
    id: "length",
    label: "At least 10 characters",
    test: (v) => v.length >= 10,
  },
  {
    id: "uppercase",
    label: "At least one uppercase letter",
    test: (v) => /[A-Z]/.test(v),
  },
  {
    id: "lowercase",
    label: "At least one lowercase letter",
    test: (v) => /[a-z]/.test(v),
  },
  {
    id: "digit",
    label: "At least one number",
    test: (v) => /[0-9]/.test(v),
  },
  {
    id: "special",
    label: "At least one special character",
    test: (v) => SPECIAL_CHAR_RE.test(v),
  },
  {
    id: "no-whitespace",
    label: "No spaces",
    test: (v) => v.length > 0 && !WHITESPACE_RE.test(v),
  },
];

// Map passedCount → 0..4 score bucket.
// 0-2 → 0 (weak), 3 → 1, 4 → 2, 5 → 3, 6 → 4 (strong).
function scoreFromPassed(passed: number): 0 | 1 | 2 | 3 | 4 {
  if (passed <= 2) return 0;
  if (passed === 3) return 1;
  if (passed === 4) return 2;
  if (passed === 5) return 3;
  return 4;
}

export function validatePassword(
  value: string,
  rules: Rule[] = DEFAULT_RULES,
): PasswordValidation {
  const results: RuleResult[] = rules.map((r) => ({
    id: r.id,
    label: r.label,
    passed: r.test(value),
  }));
  const passedCount = results.reduce((n, r) => n + (r.passed ? 1 : 0), 0);
  const totalCount = results.length;
  return {
    rules: results,
    passedCount,
    totalCount,
    score: scoreFromPassed(passedCount),
    valid: passedCount === totalCount,
  };
}
