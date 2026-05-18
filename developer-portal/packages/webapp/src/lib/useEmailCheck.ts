import { useState, useRef, useCallback } from "react";
import { apiFetch } from "./api";

type EmailStatus = "existing" | "new" | "checking";

export function useEmailCheck(orgId: string | null) {
  const [statuses, setStatuses] = useState<Record<string, EmailStatus>>({});
  const pending = useRef<Set<string>>(new Set());
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const flush = useCallback(async () => {
    if (!orgId || pending.current.size === 0) return;
    const emails = [...pending.current];
    pending.current.clear();

    try {
      const res = await apiFetch<{ results: { email: string; exists: boolean }[] }>(
        `/v1/orgs/${orgId}/members/check-emails`,
        { method: "POST", body: JSON.stringify({ emails }) },
      );
      setStatuses((prev) => {
        const next = { ...prev };
        for (const r of res.results) {
          next[r.email.toLowerCase()] = r.exists ? "existing" : "new";
        }
        return next;
      });
    } catch {
      // On error, clear checking state
      setStatuses((prev) => {
        const next = { ...prev };
        for (const e of emails) next[e.toLowerCase()] = "new";
        return next;
      });
    }
  }, [orgId]);

  const checkEmail = useCallback(
    (email: string) => {
      const key = email.toLowerCase().trim();
      if (!key || !orgId) return;
      if (statuses[key]) return; // already checked

      setStatuses((prev) => ({ ...prev, [key]: "checking" }));
      pending.current.add(key);

      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(flush, 300);
    },
    [orgId, statuses, flush],
  );

  return { statuses, checkEmail };
}
