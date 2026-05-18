import React, { useEffect, useState } from "react";
import { useAuth } from "../../lib/auth";
import { useToast } from "../../lib/toast";
import { supabase } from "../../lib/supabase";
import { apiFetch } from "../../lib/api";
import { THEME } from "../../lib/config";
import { navigate } from "../../App";

const inputCls = "w-full px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";

// ── Deletion step definitions ────────────────────────────────────────────────

type DeletionStep = {
  key: string;
  activeLabel: string;
  completedLabel: string;
  icon: string;
};

const DELETION_STEPS: DeletionStep[] = [
  { key: "memberships", activeLabel: "Removing organization memberships", completedLabel: "Removed organization memberships", icon: "fi fi-ss-users" },
  { key: "invitations", activeLabel: "Revoking pending invitations", completedLabel: "Revoked pending invitations", icon: "fi fi-ss-envelope" },
  { key: "api_keys", activeLabel: "Deleting API keys", completedLabel: "Deleted API keys", icon: "fi fi-ss-key" },
  { key: "org_cleanup", activeLabel: "Cleaning up organization data", completedLabel: "Cleaned up organization data", icon: "fi fi-ss-building" },
  { key: "auth", activeLabel: "Deleting authentication record", completedLabel: "Deleted authentication record", icon: "fi fi-ss-lock" },
  { key: "profile", activeLabel: "Removing user profile", completedLabel: "Removed user profile", icon: "fi fi-ss-user" },
];

// ── Delete Account Modal ─────────────────────────────────────────────────────

function DeleteAccountModal({
  email,
  onClose,
}: {
  email: string;
  onClose: () => void;
}) {
  const [confirmEmail, setConfirmEmail] = useState("");
  const [phase, setPhase] = useState<"confirm" | "deleting" | "done">("confirm");
  const [activeStepIdx, setActiveStepIdx] = useState(-1);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");

  const emailMatches = confirmEmail.trim().toLowerCase() === email.toLowerCase();

  async function handleDelete() {
    if (!emailMatches) return;
    setError("");
    setCompletedSteps(new Set());
    setPhase("deleting");
    setActiveStepIdx(0);

    let cancelled = false;

    async function animateSteps() {
      for (let i = 0; i < DELETION_STEPS.length; i++) {
        if (cancelled) return;
        setActiveStepIdx(i);
        await new Promise((r) => setTimeout(r, 600));
        if (cancelled) return;
        setCompletedSteps((prev) => new Set([...prev, DELETION_STEPS[i].key]));
      }
    }

    try {
      const apiPromise = apiFetch<{ deleted: boolean; steps: { step: string }[] }>(
        `/v1/auth/account?confirm_email=${encodeURIComponent(confirmEmail.trim())}`,
        { method: "DELETE" },
      );

      // Run animation alongside API call; wait for both
      const [, apiResult] = await Promise.all([animateSteps(), apiPromise]);

      if (apiResult.deleted) {
        // Mark all steps complete
        setCompletedSteps(new Set(DELETION_STEPS.map((s) => s.key)));
        setActiveStepIdx(DELETION_STEPS.length);
        setPhase("done");

        // Sign out and redirect after a brief pause
        setTimeout(() => {
          supabase.auth
            .signOut()
            .catch((err) => {
              console.error("Failed to sign out after account deletion:", err);
            })
            .finally(() => {
              localStorage.removeItem("access_token");
              localStorage.removeItem("app_mode");
              localStorage.removeItem("sandbox_subscriptions");
              localStorage.removeItem("sandbox_api_keys");
              navigate("/");
            });
        }, 2000);
      }
    } catch (e: unknown) {
      cancelled = true;
      setError((e as Error).message ?? "Failed to delete account");
      setPhase("confirm");
      setActiveStepIdx(-1);
      setCompletedSteps(new Set());
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(27,16,52,0.5)" }}
      onClick={phase === "confirm" ? onClose : undefined}
    >
      <div
        className="w-full max-w-md bg-white border-[1.5px] border-[#1B1034] shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="px-6 pt-5 pb-4 border-b"
          style={{ borderColor: phase === "confirm" ? THEME.danger : "rgba(27,16,52,0.15)" }}
        >
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold" style={{ color: phase === "done" ? THEME.textPrimary : THEME.danger }}>
              {phase === "done" ? "Account deleted" : "Delete your account"}
            </h3>
            {phase === "confirm" && (
              <button onClick={onClose} className="text-xl leading-none" style={{ color: THEME.textSecondary }}>
                ×
              </button>
            )}
          </div>
        </div>

        <div className="px-6 py-5">
          {/* ── Confirmation phase ── */}
          {phase === "confirm" && (
            <>
              <div className="px-3 py-2.5 mb-4 text-xs" style={{ background: "#FEF2F2", color: THEME.danger, border: `1px solid ${THEME.danger}33` }}>
                This action is <strong>permanent and irreversible</strong>. All your data, organization memberships, API keys, and subscriptions will be permanently deleted.
              </div>
              <p className="text-sm mb-4" style={{ color: THEME.textSecondary }}>
                To confirm, type your email address below:
              </p>
              <p className="text-xs font-mono mb-2 px-2 py-1.5" style={{ background: THEME.bg, color: THEME.textPrimary }}>
                {email}
              </p>
              <input
                type="email"
                value={confirmEmail}
                onChange={(e) => { setConfirmEmail(e.target.value); setError(""); }}
                placeholder="Type your email to confirm"
                className={inputCls}
                autoFocus
              />
              {error && (
                <p className="text-xs mt-2" style={{ color: THEME.danger }}>{error}</p>
              )}
              <div className="flex gap-3 justify-end mt-5">
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm border-[1.5px] border-[#1B1034]"
                  style={{ color: THEME.textSecondary }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={!emailMatches}
                  className="px-4 py-2 text-sm text-white font-medium disabled:opacity-30"
                  style={{ background: THEME.danger }}
                >
                  Delete my account
                </button>
              </div>
            </>
          )}

          {/* ── Deleting phase (animated steps) ── */}
          {(phase === "deleting" || phase === "done") && (
            <div className="space-y-0">
              {DELETION_STEPS.map((step, idx) => {
                const isComplete = completedSteps.has(step.key);
                const isActive = idx === activeStepIdx && !isComplete;
                const isPending = idx > activeStepIdx;

                return (
                  <div
                    key={step.key}
                    className="flex items-center gap-3 py-2.5 transition-all duration-300"
                    style={{
                      opacity: isPending ? 0.3 : 1,
                      transform: isActive ? "translateX(4px)" : "translateX(0)",
                      transition: "all 0.3s ease",
                    }}
                  >
                    {/* Status indicator */}
                    <div
                      className="w-6 h-6 flex items-center justify-center flex-shrink-0"
                      style={{ transition: "all 0.3s ease" }}
                    >
                      {isComplete ? (
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <circle cx="8" cy="8" r="8" fill="#22C55E" />
                          <path d="M5 8L7 10L11 6" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      ) : isActive ? (
                        <div
                          className="w-4 h-4 border-2 border-t-transparent rounded-full"
                          style={{ borderColor: THEME.danger, borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }}
                        />
                      ) : (
                        <div className="w-3 h-3 rounded-full" style={{ background: "#E5E7EB" }} />
                      )}
                    </div>

                    {/* Icon */}
                    <i
                      className={`${step.icon} text-sm`}
                      style={{ color: isComplete ? "#22C55E" : isActive ? THEME.danger : THEME.textMuted }}
                    />

                    {/* Label */}
                    <span
                      className="text-sm"
                      style={{
                        color: isComplete ? THEME.textPrimary : isActive ? THEME.danger : THEME.textMuted,
                        fontWeight: isActive ? 500 : 400,
                      }}
                    >
                      {isComplete ? step.completedLabel : step.activeLabel}
                      {isComplete && (
                        <span className="ml-1.5 text-xs" style={{ color: "#22C55E" }}>Done</span>
                      )}
                    </span>
                  </div>
                );
              })}

              {/* Done message */}
              {phase === "done" && (
                <div
                  className="mt-4 pt-4 text-center"
                  style={{ borderTop: `1px solid rgba(27,16,52,0.1)`, animation: "fadeIn 0.5s ease" }}
                >
                  <p className="text-sm font-medium" style={{ color: THEME.textPrimary }}>
                    Your account has been deleted.
                  </p>
                  <p className="text-xs mt-1" style={{ color: THEME.textMuted }}>
                    Redirecting you to the home page...
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to   { opacity: 1; transform: translateY(0); }
          }
        `}</style>
      </div>
    </div>
  );
}

// ── Account Settings ─────────────────────────────────────────────────────────

export function AccountSettings() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [name, setName] = useState(user?.user_metadata?.full_name ?? "");
  const email = user?.email ?? "";
  const [backupEmail, setBackupEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    apiFetch<{ user: { profile: { backup_email?: string | null } } }>("/v1/auth/me")
      .then((res) => {
        if (res.user.profile?.backup_email) {
          setBackupEmail(res.user.profile.backup_email);
        }
      })
      .catch(() => {/* ignore */});
  }, []);

  async function handleSave(e?: React.FormEvent) {
    e?.preventDefault();
    setSaving(true);
    try {
      // Update display name in Supabase Auth metadata
      const { error } = await supabase.auth.updateUser({ data: { full_name: name } });
      if (error) throw new Error(error.message);

      // Update name + backup_email in public.users via API
      await apiFetch("/v1/auth/profile", {
        method: "PATCH",
        body: JSON.stringify({
          name: name || undefined,
          backup_email: backupEmail || null,
        }),
      });

      toast("Account settings saved");
    } catch (err: unknown) {
      toast((err as Error).message ?? "Failed to save", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6" style={{ color: THEME.textPrimary }}>Account Settings</h1>
      <form onSubmit={handleSave} className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6 space-y-4 max-w-lg">
        <div>
          <label className="block text-sm font-medium mb-1.5" style={{ color: THEME.textPrimary }}>Full name</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} className={inputCls} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5" style={{ color: THEME.textPrimary }}>Email</label>
          <input type="email" value={email} disabled className={inputCls + " opacity-50 cursor-not-allowed"} />
          <p className="text-xs mt-1" style={{ color: THEME.textMuted }}>Email cannot be changed.</p>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1.5" style={{ color: THEME.textPrimary }}>Backup email</label>
          <input
            type="email"
            value={backupEmail}
            onChange={(e) => setBackupEmail(e.target.value)}
            placeholder="Optional — for account recovery"
            className={inputCls}
          />
          <p className="text-xs mt-1" style={{ color: THEME.textMuted }}>Used only for account recovery. Optional.</p>
        </div>
        <button type="button" onClick={() => handleSave()} disabled={saving} className="px-5 py-2.5 text-sm text-white rounded-none font-medium disabled:opacity-50" style={{ background: THEME.btnBg }}>{saving ? "Saving..." : "Save changes"}</button>
      </form>

      {/* ── Danger Zone ── */}
      <div className="mt-10 max-w-lg">
        <h2 className="text-sm font-semibold uppercase tracking-wide mb-3" style={{ color: THEME.danger }}>Danger Zone</h2>
        <div
          className="bg-white border-[1.5px] rounded-none p-6 flex items-start justify-between"
          style={{ borderColor: THEME.danger }}
        >
          <div className="flex-1 mr-4">
            <p className="text-sm font-medium" style={{ color: THEME.textPrimary }}>Delete your account</p>
            <p className="text-xs mt-1 leading-relaxed" style={{ color: THEME.textSecondary }}>
              Permanently delete your account and all associated data including organization memberships, API keys, and subscriptions. This action cannot be undone.
            </p>
          </div>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="flex-shrink-0 px-4 py-2 text-sm font-medium border-[1.5px]"
            style={{ borderColor: THEME.danger, color: THEME.danger }}
          >
            Delete account
          </button>
        </div>
      </div>

      {showDeleteModal && (
        <DeleteAccountModal email={email} onClose={() => setShowDeleteModal(false)} />
      )}
    </div>
  );
}
