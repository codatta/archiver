import React, { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useToast } from "../../lib/toast";
import { THEME } from "../../lib/config";
import { ENV } from "../../lib/env";
import { navigate } from "../../App";
import { DomainBrowse } from "./DomainBrowse";
import { useSandboxSubscriptions, useSandboxSubFilters, useSandboxApiKeys, useSandboxCursors } from "../../lib/useSandboxState";

// ── Types ─────────────────────────────────────────────────────────────────────

type Subscription = {
  id: string;
  vertical_id: string | null;
  frontier_id: string | null;
  delivery_mode: "pull" | "push";
  filters: Record<string, unknown> | null;
  auto_accept: boolean;
  status: "active" | "paused" | "cancelled";
  created_at: string;
  verticals?: { id: string; slug: string; name: string };
};

type Vertical = {
  id: string;
  slug: string;
  name: string;
  description: string;
  base_price_usd: number;
  topic_count?: number;
};

const VERTICAL_ICONS: Record<string, string> = {
  crypto_account_annotation: "🏦",
  food_product_intelligence: "🍲",
  fashion_item_annotation:   "👕",
  medical_literature:        "📚",
  legal_document_analysis:   "📄",
  satellite_imagery:         "🌍",
};

// ── Edit Filters Modal (Sandbox) ──────────────────────────────────────────────

type SandboxQualityGrade = "S" | "A" | "B" | "C" | "D";

const SANDBOX_GRADE_LABELS: { grade: SandboxQualityGrade; score: string }[] = [
  { grade: "S", score: "97" },
  { grade: "A", score: "85" },
  { grade: "B", score: "70" },
  { grade: "C", score: "50" },
  { grade: "D", score: "30" },
];

function SandboxEditFiltersModal({
  verticalId,
  verticalName,
  currentGrades,
  onSave,
  onCancel,
}: {
  verticalId: string;
  verticalName: string;
  currentGrades: string[] | null;
  onSave: (grades: SandboxQualityGrade[] | null) => void;
  onCancel: () => void;
}) {
  const [selected, setSelected] = useState<Set<SandboxQualityGrade | "all">>(
    currentGrades && currentGrades.length > 0
      ? new Set(currentGrades as SandboxQualityGrade[])
      : new Set(["all"])
  );

  function toggle(grade: SandboxQualityGrade | "all") {
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

  function handleSave() {
    const grades = selected.has("all") ? null : (Array.from(selected) as SandboxQualityGrade[]);
    onSave(grades);
  }

  const icon = VERTICAL_ICONS[verticalId] ?? "📦";

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
          <span className="text-lg">{icon}</span>
          <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>Edit Quality Filter</h3>
        </div>
        <p className="text-xs mb-5" style={{ color: THEME.textSecondary }}>
          Only submissions matching the selected grades will be returned on the next pull.
        </p>

        <div className="flex gap-2 mb-1">
          {(["all", "S", "A", "B", "C", "D"] as const).map((g) => {
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
                {g === "all" ? "All" : g}
              </button>
            );
          })}
        </div>
        <div className="flex gap-2 mb-5">
          <span className="flex-1 text-center text-[10px]" style={{ color: THEME.textMuted }}></span>
          {SANDBOX_GRADE_LABELS.map(({ grade, score }) => (
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
            className="px-4 py-2 text-xs text-white font-medium"
            style={{ background: THEME.btnBg }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Pull Data Drawer ──────────────────────────────────────────────────────────

type PullResult = {
  count: number;
  has_more: boolean;
  next_cursor: string;
  data: Record<string, unknown>[];
};

function PullDataDrawer({
  sub,
  vertical,
  mode,
  orgId,
  onClose,
}: {
  sub: Subscription;
  vertical: Vertical | undefined;
  mode: "production" | "simulation";
  orgId: string | null;
  onClose: () => void;
}) {
  const isSandbox = mode === "simulation";
  const { keys: sandboxKeys } = useSandboxApiKeys();
  const { getCursor, incrementCursor, resetCursor } = useSandboxCursors();
  const verticalId = sub.vertical_id ?? sub.id;

  const [pastedKey, setPastedKey] = useState("");
  const [running, setRunning] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [result, setResult] = useState<PullResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [copiedResult, setCopiedResult] = useState(false);

  // Sandbox key selector state (sandbox-only — prod uses pasted key)
  const [selectedKeyId, setSelectedKeyId] = useState<string | null>(null);
  useEffect(() => {
    if (!isSandbox) return;
    if (selectedKeyId) return;
    if (sandboxKeys.length > 0) setSelectedKeyId(sandboxKeys[sandboxKeys.length - 1].id);
  }, [isSandbox, sandboxKeys, selectedKeyId]);

  const isValidKey = pastedKey.startsWith("hb_live_sk_");
  const canRun = isSandbox ? sandboxKeys.length > 0 : isValidKey;

  async function handleRun() {
    setRunning(true);
    setRunError(null);
    try {
      if (isSandbox) {
        const slug = vertical?.slug ?? verticalId;
        const res = await apiFetch<PullResult>(`/v1/sandbox/simulate?vertical_slug=${slug}&limit=10`);
        setResult(res);
        incrementCursor(verticalId);
      } else {
        // Call the consumer API directly with the pasted key — advances subscription cursor
        const res = await apiFetch<PullResult>(
          `/v1/live/pull?subscription_id=${sub.id}&limit=50`,
          { headers: { Authorization: `Bearer ${pastedKey}` } },
        );
        setResult(res);
      }
    } catch (e: unknown) {
      setRunError((e as Error).message ?? "Pull failed");
    } finally {
      setRunning(false);
    }
  }

  async function handleReset() {
    setResetting(true);
    setRunError(null);
    try {
      if (isSandbox) {
        resetCursor(verticalId);
      } else {
        await apiFetch(`/v1/orgs/${orgId}/live/reset-cursor?subscription_id=${sub.id}`, { method: "POST" });
      }
      setResult(null);
    } catch (e: unknown) {
      setRunError((e as Error).message ?? "Reset failed");
    } finally {
      setResetting(false);
    }
  }

  const selectedSandboxKey = isSandbox ? sandboxKeys.find((k) => k.id === selectedKeyId) ?? null : null;
  const keyToken = isSandbox
    ? (selectedSandboxKey?.key ?? "YOUR_API_KEY")
    : (isValidKey ? pastedKey : "YOUR_API_KEY");

  const curlSnippet = `# Omit cursor — the server tracks your position automatically.
# Pass cursor=0 to pull from the beginning.
curl -s "${ENV.API_URL}/v1/live/pull?subscription_id=${sub.id}&limit=50" \\
  -H "Authorization: Bearer ${keyToken}"`;

  function copySnippet() {
    navigator.clipboard.writeText(curlSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const batchNum = isSandbox ? getCursor(verticalId) : null;

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
              <span className="text-lg">{VERTICAL_ICONS[vertical?.slug ?? ""] ?? "📦"}</span>
              <h2 className="text-base font-semibold" style={{ color: THEME.textPrimary }}>Pull Data</h2>
            </div>
            <p className="text-xs mt-0.5" style={{ color: THEME.textMuted }}>{vertical?.name ?? verticalId}</p>
          </div>
          <button onClick={onClose} className="w-7 h-7 flex items-center justify-center text-lg leading-none" style={{ color: THEME.textSecondary }}>×</button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {/* Subscription meta */}
          <div className="grid grid-cols-2 gap-3">
            {[
              ["Subscription ID", sub.id.slice(0, 16) + "…"],
              ["Mode", isSandbox ? "simulation" : sub.delivery_mode],
              ["Status", sub.status],
              ["Since", new Date(sub.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })],
            ].map(([label, value]) => (
              <div key={label} className="border-[1.5px] border-[#1B1034] px-3 py-2">
                <p className="text-[10px] uppercase tracking-wide" style={{ color: THEME.textMuted }}>{label}</p>
                <p className="text-xs font-mono mt-0.5 truncate" style={{ color: THEME.textPrimary }}>{value}</p>
              </div>
            ))}
          </div>

          {/* Run section */}
          {!isSandbox ? (
            /* Production: key input + run controls */
            <div className="space-y-4">
              {/* API key input */}
              <div className="border-[1.5px] border-[#1B1034] px-3 py-2.5">
                <p className="text-[10px] uppercase tracking-wide mb-1.5" style={{ color: THEME.textMuted }}>API Key</p>
                <input
                  type="text"
                  value={pastedKey}
                  onChange={(e) => { setPastedKey(e.target.value); setRunError(null); }}
                  placeholder="hb_live_sk_…"
                  className="w-full text-xs font-mono outline-none bg-transparent"
                  style={{ color: THEME.textPrimary }}
                  spellCheck={false}
                />
                {pastedKey && !isValidKey && (
                  <p className="text-[10px] mt-1.5" style={{ color: THEME.danger }}>Invalid key format</p>
                )}
                {!pastedKey && (
                  <button
                    onClick={() => { onClose(); navigate("/dashboard/api-keys"); }}
                    className="text-[10px] mt-1.5 underline"
                    style={{ color: THEME.textMuted }}
                  >
                    No key yet? Create one →
                  </button>
                )}
              </div>

              {/* Status bar */}
              <div className="flex items-center justify-between px-3 py-2 border-[1.5px] border-[#1B1034]">
                <div>
                  <p className="text-[10px] uppercase tracking-wide mb-0.5" style={{ color: THEME.textMuted }}>
                    {isSandbox ? "Batches pulled" : "Cursor position"}
                  </p>
                  <p className="text-xs font-mono" style={{ color: THEME.textPrimary }}>
                    {isSandbox
                      ? `${batchNum} batch${batchNum !== 1 ? "es" : ""}`
                      : result ? result.next_cursor : "auto-tracked"}
                  </p>
                </div>
                {result && (
                  <div className="text-right">
                    <p className="text-[10px] uppercase tracking-wide mb-0.5" style={{ color: THEME.textMuted }}>Last pull</p>
                    <p className="text-xs font-mono" style={{ color: THEME.textPrimary }}>
                      {result.count} items · {result.has_more ? "more available" : "up to date"}
                    </p>
                  </div>
                )}
              </div>

              {/* Run / Reset buttons */}
              <div className="flex gap-2">
                <button
                  onClick={handleRun}
                  disabled={!canRun || running || resetting}
                  className="flex-1 py-2.5 text-sm text-white font-medium disabled:opacity-50"
                  style={{ background: THEME.btnBg }}
                >
                  {running ? "Pulling…" : "▶ Run"}
                </button>
                <button
                  onClick={handleReset}
                  disabled={running || resetting}
                  className="px-4 py-2.5 text-xs border-[1.5px] disabled:opacity-50"
                  style={{ borderColor: THEME.border, color: THEME.textSecondary }}
                >
                  {resetting ? "…" : "Pull from beginning"}
                </button>
              </div>

              {/* Error */}
              {runError && (
                <p className="text-xs px-3 py-2 border-[1.5px]" style={{ borderColor: THEME.danger, color: THEME.danger }}>{runError}</p>
              )}

              {/* Result preview */}
              {result && result.data.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-medium" style={{ color: THEME.textSecondary }}>Result preview</p>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify(result.data, null, 2));
                        setCopiedResult(true);
                        setTimeout(() => setCopiedResult(false), 2000);
                      }}
                      className="text-xs px-2 py-0.5 border-[1.5px]"
                      style={{ borderColor: copiedResult ? THEME.accent : THEME.border, color: copiedResult ? THEME.accent : THEME.textMuted }}
                    >
                      {copiedResult ? "Copied!" : "Copy"}
                    </button>
                  </div>
                  <pre
                    className="text-[10px] font-mono p-3 overflow-x-auto max-h-48 leading-relaxed"
                    style={{ background: THEME.btnBg, color: "#C4B8E0" }}
                  >
                    {JSON.stringify(result.data.slice(0, 3), null, 2)}
                    {result.data.length > 3 && `\n… and ${result.data.length - 3} more`}
                  </pre>
                </div>
              )}

              {result && result.data.length === 0 && (
                <div className="py-6 text-center border-[1.5px] border-dashed text-sm" style={{ borderColor: THEME.textMuted, color: THEME.textMuted }}>
                  No new data — you're up to date. Click "Pull from beginning" to restart.
                </div>
              )}
            </div>
          ) : sandboxKeys.length === 0 ? (
            /* Sandbox — no keys */
            <div className="border-[1.5px] border-dashed border-[#1B1034] px-5 py-6 text-center space-y-3">
              <p className="text-sm font-medium" style={{ color: THEME.textPrimary }}>No sandbox key found</p>
              <p className="text-xs" style={{ color: THEME.textSecondary }}>Create a sandbox key to start pulling simulated data.</p>
              <button
                onClick={() => { onClose(); navigate("/dashboard/api-keys"); }}
                className="px-4 py-2 text-xs text-white font-medium"
                style={{ background: THEME.btnBg }}
              >
                Create Sandbox Key →
              </button>
            </div>
          ) : (
            /* Sandbox — has keys */
            <div className="space-y-4">
              <div className="border-[1.5px] border-[#1B1034] px-3 py-2.5">
                <p className="text-[10px] uppercase tracking-wide mb-2" style={{ color: THEME.textMuted }}>API Key</p>
                <div className="space-y-1.5">
                  {sandboxKeys.map((k) => {
                    const isSelected = selectedKeyId === k.id;
                    return (
                      <label key={k.id} className="flex items-center gap-2 cursor-pointer select-none" onClick={() => setSelectedKeyId(k.id)}>
                        <span
                          className="w-3.5 h-3.5 rounded-full border-[1.5px] flex-shrink-0 flex items-center justify-center"
                          style={{ borderColor: isSelected ? THEME.accent : THEME.border, background: isSelected ? THEME.accent : "transparent" }}
                        >
                          {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white block" />}
                        </span>
                        <span className="text-xs" style={{ color: isSelected ? THEME.textPrimary : THEME.textSecondary }}>{k.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center justify-between px-3 py-2 border-[1.5px] border-[#1B1034]">
                <div>
                  <p className="text-[10px] uppercase tracking-wide mb-0.5" style={{ color: THEME.textMuted }}>Batches pulled</p>
                  <p className="text-xs font-mono" style={{ color: THEME.textPrimary }}>{batchNum} batch{batchNum !== 1 ? "es" : ""}</p>
                </div>
                {result && (
                  <div className="text-right">
                    <p className="text-[10px] uppercase tracking-wide mb-0.5" style={{ color: THEME.textMuted }}>Last pull</p>
                    <p className="text-xs font-mono" style={{ color: THEME.textPrimary }}>{result.count} items · {result.has_more ? "more available" : "up to date"}</p>
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <button onClick={handleRun} disabled={running || resetting} className="flex-1 py-2.5 text-sm text-white font-medium disabled:opacity-50" style={{ background: THEME.btnBg }}>
                  {running ? "Pulling…" : "▶ Run"}
                </button>
                <button onClick={handleReset} disabled={running || resetting} className="px-4 py-2.5 text-xs border-[1.5px] disabled:opacity-50" style={{ borderColor: THEME.border, color: THEME.textSecondary }}>
                  {resetting ? "…" : "Pull from beginning"}
                </button>
              </div>

              {runError && <p className="text-xs px-3 py-2 border-[1.5px]" style={{ borderColor: THEME.danger, color: THEME.danger }}>{runError}</p>}

              {result && result.data.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-medium" style={{ color: THEME.textSecondary }}>Result preview</p>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify(result.data, null, 2));
                        setCopiedResult(true);
                        setTimeout(() => setCopiedResult(false), 2000);
                      }}
                      className="text-xs px-2 py-0.5 border-[1.5px]"
                      style={{ borderColor: copiedResult ? THEME.accent : THEME.border, color: copiedResult ? THEME.accent : THEME.textMuted }}
                    >
                      {copiedResult ? "Copied!" : "Copy"}
                    </button>
                  </div>
                  <pre className="text-[10px] font-mono p-3 overflow-x-auto max-h-48 leading-relaxed" style={{ background: THEME.btnBg, color: "#C4B8E0" }}>
                    {JSON.stringify(result.data.slice(0, 3), null, 2)}
                    {result.data.length > 3 && `\n… and ${result.data.length - 3} more`}
                  </pre>
                </div>
              )}

              {result && result.data.length === 0 && (
                <div className="py-6 text-center border-[1.5px] border-dashed text-sm" style={{ borderColor: THEME.textMuted, color: THEME.textMuted }}>
                  No new data — you're up to date. Click "Pull from beginning" to restart.
                </div>
              )}
            </div>
          )}

          {/* curl snippet — production only */}
          {!isSandbox && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-medium" style={{ color: THEME.textSecondary }}>Production usage</span>
                <button
                  onClick={copySnippet}
                  className="text-xs px-2 py-0.5 border-[1.5px]"
                  style={{ borderColor: copied ? THEME.accent : THEME.border, color: copied ? THEME.accent : THEME.textMuted }}
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
          )}
        </div>

        <style>{`
          @keyframes slideIn {
            from { transform: translateX(100%); }
            to   { transform: translateX(0); }
          }
        `}</style>
      </div>
    </div>
  );
}

// ── Edit Modal ────────────────────────────────────────────────────────────────

function EditModal({
  sub,
  vertical,
  orgId,
  onSave,
  onClose,
}: {
  sub: Subscription;
  vertical: Vertical | undefined;
  orgId: string;
  onSave: (updated: Subscription) => void;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const [mode, setMode] = useState<"pull" | "push">(sub.delivery_mode);
  const [autoAccept, setAutoAccept] = useState(sub.auto_accept);
  const [filtersRaw, setFiltersRaw] = useState(
    sub.filters ? JSON.stringify(sub.filters, null, 2) : "",
  );
  const [filtersError, setFiltersError] = useState("");
  const [saving, setSaving] = useState(false);

  function validateFilters(): Record<string, unknown> | null {
    if (!filtersRaw.trim()) return null;
    try {
      return JSON.parse(filtersRaw) as Record<string, unknown>;
    } catch {
      setFiltersError("Invalid JSON");
      return undefined as unknown as null;
    }
  }

  async function handleSave() {
    const filters = validateFilters();
    if (filters === undefined) return; // parse error
    setFiltersError("");
    setSaving(true);
    try {
      const res = await apiFetch<{ data: Subscription }>(
        `/v1/orgs/${orgId}/subscriptions/${sub.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({ delivery_mode: mode, auto_accept: autoAccept, filters }),
        },
      );
      onSave(res.data);
      toast("Subscription updated");
      onClose();
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to update", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(27,16,52,0.45)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-white border-[1.5px] border-[#1B1034] shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b" style={{ borderColor: "rgba(27,16,52,0.15)" }}>
          <div>
            <div className="flex items-center gap-2">
              <span>{VERTICAL_ICONS[vertical?.slug ?? ""] ?? "📦"}</span>
              <h3 className="text-base font-semibold" style={{ color: THEME.textPrimary }}>Edit Subscription</h3>
            </div>
            <p className="text-xs mt-0.5" style={{ color: THEME.textMuted }}>{vertical?.name}</p>
          </div>
          <button onClick={onClose} className="text-xl leading-none" style={{ color: THEME.textSecondary }}>×</button>
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Delivery Mode */}
          <div>
            <label className="text-xs font-medium uppercase tracking-wide mb-2 block" style={{ color: THEME.textSecondary }}>
              Delivery Mode
            </label>
            <div className="inline-flex border-[1.5px] border-[#1B1034] text-sm overflow-hidden">
              {(["pull", "push"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className="px-4 py-2 transition-colors duration-150"
                  style={{
                    background: mode === m ? THEME.btnBg : "transparent",
                    color: mode === m ? "#fff" : THEME.textSecondary,
                  }}
                >
                  {m === "pull" ? "⬇ Pull" : "⬆ Push"}
                </button>
              ))}
            </div>
            <p className="text-xs mt-1.5" style={{ color: THEME.textMuted }}>
              {mode === "pull"
                ? "You poll the API on demand with GET /v1/data/pull"
                : "Data is pushed to your endpoint as it arrives"}
            </p>
          </div>

          {/* Auto Accept */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium" style={{ color: THEME.textPrimary }}>Auto Accept</p>
              <p className="text-xs mt-0.5" style={{ color: THEME.textMuted }}>Automatically adopt all incoming items</p>
            </div>
            <button
              onClick={() => setAutoAccept(!autoAccept)}
              className="relative w-10 h-5 transition-colors duration-200"
              style={{
                background: autoAccept ? THEME.accent : "rgba(27,16,52,0.2)",
                borderRadius: 9999,
              }}
            >
              <span
                className="absolute top-0.5 w-4 h-4 bg-white transition-transform duration-200"
                style={{
                  borderRadius: "50%",
                  left: autoAccept ? "calc(100% - 18px)" : "2px",
                }}
              />
            </button>
          </div>

          {/* Filters */}
          <div>
            <label className="text-xs font-medium uppercase tracking-wide mb-2 block" style={{ color: THEME.textSecondary }}>
              Filters <span style={{ color: THEME.textMuted, fontWeight: 400 }}>(optional JSON)</span>
            </label>
            <textarea
              value={filtersRaw}
              onChange={(e) => { setFiltersRaw(e.target.value); setFiltersError(""); }}
              placeholder={'{\n  "chain": "ethereum",\n  "category": "scam"\n}'}
              rows={5}
              className="w-full text-xs font-mono p-3 outline-none resize-none border-[1.5px]"
              style={{
                background: THEME.bg,
                borderColor: filtersError ? THEME.danger : THEME.border,
                color: THEME.textPrimary,
              }}
            />
            {filtersError && <p className="text-xs mt-1" style={{ color: THEME.danger }}>{filtersError}</p>}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 pb-5 flex gap-3 justify-end" style={{ borderTop: "1px solid rgba(27,16,52,0.08)", paddingTop: 16 }}>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm border-[1.5px] border-[#1B1034]"
            style={{ color: THEME.textSecondary }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm text-white font-medium disabled:opacity-50"
            style={{ background: THEME.btnBg }}
          >
            {saving ? "Saving…" : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Unsubscribe Confirm Modal ─────────────────────────────────────────────────

function UnsubscribeModal({
  sub,
  vertical,
  onConfirm,
  onCancel,
}: {
  sub: Subscription;
  vertical: Vertical | undefined;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(27,16,52,0.45)" }}
      onClick={onCancel}
    >
      <div
        className="w-full max-w-sm bg-white border-[1.5px] border-[#1B1034] shadow-xl px-6 py-6"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-base font-semibold mb-2" style={{ color: THEME.textPrimary }}>
          Unsubscribe from {vertical?.name ?? "this vertical"}?
        </h3>
        <p className="text-sm mb-6" style={{ color: THEME.textSecondary }}>
          Data will stop flowing to your account. You can re-subscribe at any time from the Subscriptions page.
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm border-[1.5px] border-[#1B1034]"
            style={{ color: THEME.textSecondary }}
          >
            Keep
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm text-white font-medium"
            style={{ background: THEME.danger }}
          >
            Unsubscribe
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Subscriptions Page ────────────────────────────────────────────────────────

export function Subscriptions({ mode = "production" }: { mode?: "production" | "simulation" }) {
  const { orgId } = useAuth();
  const { toast } = useToast();
  const sandbox = useSandboxSubscriptions();
  const sandboxFilters = useSandboxSubFilters();
  const isSandboxNoOrg = mode === "simulation" && !orgId;

  const [subs, setSubs] = useState<Subscription[]>([]);
  const [verticals, setVerticals] = useState<Vertical[]>([]);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState<string | null>(null);

  // Modal / drawer state
  const [pullSub, setPullSub] = useState<Subscription | null>(null);
  const [editSub, setEditSub] = useState<Subscription | null>(null);
  const [unsubSub, setUnsubSub] = useState<Subscription | null>(null);
  const [editFilterVerticalId, setEditFilterVerticalId] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [vRes, sRes] = await Promise.all([
        apiFetch<{ data: Vertical[] }>("/v1/verticals"),
        orgId
          ? apiFetch<{ data: Subscription[] }>(`/v1/orgs/${orgId}/subscriptions`)
          : Promise.resolve({ data: [] as Subscription[] }),
      ]);
      setVerticals(vRes.data);
      setSubs(sRes.data);
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to load subscriptions", "error");
    } finally {
      setLoading(false);
    }
  }, [orgId, toast]);

  useEffect(() => { fetchData(); }, [fetchData]);

  async function handleUnsubscribe() {
    if (isSandboxNoOrg && unsubSub) {
      sandbox.unsubscribe(unsubSub.vertical_id ?? unsubSub.id);
      toast("Unsubscribed successfully");
      setUnsubSub(null);
      return;
    }
    if (!orgId || !unsubSub) return;
    try {
      await apiFetch(`/v1/orgs/${orgId}/subscriptions/${unsubSub.id}/cancel`, { method: "POST" });
      setSubs((p) => p.map((s) => s.id === unsubSub.id ? { ...s, status: "cancelled" as const } : s));
      toast("Unsubscribed successfully");
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to unsubscribe", "error");
    } finally {
      setUnsubSub(null);
    }
  }

  async function handleSubscribe(verticalId: string) {
    if (isSandboxNoOrg) {
      sandbox.subscribe(verticalId);
      toast("Subscribed successfully");
      return;
    }
    if (!orgId) return;
    setSubscribing(verticalId);
    try {
      const res = await apiFetch<{ data: Subscription }>(`/v1/orgs/${orgId}/subscriptions`, {
        method: "POST",
        body: JSON.stringify({ vertical_id: verticalId, delivery_mode: "pull" }),
      });
      setSubs((p) => [...p, res.data]);
      toast("Subscribed successfully");
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to subscribe", "error");
    } finally {
      setSubscribing(null);
    }
  }

  function verticalFor(sub: Subscription): Vertical | undefined {
    return verticals.find((v) => v.id === sub.vertical_id);
  }

  // Merge real subs with sandbox subs (for sandbox-no-org mode)
  const sandboxSubSet = new Set(sandbox.subs);
  const subscribedVerticalIds = isSandboxNoOrg
    ? sandboxSubSet
    : new Set(subs.filter((s) => s.status === "active").map((s) => s.vertical_id));

  // Build activeSubs: real subs or synthetic ones from sandbox localStorage
  const activeSubs = isSandboxNoOrg
    ? verticals
        .filter((v) => sandboxSubSet.has(v.id))
        .map((v): Subscription => ({
          id: v.id,
          vertical_id: v.id,
          frontier_id: null,
          delivery_mode: "pull",
          filters: null,
          auto_accept: false,
          status: "active",
          created_at: new Date().toISOString(),
          verticals: { id: v.id, slug: v.slug, name: v.name },
        }))
    : subs.filter((s) => s.status === "active");

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-2" style={{ color: THEME.textPrimary }}>Subscriptions</h1>
      <p className="text-sm mb-6" style={{ color: THEME.textSecondary }}>
        Subscribe to data verticals to start receiving crowd-sourced annotations.
      </p>

      {/* ── Production mode ─────────────────────────────────── */}
      {mode === "production" && (
        <>
          <div className="mb-8">
            <DomainBrowse />
          </div>
        </>
      )}

      {/* ── Simulation mode ─────────────────────────────────── */}
      {mode === "simulation" && (
        <>
          {/* Active simulated subscriptions */}
          {activeSubs.length > 0 && (
            <div className="mb-8">
              <h2 className="text-sm font-semibold mb-3" style={{ color: THEME.textPrimary }}>Active</h2>
              {activeSubs.map((sub) => {
                const v = verticalFor(sub);
                const icon = VERTICAL_ICONS[v?.slug ?? ""] ?? "📦";
                return (
                  <div
                    key={sub.id}
                    className="bg-white border-[1.5px] border-[#1B1034] p-5 mb-3 flex items-start justify-between"
                    style={{ borderLeft: `3px solid ${THEME.accent}` }}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-base">{icon}</span>
                        <h3 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>
                          {v?.name ?? sub.vertical_id}
                        </h3>
                      </div>
                      <p className="text-xs mb-2" style={{ color: THEME.textMuted }}>
                        {sub.delivery_mode} · {sub.auto_accept ? "auto-accept on" : "manual review"} · Since{" "}
                        {new Date(sub.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                      </p>
                      <p className="text-xs mb-3" style={{ color: THEME.textMuted }}>
                        Grades:{" "}
                        {(() => {
                          const vId = sub.vertical_id ?? sub.id;
                          const grades = sandboxFilters.filters[vId]?.quality_grades;
                          return grades?.length
                            ? grades.map((g) => (
                                <span key={g} className="inline-block px-1.5 py-0.5 text-[10px] font-semibold mr-1" style={{ background: "#F0EBFF", color: THEME.accent }}>{g}</span>
                              ))
                            : <span style={{ color: THEME.textMuted }}>all</span>;
                        })()}
                      </p>
                      <div className="flex items-center gap-2 flex-wrap">
                        <button onClick={() => setPullSub(sub)} className="px-3 py-1.5 text-xs text-white font-medium" style={{ background: THEME.btnBg }}>⬇ Pull Data</button>
                        <button onClick={() => setEditFilterVerticalId(sub.vertical_id ?? sub.id)} className="px-3 py-1.5 text-xs border-[1.5px]" style={{ borderColor: THEME.border, color: THEME.textSecondary }}>Edit Filters</button>
                        <button onClick={() => setUnsubSub(sub)} className="px-3 py-1.5 text-xs border-[1.5px]" style={{ borderColor: THEME.danger, color: THEME.danger }}>Unsubscribe</button>
                      </div>
                    </div>
                    <span className="text-xs font-medium ml-4 flex-shrink-0" style={{ color: THEME.accent }}>active</span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Available simulated verticals */}
          <h2 className="text-sm font-semibold mb-3" style={{ color: THEME.textPrimary }}>Simulated Data Verticals</h2>
      {loading ? (
        <div className="text-sm text-center py-8" style={{ color: THEME.textMuted }}>Loading…</div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {verticals.map((v) => {
            const isSubscribed = subscribedVerticalIds.has(v.id);
            const icon = VERTICAL_ICONS[v.slug] ?? "📦";
            return (
              <div
                key={v.id}
                className="bg-white border-[1.5px] border-[#1B1034] p-5 flex flex-col justify-between"
                style={{ minHeight: 170 }}
              >
                <div>
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-2xl">{icon}</span>
                    {isSubscribed && (
                      <span
                        className="text-xs font-medium px-2 py-0.5"
                        style={{ background: THEME.accentLight, color: THEME.accent }}
                      >
                        Subscribed
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-semibold mb-1" style={{ color: THEME.textPrimary }}>{v.name}</h3>
                  <p className="text-xs leading-relaxed" style={{ color: THEME.textSecondary }}>{v.description}</p>
                  {v.topic_count !== undefined && v.topic_count > 0 && (
                    <p className="text-xs mt-1" style={{ color: THEME.textMuted }}>{v.topic_count} topic{v.topic_count !== 1 ? "s" : ""}</p>
                  )}
                </div>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-xs" style={{ color: THEME.textMuted }}>from ${v.base_price_usd.toFixed(3)}/item</span>
                  {!isSubscribed && (
                    <button
                      onClick={() => handleSubscribe(v.id)}
                      disabled={subscribing === v.id}
                      className="px-4 py-1.5 text-xs text-white font-medium disabled:opacity-50"
                      style={{ background: THEME.btnBg }}
                    >
                      {subscribing === v.id ? "…" : "Subscribe"}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
        </>
      )}

      {/* Pull Data drawer */}
      {pullSub && (
        <PullDataDrawer
          sub={pullSub}
          vertical={verticalFor(pullSub)}
          mode={mode}
          orgId={orgId}
          onClose={() => setPullSub(null)}
        />
      )}

      {/* Edit modal */}
      {editSub && orgId && (
        <EditModal
          sub={editSub}
          vertical={verticalFor(editSub)}
          orgId={orgId}
          onSave={(updated) => setSubs((p) => p.map((s) => s.id === updated.id ? { ...s, ...updated } : s))}
          onClose={() => setEditSub(null)}
        />
      )}

      {/* Unsubscribe confirmation */}
      {unsubSub && (
        <UnsubscribeModal
          sub={unsubSub}
          vertical={verticalFor(unsubSub)}
          onConfirm={handleUnsubscribe}
          onCancel={() => setUnsubSub(null)}
        />
      )}

      {/* Sandbox edit filters modal */}
      {editFilterVerticalId && (
        <SandboxEditFiltersModal
          verticalId={editFilterVerticalId}
          verticalName={verticalFor({ vertical_id: editFilterVerticalId } as Subscription)?.name ?? editFilterVerticalId}
          currentGrades={sandboxFilters.filters[editFilterVerticalId]?.quality_grades ?? null}
          onSave={(grades) => {
            sandboxFilters.updateFilters(editFilterVerticalId, grades);
            setEditFilterVerticalId(null);
          }}
          onCancel={() => setEditFilterVerticalId(null)}
        />
      )}
    </div>
  );
}
