import { useCallback, useEffect, useState, useSyncExternalStore } from "react";

// ── Sandbox Subscriptions ────────────────────────────────────────────────────

const SUBS_KEY = "sandbox_subscriptions";

function getStoredSubs(): string[] {
  try {
    return JSON.parse(localStorage.getItem(SUBS_KEY) || "[]");
  } catch {
    return [];
  }
}

let subsListeners = new Set<() => void>();
let subsSnapshot = getStoredSubs();

function notifySubs() {
  subsSnapshot = getStoredSubs();
  subsListeners.forEach((l) => l());
}

// Cross-tab sync
if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === SUBS_KEY) notifySubs();
  });
}

function subsSubscribe(listener: () => void) {
  subsListeners.add(listener);
  return () => { subsListeners.delete(listener); };
}

function subsGetSnapshot() {
  return subsSnapshot;
}

export function useSandboxSubscriptions() {
  const subs = useSyncExternalStore(subsSubscribe, subsGetSnapshot);

  const subscribe = useCallback((verticalId: string) => {
    const current = getStoredSubs();
    if (current.includes(verticalId)) return;
    localStorage.setItem(SUBS_KEY, JSON.stringify([...current, verticalId]));
    notifySubs();
  }, []);

  const unsubscribe = useCallback((verticalId: string) => {
    const current = getStoredSubs();
    localStorage.setItem(SUBS_KEY, JSON.stringify(current.filter((id) => id !== verticalId)));
    notifySubs();
  }, []);

  return { subs, subscribe, unsubscribe };
}

// ── Sandbox Subscription Filters ─────────────────────────────────────────────

const SUB_FILTERS_KEY = "sandbox_sub_filters";

type SubFilters = Record<string, { quality_grades: string[] } | null>;

function getStoredSubFilters(): SubFilters {
  try {
    return JSON.parse(localStorage.getItem(SUB_FILTERS_KEY) || "{}");
  } catch {
    return {};
  }
}

let subFiltersListeners = new Set<() => void>();
let subFiltersSnapshot = getStoredSubFilters();

function notifySubFilters() {
  subFiltersSnapshot = getStoredSubFilters();
  subFiltersListeners.forEach((l) => l());
}

if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === SUB_FILTERS_KEY) notifySubFilters();
  });
}

function subFiltersSubscribe(listener: () => void) {
  subFiltersListeners.add(listener);
  return () => { subFiltersListeners.delete(listener); };
}

function subFiltersGetSnapshot() {
  return subFiltersSnapshot;
}

export function useSandboxSubFilters() {
  const filters = useSyncExternalStore(subFiltersSubscribe, subFiltersGetSnapshot);

  const updateFilters = useCallback((verticalId: string, grades: string[] | null) => {
    const current = getStoredSubFilters();
    if (grades && grades.length > 0) {
      current[verticalId] = { quality_grades: grades };
    } else {
      delete current[verticalId];
    }
    localStorage.setItem(SUB_FILTERS_KEY, JSON.stringify(current));
    notifySubFilters();
  }, []);

  return { filters, updateFilters };
}

// ── Sandbox API Keys ─────────────────────────────────────────────────────────

const KEYS_KEY = "sandbox_api_keys";

export type SandboxKey = {
  id: string;
  name: string;
  key: string;
  created_at: string;
};

function getStoredKeys(): SandboxKey[] {
  try {
    return JSON.parse(localStorage.getItem(KEYS_KEY) || "[]");
  } catch {
    return [];
  }
}

let keysListeners = new Set<() => void>();
let keysSnapshot = getStoredKeys();

function notifyKeys() {
  keysSnapshot = getStoredKeys();
  keysListeners.forEach((l) => l());
}

if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key === KEYS_KEY) notifyKeys();
  });
}

function keysSubscribe(listener: () => void) {
  keysListeners.add(listener);
  return () => { keysListeners.delete(listener); };
}

function keysGetSnapshot() {
  return keysSnapshot;
}

function generateSandboxKey(): string {
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
  const rand = Array.from({ length: 32 }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
  return `hb_sandbox_${rand}`;
}

export function useSandboxApiKeys() {
  const keys = useSyncExternalStore(keysSubscribe, keysGetSnapshot);

  const createKey = useCallback((name: string): SandboxKey => {
    const current = getStoredKeys();
    const newKey: SandboxKey = {
      id: crypto.randomUUID(),
      name: `${name}-sandbox`,
      key: generateSandboxKey(),
      created_at: new Date().toISOString(),
    };
    localStorage.setItem(KEYS_KEY, JSON.stringify([...current, newKey]));
    notifyKeys();
    return newKey;
  }, []);

  const revokeKey = useCallback((id: string) => {
    const current = getStoredKeys();
    localStorage.setItem(KEYS_KEY, JSON.stringify(current.filter((k) => k.id !== id)));
    notifyKeys();
  }, []);

  return { keys, createKey, revokeKey };
}

// ── Sandbox Cursors ───────────────────────────────────────────────────────────

const CURSORS_KEY = "sandbox_cursors";

function getStoredCursors(): Record<string, number> {
  try {
    return JSON.parse(localStorage.getItem(CURSORS_KEY) || "{}");
  } catch {
    return {};
  }
}

export function useSandboxCursors() {
  const [cursors, setCursors] = useState<Record<string, number>>(getStoredCursors);

  const getCursor = useCallback((verticalId: string) => cursors[verticalId] ?? 0, [cursors]);

  const incrementCursor = useCallback((verticalId: string) => {
    const current = getStoredCursors();
    current[verticalId] = (current[verticalId] ?? 0) + 1;
    localStorage.setItem(CURSORS_KEY, JSON.stringify(current));
    setCursors({ ...current });
  }, []);

  const resetCursor = useCallback((verticalId: string) => {
    const current = getStoredCursors();
    delete current[verticalId];
    localStorage.setItem(CURSORS_KEY, JSON.stringify(current));
    setCursors({ ...current });
  }, []);

  return { getCursor, incrementCursor, resetCursor };
}
