"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

// Dirty state reported by each step page.
// - isDirty: is there unsaved work?
// - isDraftCacheable: true = a draft exists on the backend and will be
//   restored when the contributor returns; false = leaving discards work.
// - description: human-readable summary shown in the confirm dialog.
export type DirtyState = {
  isDirty: boolean;
  isDraftCacheable: boolean;
  description: string;
};

const CLEAN: DirtyState = {
  isDirty: false,
  isDraftCacheable: true,
  description: "",
};

type NavContextValue = {
  dirty: DirtyState;
  setDirty: (state: DirtyState) => void;
  // Request navigation to `href`. If dirty, pops the confirm dialog; on
  // confirm, navigates and resets dirty. Pass `label` for the dialog body.
  guardedNavigate: (href: string, label?: string) => void;
  // Active dialog state — used by the layout to render the modal.
  pendingNav: PendingNav | null;
  acceptPendingNav: () => void;
  cancelPendingNav: () => void;
};

type PendingNav = {
  href: string;
  label: string;
};

const WorkspaceNavContext = createContext<NavContextValue | null>(null);

export function WorkspaceNavProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [dirty, setDirtyState] = useState<DirtyState>(CLEAN);
  const [pendingNav, setPendingNav] = useState<PendingNav | null>(null);

  const setDirty = useCallback((state: DirtyState) => {
    setDirtyState(state);
  }, []);

  // guardedNavigate depends on `dirty.isDirty` so React rewires event
  // handlers whenever the flag flips — callers see the current value without
  // needing a ref.
  const guardedNavigate = useCallback(
    (href: string, label: string = "Navigate away") => {
      if (dirty.isDirty) {
        setPendingNav({ href, label });
      } else {
        router.push(href);
      }
    },
    [router, dirty.isDirty]
  );

  const acceptPendingNav = useCallback(() => {
    if (!pendingNav) return;
    setDirtyState(CLEAN);
    const href = pendingNav.href;
    setPendingNav(null);
    router.push(href);
  }, [pendingNav, router]);

  const cancelPendingNav = useCallback(() => {
    setPendingNav(null);
  }, []);

  const value = useMemo<NavContextValue>(
    () => ({
      dirty,
      setDirty,
      guardedNavigate,
      pendingNav,
      acceptPendingNav,
      cancelPendingNav,
    }),
    [dirty, setDirty, guardedNavigate, pendingNav, acceptPendingNav, cancelPendingNav]
  );

  return (
    <WorkspaceNavContext.Provider value={value}>{children}</WorkspaceNavContext.Provider>
  );
}

export function useWorkspaceNav(): NavContextValue {
  const ctx = useContext(WorkspaceNavContext);
  if (!ctx) {
    throw new Error("useWorkspaceNav must be used inside WorkspaceNavProvider");
  }
  return ctx;
}
