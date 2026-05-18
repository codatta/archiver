import React, { useEffect, useRef, useState } from "react";
import { THEME } from "../../lib/config";

// ── Types ────────────────────────────────────────────────────────────────────

type Phase = "confirm" | "connecting" | "done";

interface Step {
  label: string;
  detail: string;
  durationMs: number;
}

const STEPS: Step[] = [
  { label: "Flushing simulator queue",    detail: "Clearing mock data stream",         durationMs: 600 },
  { label: "Verifying API credentials",   detail: "Checking live key authorization",   durationMs: 750 },
  { label: "Subscribing to Realtime",     detail: "Opening Supabase delivery channel", durationMs: 800 },
  { label: "Activating live feed",        detail: "Production data stream is live",    durationMs: 500 },
];

type StepStatus = "waiting" | "running" | "done";

// ── Sub-components ───────────────────────────────────────────────────────────

function Spinner() {
  return (
    <svg
      className="animate-spin"
      width="16" height="16" viewBox="0 0 16 16" fill="none"
    >
      <circle cx="8" cy="8" r="6" stroke={THEME.textMuted} strokeWidth="2" />
      <path d="M8 2 A6 6 0 0 1 14 8" stroke={THEME.accent} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function CheckIcon({ color }: { color: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="7" fill={color} fillOpacity="0.15" />
      <path d="M4.5 8.5 L7 11 L11.5 5.5" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function WaitIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6" stroke={THEME.textMuted} strokeWidth="1.5" strokeDasharray="3 3" />
    </svg>
  );
}

// Animated "plug connecting" illustration
function PlugAnimation({ phase }: { phase: Phase }) {
  const connected = phase === "done";
  const animating = phase === "connecting";

  return (
    <div className="flex items-center justify-center gap-3 py-4">
      {/* Left block: Simulator */}
      <div
        className="flex flex-col items-center gap-1"
        style={{ opacity: connected ? 0.35 : 1, transition: "opacity 0.6s ease" }}
      >
        <div
          className="w-10 h-10 flex items-center justify-center text-lg font-mono"
          style={{
            border: `1.5px solid ${THEME.textMuted}`,
            background: THEME.bg,
            color: THEME.textMuted,
          }}
        >
          ⚡
        </div>
        <span className="text-[10px]" style={{ color: THEME.textMuted }}>SIM</span>
      </div>

      {/* Cable animation */}
      <div className="relative flex items-center" style={{ width: 80, height: 20 }}>
        {/* Base cable line */}
        <div
          className="absolute inset-y-1/2 left-0 h-[1.5px]"
          style={{
            background: THEME.textMuted,
            width: "100%",
            transform: "translateY(-50%)",
          }}
        />
        {/* Animated fill — grows left to right */}
        <div
          className="absolute inset-y-1/2 left-0 h-[2px]"
          style={{
            background: connected ? "#22C55E" : THEME.accent,
            width: connected ? "100%" : animating ? "60%" : "0%",
            transform: "translateY(-50%)",
            transition: animating
              ? "width 2s cubic-bezier(0.4,0,0.2,1)"
              : connected
              ? "width 0.4s ease, background 0.4s ease"
              : "none",
          }}
        />
        {/* Travelling dot */}
        {animating && !connected && (
          <div
            style={{
              position: "absolute",
              top: "50%",
              transform: "translateY(-50%)",
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: THEME.accent,
              animation: "travelDot 1.4s ease-in-out infinite",
            }}
          />
        )}
        {/* Plug connector dots */}
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            transform: "translate(-50%, -50%)",
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: connected ? "#22C55E" : animating ? THEME.accent : THEME.textMuted,
            transition: "background 0.4s ease",
            boxShadow: connected ? "0 0 6px 2px rgba(34,197,94,0.4)" : animating ? `0 0 6px 2px ${THEME.accent}44` : "none",
          }}
        />
      </div>

      {/* Right block: Production */}
      <div
        className="flex flex-col items-center gap-1"
        style={{
          opacity: connected ? 1 : animating ? 0.7 : 0.4,
          transition: "opacity 0.6s ease",
        }}
      >
        <div
          className="w-10 h-10 flex items-center justify-center text-lg"
          style={{
            border: `1.5px solid ${connected ? "#22C55E" : THEME.textMuted}`,
            background: connected ? "rgba(34,197,94,0.08)" : THEME.bg,
            transition: "border-color 0.4s, background 0.4s",
            color: connected ? "#22C55E" : THEME.textMuted,
          }}
        >
          {connected ? "🟢" : "🔴"}
        </div>
        <span
          className="text-[10px]"
          style={{ color: connected ? "#22C55E" : THEME.textMuted, transition: "color 0.4s" }}
        >
          LIVE
        </span>
      </div>

      <style>{`
        @keyframes travelDot {
          0%   { left: 0%; }
          100% { left: 100%; }
        }
      `}</style>
    </div>
  );
}

// ── Main Modal ───────────────────────────────────────────────────────────────

type ApiKeyOption = { id: string; name: string; key_prefix: string };

interface Props {
  open: boolean;
  apiKeys?: ApiKeyOption[];
  onConfirm: () => void;
  onCancel: () => void;
}

export function DataSourceModal({ open, apiKeys = [], onConfirm, onCancel }: Props) {
  const [phase, setPhase] = useState<Phase>("confirm");
  const [stepStatuses, setStepStatuses] = useState<StepStatus[]>(STEPS.map(() => "waiting"));
  const [currentStep, setCurrentStep] = useState(-1);
  const [selectedKeyId, setSelectedKeyId] = useState<string>("");

  // Stable ref for callbacks so the animation effect doesn't re-run on parent re-renders
  const onConfirmRef = useRef(onConfirm);
  onConfirmRef.current = onConfirm;

  // Reset when reopened
  useEffect(() => {
    if (open) {
      setPhase("confirm");
      setStepStatuses(STEPS.map(() => "waiting"));
      setCurrentStep(-1);
      // Auto-select first key if only one available
      setSelectedKeyId(apiKeys.length === 1 ? apiKeys[0].id : "");
    }
  }, [open, apiKeys]);

  // Run steps sequentially once connecting begins
  useEffect(() => {
    if (phase !== "connecting") return;

    let cancelled = false;
    let stepIndex = 0;

    function runStep() {
      if (cancelled || stepIndex >= STEPS.length) return;

      setCurrentStep(stepIndex);
      setStepStatuses((prev) => {
        const next = [...prev];
        next[stepIndex] = "running";
        return next;
      });

      setTimeout(() => {
        if (cancelled) return;
        setStepStatuses((prev) => {
          const next = [...prev];
          next[stepIndex] = "done";
          return next;
        });
        stepIndex++;

        if (stepIndex < STEPS.length) {
          setTimeout(runStep, 120);
        } else {
          // All steps done
          setTimeout(() => {
            if (!cancelled) {
              setPhase("done");
              setTimeout(() => {
                if (!cancelled) onConfirmRef.current();
              }, 900);
            }
          }, 300);
        }
      }, STEPS[stepIndex]?.durationMs ?? 600);
    }

    setTimeout(runStep, 200);
    return () => { cancelled = true; };
  }, [phase]);

  if (!open) return null;

  const progressPct = phase === "done"
    ? 100
    : phase === "connecting"
    ? Math.round((stepStatuses.filter((s) => s === "done").length / STEPS.length) * 100)
    : 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(27, 16, 52, 0.5)" }}
      onClick={phase === "confirm" ? onCancel : undefined}
    >
      <div
        className="w-full max-w-sm bg-white border-[1.5px] border-[#1B1034] shadow-xl"
        style={{ borderRadius: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="px-6 pt-5 pb-3 border-b border-[#1B1034] border-opacity-20"
          style={{ borderBottom: "1px solid rgba(27,16,52,0.12)" }}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-mono px-1.5 py-0.5 rounded-sm"
              style={{ background: phase === "done" ? "rgba(34,197,94,0.15)" : "rgba(131,77,251,0.12)", color: phase === "done" ? "#16a34a" : THEME.accent }}
            >
              {phase === "confirm" ? "DATA SOURCE" : phase === "connecting" ? "CONNECTING..." : "CONNECTED"}
            </span>
            {phase === "confirm" && (
              <button
                onClick={onCancel}
                className="w-6 h-6 flex items-center justify-center hover:opacity-60 transition-opacity"
                style={{ color: THEME.textMuted }}
                aria-label="Close"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M1 1L13 13M13 1L1 13" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                </svg>
              </button>
            )}
          </div>
          <h3 className="text-base font-semibold" style={{ color: THEME.textPrimary }}>
            {phase === "confirm"
              ? "Switch to Production?"
              : phase === "connecting"
              ? "Plugging in live data..."
              : "Production feed active"}
          </h3>
          {phase !== "confirm" && selectedKeyId && (() => {
            const k = apiKeys.find((k) => k.id === selectedKeyId);
            return k ? (
              <p className="text-xs mt-0.5" style={{ color: THEME.textMuted }}>
                Using key: <span className="font-mono">{k.key_prefix}••••••••</span>
              </p>
            ) : null;
          })()}
        </div>

        {/* Body */}
        <div className="px-6 py-4">
          {/* Plug illustration */}
          <PlugAnimation phase={phase} />

          {/* Confirm copy */}
          {phase === "confirm" && (
            <div className="space-y-4">
              <div className="text-sm space-y-2" style={{ color: THEME.textSecondary }}>
                <p>You are about to switch from the <strong style={{ color: THEME.textPrimary }}>simulator</strong> to the <strong style={{ color: THEME.accent }}>live production stream</strong>.</p>
                <ul className="space-y-1 pl-3 text-xs" style={{ color: THEME.textMuted }}>
                  <li>— Mock data will be cleared from the view</li>
                  <li>— Adopting items will charge your balance</li>
                  <li>— Data comes directly from the pipeline</li>
                </ul>
              </div>

              {/* API key selector */}
              <div>
                <label className="text-xs font-medium block mb-1.5" style={{ color: THEME.textSecondary }}>
                  API Key to use
                </label>
                {apiKeys.length === 0 ? (
                  <div
                    className="px-3 py-2.5 text-xs border-[1.5px] border-dashed"
                    style={{ borderColor: THEME.danger, color: THEME.danger, background: "rgba(239,68,68,0.05)" }}
                  >
                    No active API keys — create one in the <strong>API Keys</strong> tab first.
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    {apiKeys.map((k) => {
                      const sel = selectedKeyId === k.id;
                      return (
                        <label
                          key={k.id}
                          className="flex items-center gap-3 px-3 py-2.5 cursor-pointer border-[1.5px]"
                          style={{
                            borderColor: sel ? THEME.accent : THEME.border,
                            background: sel ? THEME.accentLight : "white",
                          }}
                          onClick={() => setSelectedKeyId(k.id)}
                        >
                          <div
                            className="w-3.5 h-3.5 rounded-full border-[1.5px] flex-shrink-0 flex items-center justify-center"
                            style={{ borderColor: sel ? THEME.accent : THEME.textMuted }}
                          >
                            {sel && <div className="w-1.5 h-1.5 rounded-full" style={{ background: THEME.accent }} />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <span className="text-xs font-medium block" style={{ color: THEME.textPrimary }}>{k.name}</span>
                            <span className="text-[10px] font-mono" style={{ color: THEME.textMuted }}>{k.key_prefix}••••••••</span>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Steps list */}
          {(phase === "connecting" || phase === "done") && (
            <div className="space-y-2.5">
              {/* Progress bar */}
              <div className="w-full h-[2px] rounded-full mb-3" style={{ background: "rgba(27,16,52,0.1)" }}>
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${progressPct}%`,
                    background: phase === "done" ? "#22C55E" : THEME.accent,
                    transition: "width 0.4s ease, background 0.4s ease",
                  }}
                />
              </div>

              {STEPS.map((step, i) => {
                const status = stepStatuses[i];
                return (
                  <div
                    key={i}
                    className="flex items-start gap-2.5"
                    style={{
                      opacity: status === "waiting" ? 0.35 : 1,
                      transition: "opacity 0.3s ease",
                    }}
                  >
                    <div className="mt-0.5 flex-shrink-0">
                      {status === "running" && <Spinner />}
                      {status === "done"    && <CheckIcon color={i === STEPS.length - 1 && phase === "done" ? "#22C55E" : THEME.accent} />}
                      {status === "waiting" && <WaitIcon />}
                    </div>
                    <div>
                      <div className="text-xs font-medium" style={{ color: THEME.textPrimary }}>{step.label}</div>
                      <div className="text-[11px]" style={{ color: THEME.textMuted }}>{step.detail}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        {phase === "confirm" && (
          <div
            className="px-6 pb-5 flex gap-3 justify-end"
            style={{ borderTop: "1px solid rgba(27,16,52,0.08)", paddingTop: 16 }}
          >
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm border-[1.5px] border-[#1B1034]"
              style={{ color: THEME.textSecondary }}
            >
              Keep Simulator
            </button>
            <button
              onClick={() => setPhase("connecting")}
              disabled={apiKeys.length > 0 && !selectedKeyId}
              className="px-4 py-2 text-sm text-white font-medium disabled:opacity-40"
              style={{ background: THEME.accent }}
            >
              Connect to Production
            </button>
          </div>
        )}

        {phase === "connecting" && (
          <div
            className="px-6 pb-5 flex justify-end"
            style={{ borderTop: "1px solid rgba(27,16,52,0.08)", paddingTop: 16 }}
          >
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm border-[1.5px] border-[#1B1034]"
              style={{ color: THEME.textSecondary }}
            >
              Cancel
            </button>
          </div>
        )}

        {phase === "done" && (
          <div
            className="px-6 pb-5 flex items-center justify-between gap-2"
            style={{ borderTop: "1px solid rgba(27,16,52,0.08)", paddingTop: 14 }}
          >
            <div className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ background: "#22C55E", animation: "pulse 1.5s ease-in-out infinite", boxShadow: "0 0 0 0 rgba(34,197,94,0.4)" }}
              />
              <span className="text-xs" style={{ color: "#16a34a" }}>
                Live stream connected — switching dashboard...
              </span>
            </div>
            <button
              onClick={onConfirm}
              className="w-6 h-6 flex items-center justify-center flex-shrink-0 hover:opacity-60 transition-opacity"
              style={{ color: THEME.textMuted }}
              aria-label="Close"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M1 1L11 11M11 1L1 11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
              </svg>
            </button>
            <style>{`
              @keyframes pulse {
                0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
                50%       { box-shadow: 0 0 0 5px rgba(34,197,94,0); }
              }
            `}</style>
          </div>
        )}
      </div>
    </div>
  );
}

// ── DisconnectModal ───────────────────────────────────────────────────────────

type DisconnectPhase = "confirm" | "disconnecting" | "done";

const DISCONNECT_STEPS: Step[] = [
  { label: "Closing Realtime channel",  detail: "Unsubscribing from Supabase delivery channel", durationMs: 500 },
  { label: "Flushing live stream",      detail: "Clearing production data from view",            durationMs: 400 },
  { label: "Restoring simulator",       detail: "Switching back to mock data stream",            durationMs: 450 },
];

function PlugDisconnectAnimation({ phase }: { phase: DisconnectPhase }) {
  const disconnecting = phase === "disconnecting";
  const done = phase === "done";

  return (
    <div className="flex items-center justify-center gap-3 py-4">
      {/* Left: Simulator */}
      <div
        className="flex flex-col items-center gap-1"
        style={{ opacity: done ? 1 : disconnecting ? 0.7 : 0.4, transition: "opacity 0.6s ease" }}
      >
        <div
          className="w-10 h-10 flex items-center justify-center text-lg font-mono"
          style={{
            border: `1.5px solid ${done ? THEME.accent : THEME.textMuted}`,
            background: done ? THEME.accentLight : THEME.bg,
            color: done ? THEME.accent : THEME.textMuted,
            transition: "border-color 0.4s, background 0.4s",
          }}
        >
          ⚡
        </div>
        <span className="text-[10px]" style={{ color: done ? THEME.accent : THEME.textMuted, transition: "color 0.4s" }}>SIM</span>
      </div>

      {/* Cable — drains right to left */}
      <div className="relative flex items-center" style={{ width: 80, height: 20 }}>
        <div
          className="absolute inset-y-1/2 left-0 h-[1.5px] w-full"
          style={{ background: THEME.textMuted, transform: "translateY(-50%)" }}
        />
        <div
          className="absolute inset-y-1/2 left-0 h-[2px]"
          style={{
            background: THEME.danger,
            width: done ? "0%" : disconnecting ? "40%" : "100%",
            transform: "translateY(-50%)",
            transition: disconnecting
              ? "width 1.8s cubic-bezier(0.4,0,0.2,1)"
              : done
              ? "width 0.4s ease"
              : "none",
          }}
        />
        {/* Centre dot — dims as connection closes */}
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            transform: "translate(-50%, -50%)",
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: done ? THEME.textMuted : disconnecting ? THEME.danger : "#22C55E",
            transition: "background 0.6s ease",
            boxShadow: done ? "none" : disconnecting ? `0 0 6px 2px ${THEME.danger}44` : "0 0 6px 2px rgba(34,197,94,0.4)",
          }}
        />
      </div>

      {/* Right: Production — dims */}
      <div
        className="flex flex-col items-center gap-1"
        style={{ opacity: done ? 0.25 : 1, transition: "opacity 0.6s ease" }}
      >
        <div
          className="w-10 h-10 flex items-center justify-center text-lg"
          style={{
            border: `1.5px solid ${done ? THEME.textMuted : "#22C55E"}`,
            background: done ? THEME.bg : "rgba(34,197,94,0.08)",
            transition: "border-color 0.5s, background 0.5s",
          }}
        >
          {done ? "⬛" : "🟢"}
        </div>
        <span className="text-[10px]" style={{ color: done ? THEME.textMuted : "#22C55E", transition: "color 0.5s" }}>LIVE</span>
      </div>
    </div>
  );
}

interface DisconnectProps {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DisconnectModal({ open, onConfirm, onCancel }: DisconnectProps) {
  const [phase, setPhase] = useState<DisconnectPhase>("confirm");
  const [stepStatuses, setStepStatuses] = useState<StepStatus[]>(DISCONNECT_STEPS.map(() => "waiting"));

  const onConfirmRef = useRef(onConfirm);
  onConfirmRef.current = onConfirm;

  useEffect(() => {
    if (open) {
      setPhase("confirm");
      setStepStatuses(DISCONNECT_STEPS.map(() => "waiting"));
    }
  }, [open]);

  useEffect(() => {
    if (phase !== "disconnecting") return;
    let cancelled = false;
    let stepIndex = 0;

    function runStep() {
      if (cancelled || stepIndex >= DISCONNECT_STEPS.length) return;
      setStepStatuses((prev) => { const n = [...prev]; n[stepIndex] = "running"; return n; });
      setTimeout(() => {
        if (cancelled) return;
        setStepStatuses((prev) => { const n = [...prev]; n[stepIndex] = "done"; return n; });
        stepIndex++;
        if (stepIndex < DISCONNECT_STEPS.length) {
          setTimeout(runStep, 100);
        } else {
          setTimeout(() => {
            if (!cancelled) {
              setPhase("done");
              setTimeout(() => { if (!cancelled) onConfirmRef.current(); }, 700);
            }
          }, 200);
        }
      }, DISCONNECT_STEPS[stepIndex]?.durationMs ?? 400);
    }

    setTimeout(runStep, 150);
    return () => { cancelled = true; };
  }, [phase]);

  if (!open) return null;

  const progressPct = phase === "done"
    ? 100
    : phase === "disconnecting"
    ? Math.round((stepStatuses.filter((s) => s === "done").length / DISCONNECT_STEPS.length) * 100)
    : 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(27,16,52,0.5)" }}
      onClick={phase === "confirm" ? onCancel : undefined}
    >
      <div
        className="w-full max-w-sm bg-white border-[1.5px] border-[#1B1034] shadow-xl"
        style={{ borderRadius: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 pt-5 pb-3" style={{ borderBottom: "1px solid rgba(27,16,52,0.12)" }}>
          <div className="flex items-center justify-between mb-1">
            <span
              className="text-xs font-mono px-1.5 py-0.5 rounded-sm"
              style={{
                background: phase === "done" ? "rgba(239,68,68,0.1)" : "rgba(27,16,52,0.08)",
                color: phase === "done" ? THEME.danger : THEME.textSecondary,
              }}
            >
              {phase === "confirm" ? "LIVE CONNECTION" : phase === "disconnecting" ? "DISCONNECTING..." : "DISCONNECTED"}
            </span>
            {phase === "confirm" && (
              <button
                onClick={onCancel}
                className="w-6 h-6 flex items-center justify-center hover:opacity-60 transition-opacity"
                style={{ color: THEME.textMuted }}
                aria-label="Close"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M1 1L13 13M13 1L1 13" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
                </svg>
              </button>
            )}
          </div>
          <h3 className="text-base font-semibold" style={{ color: THEME.textPrimary }}>
            {phase === "confirm" ? "Close production connection?" : phase === "disconnecting" ? "Closing connection..." : "Switched to simulator"}
          </h3>
        </div>

        {/* Body */}
        <div className="px-6 py-4">
          <PlugDisconnectAnimation phase={phase} />

          {phase === "confirm" && (
            <div className="text-sm space-y-2" style={{ color: THEME.textSecondary }}>
              <p>You are about to disconnect from the <strong style={{ color: "#22C55E" }}>live production stream</strong> and switch back to the <strong style={{ color: THEME.textPrimary }}>simulator</strong>.</p>
              <ul className="space-y-1 pl-3 text-xs" style={{ color: THEME.textMuted }}>
                <li>— The Realtime channel will be closed</li>
                <li>— Live data in the view will be cleared</li>
                <li>— Simulator resumes with mock data</li>
              </ul>
            </div>
          )}

          {(phase === "disconnecting" || phase === "done") && (
            <div className="space-y-2.5">
              <div className="w-full h-[2px] rounded-full mb-3" style={{ background: "rgba(27,16,52,0.1)" }}>
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${progressPct}%`,
                    background: phase === "done" ? THEME.textMuted : THEME.danger,
                    transition: "width 0.4s ease, background 0.4s ease",
                  }}
                />
              </div>
              {DISCONNECT_STEPS.map((step, i) => {
                const status = stepStatuses[i];
                return (
                  <div
                    key={i}
                    className="flex items-start gap-2.5"
                    style={{ opacity: status === "waiting" ? 0.35 : 1, transition: "opacity 0.3s ease" }}
                  >
                    <div className="mt-0.5 flex-shrink-0">
                      {status === "running" && <Spinner />}
                      {status === "done"    && <CheckIcon color={THEME.textSecondary} />}
                      {status === "waiting" && <WaitIcon />}
                    </div>
                    <div>
                      <div className="text-xs font-medium" style={{ color: THEME.textPrimary }}>{step.label}</div>
                      <div className="text-[11px]" style={{ color: THEME.textMuted }}>{step.detail}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        {phase === "confirm" && (
          <div
            className="px-6 pb-5 flex gap-3 justify-end"
            style={{ borderTop: "1px solid rgba(27,16,52,0.08)", paddingTop: 16 }}
          >
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm border-[1.5px] border-[#1B1034]"
              style={{ color: THEME.textSecondary }}
            >
              Stay on Production
            </button>
            <button
              onClick={() => setPhase("disconnecting")}
              className="px-4 py-2 text-sm text-white font-medium"
              style={{ background: THEME.danger }}
            >
              Disconnect
            </button>
          </div>
        )}

        {phase === "done" && (
          <div
            className="px-6 pb-5 flex items-center gap-2"
            style={{ borderTop: "1px solid rgba(27,16,52,0.08)", paddingTop: 14 }}
          >
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: THEME.textMuted }} />
            <span className="text-xs" style={{ color: THEME.textSecondary }}>
              Connection closed — restoring simulator...
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
