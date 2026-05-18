import { cn } from "@/lib/utils";

interface StepIndicatorProps {
  steps: number;
  current: number;
}

export function StepIndicator({ steps, current }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-0">
      {Array.from({ length: steps }, (_, i) => {
        const step = i + 1;
        const isCompleted = step < current;
        const isActive = step === current;

        return (
          <div key={step} className="flex items-center">
            <div
              className={cn(
                "w-7 h-7 flex items-center justify-center text-xs font-semibold rounded-full",
                isCompleted && "bg-[#834DFB] text-white",
                isActive && "bg-[#1B1034] text-white",
                !isCompleted && !isActive && "bg-gray-200 text-gray-500",
              )}
            >
              {isCompleted ? "✓" : step}
            </div>
            {step < steps && (
              <div
                className={cn(
                  "w-12 h-[2px]",
                  step < current ? "bg-[#834DFB]" : "bg-gray-200",
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
