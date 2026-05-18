import React from "react";

interface Props {
  score: 0 | 1 | 2 | 3 | 4;
}

const SEGMENT_COUNT = 4;

const COLORS: Record<0 | 1 | 2 | 3 | 4, { bar: string; label: string }> = {
  0: { bar: "bg-red-500", label: "Too weak" },
  1: { bar: "bg-red-500", label: "Weak" },
  2: { bar: "bg-amber-500", label: "Fair" },
  3: { bar: "bg-blue-500", label: "Good" },
  4: { bar: "bg-emerald-500", label: "Strong" },
};

export function StrengthMeter({ score }: Props) {
  const { bar, label } = COLORS[score];
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={4}
      aria-valuenow={score}
      aria-label={`Password strength: ${label}`}
      className="mt-2"
    >
      <div className="flex gap-1">
        {Array.from({ length: SEGMENT_COUNT }, (_, i) => {
          const active = i < score;
          return (
            <span
              key={i}
              data-segment={i}
              data-active={active ? "true" : "false"}
              className={`h-1 flex-1 rounded-sm ${active ? bar : "bg-gray-200"}`}
            />
          );
        })}
      </div>
      <p className="mt-1 text-[11px] text-gray-500">{label}</p>
    </div>
  );
}
