import React, { useEffect, useRef, useState } from "react";
import type { AnnotationItem } from "@humanbased/shared";
import type { VerticalMeta } from "./Overview";
import { THEME } from "../../lib/config";

const PAGE_SIZE = 20;

type Props = {
  items: AnnotationItem[];
  verticals?: VerticalMeta[];
  onAdopt: (id: string) => void;
  onDispute: (id: string) => void;
  onBatchAdopt?: (ids: string[]) => void;
  onBatchDispute?: (ids: string[]) => void;
  transitioningId?: string | null;
  autoAdoptHours?: number;
};

function timeAgo(dateStr: string): string {
  const sec = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  return `${Math.floor(min / 60)}h ago`;
}

function autoAdoptCountdown(dateStr: string, hours = 48): string | null {
  const AUTO_ADOPT_MS = hours * 60 * 60 * 1000;
  const remaining = new Date(dateStr).getTime() + AUTO_ADOPT_MS - Date.now();
  if (remaining <= 0) return "auto-adopts soon";
  const h = Math.floor(remaining / (60 * 60 * 1000));
  const m = Math.floor((remaining % (60 * 60 * 1000)) / (60 * 1000));
  if (h >= 1) return `auto-adopts in ${h}h`;
  return `auto-adopts in ${m}m`;
}

export function LiveStream({ items, verticals = [], onAdopt, onDispute, onBatchAdopt, onBatchDispute, transitioningId, autoAdoptHours = 48 }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [paused, setPaused] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  useEffect(() => { if (!paused && ref.current) ref.current.scrollTop = 0; }, [items, paused]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const pageClamped = Math.min(page, totalPages);
  const pagedItems = items.slice((pageClamped - 1) * PAGE_SIZE, pageClamped * PAGE_SIZE);

  // Build lookup
  const verticalBySlug = new Map(verticals.map((v) => [v.slug, v]));
  const verticalById   = new Map(verticals.map((v) => [v.id,   v]));

  function resolveVertical(item: AnnotationItem): VerticalMeta | null {
    if (item.vertical_slug && verticalBySlug.has(item.vertical_slug)) return verticalBySlug.get(item.vertical_slug)!;
    if (item.vertical_id   && verticalById.has(item.vertical_id))     return verticalById.get(item.vertical_id)!;
    return null;
  }

  function toggleSelect(id: string) {
    const s = new Set(selected);
    s.has(id) ? s.delete(id) : s.add(id);
    setSelected(s);
  }

  function toggleSelectAll() {
    const pendingIds = pagedItems.filter((i) => i.status === "pending").map((i) => i.id);
    const allSelected = pendingIds.every((id) => selected.has(id));
    if (allSelected) {
      const s = new Set(selected);
      pendingIds.forEach((id) => s.delete(id));
      setSelected(s);
    } else {
      setSelected(new Set([...selected, ...pendingIds]));
    }
  }

  const selectedCount = selected.size;
  const pendingOnPage = pagedItems.filter((i) => i.status === "pending");
  const allPageSelected = pendingOnPage.length > 0 && pendingOnPage.every((i) => selected.has(i.id));

  return (
    <div className="bg-white rounded-none border-[1.5px] border-[#1B1034]">
      <div className="flex items-center justify-between px-5 py-3 border-b border-[#1B1034]">
        <h2 className="text-sm font-medium text-gray-400">Live Data Stream</h2>
        <div className="flex items-center gap-3">
          {selectedCount > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs" style={{ color: THEME.accent }}>{selectedCount} selected</span>
              <button
                onClick={() => { if (onBatchAdopt) onBatchAdopt([...selected]); else [...selected].forEach(onAdopt); setSelected(new Set()); }}
                className="px-3 py-1 text-xs bg-[#1B1034] text-white"
              >
                Adopt All
              </button>
              <button
                onClick={() => { if (onBatchDispute) onBatchDispute([...selected]); else [...selected].forEach(onDispute); setSelected(new Set()); }}
                className="px-3 py-1 text-xs border border-gray-300"
              >
                Dispute All
              </button>
              <button
                onClick={() => setSelected(new Set())}
                className="text-xs underline"
                style={{ color: THEME.textMuted }}
              >
                Clear
              </button>
            </div>
          )}
          {paused && <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded">Paused</span>}
          <span className="text-xs text-gray-300">{items.length} items</span>
        </div>
      </div>
      <div
        ref={ref}
        className="overflow-y-auto"
        style={{ maxHeight: 500 }}
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        {items.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-300">Waiting for data to arrive...</div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-xs text-gray-400 text-left">
                <th className="px-3 py-2.5 font-medium w-10">
                  <input
                    type="checkbox"
                    checked={allPageSelected}
                    onChange={toggleSelectAll}
                    className="accent-[#1B1034]"
                  />
                </th>
                <th className="px-2 py-2.5 font-medium w-20">ID</th>
                <th className="px-2 py-2.5 font-medium">Vertical</th>
                <th className="px-2 py-2.5 font-medium">Preview</th>
                <th className="px-2 py-2.5 font-medium w-16">Quality</th>
                <th className="px-2 py-2.5 font-medium w-16">Price</th>
                <th className="px-2 py-2.5 font-medium w-16">Time</th>
                <th className="px-5 py-2.5 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pagedItems.map((item) => {
                const isExp    = expanded.has(item.id);
                const isFading = transitioningId === item.id;
                const v        = resolveVertical(item);
                const preview  = payloadPreview(item.payload, item.vertical_slug);
                const isSelected = selected.has(item.id);

                return (
                  <React.Fragment key={item.id}>
                    <tr
                      className="border-t border-[#1B1034] hover:bg-gray-50 cursor-pointer"
                      style={{
                        transition: "opacity 0.3s ease",
                        opacity: isFading ? 0 : 1,
                        background: isSelected ? THEME.accentLight : undefined,
                      }}
                      onClick={() => {
                        const s = new Set(expanded);
                        s.has(item.id) ? s.delete(item.id) : s.add(item.id);
                        setExpanded(s);
                      }}
                    >
                      <td className="px-3 py-3" onClick={(e) => e.stopPropagation()}>
                        {item.status === "pending" && (
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSelect(item.id)}
                            className="accent-[#1B1034]"
                          />
                        )}
                      </td>
                      <td className="px-2 py-3 font-mono text-xs text-gray-400">{item.id.slice(0, 8)}</td>
                      <td className="px-2 py-3">
                        {v ? (
                          <span className="inline-flex items-center gap-1 text-xs font-medium" style={{ color: "#5C5470" }}>
                            <span>{v.icon}</span>
                            <span>{v.name}</span>
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">
                            {(item.vertical_slug ?? "").replace(/_/g, " ") || "—"}
                          </span>
                        )}
                      </td>
                      <td className="px-2 py-3 text-xs text-gray-500 max-w-[200px] truncate">{preview}</td>
                      <td className="px-2 py-3 text-sm font-medium">{item.quality_score.toFixed(2)}</td>
                      <td className="px-2 py-3 text-sm text-gray-500">${item.unit_price_usd.toFixed(3)}</td>
                      <td className="px-2 py-3 text-xs text-gray-400">{timeAgo(item.created_at)}</td>
                      <td className="px-5 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        {item.status === "pending" ? (
                          <span className="flex flex-col items-end gap-1">
                            <span className="flex gap-2">
                              <button onClick={() => onAdopt(item.id)} className="px-3 py-1 text-xs bg-[#1B1034] text-white rounded-none hover:bg-[#2A1D4E]">Adopt</button>
                              <button onClick={() => onDispute(item.id)} className="px-3 py-1 text-xs border border-gray-300 rounded-none hover:bg-gray-50">Dispute</button>
                            </span>
                            <span className="text-[10px]" style={{ color: "#9CA3AF" }}>{autoAdoptCountdown(item.created_at, autoAdoptHours)}</span>
                          </span>
                        ) : (
                          <span className={`text-xs font-medium ${item.status === "accepted" ? "text-[#834DFB]" : "text-red-500"}`}>
                            {item.status}
                          </span>
                        )}
                      </td>
                    </tr>
                    {isExp && (
                      <tr>
                        <td colSpan={8} className="px-5 pb-3">
                          <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-3 text-xs font-mono text-gray-600">
                            <pre className="whitespace-pre-wrap">{JSON.stringify(item.payload, null, 2)}</pre>
                            <div className="flex gap-4 mt-2 text-gray-400">
                              <span>validators: {item.validator_count}</span>
                              <span>consensus: {item.consensus_ratio.toFixed(2)}</span>
                              <span>method: {item.quality_method}</span>
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
        )}
      </div>
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-5 py-3" style={{ borderTop: `1.5px solid ${THEME.border}` }}>
          <span className="text-xs" style={{ color: THEME.textMuted }}>
            Page {pageClamped} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(pageClamped - 1)}
              disabled={pageClamped <= 1}
              className="px-3 py-1 text-xs border-[1.5px] disabled:opacity-30"
              style={{ borderColor: THEME.border, color: THEME.textSecondary }}
            >
              Previous
            </button>
            <button
              onClick={() => setPage(pageClamped + 1)}
              disabled={pageClamped >= totalPages}
              className="px-3 py-1 text-xs border-[1.5px] disabled:opacity-30"
              style={{ borderColor: THEME.border, color: THEME.textSecondary }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Payload preview per vertical type ────────────────────────────────────────

function payloadPreview(payload: Record<string, unknown>, slug?: string | null): string {
  if (!payload) return "—";
  if (slug === "crypto_account_annotation") {
    const addr = String(payload.address ?? "").slice(0, 10);
    return `${addr}… ${payload.chain ?? ""} · ${payload.category ?? ""}`;
  }
  if (slug === "fashion_item_annotation") {
    return `${payload.brand ?? ""} ${payload.product_name ?? payload.category ?? ""}`.trim();
  }
  if (slug === "food_product_intelligence") {
    const ns = payload.nutriscore ? `nutriscore:${payload.nutriscore}` : "";
    return `${payload.brand ?? ""} ${payload.category ?? ""} ${ns}`.trim();
  }
  const vals = Object.values(payload).filter((v) => typeof v === "string").slice(0, 2);
  return vals.join(" · ") || "—";
}
