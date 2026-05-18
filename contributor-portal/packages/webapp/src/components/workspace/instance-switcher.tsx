"use client";

import { useEffect, useMemo, useState } from "react";
import { X, ArrowRight, Layers } from "lucide-react";
import {
  MOCK_TASK_INSTANCES,
  workspaceHrefFor,
  type MockTaskInstance,
} from "@/lib/mock/task-instances";
import { useWorkspaceNav } from "./nav-context";

type InstanceSwitcherProps = {
  open: boolean;
  onClose: () => void;
  currentCampaignId: string;
  currentTaskId: string;
};

const TYPE_BG: Record<MockTaskInstance["type"], string> = {
  supply: "bg-[#1B1034]",
  labeling: "bg-[#834DFB]",
  validation: "bg-[#22C55E]",
};

const TYPE_LABEL: Record<MockTaskInstance["type"], string> = {
  supply: "📤 Supply",
  labeling: "🏷 Labeling",
  validation: "✅ Validation",
};

const STATUS_LABEL: Record<NonNullable<MockTaskInstance["priority"]>, { text: string; color: string }> = {
  resume: { text: "● In Progress", color: "text-[#834DFB]" },
  expiring: { text: "⚠ Expiring", color: "text-amber-400" },
  dispute: { text: "✕ Disputed", color: "text-red-400" },
};

// Side drawer that slides in from the right, showing task cards for the
// active campaign + a quick "other campaigns" section. Clicking a card
// triggers guardedNavigate — which pops the confirm dialog if dirty.
export function InstanceSwitcher({
  open,
  onClose,
  currentCampaignId,
  currentTaskId,
}: InstanceSwitcherProps) {
  const { guardedNavigate } = useWorkspaceNav();
  const [filter, setFilter] = useState<"same" | "all">("same");

  // Close on Escape.
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const currentInst = MOCK_TASK_INSTANCES.find((i) => i.taskId === currentTaskId);
  const currentCampaignName = currentInst?.campaign ?? "Unknown";

  const visible = useMemo(() => {
    if (filter === "same") {
      return MOCK_TASK_INSTANCES.filter((i) => i.campaignId === currentCampaignId);
    }
    return MOCK_TASK_INSTANCES;
  }, [filter, currentCampaignId]);

  // Group visible by campaign for rendering.
  const grouped = useMemo(() => {
    const out = new Map<string, MockTaskInstance[]>();
    for (const inst of visible) {
      const key = inst.campaign;
      if (!out.has(key)) out.set(key, []);
      out.get(key)!.push(inst);
    }
    return Array.from(out.entries());
  }, [visible]);

  function handleSelect(inst: MockTaskInstance) {
    onClose();
    guardedNavigate(workspaceHrefFor(inst), `${inst.id} · ${inst.campaign}`);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40" role="dialog" aria-modal="true" aria-label="Switch instance">
      {/* Scrim */}
      <button
        type="button"
        onClick={onClose}
        className="absolute inset-0 bg-black/50 cursor-default"
        aria-label="Close switcher"
      />

      {/* Drawer */}
      <aside
        className="absolute right-0 top-0 bottom-0 w-[460px] max-w-[92vw] bg-white border-l-[1.5px] border-[#1B1034] shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="h-14 px-5 flex items-center justify-between border-b-[1.5px] border-[#1B1034] shrink-0">
          <div className="flex items-center gap-2.5">
            <Layers size={16} className="text-[#834DFB]" />
            <h2 className="text-sm font-bold text-[#1B1034]">Switch instance</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[#9890A8] hover:text-[#1B1034] transition cursor-pointer"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        {/* Filter tabs */}
        <div className="px-5 pt-4 flex gap-0">
          <button
            type="button"
            onClick={() => setFilter("same")}
            className={`px-3 py-1.5 text-xs font-medium border-[1.5px] border-[#1B1034] transition cursor-pointer ${
              filter === "same"
                ? "bg-[#1B1034] text-white"
                : "bg-white text-[#1B1034] hover:bg-gray-50"
            }`}
          >
            This campaign
          </button>
          <button
            type="button"
            onClick={() => setFilter("all")}
            className={`px-3 py-1.5 text-xs font-medium border-[1.5px] border-[#1B1034] -ml-[1.5px] transition cursor-pointer ${
              filter === "all"
                ? "bg-[#1B1034] text-white"
                : "bg-white text-[#1B1034] hover:bg-gray-50"
            }`}
          >
            All enrolled
          </button>
        </div>

        <p className="px-5 pt-2 text-[11px] text-[#5C5470]">
          Currently working on <span className="font-mono text-[#1B1034]">#{currentTaskId.slice(-6)}</span>{" "}
          in <span className="font-semibold text-[#1B1034]">{currentCampaignName}</span>. Switching
          triggers a check for unsaved work.
        </p>

        {/* Cards list */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {grouped.map(([campaign, insts]) => (
            <section key={campaign}>
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 bg-[#1B1034] rounded-full" />
                <h3 className="text-xs font-semibold text-[#1B1034]">{campaign}</h3>
                <span className="text-[10px] text-[#9890A8]">({insts.length})</span>
              </div>
              <div className="grid gap-2">
                {insts.map((inst) => {
                  const isCurrent = inst.taskId === currentTaskId;
                  return (
                    <button
                      key={inst.taskId}
                      type="button"
                      disabled={isCurrent}
                      onClick={() => handleSelect(inst)}
                      className={`group flex items-center gap-3 px-3 py-2.5 border-[1.5px] transition text-left ${
                        isCurrent
                          ? "border-[#834DFB] bg-[#F0EBFF] cursor-default"
                          : "border-[#1B1034] bg-white hover:bg-gray-50 cursor-pointer"
                      }`}
                      aria-current={isCurrent ? "true" : undefined}
                    >
                      <div
                        className={`w-7 h-7 ${TYPE_BG[inst.type]} flex items-center justify-center shrink-0`}
                      >
                        <span className="text-white text-[9px]">▶</span>
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-mono text-[#5C5470] shrink-0">
                            {inst.id}
                          </span>
                          {isCurrent && (
                            <span className="text-[10px] text-[#834DFB] font-semibold">
                              (current)
                            </span>
                          )}
                          {inst.priority && (
                            <span
                              className={`text-[10px] font-medium ${STATUS_LABEL[inst.priority].color.replace("-400", "-500")}`}
                            >
                              {STATUS_LABEL[inst.priority].text}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-[#1B1034] mt-0.5 line-clamp-1">{inst.desc}</p>
                        <p className="text-[10px] text-[#9890A8] mt-0.5">
                          {TYPE_LABEL[inst.type]} · {inst.time} ·{" "}
                          {inst.pay === "royalty" || inst.pay === "bounty" ? (
                            <span className="text-[#834DFB]">{inst.pay}</span>
                          ) : (
                            inst.pay
                          )}
                        </p>
                      </div>

                      {!isCurrent && (
                        <ArrowRight
                          size={14}
                          className="text-gray-300 group-hover:text-[#1B1034] shrink-0 transition"
                        />
                      )}
                    </button>
                  );
                })}
              </div>
            </section>
          ))}
        </div>

        {/* Footer hint */}
        <div className="border-t-[1.5px] border-[#1B1034] bg-[#F5F5F3] px-5 py-3">
          <p className="text-[10px] text-[#5C5470] leading-relaxed">
            <span className="font-semibold text-[#1B1034]">Up &amp; Down:</span> click any card to
            swap into that instance. If you have unsaved contributions on the current instance, we
            cache them remotely so you can resume — or warn you when work would be lost.
          </p>
        </div>
      </aside>
    </div>
  );
}
