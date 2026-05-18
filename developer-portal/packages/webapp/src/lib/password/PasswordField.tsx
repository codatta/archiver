import React, { useState } from "react";

interface Props {
  id?: string;
  value: string;
  onChange: (v: string) => void;
  onBlur?: () => void;
  placeholder?: string;
  autoComplete?: string;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  className?: string;
  required?: boolean;
  name?: string;
}

/**
 * Password input with eye toggle. Independent visibility state per instance
 * so two fields on the same screen can be toggled independently.
 */
export function PasswordField({
  id,
  value,
  onChange,
  onBlur,
  placeholder,
  autoComplete,
  ariaLabel,
  ariaDescribedBy,
  className,
  required,
  name,
}: Props) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <input
        id={id}
        name={name}
        type={visible ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        placeholder={placeholder}
        autoComplete={autoComplete}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        required={required}
        className={className}
      />
      <button
        type="button"
        aria-pressed={visible}
        aria-label={visible ? "Hide password" : "Show password"}
        onClick={() => setVisible((v) => !v)}
        className="absolute inset-y-0 right-2 flex items-center text-xs text-gray-500 hover:text-[#1B1034]"
      >
        {visible ? "Hide" : "Show"}
      </button>
    </div>
  );
}
