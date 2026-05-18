import React, { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useToast } from "../../lib/toast";
import { useEmailCheck } from "../../lib/useEmailCheck";
import { THEME } from "../../lib/config";

// ── Types ────────────────────────────────────────────────────────────────────

type Member = {
  id: string;
  role: "owner" | "admin" | "member";
  permissions: string[];
  created_at: string;
  joined_at: string;
  users?: { id: string; name: string; email: string; avatar_url?: string };
};

type Invitation = {
  id: string;
  email: string;
  role: string;
  permissions: string[];
  created_at: string;
  expires_at: string;
};

const ALL_PERMISSIONS: { key: string; label: string; description: string }[] = [
  { key: "data.read",              label: "Data Read",         description: "Pull and view data items" },
  { key: "subscriptions.manage",   label: "Subscriptions",     description: "Subscribe / unsubscribe verticals" },
  { key: "members.invite",         label: "Invite Members",    description: "Send team invitations" },
  { key: "keys.manage",            label: "API Keys",          description: "Create and revoke API keys" },
  { key: "billing.manage",         label: "Billing",           description: "Add funds, view billing" },
];

// ── Pure permission helpers (exported for unit tests) ─────────────────────────

export function resolveCurrentRole(
  members: Array<{ role: string; users?: { email?: string } }>,
  userEmail: string | null | undefined,
): "owner" | "admin" | "member" | null {
  if (!userEmail || members.length === 0) return null;
  const self = members.find((m) => m.users?.email === userEmail);
  return (self?.role as "owner" | "admin" | "member") ?? null;
}

export function resolveIsAdmin(role: "owner" | "admin" | "member" | null): boolean {
  return role === "owner" || role === "admin";
}

export function shouldShowMemberActions(isOwner: boolean, isSelf: boolean, isAdmin: boolean): boolean {
  return !isOwner && !isSelf && isAdmin;
}

// ─────────────────────────────────────────────────────────────────────────────

const inputCls =
  "px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";

// ── InviteStep ───────────────────────────────────────────────────────────────

function InviteStep({
  label,
  status,
  warning,
}: {
  label: string;
  status: "pending" | "active" | "done" | "warning";
  warning?: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="mt-0.5 w-5 h-5 flex-shrink-0 flex items-center justify-center">
        {status === "done" && (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="8" fill="#22C55E" />
            <path d="M4.5 8L7 10.5L11.5 5.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
        {status === "active" && (
          <span
            className="inline-block w-4 h-4 rounded-full border-2 border-t-transparent"
            style={{ borderColor: `${THEME.accent} transparent ${THEME.accent} ${THEME.accent}`, animation: "spin 0.8s linear infinite" }}
          />
        )}
        {status === "warning" && (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="8" fill="#F59E0B" />
            <path d="M8 5V9" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
            <circle cx="8" cy="11" r="0.8" fill="white"/>
          </svg>
        )}
        {status === "pending" && (
          <span className="inline-block w-3 h-3 rounded-full" style={{ background: "rgba(27,16,52,0.15)" }} />
        )}
      </div>
      <div>
        <span
          className="text-sm"
          style={{
            color: status === "pending" ? THEME.textMuted : status === "warning" ? "#B45309" : THEME.textPrimary,
            fontWeight: status === "active" ? 500 : 400,
          }}
        >
          {label}
        </span>
        {warning && <p className="text-xs mt-0.5" style={{ color: "#B45309" }}>{warning}</p>}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ── EditMemberModal ───────────────────────────────────────────────────────────

function EditMemberModal({
  member,
  orgId,
  onClose,
  onUpdated,
}: {
  member: Member;
  orgId: string;
  onClose: () => void;
  onUpdated: (m: Member) => void;
}) {
  const { toast } = useToast();
  const [role, setRole] = useState<"admin" | "member">(
    member.role === "owner" ? "admin" : (member.role as "admin" | "member")
  );
  const [permissions, setPermissions] = useState<Set<string>>(
    new Set(member.permissions ?? [])
  );
  const [saving, setSaving] = useState(false);

  function togglePerm(key: string) {
    setPermissions((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  async function handleSave() {
    setSaving(true);
    try {
      const res = await apiFetch<{ data: Member }>(
        `/v1/orgs/${orgId}/members/${member.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({ role, permissions: Array.from(permissions) }),
        }
      );
      onUpdated(res.data);
      toast("Member updated");
      onClose();
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to update member", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div
        className="bg-white w-full max-w-md shadow-xl"
        style={{ border: `1.5px solid ${THEME.border}` }}
      >
        {/* Header */}
        <div
          className="px-6 py-4"
          style={{ borderBottom: `1.5px solid ${THEME.border}` }}
        >
          <h3 className="text-base font-semibold" style={{ color: THEME.textPrimary }}>
            Edit Member
          </h3>
          <p className="text-sm mt-0.5" style={{ color: THEME.textMuted }}>
            {member.users?.name ?? member.users?.email ?? "Member"}
          </p>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5">
          {/* Role */}
          <div>
            <label className="text-xs font-medium mb-1.5 block" style={{ color: THEME.textSecondary }}>
              Role
            </label>
            <div className="flex gap-2">
              {(["admin", "member"] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setRole(r)}
                  className="px-4 py-2 text-sm capitalize border-[1.5px]"
                  style={{
                    borderColor: role === r ? THEME.accent : THEME.border,
                    background: role === r ? THEME.accentLight : "white",
                    color: role === r ? THEME.accent : THEME.textSecondary,
                    fontWeight: role === r ? 500 : 400,
                  }}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Permissions */}
          <div>
            <label className="text-xs font-medium mb-2 block" style={{ color: THEME.textSecondary }}>
              Permissions
            </label>
            <div className="space-y-2">
              {ALL_PERMISSIONS.map(({ key, label, description }) => {
                const checked = permissions.has(key);
                return (
                  <label
                    key={key}
                    className="flex items-start gap-3 cursor-pointer group"
                    onClick={() => togglePerm(key)}
                  >
                    <div
                      className="mt-0.5 w-4 h-4 flex-shrink-0 flex items-center justify-center border-[1.5px]"
                      style={{
                        borderColor: checked ? THEME.accent : THEME.border,
                        background: checked ? THEME.accent : "white",
                      }}
                    >
                      {checked && (
                        <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                          <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      )}
                    </div>
                    <div>
                      <div className="text-sm font-medium" style={{ color: THEME.textPrimary }}>{label}</div>
                      <div className="text-xs" style={{ color: THEME.textMuted }}>{description}</div>
                    </div>
                  </label>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div
          className="px-6 py-4 flex gap-2 justify-end"
          style={{ borderTop: `1.5px solid ${THEME.border}` }}
        >
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm"
            style={{ color: THEME.textMuted }}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2 text-sm text-white font-medium disabled:opacity-50"
            style={{ background: THEME.btnBg }}
          >
            {saving ? "Saving..." : "Save changes"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export function Members() {
  const { orgId } = useAuth();
  const { toast } = useToast();

  const [members, setMembers] = useState<Member[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"admin" | "member">("member");
  const [inviting, setInviting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [inviteProgress, setInviteProgress] = useState<null | {
    step: "sending" | "invite_sent" | "confirming" | "confirmed" | "done";
    emailSent: boolean;
  }>(null);
  const [removeConfirm, setRemoveConfirm] = useState<string | null>(null);
  const { statuses: emailStatuses, checkEmail } = useEmailCheck(orgId);
  const [editMember, setEditMember] = useState<Member | null>(null);
  const [currentRole, setCurrentRole] = useState<"owner" | "admin" | "member" | null>(null);

  const fetchAll = useCallback(async () => {
    if (!orgId) return;
    try {
      const [mRes, iRes] = await Promise.all([
        apiFetch<{ data: Member[] }>(`/v1/orgs/${orgId}/members`),
        apiFetch<{ data: Invitation[] }>(`/v1/orgs/${orgId}/members/invitations`),
      ]);
      setMembers(mRes.data);
      setInvitations(iRes.data);
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to load members", "error");
    } finally {
      setLoading(false);
    }
  }, [orgId, toast]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  function handleInviteClick(e?: React.FormEvent) {
    e?.preventDefault();
    const email = inviteEmail.trim().toLowerCase();
    if (!email) return;

    // Client-side duplicate checks
    const alreadyMember = members.some(
      (m) => m.users?.email?.toLowerCase() === email
    );
    if (alreadyMember) {
      toast("This person is already a member of the organization", "error");
      return;
    }
    const alreadyInvited = invitations.some(
      (inv) => inv.email.toLowerCase() === email
    );
    if (alreadyInvited) {
      toast("A pending invitation already exists for this email", "error");
      return;
    }

    setShowConfirm(true);
  }

  async function confirmInvite() {
    if (!orgId) return;
    setShowConfirm(false);
    setInviting(true);
    setInviteProgress({ step: "sending", emailSent: false });
    try {
      const res = await apiFetch<{ data: Member | Invitation; status: string; email_sent?: boolean }>(
        `/v1/orgs/${orgId}/members/invite`,
        { method: "POST", body: JSON.stringify({ email: inviteEmail, role: inviteRole }) }
      );
      const emailSent = res.email_sent !== false;
      setInviteProgress({ step: "invite_sent", emailSent });
      // Brief pause to show the invite sent step
      await new Promise((r) => setTimeout(r, 800));
      setInviteProgress({ step: "confirming", emailSent });
      await new Promise((r) => setTimeout(r, 600));
      setInviteProgress({ step: "confirmed", emailSent });
      await new Promise((r) => setTimeout(r, 600));
      setInviteProgress({ step: "done", emailSent });
      await fetchAll();
      await new Promise((r) => setTimeout(r, 400));
      toast(res.status === "added" ? `${inviteEmail} added to the organization` : `Invitation sent to ${inviteEmail}`);
      setInviteEmail("");
      setInviteProgress(null);
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to send invite", "error");
      setInviteProgress(null);
    } finally {
      setInviting(false);
    }
  }

  async function handleRemove(id: string) {
    if (!orgId) return;
    try {
      await apiFetch(`/v1/orgs/${orgId}/members/${id}`, { method: "DELETE" });
      setMembers((p) => p.filter((m) => m.id !== id));
      toast("Member removed");
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to remove member", "error");
    }
    setRemoveConfirm(null);
  }

  async function handleRevokeInvitation(id: string, email: string) {
    if (!orgId) return;
    try {
      await apiFetch(`/v1/orgs/${orgId}/members/invitations/${id}`, { method: "DELETE" });
      setInvitations((p) => p.filter((i) => i.id !== id));
      toast(`Invitation to ${email} revoked`);
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to revoke invitation", "error");
    }
  }

  function handleMemberUpdated(updated: Member) {
    setMembers((p) => p.map((m) => (m.id === updated.id ? { ...m, ...updated } : m)));
  }

  const currentUser = useAuth().user;

  useEffect(() => {
    if (!currentUser || members.length === 0) return;
    const self = members.find((m) => m.users?.email === currentUser.email);
    if (self) setCurrentRole(self.role);
  }, [members, currentUser]);

  const isAdmin = currentRole === "owner" || currentRole === "admin";

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6" style={{ color: THEME.textPrimary }}>Members</h1>

      {/* Invite form — admin/owner only */}
      {isAdmin && <form onSubmit={handleInviteClick} className="mb-6">
        <div className="flex items-center gap-2">
        <input
          type="email"
          value={inviteEmail}
          onChange={(e) => setInviteEmail(e.target.value)}
          onBlur={() => { if (inviteEmail.trim()) checkEmail(inviteEmail.trim()); }}
          placeholder="colleague@company.com"
          required
          className={"flex-1 " + inputCls}
        />
        <select
          value={inviteRole}
          onChange={(e) => setInviteRole(e.target.value as "admin" | "member")}
          className={inputCls}
        >
          <option value="admin">Admin</option>
          <option value="member">Member</option>
        </select>
        <button
          type="button"
          onClick={() => handleInviteClick()}
          disabled={inviting}
          className="px-5 py-2.5 text-sm text-white rounded-none font-medium disabled:opacity-50"
          style={{ background: THEME.accent }}
        >
          {inviting ? "Sending..." : "Invite"}
        </button>
        </div>
        {inviteEmail.trim() && emailStatuses[inviteEmail.trim().toLowerCase()] && (
          <div className="mt-1.5 ml-1">
            {emailStatuses[inviteEmail.trim().toLowerCase()] === "checking" && (
              <span className="text-xs text-gray-400">Checking...</span>
            )}
            {emailStatuses[inviteEmail.trim().toLowerCase()] === "existing" && (
              <span className="text-xs text-green-600">Existing user — will be added directly</span>
            )}
            {emailStatuses[inviteEmail.trim().toLowerCase()] === "new" && (
              <span className="text-xs text-gray-400">New user — will receive signup invitation</span>
            )}
          </div>
        )}
      </form>}

      {/* Confirm invite dialog */}
      {showConfirm && !inviteProgress && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white p-6 w-96 shadow-lg" style={{ border: `1.5px solid ${THEME.border}` }}>
            <h3 className="text-base font-semibold mb-2" style={{ color: THEME.textPrimary }}>Send invitation?</h3>
            <p className="text-sm mb-1" style={{ color: THEME.textSecondary }}>An invitation email will be sent to:</p>
            <p className="text-sm font-medium mb-1" style={{ color: THEME.textPrimary }}>{inviteEmail}</p>
            <p className="text-xs mb-4" style={{ color: THEME.textMuted }}>Role: {inviteRole}</p>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowConfirm(false)} className="px-4 py-2 text-sm" style={{ color: THEME.textMuted }}>Cancel</button>
              <button onClick={confirmInvite} className="px-5 py-2 text-sm text-white rounded-none font-medium" style={{ background: THEME.btnBg }}>Send invitation</button>
            </div>
          </div>
        </div>
      )}

      {/* Invitation progress modal */}
      {inviteProgress && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white p-6 w-[26rem] shadow-lg" style={{ border: `1.5px solid ${THEME.border}` }}>
            <h3 className="text-base font-semibold mb-4" style={{ color: THEME.textPrimary }}>
              Sending invitation to {inviteEmail}
            </h3>
            <div className="space-y-3">
              <InviteStep
                label="Sending invitation email"
                status={
                  inviteProgress.step === "sending" ? "active" :
                  inviteProgress.emailSent ? "done" : "warning"
                }
              />
              <InviteStep
                label="Invitation delivered"
                status={
                  ["invite_sent", "confirming", "confirmed", "done"].includes(inviteProgress.step)
                    ? (inviteProgress.emailSent ? "done" : "warning")
                    : "pending"
                }
                warning={!inviteProgress.emailSent && inviteProgress.step !== "sending" ? "Email service unavailable — invite saved" : undefined}
              />
              <InviteStep
                label="Sending confirmation to you"
                status={
                  inviteProgress.step === "confirming" ? "active" :
                  ["confirmed", "done"].includes(inviteProgress.step) ? "done" : "pending"
                }
              />
              <InviteStep
                label="Done"
                status={inviteProgress.step === "done" ? "done" : "pending"}
              />
            </div>
          </div>
        </div>
      )}

      {/* Edit modal */}
      {editMember && (
        <EditMemberModal
          member={editMember}
          orgId={orgId ?? ""}
          onClose={() => setEditMember(null)}
          onUpdated={(m) => { handleMemberUpdated(m); setEditMember(null); }}
        />
      )}

      {/* Members table */}
      <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none overflow-hidden mb-6">
        <table className="w-full">
          <thead>
            <tr className="text-xs text-left" style={{ color: THEME.textMuted }}>
              <th className="px-5 py-3 font-medium">Member</th>
              <th className="px-3 py-3 font-medium">Role</th>
              <th className="px-3 py-3 font-medium">Permissions</th>
              <th className="px-3 py-3 font-medium">Joined</th>
              <th className="px-5 py-3 font-medium text-right"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-sm" style={{ color: THEME.textMuted }}>Loading...</td></tr>
            ) : members.length === 0 ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-sm" style={{ color: THEME.textMuted }}>No members yet.</td></tr>
            ) : members.map((m) => {
              const perms = m.permissions ?? [];
              const permLabels = ALL_PERMISSIONS.filter((p) => perms.includes(p.key)).map((p) => p.label);
              const isOwner = m.role === "owner";
              const isSelf = m.users?.email === currentUser?.email;

              return (
                <tr key={m.id} className="hover:bg-gray-50" style={{ borderTop: `1.5px solid ${THEME.border}` }}>
                  <td className="px-5 py-4">
                    <p className="text-sm font-medium" style={{ color: THEME.textPrimary }}>{m.users?.name ?? "Unknown"}</p>
                    <p className="text-xs" style={{ color: THEME.textMuted }}>{m.users?.email ?? ""}</p>
                  </td>
                  <td className="px-3 py-4">
                    <span
                      className="text-xs px-2 py-0.5 font-medium capitalize"
                      style={{
                        background: isOwner ? THEME.accentLight : "rgba(27,16,52,0.06)",
                        color: isOwner ? THEME.accent : THEME.textSecondary,
                      }}
                    >
                      {m.role}
                    </span>
                  </td>
                  <td className="px-3 py-4">
                    {isOwner ? (
                      <span className="text-xs" style={{ color: THEME.accent }}>Full access</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {permLabels.length > 0 ? permLabels.map((l) => (
                          <span key={l} className="text-xs px-1.5 py-0.5" style={{ background: "rgba(131,77,251,0.08)", color: THEME.accent }}>{l}</span>
                        )) : (
                          <span className="text-xs" style={{ color: THEME.textMuted }}>No permissions</span>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-4 text-xs" style={{ color: THEME.textMuted }}>
                    {new Date(m.joined_at ?? m.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </td>
                  <td className="px-5 py-4 text-right">
                    {!isOwner && !isSelf && isAdmin && (
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => setEditMember(m)}
                          className="px-3 py-1 text-xs border-[1.5px]"
                          style={{ borderColor: THEME.border, color: THEME.textSecondary }}
                        >
                          Edit
                        </button>
                        {removeConfirm === m.id ? (
                          <span className="flex gap-2">
                            <button onClick={() => handleRemove(m.id)} className="text-xs font-medium" style={{ color: THEME.danger }}>Confirm</button>
                            <button onClick={() => setRemoveConfirm(null)} className="text-xs" style={{ color: THEME.textMuted }}>Cancel</button>
                          </span>
                        ) : (
                          <button onClick={() => setRemoveConfirm(m.id)} className="text-xs font-medium" style={{ color: THEME.danger }}>Remove</button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pending Invitations */}
      <div>
        <h2 className="text-sm font-medium mb-3" style={{ color: THEME.textSecondary }}>
          Pending Invitations{invitations.length > 0 ? ` (${invitations.length})` : ""}
        </h2>
        <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="text-xs text-left" style={{ color: THEME.textMuted }}>
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-3 py-3 font-medium">Role</th>
                <th className="px-3 py-3 font-medium">Permissions</th>
                <th className="px-3 py-3 font-medium">Invited</th>
                <th className="px-5 py-3 font-medium text-right"></th>
              </tr>
            </thead>
            <tbody>
              {invitations.length === 0 ? (
                <tr><td colSpan={5} className="px-5 py-6 text-center text-sm" style={{ color: THEME.textMuted }}>No pending invitations</td></tr>
              ) : invitations.map((inv) => {
                const permLabels = ALL_PERMISSIONS.filter((p) => (inv.permissions ?? []).includes(p.key)).map((p) => p.label);
                return (
                  <tr key={inv.id} style={{ borderTop: `1.5px solid ${THEME.border}` }}>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <span className="text-sm" style={{ color: THEME.textPrimary }}>{inv.email}</span>
                        <span className="text-xs px-1.5 py-0.5" style={{ background: "rgba(245,158,11,0.12)", color: "#B45309" }}>Pending</span>
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <span className="text-xs px-2 py-0.5 capitalize" style={{ background: "rgba(27,16,52,0.06)", color: THEME.textSecondary }}>
                        {inv.role}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex flex-wrap gap-1">
                        {permLabels.map((l) => (
                          <span key={l} className="text-xs px-1.5 py-0.5" style={{ background: "rgba(131,77,251,0.08)", color: THEME.accent }}>{l}</span>
                        ))}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-xs" style={{ color: THEME.textMuted }}>
                      {new Date(inv.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </td>
                    <td className="px-5 py-3 text-right">
                      {isAdmin && (
                        <button
                          onClick={() => handleRevokeInvitation(inv.id, inv.email)}
                          className="text-xs font-medium"
                          style={{ color: THEME.danger }}
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
