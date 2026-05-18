"use client";

import { useState, useEffect, useCallback } from "react";
import { Check, X, ChevronLeft, ChevronRight } from "lucide-react";
import {
  MOCK_SEGMENTS,
  MOCK_TOTAL_FRAMES,
  mockFrameForIndex,
  type Segment,
} from "@/lib/mock/workspace";
import { FramePlayer } from "@/components/workspace/frame-player";
import { SegmentTimeline } from "@/components/workspace/segment-timeline";
import { useWorkspaceNav } from "@/components/workspace/nav-context";

// Review page — maps to labeling.codatta.io/web/annotate/:id/filter.
// Contributor cycles through Vision Engine segments and marks each valid/invalid.
// Keyboard shortcuts: Y (keep), N (cull), ← → (navigate), M (merge — stub).

const STATE_LABELS: Record<Segment["state"], { label: string; color: string; reason: string }> = {
  keep: { label: "KEEP", color: "text-green-500", reason: "Vision Engine kept this segment." },
  review: {
    label: "NEEDS REVIEW",
    color: "text-amber-500",
    reason: "Vision Engine is uncertain.",
  },
  culled_motion: {
    label: "CULLED — MOTION",
    color: "text-gray-400",
    reason: "Vision Engine flagged motion outside the acceptable range.",
  },
  culled_low_action: {
    label: "CULLED — LOW ACTION",
    color: "text-gray-400",
    reason: "Vision Engine detected too little arm activity.",
  },
  culled_person: {
    label: "CULLED — NO PERSON",
    color: "text-gray-400",
    reason: "Vision Engine did not detect a person near frame center.",
  },
};

export default function ReviewPage() {
  const [activeIdx, setActiveIdx] = useState<number>(0);
  const [decisions, setDecisions] = useState<Record<string, "valid" | "invalid" | null>>({});
  const { setDirty } = useWorkspaceNav();

  const activeSegment = MOCK_SEGMENTS[activeIdx];
  const activeFrame = mockFrameForIndex(activeSegment.id, activeSegment.start_idx);

  // Cull decisions ARE draft-cacheable — they're saved to segments.review_decision
  // in I2-1. Leaving preserves the partial review; returning restores it.
  useEffect(() => {
    const n = Object.keys(decisions).length;
    setDirty({
      isDirty: n > 0,
      isDraftCacheable: true,
      description:
        n > 0
          ? `${n} of ${MOCK_SEGMENTS.length} segments reviewed. Your decisions haven't been finalized yet.`
          : "",
    });
    return () => setDirty({ isDirty: false, isDraftCacheable: true, description: "" });
  }, [decisions, setDirty]);

  const decide = useCallback(
    (segmentId: string, decision: "valid" | "invalid") => {
      setDecisions((prev) => ({ ...prev, [segmentId]: decision }));
      // Auto-advance to next unreviewed segment.
      setActiveIdx((idx) => Math.min(idx + 1, MOCK_SEGMENTS.length - 1));
    },
    []
  );

  const goTo = useCallback((direction: -1 | 1) => {
    setActiveIdx((idx) => {
      const next = idx + direction;
      if (next < 0) return 0;
      if (next >= MOCK_SEGMENTS.length) return MOCK_SEGMENTS.length - 1;
      return next;
    });
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      // Ignore when typing in an input
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;

      if (e.key === "y" || e.key === "Y") {
        e.preventDefault();
        decide(activeSegment.id, "valid");
      } else if (e.key === "n" || e.key === "N") {
        e.preventDefault();
        decide(activeSegment.id, "invalid");
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goTo(1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        goTo(-1);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [activeSegment.id, decide, goTo]);

  const stateMeta = STATE_LABELS[activeSegment.state];
  const currentDecision = decisions[activeSegment.id];
  const reviewedCount = Object.keys(decisions).length;

  return (
    <div className="flex-1 flex flex-col bg-[#111827] overflow-hidden">
      {/* Main canvas area */}
      <div className="flex-1 flex min-h-0">
        {/* Left: nav rail */}
        <div className="w-10 bg-[#1F2937] flex flex-col items-center justify-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => goTo(-1)}
            disabled={activeIdx === 0}
            className="w-8 h-8 bg-[#1B1034] text-white flex items-center justify-center hover:bg-[#2D2250] transition cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
            aria-label="Previous segment"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            type="button"
            onClick={() => goTo(1)}
            disabled={activeIdx === MOCK_SEGMENTS.length - 1}
            className="w-8 h-8 bg-[#1B1034] text-white flex items-center justify-center hover:bg-[#2D2250] transition cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
            aria-label="Next segment"
          >
            <ChevronRight size={18} />
          </button>
        </div>

        {/* Center: frame player */}
        <div className="flex-1 flex items-center justify-center bg-[#374151] border-l border-gray-600 overflow-hidden">
          <div className="flex flex-col items-center gap-3">
            <FramePlayer
              frameUrl={null}
              bbox={activeFrame.person_bbox}
              keypoints={activeFrame.arm_keypoints}
              width={640}
              frameIdx={activeFrame.frame_idx}
            />
            <p className="text-[11px] text-gray-400 font-mono">
              segment {activeIdx + 1} / {MOCK_SEGMENTS.length} · frames{" "}
              {activeSegment.start_idx}–{activeSegment.end_idx}
            </p>
          </div>
        </div>

        {/* Right: review panel */}
        <div className="w-[280px] bg-[#1F2937] border-l border-gray-700 shrink-0 flex flex-col">
          <div className="p-4 border-b border-gray-700">
            <p className="text-[10px] text-gray-400 uppercase tracking-wide font-semibold">
              Segment info
            </p>
            <p className={`text-xs font-bold mt-2 ${stateMeta.color}`}>{stateMeta.label}</p>
            <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">{stateMeta.reason}</p>
            {activeSegment.cull_reason && (
              <p className="text-[10px] text-gray-500 mt-2 italic">
                VE note: {activeSegment.cull_reason}
              </p>
            )}
          </div>

          <div className="p-4 border-b border-gray-700 space-y-2">
            <MetricRow label="Frames" value={String(activeSegment.frame_count)} />
            <MetricRow
              label="Duration"
              value={`${(activeSegment.duration_ms / 1000).toFixed(1)}s`}
            />
            <MetricRow label="Person detected" value={activeFrame.person_detected ? "yes" : "no"} />
            <MetricRow label="Motion score" value={activeFrame.motion_score.toFixed(2)} />
            <MetricRow label="Blur score" value={activeFrame.blur_score.toFixed(3)} />
          </div>

          {/* Decision buttons */}
          <div className="p-4 flex-1">
            <p className="text-[10px] text-gray-400 uppercase tracking-wide font-semibold mb-2">
              Your decision
            </p>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => decide(activeSegment.id, "valid")}
                className={`h-12 border-[1.5px] flex flex-col items-center justify-center gap-0.5 transition cursor-pointer ${
                  currentDecision === "valid"
                    ? "bg-green-500 border-green-500 text-white"
                    : "border-green-500 text-green-500 hover:bg-green-500/20"
                }`}
              >
                <Check size={16} />
                <span className="text-[10px] font-semibold">Keep (Y)</span>
              </button>
              <button
                type="button"
                onClick={() => decide(activeSegment.id, "invalid")}
                className={`h-12 border-[1.5px] flex flex-col items-center justify-center gap-0.5 transition cursor-pointer ${
                  currentDecision === "invalid"
                    ? "bg-red-500 border-red-500 text-white"
                    : "border-red-500 text-red-500 hover:bg-red-500/20"
                }`}
              >
                <X size={16} />
                <span className="text-[10px] font-semibold">Cull (N)</span>
              </button>
            </div>

            <p className="text-[10px] text-gray-500 mt-3 leading-relaxed">
              Review uses keyboard shortcuts: <kbd className="text-gray-300">Y</kbd> keep,{" "}
              <kbd className="text-gray-300">N</kbd> cull,{" "}
              <kbd className="text-gray-300">←</kbd>/<kbd className="text-gray-300">→</kbd>{" "}
              navigate.
            </p>
          </div>

          <div className="border-t border-gray-700 p-4 bg-[#111827]">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-gray-400">Progress</span>
              <span className="text-gray-200 font-mono">
                {reviewedCount} / {MOCK_SEGMENTS.length}
              </span>
            </div>
            <div className="mt-2 h-1 bg-gray-700 overflow-hidden">
              <div
                className="h-full bg-[#834DFB] transition-all"
                style={{
                  width: `${(reviewedCount / MOCK_SEGMENTS.length) * 100}%`,
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Bottom: segment timeline */}
      <SegmentTimeline
        segments={MOCK_SEGMENTS}
        totalFrames={MOCK_TOTAL_FRAMES}
        activeSegmentId={activeSegment.id}
        onSelectSegment={(id) => {
          const idx = MOCK_SEGMENTS.findIndex((s) => s.id === id);
          if (idx >= 0) setActiveIdx(idx);
        }}
        reviewDecisions={decisions}
      />
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-[11px]">
      <span className="text-gray-400">{label}</span>
      <span className="text-gray-200 font-mono">{value}</span>
    </div>
  );
}
