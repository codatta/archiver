import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { supabase } from "./supabase";
import { ENV } from "./env";

export type HealthStatus = "checking" | "connected" | "error" | "inactive";

export interface ConnectionInfo {
  status: HealthStatus;
  latencyMs?: number;
  detail?: string;
  checkedAt?: Date;
}

export interface ConnectionHealth {
  api: ConnectionInfo;
  db: ConnectionInfo;
  realtime: ConnectionInfo;
  aggregate: HealthStatus;
  refresh: () => void;
}

const POLL_MS = 30_000;

const defaultInfo: ConnectionInfo = { status: "checking" };

const ConnectionHealthContext = createContext<ConnectionHealth>({
  api: defaultInfo,
  db: defaultInfo,
  realtime: { status: "inactive" },
  aggregate: "checking",
  refresh: () => {},
});

export function useConnectionHealth(): ConnectionHealth {
  return useContext(ConnectionHealthContext);
}

export function ConnectionHealthProvider({ children }: { children: React.ReactNode }) {
  const [api, setApi] = useState<ConnectionInfo>(defaultInfo);
  const [db, setDb] = useState<ConnectionInfo>(defaultInfo);
  const [realtime, setRealtime] = useState<ConnectionInfo>({ status: "inactive" });

  const checkApi = useCallback(async () => {
    setApi((p) => ({ ...p, status: "checking" }));
    const t0 = Date.now();
    try {
      const res = await fetch(`${ENV.API_URL}/healthz`, { method: "GET", signal: AbortSignal.timeout(5000) });
      const latencyMs = Date.now() - t0;
      if (res.ok) {
        setApi({ status: "connected", latencyMs, checkedAt: new Date() });
      } else {
        setApi({ status: "error", detail: `HTTP ${res.status}`, checkedAt: new Date() });
      }
    } catch (e) {
      setApi({ status: "error", detail: (e as Error).message?.slice(0, 60), checkedAt: new Date() });
    }
  }, []);

  const checkDb = useCallback(async () => {
    setDb((p) => ({ ...p, status: "checking" }));
    const t0 = Date.now();
    try {
      // Use the REST health endpoint via Supabase URL rather than querying
      // a table — avoids RLS issues and doesn't need a populated table.
      const res = await fetch(`${ENV.SUPABASE_URL}/rest/v1/`, {
        method: "HEAD",
        headers: { apikey: ENV.SUPABASE_PUBLISHABLE_KEY },
        signal: AbortSignal.timeout(5000),
      });
      const latencyMs = Date.now() - t0;
      if (res.ok || res.status === 404) {
        // 404 is fine — it means PostgREST is running, just no root resource
        setDb({ status: "connected", latencyMs, checkedAt: new Date() });
      } else {
        setDb({ status: "error", detail: `HTTP ${res.status}`, checkedAt: new Date() });
      }
    } catch (e) {
      setDb({ status: "error", detail: (e as Error).message?.slice(0, 60), checkedAt: new Date() });
    }
  }, []);

  const checkRealtime = useCallback(() => {
    const channels = supabase.getChannels();
    const live = channels.find((c) => (c as unknown as { topic: string }).topic?.includes("delivery_items"));
    if (!live) {
      // No active channel is normal — Realtime only starts on Overview page
      setRealtime({ status: "inactive", detail: "No active channel", checkedAt: new Date() });
      return;
    }
    const state: string = (live as unknown as { state: string }).state ?? "UNKNOWN";
    if (state === "joined") {
      setRealtime({ status: "connected", detail: "Realtime SUBSCRIBED", checkedAt: new Date() });
    } else if (state === "joining") {
      setRealtime({ status: "checking", detail: "Subscribing…" });
    } else if (state === "errored") {
      setRealtime({ status: "error", detail: "Channel error" });
    } else {
      setRealtime({ status: "inactive", detail: state || "Idle", checkedAt: new Date() });
    }
  }, []);

  const refresh = useCallback(() => {
    checkApi();
    checkDb();
    checkRealtime();
  }, [checkApi, checkDb, checkRealtime]);

  useEffect(() => {
    refresh();
    const poll = setInterval(() => { checkApi(); checkDb(); checkRealtime(); }, POLL_MS);
    const rtPoll = setInterval(checkRealtime, 3000);
    return () => { clearInterval(poll); clearInterval(rtPoll); };
  }, [refresh, checkApi, checkDb, checkRealtime]);

  // Only API and DB matter for aggregate — Realtime is optional
  const coreConnections = [api, db];
  const hasError = coreConnections.some((c) => c.status === "error");
  const allOk = coreConnections.every((c) => c.status === "connected");
  const aggregate: HealthStatus = hasError ? "error" : allOk ? "connected" : "checking";

  return React.createElement(
    ConnectionHealthContext.Provider,
    { value: { api, db, realtime, aggregate, refresh } },
    children,
  );
}
