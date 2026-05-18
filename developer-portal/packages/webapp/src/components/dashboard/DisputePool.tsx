import React, { useState } from "react";
import type { AnnotationItem } from "@humanbased/shared";
import { THEME } from "../../lib/config";

const PAGE_SIZE = 20;

type Props = {
  items: AnnotationItem[];
  newestId?: string | null;
};

function timeAgo(dateStr: string): string {
  const sec = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (sec < 60) return `${sec}s ago`; const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`; return `${Math.floor(min / 60)}h ago`;
}

export function DisputePool({ items, newestId }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);

  if (items.length === 0) return null;

  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const pageClamped = Math.min(page, totalPages);
  const pagedItems = items.slice((pageClamped - 1) * PAGE_SIZE, pageClamped * PAGE_SIZE);

  return (
    <div className="rounded-none" style={{ border: "1.5px solid #EF4444" }}>
      <div className="flex items-center justify-between px-5 py-3" style={{ borderBottom: "1.5px solid #EF4444" }}>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
          <h2 className="text-sm font-medium text-red-500">Dispute Pool</h2>
        </div>
        <span className="text-xs text-red-400">{items.length} disputed</span>
      </div>
      <div className="overflow-y-auto" style={{ maxHeight: 400 }}>
        <table className="w-full">
          <thead>
            <tr className="text-xs text-left" style={{ color: "#f87171" }}>
              <th className="px-5 py-2.5 font-medium w-20">ID</th>
              <th className="px-2 py-2.5 font-medium">Vertical</th>
              <th className="px-2 py-2.5 font-medium">Topic</th>
              <th className="px-2 py-2.5 font-medium w-16">Quality</th>
              <th className="px-2 py-2.5 font-medium w-16">Price</th>
              <th className="px-2 py-2.5 font-medium w-16">Time</th>
              <th className="px-5 py-2.5 font-medium text-right w-24">Status</th>
            </tr>
          </thead>
          <tbody>
            {pagedItems.map((item) => {
              const isExp = expanded.has(item.id);
              const isNew = newestId === item.id;
              return (
                <React.Fragment key={item.id}>
                  <tr
                    className={`cursor-pointer hover:bg-red-50/30 ${isNew ? "row-slide-in" : ""}`}
                    style={{ borderTop: "1px solid #fca5a5" }}
                    onClick={() => {
                      const s = new Set(expanded);
                      s.has(item.id) ? s.delete(item.id) : s.add(item.id);
                      setExpanded(s);
                    }}
                  >
                    <td className="px-5 py-3 font-mono text-xs text-red-400">{item.id.slice(0, 8)}</td>
                    <td className="px-2 py-3 text-sm text-red-400">{(item.vertical_slug ?? "").replace(/_/g, " ")}</td>
                    <td className="px-2 py-3 text-sm text-red-400">{item.topic_name ?? ""}</td>
                    <td className="px-2 py-3 text-sm font-medium text-red-500">{item.quality_score.toFixed(2)}</td>
                    <td className="px-2 py-3 text-sm text-red-400">${item.unit_price_usd.toFixed(3)}</td>
                    <td className="px-2 py-3 text-xs text-red-400">{timeAgo(item.created_at)}</td>
                    <td className="px-5 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <span className="text-xs font-medium px-2 py-0.5 bg-red-100 text-red-600 rounded-none">disputed</span>
                    </td>
                  </tr>
                  {isExp && (
                    <tr>
                      <td colSpan={7} className="px-5 pb-3">
                        <div className="rounded-none p-3 text-xs font-mono text-red-500" style={{ border: "1.5px solid #fca5a5", background: "#fff5f5" }}>
                          <pre className="whitespace-pre-wrap">{JSON.stringify(item.payload, null, 2)}</pre>
                          <div className="flex gap-4 mt-2 text-red-400">
                            <span>validators: {item.validator_count}</span>
                            <span>consensus: {item.consensus_ratio.toFixed(2)}</span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3" style={{ borderTop: "1.5px solid #EF4444" }}>
          <span className="text-xs" style={{ color: THEME.textMuted }}>
            Page {pageClamped} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(pageClamped - 1)}
              disabled={pageClamped <= 1}
              className="px-3 py-1 text-xs border-[1.5px] disabled:opacity-30"
              style={{ borderColor: "#EF4444", color: "#EF4444" }}
            >
              Previous
            </button>
            <button
              onClick={() => setPage(pageClamped + 1)}
              disabled={pageClamped >= totalPages}
              className="px-3 py-1 text-xs border-[1.5px] disabled:opacity-30"
              style={{ borderColor: "#EF4444", color: "#EF4444" }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
