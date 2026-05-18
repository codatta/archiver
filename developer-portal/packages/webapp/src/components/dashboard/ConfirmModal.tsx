import React from "react";
import { THEME } from "../../lib/config";

type Props = {
  open: boolean;
  title: string;
  body: React.ReactNode;
  confirmLabel?: string;
  confirmDanger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export function ConfirmModal({ open, title, body, confirmLabel = "Confirm", confirmDanger, onConfirm, onCancel }: Props) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(27, 16, 52, 0.45)" }}
      onClick={onCancel}
    >
      <div
        className="w-full max-w-sm bg-white border-[1.5px] border-[#1B1034] rounded-none p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-base font-semibold mb-3" style={{ color: THEME.textPrimary }}>{title}</h3>
        <div className="text-sm mb-6" style={{ color: THEME.textSecondary }}>{body}</div>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm border-[1.5px] border-[#1B1034] rounded-none"
            style={{ color: THEME.textSecondary }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm text-white rounded-none font-medium"
            style={{ background: confirmDanger ? THEME.danger : THEME.btnBg }}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
