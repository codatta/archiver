import { useMemo } from "react";
import { DEFAULT_RULES, validatePassword, type Rule, type PasswordValidation } from "./rules";

export function usePasswordRules(value: string, rules: Rule[] = DEFAULT_RULES): PasswordValidation {
  return useMemo(() => validatePassword(value, rules), [value, rules]);
}
