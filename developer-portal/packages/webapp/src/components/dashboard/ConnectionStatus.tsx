import React, { useState } from "react";
import { useConnectionHealth, type HealthStatus } from "../../lib/connectionHealth";
import { THEME } from "../../lib/config";

// ── Helpers ───────────────────────────────────────────────────────────────────

function statusColor(s: HealthStatus): string {
  if (s === "connected") return "#22C55E";
  if (s === "checking")  return "#F59E0B";
  if (s === "error")     return THEME.danger;
  return THEME.textMuted;
}

function statusLabel(s: HealthStatus): string {
  if (s === "connected") return "Connected";
  if (s === "checking")  return "Checking…";
  if (s === "error")     return "Error";
  return "Inactive";
}

function Dot({ status, pulse }: { status: HealthStatus; pulse?: boolean }) {
  const color = statusColor(status);
  return (
    <span
      className="inline-block w-2 h-2 rounded-full flex-shrink-0"
      style={{
        background: color,
        animation: pulse && status === "connected" ? "connPulse 2s ease-in-out infinite" : undefined,
        boxShadow: status === "connected" ? `0 0 0 0 ${color}66` : undefined,
      }}
    />
  );
}

// ── ConnectionStatus ──────────────────────────────────────────────────────────

export function ConnectionStatus() {
  const { api, db, realtime, aggregate, refresh } = useConnectionHealth();
  const [expanded, setExpanded] = useState(false);

  const connections = [
    { key: "api",      label: "REST API",  info: api },
    { key: "db",       label: "Database",  info: db },
    { key: "realtime", label: "Realtime",  info: realtime, pulse: true },
  ];

  return (
    <div className="select-none">
      <style>{`
        @keyframes connPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
          60%       { box-shadow: 0 0 0 4px rgba(34,197,94,0); }
        }
      `}</style>

      {/* Collapsed pill */}
      <button
        onClick={() => setExpanded((p) => !p)}
        className="flex items-center gap-2 px-3 py-1.5 text-xs transition-opacity hover:opacity-80"
        style={{ color: THEME.textMuted }}
      >
        <span
          className="inline-block w-2 h-2 rounded-full flex-shrink-0"
          style={{
            background: statusColor(aggregate),
            animation: aggregate === "connected" ? "connPulse 2s ease-in-out infinite" : undefined,
          }}
        />
        <span>{aggregate === "error" ? "Connection issue" : aggregate === "connected" ? "All connections healthy" : "Checking connections…"}</span>
        <svg
          width="10" height="10" viewBox="0 0 10 10" fill="none"
          style={{ transform: expanded ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}
        >
          <path d="M1 3L5 7L9 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>

      {/* Expanded panel */}
      {expanded && (
        <div
          className="mt-1 mb-3 mx-0 border-[1.5px] border-[#1B1034] bg-white overflow-hidden"
          style={{ borderRadius: 0 }}
        >
          <div className="px-4 py-2.5" style={{ borderBottom: "1px solid rgba(27,16,52,0.1)" }}>
            <span className="text-xs font-medium" style={{ color: THEME.textSecondary }}>Active Connections</span>
          </div>
          <div className="divide-y" style={{ borderColor: "rgba(27,16,52,0.08)" }}>
            {connections.map(({ key, label, info, pulse }) => (
              <div key={key} className="flex items-center justify-between px-4 py-2.5">
                <div className="flex items-center gap-2.5">
                  <Dot status={info.status} pulse={pulse} />
                  <div>
                    <span className="text-xs font-medium block" style={{ color: THEME.textPrimary }}>{label}</span>
                    {info.detail && (
                      <span className="text-[10px]" style={{ color: THEME.textMuted }}>{info.detail}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3 text-right">
                  {info.latencyMs !== undefined && (
                    <span className="text-[10px] font-mono" style={{ color: THEME.textMuted }}>{info.latencyMs}ms</span>
                  )}
                  <span
                    className="text-[10px] font-medium"
                    style={{ color: statusColor(info.status) }}
                  >
                    {statusLabel(info.status)}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <div
            className="px-4 py-2 flex items-center justify-between"
            style={{ borderTop: "1px solid rgba(27,16,52,0.08)" }}
          >
            <span className="text-[10px]" style={{ color: THEME.textMuted }}>
              Polling every 30s · Realtime every 3s
            </span>
            <button
              onClick={refresh}
              className="text-[10px] font-medium hover:underline"
              style={{ color: THEME.accent }}
            >
              Refresh now
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
