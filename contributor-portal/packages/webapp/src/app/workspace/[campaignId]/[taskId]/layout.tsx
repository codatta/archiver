"use client";

import { useState, useEffect } from "react";
import { usePathname, useParams } from "next/navigation";
import { ArrowLeft, SkipForward, Save, Users } from "lucide-react";
import { WorkspaceNavProvider, useWorkspaceNav } from "@/components/workspace/nav-context";
import { ConfirmNavDialog } from "@/components/workspace/confirm-nav-dialog";
import { InstanceSwitcher } from "@/components/workspace/instance-switcher";

// Step definitions — source of truth for the workspace contribution pipeline.
// Routes map to the three production URLs in labeling.codatta.io and extend them:
//   /supply   → labeling.codatta.io/web
//   /review   → labeling.codatta.io/web/annotate/:id/filter
//   /annotate → labeling.codatta.io/web/annotate/:id/slice
//   /export   → (new) final submit
const STEPS = [
  { slug: "supply", label: "Supply", taskKey: "T1" },
  { slug: "review", label: "Cull Review", taskKey: "T3a" },
  { slug: "annotate", label: "Slice & Annotate", taskKey: "T3b" },
  { slug: "export", label: "Export", taskKey: "T3c" },
] as const;

type StepSlug = (typeof STEPS)[number]["slug"];

// Pipeline context bar — T1/T2/T3/T4 stages at the campaign DAG level.
// Independent from the sub-step bar below, which is scoped to the current T-level task.
const PIPELINE = [
  { label: "supply", taskKey: "T1", progressFor: "supply" },
  { label: "vision", taskKey: "T2", progressFor: null },
  { label: "annotate", taskKey: "T3", progressFor: ["review", "annotate", "export"] },
  { label: "validate", taskKey: "T4", progressFor: null },
] as const;

function getCurrentStep(pathname: string): StepSlug {
  const segments = pathname.split("/");
  const last = segments[segments.length - 1] as StepSlug;
  if (STEPS.some((s) => s.slug === last)) return last;
  return "supply";
}

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}m ${sec.toString().padStart(2, "0")}s`;
}

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <WorkspaceNavProvider>
      <WorkspaceShell>{children}</WorkspaceShell>
    </WorkspaceNavProvider>
  );
}

function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const params = useParams<{ campaignId: string; taskId: string }>();
  const { guardedNavigate } = useWorkspaceNav();
  const currentStep = getCurrentStep(pathname);

  const [elapsed, setElapsed] = useState(0);
  const [switcherOpen, setSwitcherOpen] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, []);

  // Determine pipeline bar states based on current step.
  // T1 (supply) is in progress on /supply; T3 (annotate) is in progress on /review, /annotate, /export.
  // Prior stages are "completed" in this mock; future stages are "pending".
  const pipelineWithState = PIPELINE.map((stage) => {
    const progressMatches =
      stage.progressFor === currentStep ||
      (Array.isArray(stage.progressFor) && stage.progressFor.includes(currentStep));
    if (progressMatches) return { ...stage, status: "current" as const };

    // Stages before the current one are completed; after are pending.
    const order = ["T1", "T2", "T3", "T4"];
    const currentTaskKey = currentStep === "supply" ? "T1" : "T3";
    const stageIdx = order.indexOf(stage.taskKey);
    const currentIdx = order.indexOf(currentTaskKey);
    if (stageIdx < currentIdx) return { ...stage, status: "completed" as const };
    return { ...stage, status: "pending" as const };
  });

  const currentStepIdx = STEPS.findIndex((s) => s.slug === currentStep);

  function navigateStep(direction: "prev" | "next") {
    if (direction === "next" && currentStepIdx < STEPS.length - 1) {
      const nextStep = STEPS[currentStepIdx + 1];
      guardedNavigate(
        `/workspace/${params.campaignId}/${params.taskId}/${nextStep.slug}`,
        `${nextStep.label} step`
      );
    } else if (direction === "prev" && currentStepIdx > 0) {
      const prevStep = STEPS[currentStepIdx - 1];
      guardedNavigate(
        `/workspace/${params.campaignId}/${params.taskId}/${prevStep.slug}`,
        `${prevStep.label} step`
      );
    }
  }

  function goToStep(slug: StepSlug, label: string) {
    guardedNavigate(
      `/workspace/${params.campaignId}/${params.taskId}/${slug}`,
      `${label} step`
    );
  }

  // Action bar button config differs per step.
  const actionConfig = {
    supply: { primary: "Upload & Process", secondary: "Save Draft" },
    review: { primary: "Finalize Review", secondary: "Save Draft" },
    annotate: { primary: "Continue to Export", secondary: "Save Draft" },
    export: { primary: "Submit Contribution", secondary: "Save Draft" },
  }[currentStep];

  return (
    <div className="h-screen flex flex-col bg-[#111827]">
      {/* Pipeline context bar */}
      <div className="h-12 bg-white border-b-[1.5px] border-[#1B1034] px-6 flex items-center gap-0 shrink-0">
        <button
          type="button"
          onClick={() => guardedNavigate("/contribute/tasks", "Back to task queue")}
          className="text-gray-400 hover:text-[#1B1034] mr-4 cursor-pointer"
          aria-label="Back to tasks"
        >
          <ArrowLeft size={16} />
        </button>

        <div className="flex items-center gap-[2px] flex-1">
          {pipelineWithState.map((stage, i) => (
            <div key={stage.taskKey} className="flex items-center flex-1">
              <div className="flex-1 relative">
                {stage.status === "completed" && (
                  <div className="h-8 bg-[#1B1034] flex items-center justify-center">
                    <span className="text-[10px] font-medium text-white">{stage.label}</span>
                  </div>
                )}
                {stage.status === "current" && (
                  <div className="h-8 flex overflow-hidden">
                    <div
                      className="bg-[#834DFB] flex items-center justify-center"
                      style={{ width: `${stepProgress(currentStep)}%` }}
                    >
                      <span className="text-[10px] font-medium text-white whitespace-nowrap">
                        {stage.label}
                      </span>
                    </div>
                    <div className="bg-gray-200 flex-1" />
                  </div>
                )}
                {stage.status === "pending" && (
                  <div className="h-8 border border-gray-300 border-dashed flex items-center justify-center">
                    <span className="text-[10px] text-gray-400">{stage.label}</span>
                  </div>
                )}
              </div>
              {i < pipelineWithState.length - 1 && (
                <div className="w-[2px] h-8 bg-gray-300 shrink-0" />
              )}
            </div>
          ))}
        </div>

        <button
          type="button"
          onClick={() => setSwitcherOpen(true)}
          className="ml-4 flex items-center gap-1.5 text-xs text-gray-500 hover:text-[#1B1034] border border-transparent hover:border-[#1B1034] px-2 py-1 transition cursor-pointer"
          title="Switch to a different task instance"
        >
          <Users size={12} />
          <span className="font-mono">
            {params.taskId ? `Instance #${params.taskId.slice(-6)}` : "—"}
          </span>
        </button>
      </div>

      {/* Sub-task breakdown bar — shows the 4 steps within the current T-level task */}
      <div className="h-11 flex gap-0 mx-6 mt-2 shrink-0">
        {STEPS.map((step, idx) => {
          const isDone = idx < currentStepIdx;
          const isCurrent = idx === currentStepIdx;
          const isPending = idx > currentStepIdx;

          return (
            <button
              key={step.slug}
              type="button"
              onClick={() => {
                if (!isPending && !isCurrent) goToStep(step.slug, step.label);
              }}
              disabled={isPending}
              className={`flex-1 flex items-center justify-center text-xs font-medium transition ${
                isDone
                  ? "bg-gray-500 text-white hover:bg-gray-600 cursor-pointer"
                  : isCurrent
                    ? "bg-white border-[1.5px] border-[#1B1034] text-[#1B1034] cursor-default"
                    : "bg-white/30 border-[1.5px] border-dashed border-gray-500 text-gray-400 cursor-not-allowed"
              }`}
              style={
                isCurrent
                  ? {
                      backgroundImage:
                        "repeating-linear-gradient(45deg, transparent, transparent 4px, rgba(27,16,52,0.08) 4px, rgba(27,16,52,0.08) 8px)",
                    }
                  : undefined
              }
              aria-current={isCurrent ? "step" : undefined}
              aria-disabled={isPending}
            >
              {step.label}
            </button>
          );
        })}
      </div>

      {/* Step canvas — children render here */}
      <div className="flex-1 flex mt-2 mx-6 mb-0 overflow-hidden">{children}</div>

      {/* Action bar */}
      <div className="h-14 bg-[#111827] px-6 flex items-center justify-between shrink-0 border-t border-gray-700">
        <div className="bg-amber-500/20 text-amber-400 text-sm px-3 py-1.5">
          Task time: {formatTime(elapsed)}
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => guardedNavigate("/contribute/tasks", "Skip — back to task queue")}
            className="h-9 px-4 text-gray-400 text-xs font-medium hover:text-gray-200 transition cursor-pointer flex items-center gap-1.5"
          >
            <SkipForward size={14} />
            Skip
          </button>

          <button
            type="button"
            onClick={() => alert("Draft saved.")}
            className="h-9 px-4 border border-gray-600 text-gray-300 text-xs font-medium hover:bg-gray-800 transition cursor-pointer flex items-center gap-1.5"
          >
            <Save size={14} />
            {actionConfig.secondary}
          </button>

          <button
            type="button"
            onClick={() => navigateStep("prev")}
            disabled={currentStepIdx === 0}
            className="h-9 px-4 border border-gray-600 text-white text-xs font-medium hover:bg-gray-800 transition cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Prev
          </button>

          <button
            type="button"
            onClick={() => {
              if (currentStepIdx === STEPS.length - 1) {
                guardedNavigate("/contribute/tasks", "Submit & return to task queue");
              } else {
                navigateStep("next");
              }
            }}
            className="h-9 px-5 bg-white text-[#1B1034] text-xs font-semibold hover:bg-gray-100 transition cursor-pointer"
          >
            {actionConfig.primary}
          </button>
        </div>
      </div>

      {/* Overlays */}
      <ConfirmNavDialog />
      <InstanceSwitcher
        open={switcherOpen}
        onClose={() => setSwitcherOpen(false)}
        currentCampaignId={params.campaignId}
        currentTaskId={params.taskId}
      />
    </div>
  );
}

// Mock progress percentage per step — will come from real instance state in I1-2/I2-1/I2-2.
function stepProgress(step: StepSlug): number {
  switch (step) {
    case "supply":
      return 15;
    case "review":
      return 35;
    case "annotate":
      return 70;
    case "export":
      return 95;
  }
}
