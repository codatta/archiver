"use client";

import type { Segment, SegmentState } from "@/lib/mock/workspace";

// Color-coding for segment states on the timeline.
// Green/amber/red encode Vision Engine's confidence; strikethrough = culled.
const STATE_STYLES: Record<SegmentState, { bg: string; label: string; border: string }> = {
  keep: { bg: "#22C55E", label: "keep", border: "#15803D" },
  review: { bg: "#F59E0B", label: "review", border: "#B45309" },
  culled_motion: { bg: "#9CA3AF", label: "cull: motion", border: "#4B5563" },
  culled_low_action: { bg: "#9CA3AF", label: "cull: low action", border: "#4B5563" },
  culled_person: { bg: "#9CA3AF", label: "cull: no person", border: "#4B5563" },
};

type SegmentTimelineProps = {
  segments: Segment[];
  totalFrames: number;
  activeSegmentId: string | null;
  onSelectSegment: (segmentId: string) => void;
  reviewDecisions: Record<string, "valid" | "invalid" | null>;
};

export function SegmentTimeline({
  segments,
  totalFrames,
  activeSegmentId,
  onSelectSegment,
  reviewDecisions,
}: SegmentTimelineProps) {
  return (
    <div className="bg-[#1F2937] border-t border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <p className="text-[10px] text-gray-400 uppercase tracking-wide font-semibold">
          Segment timeline — {segments.length} segments · {totalFrames} frames
        </p>
        <div className="flex items-center gap-3 text-[10px] text-gray-400">
          <LegendChip color="#22C55E" label="keep" />
          <LegendChip color="#F59E0B" label="review" />
          <LegendChip color="#9CA3AF" label="culled" />
        </div>
      </div>

      <div className="flex h-9 border border-gray-700 overflow-hidden">
        {segments.map((seg) => {
          const widthPct = (seg.frame_count / totalFrames) * 100;
          const style = STATE_STYLES[seg.state];
          const isActive = seg.id === activeSegmentId;
          const decision = reviewDecisions[seg.id];
          const isCulledState = seg.state.startsWith("culled_");

          return (
            <button
              key={seg.id}
              type="button"
              onClick={() => onSelectSegment(seg.id)}
              style={{
                width: `${widthPct}%`,
                backgroundColor: style.bg,
                borderLeft: isActive ? "2px solid #834DFB" : "1px solid rgba(0,0,0,0.15)",
                borderRight: isActive ? "2px solid #834DFB" : "1px solid rgba(0,0,0,0.15)",
              }}
              className={`relative text-[10px] font-medium flex items-center justify-center cursor-pointer transition hover:brightness-110 ${
                isActive ? "ring-2 ring-[#834DFB] ring-inset z-10" : ""
              }`}
              title={`${seg.id} — ${style.label} (${seg.frame_count} frames)`}
            >
              <span
                className={`text-[9px] ${isCulledState ? "line-through text-white/70" : "text-black/80"}`}
              >
                {seg.id.replace("seg-", "")}
              </span>
              {decision && (
                <span
                  className={`absolute top-0.5 right-1 text-[9px] font-bold ${
                    decision === "valid" ? "text-green-900" : "text-red-900"
                  }`}
                >
                  {decision === "valid" ? "✓" : "✕"}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function LegendChip({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1">
      <span className="w-2.5 h-2.5" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}
