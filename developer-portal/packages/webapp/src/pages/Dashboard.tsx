import React, { useState, useRef, useEffect } from "react";
import { navigate } from "../App";
import { useAuth } from "../lib/auth";
import { apiFetch } from "../lib/api";
import { supabase } from "../lib/supabase";
import { BRAND, THEME } from "../lib/config";
import { Overview } from "../components/dashboard/Overview";
import { ApiKeys } from "../components/dashboard/ApiKeys";
import { SandboxApiKeys } from "../components/dashboard/SandboxApiKeys";
import { Members } from "../components/dashboard/Members";
import { Subscriptions } from "../components/dashboard/Subscriptions";
import { Billing } from "../components/dashboard/Billing";
import { AccountSettings } from "../components/dashboard/AccountSettings";
import { OrgSettings } from "../components/dashboard/OrgSettings";

// ── Org-required guard ─────────────────────────────────────────────────────

function CreateOrgCTA() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-14 h-14 rounded-full flex items-center justify-center mb-4" style={{ background: THEME.border }}>
        <i className="fi fi-ss-building text-xl" style={{ color: THEME.textPrimary }} />
      </div>
      <h2 className="text-lg font-semibold mb-2" style={{ color: THEME.textPrimary }}>Create your organization</h2>
      <p className="text-sm mb-6 max-w-sm" style={{ color: THEME.textMuted }}>
        You need an organization to manage API keys, team members, subscriptions, and billing.
      </p>
      <button onClick={() => navigate("/onboarding")} className="px-5 py-2.5 text-white text-sm font-medium rounded-none" style={{ background: THEME.btnBg }}>
        Create organization
      </button>
    </div>
  );
}

function OrgRequired({ children }: { children: React.ReactNode }) {
  const { orgId } = useAuth();
  if (!orgId) return <CreateOrgCTA />;
  return <>{children}</>;
}

// ── Nav structure ───────────────────────────────────────────────────────────

type NavItem = {
  label: string;
  path: string;
  icon: string;
  comingSoon?: boolean;
};

type NavGroup = {
  title: string;
  items: NavItem[];
};

const NAV_GROUPS: NavGroup[] = [
  {
    title: "Data",
    items: [
      { label: "Dashboard", path: "/dashboard", icon: "fi fi-ss-dashboard" },
      { label: "Subscriptions", path: "/dashboard/subscriptions", icon: "fi fi-ss-rss" },
      { label: "API Keys", path: "/dashboard/api-keys", icon: "fi fi-ss-key" },
    ],
  },
  {
    title: "Tasks",
    items: [
      { label: "Launch Task", path: "/dashboard/launch-task", icon: "fi fi-ss-rocket", comingSoon: true },
      { label: "Task Manager", path: "/dashboard/task-manager", icon: "fi fi-ss-clipboard-list", comingSoon: true },
      { label: "Task Analytics", path: "/dashboard/task-analytics", icon: "fi fi-ss-chart-histogram", comingSoon: true },
    ],
  },
  {
    title: "Settings",
    items: [
      { label: "Team", path: "/dashboard/members", icon: "fi fi-ss-users" },
      { label: "Organization", path: "/dashboard/organization", icon: "fi fi-ss-building" },
      { label: "Billing", path: "/dashboard/billing", icon: "fi fi-ss-credit-card" },
      { label: "Account", path: "/dashboard/account", icon: "fi fi-ss-user" },
    ],
  },
];

// ── Component ───────────────────────────────────────────────────────────────

export type AppMode = "production" | "simulation";

export function Dashboard() {
  const [active, setActive] = useState(window.location.pathname);
  const { user, orgId } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [orgLogoUrl, setOrgLogoUrl] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mode, setMode] = useState<AppMode>(
    () => (localStorage.getItem("app_mode") as AppMode) || "simulation",
  );

  function toggleMode() {
    const next = mode === "production" ? "simulation" : "production";
    // Switching to production requires an org
    if (next === "production" && !orgId) {
      navigate("/onboarding");
      return;
    }
    setMode(next);
    localStorage.setItem("app_mode", next);
  }

  function handleNav(path: string) {
    setActive(path);
    navigate(path);
    setDropdownOpen(false);
  }


  async function handleSignOut() {
    await supabase.auth.signOut();
    localStorage.removeItem("access_token");
    navigate("/");
  }

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node))
        setDropdownOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (!orgId) return;
    apiFetch<{ data: { logo_url: string | null } }>(`/v1/orgs/${orgId}`)
      .then((r) => setOrgLogoUrl(r.data.logo_url ?? null))
      .catch(() => {});
  }, [orgId]);

  const displayName =
    user?.user_metadata?.full_name ?? user?.email ?? "User";
  const initials = displayName
    .split(" ")
    .map((w: string) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const sideW = sidebarCollapsed ? 64 : 220;

  return (
    <div className="min-h-screen flex" style={{ background: THEME.bg }}>
      {/* ── Sidebar ──────────────────────────────────────────────── */}
      <aside
        className="fixed top-0 left-0 h-full flex flex-col z-30"
        style={{
          width: sideW,
          background: THEME.surface,
          borderRight: `1.5px solid ${THEME.border}`,
          transition: "width 0.2s ease",
        }}
      >
        {/* Logo */}
        <div
          className="flex items-center justify-center px-4 h-14 flex-shrink-0"
          style={{ borderBottom: `1.5px solid ${THEME.border}` }}
        >
          <img
            src={BRAND.logo}
            alt={BRAND.name}
            className="h-8 w-auto"
          />
        </div>

        {/* Nav groups */}
        <nav className="flex-1 overflow-y-auto py-2 px-2">
          {NAV_GROUPS.map((group, idx) => (
            <div
              key={group.title}
              className="py-2"
              style={{
                borderTop: idx > 0 ? `1px solid rgba(27,16,52,0.1)` : "none",
              }}
            >
              {!sidebarCollapsed && (
                <p
                  className="text-[11px] uppercase tracking-wider px-3 mb-1.5 font-semibold"
                  style={{ color: THEME.textMuted }}
                >
                  {group.title}
                </p>
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = active === item.path;
                  return (
                    <button
                      key={item.path}
                      onClick={() => !item.comingSoon && handleNav(item.path)}
                      className="w-full flex items-center gap-3 px-3 py-2 text-left transition-colors duration-100"
                      style={{
                        background: isActive
                          ? THEME.accentLight
                          : "transparent",
                        color: item.comingSoon
                          ? "rgba(152,144,168,0.6)"
                          : isActive
                            ? THEME.accent
                            : THEME.textPrimary,
                        cursor: item.comingSoon
                          ? "default"
                          : "pointer",
                        fontWeight: isActive ? 600 : 400,
                        borderLeft: isActive
                          ? `2px solid ${THEME.accent}`
                          : "2px solid transparent",
                      }}
                    >
                      <span className="text-sm w-5 text-center flex-shrink-0 flex items-center justify-center">
                        <i className={item.icon} />
                      </span>
                      {!sidebarCollapsed && (
                        <span className="text-[13px] flex-1 truncate">
                          {item.label}
                        </span>
                      )}
                      {!sidebarCollapsed && item.comingSoon && (
                        <span
                          className="text-[9px] px-1.5 py-0.5 flex-shrink-0"
                          style={{
                            background: "#F0EDFA",
                            color: THEME.textMuted,
                          }}
                        >
                          Soon
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Collapse toggle */}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="flex items-center justify-center h-10 flex-shrink-0"
          style={{
            borderTop: `1px solid rgba(27,16,52,0.08)`,
            color: THEME.textMuted,
          }}
        >
          <span className="text-xs flex items-center justify-center">
            <i className={sidebarCollapsed ? "fi fi-ss-arrow-small-right" : "fi fi-ss-arrow-small-left"} />
          </span>
        </button>

        {/* Docs link */}
        <a
          href="https://docs.humanbased.ai"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2.5 px-5 py-3 flex-shrink-0"
          style={{
            borderTop: `1px solid rgba(27,16,52,0.08)`,
            color: THEME.textMuted,
          }}
        >
          <span className="text-sm w-5 text-center flex items-center justify-center"><i className="fi fi-ss-book" /></span>
          {!sidebarCollapsed && (
            <span className="text-xs">Docs ↗</span>
          )}
        </a>
      </aside>

      {/* ── Main area ────────────────────────────────────────────── */}
      <div
        className="flex-1 flex flex-col min-h-screen"
        style={{ marginLeft: sideW, transition: "margin-left 0.2s ease" }}
      >
        {/* Top bar */}
        <header
          className="flex items-center justify-between px-8 h-14 flex-shrink-0"
          style={{
            background: THEME.surface,
            borderBottom: `1.5px solid ${THEME.border}`,
          }}
        >
          <div className="flex items-center gap-3">
            {orgLogoUrl && (
              <img
                src={orgLogoUrl}
                alt="Org"
                className="h-7 w-7 object-cover"
                style={{ border: `1px solid ${THEME.border}` }}
              />
            )}
          </div>

          {/* Mode toggle + User menu */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-medium" style={{ color: mode === "simulation" ? THEME.accent : THEME.textMuted }}>
                Sandbox
              </span>
              <button
                onClick={toggleMode}
                className="relative w-10 h-5 transition-colors duration-200"
                style={{ background: mode === "production" ? "#22C55E" : THEME.accent, borderRadius: 9999 }}
              >
                <span
                  className="absolute top-0.5 w-4 h-4 bg-white transition-all duration-200"
                  style={{ borderRadius: "50%", left: mode === "production" ? "calc(100% - 18px)" : "2px" }}
                />
              </button>
              <span className="text-[11px] font-medium" style={{ color: mode === "production" ? "#22C55E" : THEME.textMuted }}>
                Production
              </span>
            </div>
            <div className="w-px h-6" style={{ background: THEME.border }} />
            <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 cursor-pointer"
            >
              <span
                className="text-sm"
                style={{ color: THEME.textSecondary }}
              >
                {displayName}
              </span>
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-medium"
                style={{ background: THEME.avatarBg }}
              >
                {initials}
              </div>
            </button>
            {dropdownOpen && (
              <div
                className="absolute right-0 top-full mt-1 w-48 bg-white border shadow-sm z-50"
                style={{ borderColor: THEME.border }}
              >
                <button
                  onClick={() => handleNav("/dashboard/account")}
                  className="w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50"
                  style={{ color: THEME.textPrimary }}
                >
                  Account Settings
                </button>
                <button
                  onClick={() => handleNav("/dashboard/organization")}
                  className="w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50"
                  style={{ color: THEME.textPrimary }}
                >
                  Organization
                </button>
                <div style={{ borderTop: `1.5px solid ${THEME.border}` }} />
                <button
                  onClick={handleSignOut}
                  className="w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50"
                  style={{ color: THEME.danger }}
                >
                  Sign out
                </button>
              </div>
            )}
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 px-8 py-8 max-w-5xl w-full">
          {/* Sandbox banner for users without org */}
          {mode === "simulation" && !orgId && (
            <div className="flex items-center justify-between px-4 py-2.5 mb-6 border-[1.5px]" style={{ borderColor: THEME.accent, background: THEME.accentLight }}>
              <div className="flex items-center gap-2">
                <i className="fi fi-ss-flask text-sm" style={{ color: THEME.accent }} />
                <span className="text-xs" style={{ color: THEME.accent }}>
                  You're in sandbox mode — data is simulated.
                </span>
              </div>
              <button onClick={() => navigate("/onboarding")} className="text-xs font-medium px-3 py-1" style={{ color: THEME.accent, border: `1px solid ${THEME.accent}` }}>
                Create organization
              </button>
            </div>
          )}
          {active === "/dashboard" && <Overview mode={mode} />}
          {active === "/dashboard/api-keys" && (
            mode === "simulation" ? <SandboxApiKeys /> : <OrgRequired><ApiKeys /></OrgRequired>
          )}
          {active === "/dashboard/subscriptions" && (
            mode === "simulation" ? <Subscriptions mode={mode} /> : <OrgRequired><Subscriptions mode={mode} /></OrgRequired>
          )}
          {active === "/dashboard/members" && <OrgRequired><Members /></OrgRequired>}
          {active === "/dashboard/billing" && <OrgRequired><Billing /></OrgRequired>}
          {active === "/dashboard/account" && <AccountSettings />}
          {active === "/dashboard/organization" && <OrgRequired><OrgSettings /></OrgRequired>}

          {/* Coming soon pages */}
          {active === "/dashboard/launch-task" && <ComingSoon title="Launch Task" description="Create and configure human-executed tasks — data collection, annotation, surveys, and more." />}
          {active === "/dashboard/task-manager" && <ComingSoon title="Task Manager" description="Monitor active tasks, review submissions, manage worker assignments, and update task status." />}
          {active === "/dashboard/task-analytics" && <ComingSoon title="Task Analytics" description="Track task completion rates, quality metrics, cost per submission, and worker performance." />}
        </main>

        {/* Footer */}
        <footer className="px-8 pb-4 text-center text-xs" style={{ color: THEME.textMuted }}>
          All rights reserved by Codatta PTE LTD
        </footer>
      </div>
    </div>
  );
}

// ── Coming Soon placeholder ─────────────────────────────────────────────────

function ComingSoon({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div
        className="w-16 h-16 flex items-center justify-center text-2xl mb-4"
        style={{ background: THEME.accentLight, color: THEME.accent }}
      >
        🚀
      </div>
      <h2 className="text-xl font-semibold mb-2" style={{ color: THEME.textPrimary }}>
        {title}
      </h2>
      <p
        className="text-sm text-center max-w-md mb-6"
        style={{ color: THEME.textSecondary }}
      >
        {description}
      </p>
      <span
        className="text-xs font-medium px-4 py-2"
        style={{ background: THEME.accentLight, color: THEME.accent }}
      >
        Coming Soon
      </span>
    </div>
  );
}
