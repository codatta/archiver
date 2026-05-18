import React, { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "./lib/auth";
import { ToastProvider } from "./lib/toast";
import { Landing } from "./pages/Landing";
import { SignIn } from "./pages/SignIn";
import { SignUp } from "./pages/SignUp";
import { Dashboard } from "./pages/Dashboard";
import { Onboarding } from "./pages/Onboarding";
import { VerifyEmail } from "./pages/VerifyEmail";
import { AuthCallback } from "./pages/AuthCallback";

type Route = "landing" | "signin" | "signup" | "onboarding" | "dashboard" | "verify-email" | "auth-callback";

export function getRoute(path?: string): Route {
  const p = path ?? window.location.pathname;
  if (p.startsWith("/dashboard")) return "dashboard";
  if (p.startsWith("/onboarding")) return "onboarding";
  if (p === "/auth/signin") return "signin";
  if (p === "/auth/signup") return "signup";
  if (p === "/auth/verify-email") return "verify-email";
  if (p === "/auth/callback") return "auth-callback";
  return "landing";
}

export function navigate(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function Router() {
  const [route, setRoute] = useState<Route>(getRoute);
  const { user, loading } = useAuth();

  useEffect(() => {
    const handler = () => setRoute(getRoute());
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  // Redirect authenticated users away from auth pages
  // Note: signup is excluded — the OTP flow grants a session mid-signup
  // (after verifyOtp) but the user still needs to set their password.
  useEffect(() => {
    if (!loading && user && (route === "signin" || route === "landing")) {
      navigate("/dashboard");
    }
  }, [user, loading, route]);

  // Redirect unauthenticated users away from protected pages
  useEffect(() => {
    if (!loading && !user && (route === "dashboard" || route === "onboarding")) {
      navigate("/auth/signin");
    }
  }, [user, loading, route]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-sm text-gray-400">Loading...</div>
      </div>
    );
  }

  switch (route) {
    case "signin":
      return <SignIn />;
    case "signup":
      return <SignUp />;
    case "verify-email":
      return <VerifyEmail />;
    case "auth-callback":
      return <AuthCallback />;
    case "onboarding":
      return user ? <Onboarding /> : null;
    case "dashboard":
      return user ? <Dashboard /> : null;
    default:
      return <Landing />;
  }
}

export function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Router />
      </ToastProvider>
    </AuthProvider>
  );
}
