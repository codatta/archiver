import React, { createContext, useContext, useEffect, useState } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { supabase } from "./supabase";
import { apiFetch } from "./api";

type AuthState = {
  user: User | null;
  session: Session | null;
  loading: boolean;
  orgId: string | null;
  refreshAuth: () => Promise<void>;
};

const noop = async () => {};
const AuthContext = createContext<AuthState>({ user: null, session: null, loading: true, orgId: null, refreshAuth: noop });

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, session: null, loading: true, orgId: null });

  async function syncSession(session: Session | null) {
    if (session) {
      localStorage.setItem("access_token", session.access_token);
      try {
        const res = await apiFetch<{ user: { org_id: string | null } }>("/v1/auth/me");
        setState({ user: session.user, session, loading: false, orgId: res.user.org_id });
      } catch {
        setState({ user: session.user, session, loading: false, orgId: null });
      }
    } else {
      localStorage.removeItem("access_token");
      setState({ user: null, session: null, loading: false, orgId: null });
    }
  }

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      syncSession(session);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      syncSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  async function refreshAuth() {
    const { data: { session } } = await supabase.auth.getSession();
    await syncSession(session);
  }

  return <AuthContext.Provider value={{ ...state, refreshAuth }}>{children}</AuthContext.Provider>;
}
