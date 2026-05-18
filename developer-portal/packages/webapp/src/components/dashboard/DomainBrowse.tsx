import React, { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useToast } from "../../lib/toast";
import { THEME } from "../../lib/config";
import { ENV } from "../../lib/env";
import { useFakeProgress, progressLabel } from "../../lib/useFakeProgress";

type DomainSummary = {
  domain_id: string;
  title: string;
  status: string;
  task_count: number;
  total_submissions: number;
};

type FrontierSub = {
  id: string;
  frontier_id: string;
  status: string;
  delivery_mode: string;
  created_at: string;
  filters?: { quality_grades?: string[] } | null;
};

type TaskSummary = {
  task_id: string;
  domain_id: string;
  name: string;
  task_type: string;
  status: string;
  submission_count: number;
};

type PreviewItem = {
  submission_id: string;
  data: Record<string, unknown>;
  quality_score: number;
  quality_grade: string;
  source: string;
  created_at: string | null;
};

// ── Frontier metadata (descriptions, icons, tags) ───────────────────────────

type DomainMeta = { icon: string; description: string; tags: string[] };

const DOMAIN_META: Record<string, DomainMeta> = {
  "CEX Hot Wallet": {
    icon: "🏦",
    description: "Deposit and withdrawal address annotations from centralized exchanges. Includes tx hashes, sender/receiver addresses, screenshots, and audit grades.",
    tags: ["crypto", "on-chain", "exchange"],
  },
  "User Skill Profiling": {
    icon: "🎓",
    description: "User skill assessments via surveys and exams. Evaluates knowledge levels across domains for contributor qualification and task matching.",
    tags: ["workforce", "qualification"],
  },
  "Food Science": {
    icon: "🍲",
    description: "Food product images with structured descriptions — ingredients, nutrition facts, and category labels for food intelligence applications.",
    tags: ["image", "food", "annotation"],
  },
  "Fashion": {
    icon: "👕",
    description: "Fashion item photos with brand, category, and attribute annotations. Covers apparel, accessories, and style classification.",
    tags: ["image", "fashion", "annotation"],
  },
  "Crypto & Stock Information": {
    icon: "📈",
    description: "Crowd-sourced crypto and stock market data points — price observations, project research, and market sentiment signals.",
    tags: ["crypto", "finance", "research"],
  },
  "Robotics": {
    icon: "🤖",
    description: "Image labels for robotics training datasets. Covers object manipulation, scene understanding, and task-oriented visual annotations.",
    tags: ["image", "robotics", "ML"],
  },
  "Appliance Knob": {
    icon: "🎛",
    description: "Kitchen appliance knob images with dial position and setting annotations for smart-home and appliance recognition models.",
    tags: ["image", "IoT", "annotation"],
  },
  "Real‑world Photo": {
    icon: "📸",
    description: "Diverse real-world photo collection covering everyday scenes, objects, and environments for general-purpose vision models.",
    tags: ["image", "photo", "collection"],
  },
  "Spot LLM's Mistakes": {
    icon: "🔍",
    description: "Human-identified errors in LLM outputs. Contributors find and document cases where language models produce incorrect or misleading responses.",
    tags: ["LLM", "evaluation", "text"],
  },
  "Model Comparison": {
    icon: "⚖️",
    description: "Side-by-side AI model evaluations. Human raters compare outputs from different models on standardized criteria.",
    tags: ["LLM", "evaluation", "benchmark"],
  },
  "Correct LLM's Mistakes": {
    icon: "✏️",
    description: "Human-provided corrections for LLM errors. Contributors supply the right answer to expose and fix model failure modes.",
    tags: ["LLM", "evaluation", "text"],
  },
  "Speech": {
    icon: "🎙",
    description: "Voice recordings with transcription and metadata for speech recognition and audio processing datasets.",
    tags: ["audio", "speech", "collection"],
  },
  "Lifelog Canvas": {
    icon: "📓",
    description: "Personal lifelog data contributions — daily activity records, location traces, and contextual annotations.",
    tags: ["lifelog", "personal", "collection"],
  },
  "Outfit of the Day": {
    icon: "👗",
    description: "Daily outfit photos with style tags, color palettes, and occasion labels for fashion recommendation systems.",
    tags: ["image", "fashion", "lifestyle"],
  },
  "NFT": {
    icon: "🖼",
    description: "NFT image annotations with collection, rarity, and visual attribute labels for digital art classification.",
    tags: ["crypto", "image", "annotation"],
  },
  "Advanced Physics Questions": {
    icon: "⚛️",
    description: "Expert-level physics Q&A for training and evaluating scientific reasoning in AI models.",
    tags: ["STEM", "text", "evaluation"],
  },
  "Food Annotation": {
    icon: "🥗",
    description: "Detailed food image labeling with ingredient detection, portion estimation, and nutritional categorization.",
    tags: ["image", "food", "annotation"],
  },
};

const DEFAULT_META: DomainMeta = {
  icon: "📦",
  description: "Crowd-sourced data collection and annotation tasks.",
  tags: ["data"],
};

function getMeta(title: string): DomainMeta {
  return DOMAIN_META[title] ?? DEFAULT_META;
}

// Fallback data when API is unreachable (e.g., local dev without VPS proxy)
const FALLBACK_DOMAINS: DomainSummary[] = [
  { domain_id: "fb-1", title: "CEX Hot Wallet", status: "ONLINE", task_count: 3, total_submissions: 142800 },
  { domain_id: "fb-2", title: "Food Science", status: "ONLINE", task_count: 2, total_submissions: 51200 },
  { domain_id: "fb-3", title: "Fashion", status: "COLLECTING", task_count: 4, total_submissions: 89300 },
  { domain_id: "fb-4", title: "Crypto & Stock Information", status: "OFFLINE", task_count: 1, total_submissions: 23400 },
  { domain_id: "fb-5", title: "NFT", status: "PAUSED", task_count: 2, total_submissions: 17600 },
  { domain_id: "fb-6", title: "Advanced Physics Questions", status: "ONLINE", task_count: 1, total_submissions: 8900 },
];

// ── Progress Bar ───────────────────────────────────────────────────────────

function ProgressBar({ percent, label }: { percent: number; label: string }) {
  return (
    <div className="py-12 px-4 flex justify-center">
      <div className="w-full max-w-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-medium" style={{ color: THEME.textSecondary }}>{label}</span>
          <span className="text-[11px] font-mono" style={{ color: THEME.textMuted }}>{Math.round(percent)}%</span>
        </div>
        <div className="w-full h-1 bg-[#E8E5ED] overflow-hidden">
          <div
            className="h-full"
            style={{
              width: `${percent}%`,
              background: THEME.btnBg,
              transition: percent >= 100 ? "width 0.3s ease" : "none",
            }}
          />
        </div>
      </div>
    </div>
  );
}

// ── Helpers ─────────────────────────────────────────────────────────────────

const STATUS_BADGE: Record<string, { label: string; color: string; bg: string }> = {
  ONLINE: { label: "Live", color: "#22C55E", bg: "#F0FDF4" },
  COLLECTING: { label: "Collecting", color: "#22C55E", bg: "#F0FDF4" },
  PREPARING: { label: "Preparing", color: "#F59E0B", bg: "#FFFBEB" },
  OFFLINE: { label: "Historical", color: "#6366F1", bg: "#EEF2FF" },
  PAUSED: { label: "Historical", color: "#6366F1", bg: "#EEF2FF" },
  FINISHED: { label: "Historical", color: "#6366F1", bg: "#EEF2FF" },
  STOP: { label: "Historical", color: "#6366F1", bg: "#EEF2FF" },
  PAUSE: { label: "Historical", color: "#6366F1", bg: "#EEF2FF" },
};

function StatusBadge({ status }: { status: string }) {
  const badge = STATUS_BADGE[status] ?? { label: status, color: THEME.textMuted, bg: "#F5F3F7" };
  return (
    <span className="text-[10px] font-medium px-2 py-0.5" style={{ color: badge.color, background: badge.bg }}>
      {badge.label}
    </span>
  );
}

function Tag({ label }: { label: string }) {
  return (
    <span
      className="text-[10px] px-1.5 py-0.5"
      style={{ color: THEME.textMuted, background: "#F5F3F7" }}
    >
      {label}
    </span>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

type SortKey = "submissions" | "name" | "tasks";
type QualityGrade = "S" | "A" | "B" | "C" | "D";

const LIVE_TASK_STATUSES = new Set(["ONLINE", "COLLECTING", "PREPARING"]);

// ── Flat Dropdown ──────────────────────────────────────────────────────────

type DropdownOption<T extends string> = { value: T; label: string };

function FlatDropdown<T extends string>({
  options,
  value,
  onChange,
  placeholder,
}: {
  options: DropdownOption<T>[];
  value: T;
  onChange: (v: T) => void;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const [dropUp, setDropUp] = useState(false);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (open && btnRef.current) {
      const rect = btnRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      const menuHeight = options.length * 30 + 4;
      setDropUp(spaceBelow < menuHeight && rect.top > menuHeight);
    }
  }, [open, options.length]);

  const selected = options.find((o) => o.value === value);

  return (
    <div ref={ref} className="relative">
      <button
        ref={btnRef}
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 text-[11px] px-2 py-1.5 border-[1.5px] bg-white transition-colors"
        style={{
          borderColor: THEME.border,
          color: THEME.textSecondary,
        }}
      >
        <span>{selected?.label ?? placeholder ?? "Select"}</span>
        <span className="text-[9px] ml-0.5" style={{ color: THEME.textMuted }}>
          {open ? "▲" : "▼"}
        </span>
      </button>
      {open && (
        <div
          className="absolute z-50 min-w-full border-[1.5px] bg-white"
          style={{
            borderColor: THEME.border,
            ...(dropUp
              ? { bottom: "100%", marginBottom: 2 }
              : { top: "100%", marginTop: 2 }),
            left: 0,
          }}
        >
          {options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => { onChange(opt.value); setOpen(false); }}
              className="w-full text-left text-[11px] px-3 py-1.5 flex items-center gap-2 transition-colors hover:bg-[#F5F3F7]"
              style={{
                color: opt.value === value ? THEME.accent : THEME.textSecondary,
                fontWeight: opt.value === value ? 600 : 400,
              }}
            >
              {opt.value === value && (
                <span className="text-[10px]" style={{ color: THEME.accent }}>✓</span>
              )}
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Subscription Agreement Modal ────────────────────────────────────────────

function SubscriptionAgreementModal({
  domain,
  onConfirm,
  onCancel,
}: {
  domain: DomainSummary;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const [agreed, setAgreed] = useState(false);
  const [showAgreementError, setShowAgreementError] = useState(false);
  const meta = getMeta(domain.title);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(27,16,52,0.45)" }}
      onClick={onCancel}
    >
      <div
        className="w-full max-w-lg bg-white border-[1.5px] border-[#1B1034] shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 pt-5 pb-4 border-b" style={{ borderColor: "rgba(27,16,52,0.15)" }}>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">{meta.icon}</span>
            <h3 className="text-base font-semibold" style={{ color: THEME.textPrimary }}>
              Subscribe to {domain.title}
            </h3>
          </div>
          <p className="text-xs" style={{ color: THEME.textMuted }}>
            {formatNumber(domain.total_submissions)} submissions available
          </p>
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Pricing overview */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: THEME.textSecondary }}>
              Pricing Model
            </h4>
            <div className="p-3 text-xs leading-relaxed" style={{ background: "#FAFAFA", color: THEME.textSecondary }}>
              <p className="mb-2">
                <strong>Currently free</strong> during the platform beta period. Usage is metered and will be billed in a future release.
              </p>
              <p className="mb-2">
                Future pricing formula: <code className="px-1 py-0.5" style={{ background: "#F0EBFF", color: THEME.accent }}>
                  unit_price = base_price x quality_multiplier
                </code>
              </p>
              <p>
                The quality multiplier factors in contributor count, reputation scores, and validation consensus. Higher-quality data commands a higher price per record.
              </p>
            </div>
          </div>

          {/* Terms */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: THEME.textSecondary }}>
              Data Usage Agreement
            </h4>
            <div
              className="p-3 text-xs leading-relaxed max-h-32 overflow-y-auto"
              style={{ background: "#FAFAFA", color: THEME.textSecondary }}
            >
              <p className="mb-2">By subscribing to this data source, you agree to the following terms:</p>
              <ul className="list-disc pl-4 space-y-1">
                <li>Data is licensed for your organization's internal use only.</li>
                <li>Redistribution of raw data to third parties is prohibited without written consent.</li>
                <li>You may use the data for model training, analytics, and product development.</li>
                <li>Contributor PII (if any) must be handled in compliance with applicable privacy regulations.</li>
                <li>Humanbased reserves the right to audit data usage and revoke access for violations.</li>
              </ul>
              <p className="mt-2 italic" style={{ color: THEME.textMuted }}>
                [Placeholder — full legal terms will be provided before general availability.]
              </p>
            </div>
          </div>

          {/* Checkbox */}
          <div>
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => { setAgreed(e.target.checked); if (e.target.checked) setShowAgreementError(false); }}
                className="mt-0.5"
                style={{ accentColor: THEME.accent, outline: showAgreementError ? `2px solid ${THEME.danger}` : undefined, borderRadius: 2 }}
              />
              <span className="text-xs" style={{ color: THEME.textPrimary }}>
                I have read and agree to the pricing terms and data usage agreement.
              </span>
            </label>
            {showAgreementError && (
              <p className="text-xs mt-1.5 ml-5" style={{ color: THEME.danger }}>
                Please check the box above to continue.
              </p>
            )}
          </div>
        </div>

        {/* Footer */}
        <div
          className="px-6 pb-5 flex gap-3 justify-end"
          style={{ borderTop: "1px solid rgba(27,16,52,0.08)", paddingTop: 16 }}
        >
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm border-[1.5px] border-[#1B1034]"
            style={{ color: THEME.textSecondary }}
          >
            Cancel
          </button>
          <button
            onClick={() => { if (!agreed) { setShowAgreementError(true); return; } onConfirm(); }}
            className="px-4 py-2 text-sm text-white font-medium"
            style={{ background: THEME.btnBg }}
          >
            Subscribe
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Task List (expandable under a frontier) ─────────────────────────────────

function TaskList({
  domain,
  statusFilter,
  onSubscribe,
}: {
  domain: DomainSummary;
  statusFilter: "all" | "live" | "historical";
  onSubscribe: (domainId: string, taskIds?: string[]) => void;
}) {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<{ taskId: string; items: PreviewItem[] } | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    apiFetch<{ data: Record<string, unknown>[] }>(`/v1/frontiers/${domain.domain_id}/tasks`)
      .then((res) => setTasks(res.data.map((t) => ({
        task_id: String(t.task_id ?? ""),
        domain_id: String(t.domain_id ?? t.frontier_id ?? ""),
        name: String(t.name ?? ""),
        task_type: String(t.task_type ?? ""),
        status: String(t.status ?? ""),
        submission_count: Number(t.submission_count ?? 0),
      }))))
      .catch(() => setTasks([]))
      .finally(() => setLoading(false));
  }, [domain.domain_id]);

  const visibleTasks = tasks.filter((t) => {
    if (statusFilter === "live") return LIVE_TASK_STATUSES.has(t.status);
    if (statusFilter === "historical") return !LIVE_TASK_STATUSES.has(t.status);
    return true;
  });

  async function handlePreview(taskId: string) {
    if (preview?.taskId === taskId) { setPreview(null); return; }
    setPreviewLoading(true);
    try {
      const res = await apiFetch<{ data: PreviewItem[] }>(
        `/v1/frontiers/${domain.domain_id}/tasks/${taskId}/preview?limit=5`
      );
      setPreview({ taskId, items: res.data });
    } catch {
      setPreview({ taskId, items: [] });
    } finally {
      setPreviewLoading(false);
    }
  }

  if (loading) return (
    <div className="py-4 px-5">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px]" style={{ color: THEME.textSecondary }}>Loading tasks...</span>
      </div>
      <div className="w-full h-0.5 bg-[#E8E5ED] overflow-hidden">
        <div className="h-full w-1/3 animate-pulse" style={{ background: THEME.btnBg }} />
      </div>
    </div>
  );

  return (
    <div className="border-t" style={{ borderColor: "rgba(27,16,52,0.1)" }}>
      <div className="px-5 py-3 flex items-center justify-between" style={{ background: "#FAFAFA" }}>
        <span className="text-xs" style={{ color: THEME.textSecondary }}>
          {visibleTasks.length} task{visibleTasks.length !== 1 ? "s" : ""}
          {statusFilter !== "all" && tasks.length !== visibleTasks.length && (
            <span style={{ color: THEME.textMuted }}> of {tasks.length}</span>
          )}
        </span>
        <button
          onClick={() => {
            const ids = statusFilter === "all" ? undefined : visibleTasks.map((t) => t.task_id);
            onSubscribe(domain.domain_id, ids);
          }}
          className="px-3 py-1.5 text-xs text-white font-medium"
          style={{ background: THEME.btnBg }}
        >
          Subscribe to All
        </button>
      </div>

      {visibleTasks.map((task) => (
        <div key={task.task_id}>
          <div className="px-5 py-3 flex items-center justify-between border-t" style={{ borderColor: "rgba(27,16,52,0.06)" }}>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-xs font-medium truncate" style={{ color: THEME.textPrimary }}>{task.name}</p>
                <StatusBadge status={task.status} />
              </div>
              <p className="text-[11px] mt-0.5" style={{ color: THEME.textMuted }}>
                {task.task_type} · {formatNumber(task.submission_count)} submissions
              </p>
            </div>
            <button
              onClick={() => handlePreview(task.task_id)}
              className="px-2.5 py-1 text-[11px] border-[1.5px] ml-3 flex-shrink-0"
              style={{
                borderColor: preview?.taskId === task.task_id ? THEME.accent : THEME.border,
                color: preview?.taskId === task.task_id ? THEME.accent : THEME.textSecondary,
              }}
            >
              {preview?.taskId === task.task_id ? "Hide" : "Preview"}
            </button>
          </div>

          {preview?.taskId === task.task_id && (
            <div className="px-5 pb-3">
              {previewLoading ? (
                <div className="text-xs py-3 text-center" style={{ color: THEME.textMuted }}>Loading...</div>
              ) : preview.items.length === 0 ? (
                <div className="text-xs py-3 text-center" style={{ color: THEME.textMuted }}>No preview data</div>
              ) : (
                <div className="border-[1.5px] border-[#1B1034] divide-y" style={{ fontSize: 11 }}>
                  <div className="grid grid-cols-12 px-3 py-2 text-[10px] uppercase tracking-wide" style={{ color: THEME.textMuted }}>
                    <span className="col-span-7">Data</span>
                    <span className="col-span-2 text-right">Grade</span>
                    <span className="col-span-3 text-right">Source</span>
                  </div>
                  {preview.items.map((item) => {
                    const dataStr = typeof item.data === "object"
                      ? Object.entries(item.data)
                          .filter(([, v]) => typeof v === "string" || typeof v === "number")
                          .slice(0, 3)
                          .map(([k, v]) => `${k}: ${String(v).slice(0, 20)}`)
                          .join(" | ")
                      : String(item.data).slice(0, 60);
                    return (
                      <div key={item.submission_id} className="grid grid-cols-12 px-3 py-2 items-center" style={{ borderTop: "1px solid rgba(27,16,52,0.08)" }}>
                        <span className="col-span-7 truncate font-mono" style={{ color: THEME.textSecondary }}>{dataStr}</span>
                        <span className="col-span-2 text-right font-medium" style={{ color: THEME.accent }}>{item.quality_grade}</span>
                        <span className="col-span-3 text-right" style={{ color: THEME.textMuted }}>{item.source}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Live Pull Data Drawer ─────────────────────────────────────────────────

type LiveSubmission = {
  submission_id: string;
  task_id: string;
  frontier_id: string;
  data: Record<string, unknown>;
  quality_score: number;
  quality_grade: string;
  unit_price_usd: number;
  source: string;
  created_at: string | null;
  consumer_feedback: string | null;
};

function LivePullDrawer({
  sub,
  domain,
  orgId,
  onClose,
}: {
  sub: FrontierSub;
  domain: DomainSummary | undefined;
  orgId: string;
  onClose: () => void;
}) {
  const [items, setItems] = useState<LiveSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [copied, setCopied] = useState(false);
  const meta = domain ? getMeta(domain.title) : { icon: "📦", description: "", tags: [] };

  const fetchData = useCallback(async (cursor?: string) => {
    const isMore = !!cursor;
    if (isMore) setLoadingMore(true); else setLoading(true);
    try {
      const qs = new URLSearchParams({ subscription_id: sub.id, limit: "50" });
      if (cursor) qs.set("cursor", cursor);
      const res = await apiFetch<{ data: LiveSubmission[]; next_cursor: string; has_more: boolean }>(
        `/v1/orgs/${orgId}/live/pull?${qs}`
      );
      setItems((prev) => isMore ? [...prev, ...res.data] : res.data);
      setNextCursor(res.next_cursor);
      setHasMore(res.has_more);
    } catch {
      // silent
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [orgId, sub.id]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const curlSnippet = `# cursor: start position for pagination. Use 0 for the first request; use next_cursor from the previous response to continue.
curl -s "${ENV.API_URL}/v1/live/pull?subscription_id=${sub.id}&limit=50&cursor=0" -H "Authorization: Bearer YOUR_API_KEY"`;

  function copySnippet() {
    navigator.clipboard.writeText(curlSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end"
      style={{ background: "rgba(27,16,52,0.4)" }}
      onClick={onClose}
    >
      <div
        className="h-full w-full max-w-xl bg-white border-l-[1.5px] border-[#1B1034] flex flex-col"
        style={{ animation: "slideIn 0.2s ease" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1B1034]" style={{ borderBottomWidth: 1.5 }}>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg">{meta.icon}</span>
              <h2 className="text-base font-semibold" style={{ color: THEME.textPrimary }}>
                Pull Data
              </h2>
            </div>
            <p className="text-xs mt-0.5" style={{ color: THEME.textMuted }}>{domain?.title ?? sub.frontier_id}</p>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center text-lg leading-none"
            style={{ color: THEME.textSecondary }}
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {/* Subscription meta */}
          <div className="grid grid-cols-2 gap-3">
            {([
              ["Subscription ID", sub.id.slice(0, 16) + "…"],
              ["Mode", sub.delivery_mode],
              ["Status", sub.status],
              ["Since", new Date(sub.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })],
            ] as const).map(([label, value]) => (
              <div key={label} className="border-[1.5px] border-[#1B1034] px-3 py-2">
                <p className="text-[10px] uppercase tracking-wide" style={{ color: THEME.textMuted }}>{label}</p>
                <p className="text-xs font-mono mt-0.5 truncate" style={{ color: THEME.textPrimary }}>{value}</p>
              </div>
            ))}
          </div>

          {/* Code snippet */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-medium" style={{ color: THEME.textSecondary }}>API Usage</span>
              <button
                onClick={copySnippet}
                className="text-xs px-2 py-0.5 border-[1.5px]"
                style={{
                  borderColor: copied ? THEME.accent : THEME.border,
                  color: copied ? THEME.accent : THEME.textMuted,
                }}
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
            <pre
              className="text-[11px] font-mono p-3 overflow-x-auto leading-relaxed"
              style={{ background: THEME.btnBg, color: "#C4B8E0" }}
            >
              {curlSnippet}
            </pre>
          </div>

          {/* Live items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium" style={{ color: THEME.textSecondary }}>
                Submissions
              </span>
              <span className="text-xs" style={{ color: THEME.textMuted }}>
                {loading ? "Loading…" : `${items.length} items`}
              </span>
            </div>

            {loading ? (
              <div className="py-8 text-center text-sm" style={{ color: THEME.textMuted }}>Loading…</div>
            ) : items.length === 0 ? (
              <div className="py-8 text-center border-[1.5px] border-dashed text-sm" style={{ borderColor: THEME.textMuted, color: THEME.textMuted }}>
                No submissions available yet
              </div>
            ) : (
              <>
                <div className="border-[1.5px] border-[#1B1034] divide-y" style={{ divideColor: "#1B1034" }}>
                  <div className="grid grid-cols-12 px-3 py-2 text-[10px] uppercase tracking-wide" style={{ color: THEME.textMuted }}>
                    <span className="col-span-6">Data</span>
                    <span className="col-span-2 text-right">Grade</span>
                    <span className="col-span-2 text-right">Price</span>
                    <span className="col-span-2 text-right">Source</span>
                  </div>
                  {items.map((item) => {
                    const dataStr = typeof item.data === "object"
                      ? Object.entries(item.data)
                          .filter(([, v]) => typeof v === "string" || typeof v === "number")
                          .slice(0, 3)
                          .map(([k, v]) => `${k}: ${String(v).slice(0, 20)}`)
                          .join(" | ")
                      : String(item.data).slice(0, 60);
                    return (
                      <div key={item.submission_id} className="grid grid-cols-12 px-3 py-2 items-center" style={{ borderTop: "1px solid rgba(27,16,52,0.08)" }}>
                        <span className="col-span-6 truncate font-mono text-[11px]" style={{ color: THEME.textSecondary }}>{dataStr}</span>
                        <span className="col-span-2 text-right text-[11px] font-medium" style={{ color: THEME.accent }}>{item.quality_grade}</span>
                        <span className="col-span-2 text-right text-[11px]" style={{ color: THEME.textMuted }}>${item.unit_price_usd.toFixed(3)}</span>
                        <span className="col-span-2 text-right text-[11px]" style={{ color: THEME.textMuted }}>{item.source}</span>
                      </div>
                    );
                  })}
                </div>
                {hasMore && (
                  <button
                    onClick={() => nextCursor && fetchData(nextCursor)}
                    disabled={loadingMore}
                    className="w-full mt-3 py-2 text-xs border-[1.5px] disabled:opacity-50"
                    style={{ borderColor: THEME.border, color: THEME.textSecondary }}
                  >
                    {loadingMore ? "Loading…" : "Load More"}
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Unsubscribe Confirm Modal ────────────────────────────────────────────────

function UnsubscribeConfirmModal({
  sub,
  domain,
  onConfirm,
  onCancel,
}: {
  sub: FrontierSub;
  domain: DomainSummary | undefined;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const meta = domain ? getMeta(domain.title) : { icon: "📦", description: "", tags: [] };
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(27,16,52,0.45)" }}
      onClick={onCancel}
    >
      <div
        className="w-full max-w-sm bg-white border-[1.5px] border-[#1B1034] shadow-xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">{meta.icon}</span>
          <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>
            Unsubscribe from {domain?.title ?? sub.frontier_id}?
          </h3>
        </div>
        <p className="text-xs mb-5" style={{ color: THEME.textSecondary }}>
          You will stop receiving new data from this source. Existing pulled data is not affected. You can re-subscribe at any time.
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-xs border-[1.5px]"
            style={{ borderColor: THEME.border, color: THEME.textSecondary }}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-xs text-white font-medium"
            style={{ background: THEME.danger }}
          >
            Unsubscribe
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Edit Filters Modal ───────────────────────────────────────────────────────

const GRADE_LABELS: { grade: QualityGrade; score: string }[] = [
  { grade: "S", score: "97" },
  { grade: "A", score: "85" },
  { grade: "B", score: "70" },
  { grade: "C", score: "50" },
  { grade: "D", score: "30" },
];

function EditFiltersModal({
  sub,
  domain,
  onSave,
  onCancel,
}: {
  sub: FrontierSub;
  domain: DomainSummary | undefined;
  onSave: (grades: QualityGrade[] | null) => Promise<void>;
  onCancel: () => void;
}) {
  const currentGrades = sub.filters?.quality_grades as QualityGrade[] | undefined;
  const [selected, setSelected] = useState<Set<QualityGrade | "all">>(
    currentGrades && currentGrades.length > 0
      ? new Set(currentGrades)
      : new Set(["all"])
  );
  const [saving, setSaving] = useState(false);
  const meta = domain ? getMeta(domain.title) : { icon: "📦", description: "", tags: [] };

  function toggle(grade: QualityGrade | "all") {
    setSelected((prev) => {
      if (grade === "all") return new Set(["all"]);
      const next = new Set(prev);
      next.delete("all");
      if (next.has(grade)) {
        next.delete(grade);
        if (next.size === 0) return new Set(["all"]);
      } else {
        next.add(grade);
      }
      return next;
    });
  }

  async function handleSave() {
    setSaving(true);
    const grades = selected.has("all") ? null : (Array.from(selected) as QualityGrade[]);
    await onSave(grades);
    setSaving(false);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(27,16,52,0.45)" }}
      onClick={onCancel}
    >
      <div
        className="w-full max-w-sm bg-white border-[1.5px] border-[#1B1034] shadow-xl p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="text-lg">{meta.icon}</span>
          <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>Edit Quality Filter</h3>
        </div>
        <p className="text-xs mb-5" style={{ color: THEME.textSecondary }}>
          Only submissions matching the selected grades will be returned on the next pull.
        </p>

        <div className="flex gap-2 mb-1">
          {(["all", "S", "A", "B", "C", "D"] as const).map((g) => {
            const isAll = g === "all";
            const active = selected.has(g);
            return (
              <button
                key={g}
                onClick={() => toggle(g)}
                className="flex-1 py-2 text-xs font-semibold border-[1.5px] transition-colors"
                style={{
                  borderColor: active ? THEME.accent : THEME.border,
                  background: active ? THEME.accent : "transparent",
                  color: active ? "#fff" : THEME.textSecondary,
                }}
              >
                {isAll ? "All" : g}
              </button>
            );
          })}
        </div>
        <div className="flex gap-2 mb-5">
          <span className="flex-1 text-center text-[10px]" style={{ color: THEME.textMuted }}></span>
          {GRADE_LABELS.map(({ grade, score }) => (
            <span key={grade} className="flex-1 text-center text-[10px]" style={{ color: THEME.textMuted }}>{score}</span>
          ))}
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-xs border-[1.5px]"
            style={{ borderColor: THEME.border, color: THEME.textSecondary }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-xs text-white font-medium disabled:opacity-50"
            style={{ background: THEME.btnBg }}
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Frontier Card ───────────────────────────────────────────────────────────

function DomainCard({
  domain,
  isExpanded,
  isSubscribed,
  statusFilter,
  onToggle,
  onSubscribe,
}: {
  domain: DomainSummary;
  isExpanded: boolean;
  isSubscribed: boolean;
  statusFilter: "all" | "live" | "historical";
  onToggle: () => void;
  onSubscribe: (domainId: string, taskIds?: string[]) => void;
}) {
  const meta = getMeta(domain.title);
  const isLive = domain.status === "ONLINE";
  const innerRef = useRef<HTMLDivElement>(null);
  const [measuredHeight, setMeasuredHeight] = useState(0);

  useEffect(() => {
    const el = innerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setMeasuredHeight(el.scrollHeight));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!isExpanded) setMeasuredHeight(0);
  }, [isExpanded]);

  // Fixed collapsed height keeps all cards uniform. Update if card design changes.
  const CARD_HEIGHT = 240;

  return (
    <div
      className="bg-white border-[1.5px] border-[#1B1034] flex flex-col"
      style={{ height: isExpanded ? undefined : CARD_HEIGHT, transition: "all 0.3s ease" }}
    >
      <div className="p-5 flex-1 overflow-hidden cursor-pointer" onClick={onToggle}>
        <div className="flex items-start justify-between mb-2">
          <span className="text-2xl">{meta.icon}</span>
          <div className="flex items-center gap-1.5">
            {isSubscribed && (
              <span className="text-[10px] font-medium px-2 py-0.5" style={{ color: THEME.accent, background: "#F0EBFF" }}>
                Subscribed
              </span>
            )}
            <StatusBadge status={domain.status} />
            {!isLive && domain.total_submissions > 0 && (
              <span className="text-[10px] font-medium px-2 py-0.5" style={{ color: "#6366F1", background: "#EEF2FF" }}>
                Data available
              </span>
            )}
            {isExpanded && (
              <button
                onClick={(e) => { e.stopPropagation(); onToggle(); }}
                className="w-6 h-6 flex items-center justify-center border-[1.5px] text-xs"
                style={{ borderColor: THEME.border, color: THEME.textSecondary, background: "white" }}
                aria-label="Close detail view"
              >
                ✕
              </button>
            )}
          </div>
        </div>
        <h3 className="text-sm font-semibold mb-1" style={{ color: THEME.textPrimary }}>{domain.title}</h3>
        <p className="text-xs leading-relaxed mb-2 line-clamp-2" style={{ color: THEME.textSecondary }}>{meta.description}</p>
        <div className="flex flex-wrap gap-1 mb-2">
          {meta.tags.map((t) => <Tag key={t} label={t} />)}
        </div>
      </div>

      <div className="px-5 pb-4 flex items-center justify-between">
        <span className="text-xs" style={{ color: THEME.textMuted }}>
          {domain.task_count} task{domain.task_count !== 1 ? "s" : ""} · {formatNumber(domain.total_submissions)} records
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); onToggle(); }}
          className="text-xs px-3 py-1 border-[1.5px]"
          style={{ borderColor: THEME.border, color: isExpanded ? THEME.accent : THEME.textSecondary }}
        >
          {isExpanded ? "Collapse" : "Explore"}
        </button>
      </div>

      <div
        className="overflow-hidden"
        style={{
          height: isExpanded ? measuredHeight : 0,
          opacity: isExpanded ? 1 : 0,
          transition: "height 0.3s ease, opacity 0.2s ease",
        }}
      >
        <div ref={innerRef}>
          {isExpanded && <TaskList domain={domain} statusFilter={statusFilter} onSubscribe={onSubscribe} />}
        </div>
      </div>
    </div>
  );
}

// ── Domain Grid ────────────────────────────────────────────────────────────
// Stable 2-column grid. Expanded card uses col-span-2 (full width).
// If the expanded card is in the right column, swap it with its left neighbor
// (within the same row only) so col-span-2 starts at column 1 cleanly.
// No cross-row reordering — cards stay in stable DOM positions.

function DomainGrid({
  items,
  expandedId,
  subscribedDomainIds,
  statusFilter,
  onToggle,
  onSubscribe,
}: {
  items: DomainSummary[];
  expandedId: string | null;
  subscribedDomainIds: Set<string>;
  statusFilter: "all" | "live" | "historical";
  onToggle: (id: string) => void;
  onSubscribe: (domainId: string, taskIds?: string[]) => void;
}) {
  // Swap within-row only when expanded card is in the right column
  const ordered = [...items];
  if (expandedId) {
    const idx = ordered.findIndex((f) => f.domain_id === expandedId);
    if (idx !== -1 && idx % 2 === 1 && idx - 1 >= 0) {
      [ordered[idx - 1], ordered[idx]] = [ordered[idx], ordered[idx - 1]];
    }
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {ordered.map((item) => (
        <div
          key={item.domain_id}
          className={item.domain_id === expandedId ? "col-span-2" : ""}
        >
          <DomainCard
            domain={item}
            isExpanded={item.domain_id === expandedId}
            isSubscribed={subscribedDomainIds.has(item.domain_id)}
            statusFilter={statusFilter}
            onToggle={() => onToggle(item.domain_id)}
            onSubscribe={onSubscribe}
          />
        </div>
      ))}
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────────────

export function DomainBrowse() {
  const { orgId } = useAuth();
  const { toast } = useToast();
  const [domains, setDomains] = useState<DomainSummary[]>([]);
  const [activeSubs, setActiveSubs] = useState<FrontierSub[]>([]);
  const [done, setDone] = useState(false);
  const progress = useFakeProgress(done, 3000);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortKey>("submissions");
  const [tagFilter, setTagFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"all" | "live" | "historical">("all");
  const [agreementDomain, setAgreementDomain] = useState<DomainSummary | null>(null);
  const [pendingTaskIds, setPendingTaskIds] = useState<string[] | undefined>(undefined);
  const [pullSub, setPullSub] = useState<FrontierSub | null>(null);
  const [unsubSub, setUnsubSub] = useState<FrontierSub | null>(null);
  const [editFiltersSub, setEditFiltersSub] = useState<FrontierSub | null>(null);

  const fetchDomains = useCallback(async () => {
    try {
      const [domainsRes, subsRes] = await Promise.all([
        // Use /v1/frontiers until API is redeployed with /v1/domains
        apiFetch<{ data: Record<string, unknown>[] }>("/v1/frontiers?status=all"),
        orgId
          ? apiFetch<{ data: Record<string, unknown>[] }>(`/v1/orgs/${orgId}/subscriptions`)
          : Promise.resolve({ data: [] as Record<string, unknown>[] }),
      ]);
      const mapped: DomainSummary[] = domainsRes.data.map((d) => ({
        domain_id: String(d.domain_id ?? d.frontier_id ?? ""),
        title: String(d.title ?? ""),
        status: String(d.status ?? ""),
        task_count: Number(d.task_count ?? 0),
        total_submissions: Number(d.total_submissions ?? 0),
      }));
      setDomains(mapped.length > 0 ? mapped : FALLBACK_DOMAINS);
      const frontierSubs = (subsRes.data ?? []).filter(
        (s) => s.frontier_id && s.status === "active"
      ) as FrontierSub[];
      setActiveSubs(frontierSubs);
    } catch {
      setDomains(FALLBACK_DOMAINS);
    } finally {
      setDone(true);
    }
  }, [orgId]);

  useEffect(() => { fetchDomains(); }, [fetchDomains]);

  // Collect all unique tags
  const allTags = Array.from(new Set(domains.flatMap((f) => getMeta(f.title).tags))).sort();

  // Filter
  let filtered = domains;
  if (statusFilter === "live") filtered = filtered.filter((f) => f.status === "ONLINE");
  if (statusFilter === "historical") filtered = filtered.filter((f) => f.status !== "ONLINE");
  if (tagFilter) filtered = filtered.filter((f) => getMeta(f.title).tags.includes(tagFilter));

  // Sort
  filtered = [...filtered].sort((a, b) => {
    if (sortBy === "submissions") return b.total_submissions - a.total_submissions;
    if (sortBy === "tasks") return b.task_count - a.task_count;
    return a.title.localeCompare(b.title);
  });

  function handleSubscribeIntent(domainId: string, taskIds?: string[]) {
    const f = domains.find((x) => x.domain_id === domainId);
    if (!f) return;
    setAgreementDomain(f);
    setPendingTaskIds(taskIds);
  }

  async function confirmSubscribe() {
    if (!orgId || !agreementDomain) return;
    try {
      // Check if org already has an active subscription for this domain
      const existing = await apiFetch<{ data: Array<{ id: string; frontier_id: string; status: string }> }>(
        `/v1/orgs/${orgId}/subscriptions`
      );
      const alreadySubscribed = existing.data.find(
        (s) => s.frontier_id === agreementDomain.domain_id && s.status === "active"
      );
      if (alreadySubscribed) {
        toast("Your organization is already subscribed to this data source. A team member may have subscribed earlier.", "error");
        setAgreementDomain(null);
        setPendingTaskIds(undefined);
        return;
      }

      const newSub = await apiFetch<{ data: Record<string, unknown> }>(`/v1/orgs/${orgId}/subscriptions`, {
        method: "POST",
        body: JSON.stringify({
          // Send both for backward compat with old/new API
          frontier_id: agreementDomain.domain_id,
          domain_id: agreementDomain.domain_id,
          task_ids: pendingTaskIds,
          delivery_mode: "pull",
          filters: null,
        }),
      });
      if (newSub.data) {
        setActiveSubs((prev) => [...prev, newSub.data as FrontierSub]);
      }
      toast("Subscribed successfully");
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to subscribe", "error");
    } finally {
      setAgreementDomain(null);
      setPendingTaskIds(undefined);
    }
  }

  async function handleUpdateFilters(grades: QualityGrade[] | null) {
    if (!orgId || !editFiltersSub) return;
    try {
      const res = await apiFetch<{ data: FrontierSub }>(`/v1/orgs/${orgId}/subscriptions/${editFiltersSub.id}`, {
        method: "PATCH",
        body: JSON.stringify({ filters: grades ? { quality_grades: grades } : null }),
      });
      setActiveSubs((prev) => prev.map((s) => s.id === editFiltersSub.id ? { ...s, filters: res.data.filters } : s));
      toast("Filter updated");
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to update filter", "error");
    } finally {
      setEditFiltersSub(null);
    }
  }

  async function handleUnsubscribe() {
    if (!orgId || !unsubSub) return;
    try {
      await apiFetch(`/v1/orgs/${orgId}/subscriptions/${unsubSub.id}/cancel`, { method: "POST" });
      setActiveSubs((prev) => prev.filter((s) => s.id !== unsubSub.id));
      toast("Unsubscribed successfully");
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to unsubscribe", "error");
    } finally {
      setUnsubSub(null);
    }
  }

  const subscribedDomainIds = new Set(activeSubs.map((s) => s.frontier_id));

  if (progress < 100) {
    return <ProgressBar percent={progress} label={progressLabel(progress, done)} />;
  }

  return (
    <div>
      {/* Active subscriptions summary */}
      {activeSubs.length > 0 && (
        <div className="mb-8">
          <h3 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: THEME.textSecondary }}>
            Active Subscriptions
          </h3>
          <div className="space-y-3">
            {activeSubs.map((sub) => {
              const domain = domains.find((d) => d.domain_id === sub.frontier_id);
              const meta = domain ? getMeta(domain.title) : { icon: "📦", description: "", tags: [] };
              return (
                <div
                  key={sub.id}
                  className="bg-white border-[1.5px] border-[#1B1034] p-5 flex items-start justify-between"
                  style={{ borderLeft: `3px solid ${THEME.accent}` }}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg flex-shrink-0">{meta.icon}</span>
                      <p className="text-sm font-semibold truncate" style={{ color: THEME.textPrimary }}>
                        {domain?.title ?? sub.frontier_id}
                      </p>
                    </div>
                    <p className="text-xs mb-2" style={{ color: THEME.textMuted }}>
                      {sub.delivery_mode} · since{" "}
                      {new Date(sub.created_at).toLocaleDateString("en-US", {
                        month: "short", day: "numeric", year: "numeric",
                      })}
                      {" · "}
                      <span className="font-mono">{sub.id.slice(0, 8)}…</span>
                    </p>
                    <p className="text-xs mb-3" style={{ color: THEME.textMuted }}>
                      Grades:{" "}
                      {sub.filters?.quality_grades?.length
                        ? sub.filters.quality_grades.map((g) => (
                            <span
                              key={g}
                              className="inline-block px-1.5 py-0.5 text-[10px] font-semibold mr-1"
                              style={{ background: "#F0EBFF", color: THEME.accent }}
                            >
                              {g}
                            </span>
                          ))
                        : <span style={{ color: THEME.textMuted }}>all</span>
                      }
                    </p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        onClick={() => setPullSub(sub)}
                        className="px-3 py-1.5 text-xs text-white font-medium"
                        style={{ background: THEME.btnBg }}
                      >
                        ⬇ Pull Data
                      </button>
                      <button
                        onClick={() => setEditFiltersSub(sub)}
                        className="px-3 py-1.5 text-xs border-[1.5px]"
                        style={{ borderColor: THEME.border, color: THEME.textSecondary }}
                      >
                        Edit Filters
                      </button>
                      <button
                        onClick={() => setUnsubSub(sub)}
                        className="px-3 py-1.5 text-xs border-[1.5px]"
                        style={{ borderColor: THEME.danger, color: THEME.danger }}
                      >
                        Unsubscribe
                      </button>
                    </div>
                  </div>
                  <span className="text-xs font-medium ml-4 flex-shrink-0" style={{ color: THEME.accent }}>active</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <h3 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: THEME.textSecondary }}>
        Live Data Sources
      </h3>

      {/* Filter & sort bar */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {/* Status filter */}
        <div className="inline-flex border-[1.5px] border-[#1B1034] text-[11px] overflow-hidden">
          {(["all", "live", "historical"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className="px-3 py-1.5 transition-colors"
              style={{
                background: statusFilter === s ? THEME.btnBg : "transparent",
                color: statusFilter === s ? "#fff" : THEME.textSecondary,
              }}
            >
              {s === "all" ? "All" : s === "live" ? "Live" : "Historical"}
            </button>
          ))}
        </div>

        {/* Tag filter */}
        <FlatDropdown
          options={[
            { value: "", label: "All categories" },
            ...allTags.map((t) => ({ value: t, label: t })),
          ]}
          value={tagFilter ?? ""}
          onChange={(v) => setTagFilter(v || null)}
          placeholder="All categories"
        />

        {/* Sort */}
        <FlatDropdown<SortKey>
          options={[
            { value: "submissions", label: "Most data" },
            { value: "tasks", label: "Most tasks" },
            { value: "name", label: "A-Z" },
          ]}
          value={sortBy}
          onChange={setSortBy}
        />

        <span className="text-[11px] ml-auto" style={{ color: THEME.textMuted }}>
          {filtered.length} source{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Cards grid */}
      {filtered.length > 0 ? (
        <DomainGrid
          items={filtered}
          expandedId={expanded}
          subscribedDomainIds={subscribedDomainIds}
          statusFilter={statusFilter}
          onToggle={(id) => setExpanded(expanded === id ? null : id)}
          onSubscribe={handleSubscribeIntent}
        />
      ) : (
        <div className="text-sm text-center py-12 border-[1.5px] border-dashed" style={{ borderColor: THEME.textMuted, color: THEME.textMuted }}>
          No data sources match your filters
        </div>
      )}

      {/* Subscription agreement modal */}
      {agreementDomain && (
        <SubscriptionAgreementModal
          domain={agreementDomain}
          onConfirm={confirmSubscribe}
          onCancel={() => { setAgreementDomain(null); setPendingTaskIds(undefined); }}
        />
      )}

      {/* Live Pull Data drawer */}
      {pullSub && orgId && (
        <LivePullDrawer
          sub={pullSub}
          domain={domains.find((d) => d.domain_id === pullSub.frontier_id)}
          orgId={orgId}
          onClose={() => setPullSub(null)}
        />
      )}

      {/* Unsubscribe confirmation */}
      {unsubSub && (
        <UnsubscribeConfirmModal
          sub={unsubSub}
          domain={domains.find((d) => d.domain_id === unsubSub.frontier_id)}
          onConfirm={handleUnsubscribe}
          onCancel={() => setUnsubSub(null)}
        />
      )}

      {/* Edit filters modal */}
      {editFiltersSub && (
        <EditFiltersModal
          sub={editFiltersSub}
          domain={domains.find((d) => d.domain_id === editFiltersSub.frontier_id)}
          onSave={handleUpdateFilters}
          onCancel={() => setEditFiltersSub(null)}
        />
      )}
    </div>
  );
}
