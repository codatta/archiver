import React, { useEffect, useRef, useState } from "react";
import { THEME } from "../../lib/config";

export type WaffleBlock = {
  id: string;
  vertical: number; // 0, 1, or 2
  status: "pending" | "adopted" | "disputed";
  timestamp: number; // epoch ms
};

type Props = {
  blocks: WaffleBlock[];
  verticalNames: string[];
  bucketMs?: number; // time bucket width in ms (default 60000 = 1 min)
};

const VERTICAL_FILLS = ["#1B1034", "#5C5470", "#B0A8C0"];
const STATUS_BORDER: Record<string, string | null> = {
  pending: null,
  adopted: "#22C55E",
  disputed: "#EF4444",
};

const BLOCK_SIZE = 10;
const BLOCK_GAP = 2;
const BLOCK_STEP = BLOCK_SIZE + BLOCK_GAP;
const COL_GAP = 4;
const COL_STEP = BLOCK_SIZE + COL_GAP;
const MARGIN = { top: 8, right: 16, bottom: 28, left: 8 };
const TICK_HEIGHT = 6;
/** 5-min grouping for tick marks (in ms) */
const TICK_INTERVAL_MS = 5 * 60 * 1000;

function formatTime(ms: number): string {
  const d = new Date(ms);
  return d.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit" });
}

export function WaffleChart({ blocks, verticalNames, bucketMs = 60000 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{
    x: number; y: number; time: string;
    verticals: { name: string; count: number; color: string }[];
    adopted: number; disputed: number;
  } | null>(null);

  // Bucket blocks by time, sorted newest-first (right to left: newest on right)
  const buckets = React.useMemo(() => {
    if (blocks.length === 0) return [];
    const map = new Map<number, WaffleBlock[]>();
    for (const b of blocks) {
      const key = Math.floor(b.timestamp / bucketMs) * bucketMs;
      const arr = map.get(key) ?? [];
      arr.push(b);
      map.set(key, arr);
    }
    // Sort ascending by time — we'll draw right-to-left
    return Array.from(map.entries())
      .sort(([a], [b]) => a - b)
      .map(([time, items]) => ({ time, items }));
  }, [blocks, bucketMs]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const W = rect.width;
    const H = rect.height;
    ctx.clearRect(0, 0, W, H);

    const plotW = W - MARGIN.left - MARGIN.right;
    const plotH = H - MARGIN.top - MARGIN.bottom;
    const plotX = MARGIN.left;
    const plotY = MARGIN.top;
    const baselineY = plotY + plotH;

    // Baseline
    ctx.strokeStyle = "#D4CDE0";
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.moveTo(plotX, baselineY);
    ctx.lineTo(plotX + plotW, baselineY);
    ctx.stroke();

    if (buckets.length === 0) {
      ctx.fillStyle = "#9890A8";
      ctx.font = "12px 'DM Sans', sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Waiting for data...", W / 2, H / 2);
      return;
    }

    // Draw columns right-to-left: newest bucket at right edge
    const maxCols = Math.floor(plotW / COL_STEP);
    const visibleBuckets = buckets.slice(-maxCols);

    visibleBuckets.forEach((bucket, i) => {
      // Position: rightmost column for last bucket
      const colFromRight = visibleBuckets.length - 1 - i;
      const cx = plotX + plotW - (colFromRight + 1) * COL_STEP;

      // Draw blocks bottom-up
      bucket.items.forEach((block, bi) => {
        const bx = cx;
        const by = baselineY - (bi + 1) * BLOCK_STEP;
        if (by < plotY) return; // clip

        // Fill always reflects the vertical — status never changes fill
        ctx.fillStyle = VERTICAL_FILLS[block.vertical] ?? VERTICAL_FILLS[0];
        ctx.fillRect(bx, by, BLOCK_SIZE, BLOCK_SIZE);

        const borderColor = STATUS_BORDER[block.status];
        if (borderColor) {
          ctx.strokeStyle = borderColor;
          ctx.lineWidth = 2;
          ctx.strokeRect(bx, by, BLOCK_SIZE, BLOCK_SIZE);
        }
      });

      // 5-min tick marks: paired vertical sticks at the boundary
      const bucketMin = new Date(bucket.time).getMinutes();
      const bucketSec = new Date(bucket.time).getSeconds();
      const isTickBoundary = (bucket.time % TICK_INTERVAL_MS) === 0
        || (bucketMs < TICK_INTERVAL_MS && bucketMin % 5 === 0 && bucketSec === 0);

      if (isTickBoundary) {
        ctx.strokeStyle = "#9890A8";
        ctx.lineWidth = 1;
        // Left stick of the pair
        ctx.beginPath();
        ctx.moveTo(cx - 1, baselineY);
        ctx.lineTo(cx - 1, baselineY + TICK_HEIGHT);
        ctx.stroke();
        // Right stick of the pair
        ctx.beginPath();
        ctx.moveTo(cx + BLOCK_SIZE + 1, baselineY);
        ctx.lineTo(cx + BLOCK_SIZE + 1, baselineY + TICK_HEIGHT);
        ctx.stroke();

        // Time label
        ctx.fillStyle = "#9890A8";
        ctx.font = "9px 'DM Sans', sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(formatTime(bucket.time), cx + BLOCK_SIZE / 2, baselineY + TICK_HEIGHT + 10);
      }
    });
  }, [buckets, bucketMs]);

  // Tooltip on hover
  function handleMouseMove(e: React.MouseEvent) {
    const canvas = canvasRef.current;
    if (!canvas || buckets.length === 0) { setTooltip(null); return; }
    const rect = canvas.getBoundingClientRect();
    const W = rect.width;
    const plotW = W - MARGIN.left - MARGIN.right;
    const mx = e.clientX - rect.left;

    const maxCols = Math.floor(plotW / COL_STEP);
    const visibleBuckets = buckets.slice(-maxCols);

    // Find which column from right
    const pxFromRight = MARGIN.left + plotW - mx;
    const colFromRight = Math.floor(pxFromRight / COL_STEP);
    const bucketIdx = visibleBuckets.length - 1 - colFromRight;

    if (bucketIdx < 0 || bucketIdx >= visibleBuckets.length) { setTooltip(null); return; }

    const bucket = visibleBuckets[bucketIdx];
    const vCounts = verticalNames.map((name, vi) => ({
      name, count: bucket.items.filter((b) => b.vertical === vi).length, color: VERTICAL_FILLS[vi],
    })).filter((v) => v.count > 0);

    const cx = MARGIN.left + plotW - (colFromRight + 1) * COL_STEP;

    setTooltip({
      x: cx + COL_STEP / 2,
      y: 16,
      time: formatTime(bucket.time),
      verticals: vCounts,
      adopted: bucket.items.filter((b) => b.status === "adopted").length,
      disputed: bucket.items.filter((b) => b.status === "disputed").length,
    });
  }

  return (
    <div className="border-[1.5px] rounded-none p-5" style={{ borderColor: THEME.border, background: THEME.bg }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium tracking-widest" style={{ color: "#9890A8" }}>DATA ARRIVALS</span>
          <span className="text-xl font-bold" style={{ color: THEME.textPrimary }}>{blocks.length.toLocaleString()}</span>
          <span className="text-sm" style={{ color: "#9890A8" }}>records</span>
        </div>
      </div>

      {/* Canvas */}
      <div ref={containerRef} className="relative" onMouseMove={handleMouseMove} onMouseLeave={() => setTooltip(null)}>
        <canvas ref={canvasRef} className="w-full" style={{ height: 260 }} />

        {tooltip && (
          <div className="absolute pointer-events-none bg-white border-[1.5px] p-2.5 z-10" style={{ left: Math.min(tooltip.x + 10, 600), top: tooltip.y, borderColor: THEME.border, minWidth: 120 }}>
            <p className="text-xs font-bold mb-1" style={{ color: THEME.textPrimary }}>{tooltip.time}</p>
            {tooltip.verticals.map((v) => (
              <div key={v.name} className="flex items-center gap-1.5 mb-0.5">
                <span className="inline-block w-2 h-2" style={{ background: v.color }} />
                <span className="text-[10px]" style={{ color: "#5C5470" }}>{v.name} {v.count}</span>
              </div>
            ))}
            {(tooltip.adopted > 0 || tooltip.disputed > 0) && (
              <>
                <div className="my-1" style={{ borderTop: "1px solid #D4CDE0" }} />
                {tooltip.adopted > 0 && (
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="inline-block w-2 h-2 border" style={{ background: THEME.textPrimary, borderColor: "#22C55E", borderWidth: 1.5 }} />
                    <span className="text-[10px]" style={{ color: "#22C55E" }}>Adopted {tooltip.adopted}</span>
                  </div>
                )}
                {tooltip.disputed > 0 && (
                  <div className="flex items-center gap-1.5">
                    <span className="inline-block w-2 h-2 border" style={{ background: THEME.bg, borderColor: "#EF4444", borderWidth: 1.5 }} />
                    <span className="text-[10px]" style={{ color: "#EF4444" }}>Disputed {tooltip.disputed}</span>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Legend + Description — bottom right */}
      <div className="flex items-start justify-between mt-3">
        <p className="text-[10px] max-w-sm" style={{ color: "#9890A8" }}>
          Each block = one data unit. Fill color indicates the vertical source and never changes.
          Status is shown by outline only: green border = adopted, red border = disputed.
          Time flows right to left. Ticks mark 5-min intervals.
        </p>
        <div className="flex items-center gap-4 flex-shrink-0">
          {verticalNames.map((name, i) => (
            <div key={name} className="flex items-center gap-1.5">
              <span className="inline-block w-2.5 h-2.5" style={{ background: VERTICAL_FILLS[i] }} />
              <span className="text-[11px]" style={{ color: "#5C5470" }}>{name}</span>
            </div>
          ))}
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 border-2" style={{ background: THEME.textPrimary, borderColor: "#22C55E" }} />
            <span className="text-[11px]" style={{ color: "#5C5470" }}>Adopted</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 border-2" style={{ background: THEME.textPrimary, borderColor: "#EF4444" }} />
            <span className="text-[11px]" style={{ color: "#5C5470" }}>Disputed</span>
          </div>
        </div>
      </div>
    </div>
  );
}
