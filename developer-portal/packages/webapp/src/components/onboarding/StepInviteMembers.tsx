import React, { useState } from "react";
import { apiFetch } from "../../lib/api";
import { useEmailCheck } from "../../lib/useEmailCheck";

type Invite = { email: string; role: "admin" | "member" };
type Props = { orgId: string; onDone: () => void };
const inputCls = "px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";

export function StepInviteMembers({ orgId, onDone }: Props) {
  const [invites, setInvites] = useState<Invite[]>([{ email: "", role: "member" }]);
  const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  const { statuses: emailStatuses, checkEmail } = useEmailCheck(orgId);

  async function handleSubmit() {
    setError(""); const valid = invites.filter((i) => i.email.trim());
    if (valid.length === 0) { onDone(); return; }
    setLoading(true);
    try { await apiFetch("/v1/onboarding/invite", { method: "POST", body: JSON.stringify({ org_id: orgId, invites: valid }) }); onDone(); } catch (err: any) { setError(err.message); } finally { setLoading(false); }
  }

  return (
    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="space-y-4">
      <p className="text-sm text-gray-400">Add colleagues who need access. You can always do this later.</p>
      {invites.map((inv, i) => (
        <div key={i}>
          <div className="flex items-center gap-2">
            <input type="email" value={inv.email} onChange={(e) => setInvites((p) => p.map((x, j) => (j === i ? { ...x, email: e.target.value } : x)))} onBlur={() => { if (inv.email.trim()) checkEmail(inv.email.trim()); }} placeholder="email@company.com" className={"flex-1 " + inputCls} />
            <select value={inv.role} onChange={(e) => setInvites((p) => p.map((x, j) => (j === i ? { ...x, role: e.target.value as Invite["role"] } : x)))} className={inputCls}><option value="admin">Admin</option><option value="member">Member</option></select>
            {invites.length > 1 && <button type="button" onClick={() => setInvites((p) => p.filter((_, j) => j !== i))} className="text-gray-300 hover:text-red-500 text-lg">&times;</button>}
          </div>
          {inv.email.trim() && emailStatuses[inv.email.trim().toLowerCase()] === "existing" && (
            <span className="text-xs text-green-600 ml-1">Existing user — will be added directly</span>
          )}
          {inv.email.trim() && emailStatuses[inv.email.trim().toLowerCase()] === "new" && (
            <span className="text-xs text-gray-400 ml-1">New user — will receive signup invitation</span>
          )}
        </div>
      ))}
      <button type="button" onClick={() => setInvites((p) => [...p, { email: "", role: "member" }])} className="text-sm text-[#834DFB] font-medium">+ Add another</button>
      {error && <p className="text-sm text-red-500">{error}</p>}
      <div className="flex gap-3">
        <button type="button" onClick={handleSubmit} disabled={loading} className="flex-1 py-2.5 bg-[#1B1034] text-white rounded-none text-sm font-medium hover:bg-[#2A1D4E] disabled:opacity-50">{loading ? "Sending..." : "Send invites & continue"}</button>
        <button type="button" onClick={onDone} className="px-4 py-2.5 text-sm text-gray-400 hover:text-[#834DFB]">Do this later</button>
      </div>
    </form>
  );
}
