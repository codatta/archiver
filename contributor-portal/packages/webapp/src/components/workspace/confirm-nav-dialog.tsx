"use client";

import { useEffect } from "react";
import { AlertTriangle, CloudCheck, CloudOff, X } from "lucide-react";
import { useWorkspaceNav } from "./nav-context";

// Confirmation modal that opens when a guarded navigation is requested
// while there's unsaved work. Rendered once at the workspace layout level;
// pendingNav in context drives visibility.
export function ConfirmNavDialog() {
  const { dirty, pendingNav, acceptPendingNav, cancelPendingNav } = useWorkspaceNav();

  // Close on Escape.
  useEffect(() => {
    if (!pendingNav) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") cancelPendingNav();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pendingNav, cancelPendingNav]);

  if (!pendingNav) return null;

  const cacheable = dirty.isDraftCacheable;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-[1px]"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-nav-title"
    >
      <div className="bg-white border-[1.5px] border-[#1B1034] shadow-2xl w-[480px] max-w-[92vw]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b-[1.5px] border-[#1B1034]">
          <div className="flex items-center gap-2.5">
            <AlertTriangle size={18} className="text-amber-500" />
            <h2 id="confirm-nav-title" className="text-sm font-bold text-[#1B1034]">
              Unsaved contribution
            </h2>
          </div>
          <button
            type="button"
            onClick={cancelPendingNav}
            className="text-[#9890A8] hover:text-[#1B1034] transition cursor-pointer"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-3">
          <p className="text-sm text-[#1B1034] font-medium">{dirty.description}</p>

          <div
            className={`flex items-start gap-2.5 px-3.5 py-3 border-[1.5px] ${
              cacheable ? "border-green-200 bg-green-50" : "border-amber-200 bg-amber-50"
            }`}
          >
            {cacheable ? (
              <CloudCheck size={16} className="text-green-600 mt-0.5 shrink-0" />
            ) : (
              <CloudOff size={16} className="text-amber-600 mt-0.5 shrink-0" />
            )}
            <div>
              <p
                className={`text-xs font-semibold ${
                  cacheable ? "text-green-700" : "text-amber-700"
                }`}
              >
                {cacheable
                  ? "Your draft will be cached remotely"
                  : "Your work cannot be saved yet"}
              </p>
              <p className="text-xs text-[#5C5470] mt-1 leading-relaxed">
                {cacheable
                  ? "We'll restore this step exactly where you left off next time you open this instance. No work will be lost."
                  : "This step doesn't support drafts yet. If you leave now, your in-progress changes will be discarded."}
              </p>
            </div>
          </div>

          <p className="text-xs text-[#5C5470]">
            Destination: <span className="font-mono text-[#1B1034]">{pendingNav.label}</span>
          </p>
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t-[1.5px] border-[#1B1034] bg-[#F5F5F3] flex items-center justify-end gap-2.5">
          <button
            type="button"
            onClick={cancelPendingNav}
            className="h-9 px-4 border-[1.5px] border-[#1B1034] text-[#1B1034] text-xs font-medium hover:bg-white transition cursor-pointer"
          >
            Stay on this step
          </button>
          <button
            type="button"
            onClick={acceptPendingNav}
            className={`h-9 px-4 text-white text-xs font-semibold transition cursor-pointer ${
              cacheable
                ? "bg-[#1B1034] hover:bg-[#2D2250]"
                : "bg-amber-500 hover:bg-amber-600"
            }`}
          >
            {cacheable ? "Save draft & continue" : "Discard changes & continue"}
          </button>
        </div>
      </div>
    </div>
  );
}
