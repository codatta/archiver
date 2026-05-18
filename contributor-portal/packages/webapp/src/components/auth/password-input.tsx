"use client";

import { useMemo } from "react";

interface PasswordInputProps {
  value: string;
  onChange: (value: string) => void;
  id?: string;
}

const rules = [
  { label: "At least 8 characters", test: (p: string) => p.length >= 8 },
  { label: "One uppercase letter", test: (p: string) => /[A-Z]/.test(p) },
  { label: "One number", test: (p: string) => /\d/.test(p) },
  { label: "One special character", test: (p: string) => /[!@#$%^&*(),.?":{}|<>]/.test(p) },
];

const strengthLabels = ["", "Weak", "Fair", "Good", "Strong"] as const;
const strengthColors = ["", "bg-red-500", "bg-amber-500", "bg-amber-400", "bg-green-500"] as const;
const strengthTextColors = ["", "text-red-500", "text-amber-500", "text-amber-500", "text-green-600"] as const;

export function PasswordInput({ value, onChange, id = "password" }: PasswordInputProps) {
  const passed = useMemo(() => rules.filter((r) => r.test(value)).length, [value]);

  return (
    <div>
      <input
        id={id}
        type="password"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full px-5 py-3 border-[1.5px] border-[#1B1034] bg-white text-sm text-[#1B1034] focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10 outline-none transition"
      />

      {value.length > 0 && (
        <>
          {/* Strength bar */}
          <div className="flex gap-1 mt-2">
            {Array.from({ length: 4 }, (_, i) => (
              <div
                key={i}
                className={`h-1 flex-1 ${i < passed ? strengthColors[passed] : "bg-gray-200"}`}
              />
            ))}
          </div>
          <p className={`text-[11px] mt-1 ${strengthTextColors[passed]}`}>
            {strengthLabels[passed]}
          </p>

          {/* Rules checklist */}
          <ul className="mt-2 space-y-0.5">
            {rules.map((rule) => {
              const met = rule.test(value);
              return (
                <li
                  key={rule.label}
                  className={`text-[11px] ${met ? "text-green-600" : "text-gray-400"}`}
                >
                  {met ? "✓" : "✕"} {rule.label}
                </li>
              );
            })}
          </ul>
        </>
      )}
    </div>
  );
}

export function isPasswordValid(password: string): boolean {
  return rules.every((r) => r.test(password));
}
