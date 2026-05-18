"use client";

import { useState } from "react";
import { CheckCircle2, Download, Hash } from "lucide-react";
import { MOCK_CAMPAIGN, MOCK_DRAFT_SEGMENTS, MOCK_SEGMENTS } from "@/lib/mock/workspace";

// Export page — T3c. Show what will be submitted, surface any gaps, submit.
// On submit (I3-3), we compute content_hash = SHA-256(canonical payload) and
// create the T3 task_instance with parent_instances: [T2.id].

export default function ExportPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const drafts = MOCK_DRAFT_SEGMENTS;
  const totalSourceSegments = MOCK_SEGMENTS.length;
  const validSourceSegments = drafts.length;

  // In a real run these come from the review step's state; mock = 0 complete.
  const withActionLabel = drafts.filter((d) => d.actionLabel).length;
  const withLanguage = drafts.filter((d) => d.languageInstruction.length > 0).length;
  const withTaskPlan = drafts.filter((d) => d.taskPlan.length > 0).length;

  // Mock label distribution (since drafts are empty labels by default).
  const labelCounts = MOCK_CAMPAIGN.actionVocabulary.map((label) => {
    const count = drafts.filter((d) => d.actionLabel === label.value).length;
    return { ...label, count };
  });

  const readyToSubmit = withActionLabel === drafts.length && withLanguage === drafts.length;

  function handleSubmit() {
    setIsSubmitting(true);
    setTimeout(() => {
      alert(
        "Mock submit — in I3-3, this computes content_hash and creates a T3 task_instance."
      );
      setIsSubmitting(false);
    }, 600);
  }

  return (
    <div className="flex-1 flex flex-col bg-[#F5F5F3] overflow-y-auto">
      <div className="max-w-[880px] w-full mx-auto px-8 py-10">
        <header className="mb-8">
          <p className="text-xs font-semibold text-[#834DFB] uppercase tracking-wide">
            Step 4 of 4 — Submit Contribution
          </p>
          <h1 className="text-2xl font-bold text-[#1B1034] mt-1">Review &amp; submit</h1>
          <p className="text-sm text-[#5C5470] mt-1">
            Confirm your annotation is complete before creating the T3 instance. Once submitted,
            the instance enters the T4 validation pipeline.
          </p>
        </header>

        {/* Completion checklist */}
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-[#1B1034] mb-3">Completion checklist</h2>
          <div className="border-[1.5px] border-[#1B1034] bg-white divide-y divide-gray-200">
            <ChecklistRow
              label="Source segments reviewed"
              actual={validSourceSegments}
              target={totalSourceSegments}
              note="From the cull review step — kept segments become draft action segments."
            />
            <ChecklistRow
              label="Action labels assigned"
              actual={withActionLabel}
              target={drafts.length}
              note="Each action segment must have a label from the campaign vocabulary."
            />
            <ChecklistRow
              label="Language instructions written"
              actual={withLanguage}
              target={drafts.length}
              note="One sentence per segment describing what the person is doing."
            />
            <ChecklistRow
              label="Task plan steps added"
              actual={withTaskPlan}
              target={drafts.length}
              note="Optional but encouraged — high-level steps improve downstream training quality."
              optional
            />
          </div>
        </section>

        {/* Label distribution */}
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-[#1B1034] mb-3">Label distribution</h2>
          <div className="border-[1.5px] border-[#1B1034] bg-white p-5">
            {labelCounts.every((l) => l.count === 0) ? (
              <p className="text-xs text-[#9890A8] italic">
                No labels assigned yet — go to the annotate step to tag each action segment.
              </p>
            ) : (
              <div className="space-y-2">
                {labelCounts.map((label) => (
                  <div key={label.value} className="flex items-center gap-3 text-xs">
                    <span
                      className="w-3 h-3 shrink-0"
                      style={{ backgroundColor: label.background }}
                    />
                    <span className="font-mono text-[#1B1034] w-32">{label.value}</span>
                    <div className="flex-1 h-2 bg-gray-100">
                      <div
                        className="h-full transition-all"
                        style={{
                          backgroundColor: label.background,
                          width: `${drafts.length > 0 ? (label.count / drafts.length) * 100 : 0}%`,
                        }}
                      />
                    </div>
                    <span className="text-[#5C5470] font-mono w-10 text-right">
                      {label.count}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Instance fingerprint preview */}
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-[#1B1034] mb-3">Instance fingerprint</h2>
          <div className="border-[1.5px] border-[#1B1034] bg-white p-5">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-[10px] text-[#9890A8] uppercase tracking-wide">Schema</p>
                <p className="text-sm font-mono text-[#1B1034] mt-0.5">embodiment_x_v1.0.0</p>
              </div>
              <div>
                <p className="text-[10px] text-[#9890A8] uppercase tracking-wide">Campaign</p>
                <p className="text-sm font-mono text-[#1B1034] mt-0.5">{MOCK_CAMPAIGN.id}</p>
              </div>
              <div>
                <p className="text-[10px] text-[#9890A8] uppercase tracking-wide">
                  Content hash (preview)
                </p>
                <p className="text-sm font-mono text-[#5C5470] mt-0.5 flex items-center gap-1">
                  <Hash size={12} />
                  sha256:computed-on-submit
                </p>
              </div>
              <div>
                <p className="text-[10px] text-[#9890A8] uppercase tracking-wide">
                  Parent instances
                </p>
                <p className="text-sm font-mono text-[#5C5470] mt-0.5">T2 (vision processing)</p>
              </div>
            </div>
            <p className="text-[10px] text-[#9890A8] mt-4 leading-relaxed">
              Content hash is computed on submit from the canonicalised payload (sorted keys, no
              whitespace) via SHA-256. The hash becomes the anchor for on-chain attribution (mock
              in V1 via <code className="font-mono">lineage_staging</code>).
            </p>
          </div>
        </section>

        {/* Submit */}
        <section>
          <div className="border-[1.5px] border-[#1B1034] bg-white px-5 py-5 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-[#1B1034]">
                {readyToSubmit ? (
                  <span className="flex items-center gap-2 text-green-600">
                    <CheckCircle2 size={16} />
                    Ready to submit
                  </span>
                ) : (
                  <span className="text-amber-600">⚠ Checklist incomplete</span>
                )}
              </p>
              <p className="text-xs text-[#5C5470] mt-1">
                {readyToSubmit
                  ? "All required items complete. Your contribution will enter T4 validation."
                  : "Return to the annotate step to finish labels and language instructions."}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                className="h-10 px-4 border-[1.5px] border-[#1B1034] text-[#1B1034] text-xs font-medium hover:bg-gray-100 transition cursor-pointer flex items-center gap-1.5"
              >
                <Download size={14} />
                Download preview
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!readyToSubmit || isSubmitting}
                className="h-10 px-5 bg-[#1B1034] text-white text-xs font-semibold hover:bg-[#2D2250] transition cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Submitting…" : "Submit contribution"}
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

type ChecklistRowProps = {
  label: string;
  actual: number;
  target: number;
  note: string;
  optional?: boolean;
};

function ChecklistRow({ label, actual, target, note, optional = false }: ChecklistRowProps) {
  const complete = actual >= target;
  return (
    <div className="px-5 py-3 flex items-center gap-3">
      <span
        className={`text-sm w-6 text-center ${
          complete ? "text-green-500" : optional ? "text-[#9890A8]" : "text-amber-500"
        }`}
      >
        {complete ? "✓" : optional ? "○" : "⚠"}
      </span>
      <div className="flex-1">
        <p className="text-sm font-medium text-[#1B1034]">{label}</p>
        <p className="text-[11px] text-[#9890A8] mt-0.5">{note}</p>
      </div>
      <span className="text-xs font-mono text-[#5C5470]">
        {actual} / {target}
        {optional && " (optional)"}
      </span>
    </div>
  );
}
