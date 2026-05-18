import React, { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useToast } from "../../lib/toast";

type ApiKey = { id: string; name: string; key_prefix: string; status: "active" | "expired" | "revoked"; expires_at: string | null; last_used_at: string | null; created_at: string; created_by_name?: string | null; subscription_ids?: string[] | null; raw_key?: string };
type OrgSubscription = { id: string; status: string; frontier_id?: string | null; frontier_name?: string | null; verticals?: { id: string; name: string } | null };
const inputCls = "px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";
const EXPIRY_OPTIONS = [{ label: "7d", days: 7 }, { label: "30d", days: 30 }, { label: "90d", days: 90 }, { label: "1y", days: 365 }, { label: "Never", days: null }] as const;

function subDisplayName(s: OrgSubscription): string {
  if (s.verticals?.name) return s.verticals.name;
  if (s.frontier_name) return s.frontier_name;
  if (s.frontier_id) return `Frontier ${s.frontier_id}`;
  return s.id.slice(0, 8);
}

export function ApiKeys() {
  const { orgId } = useAuth();
  const { toast } = useToast();
  const [keys, setKeys] = useState<ApiKey[]>([]); const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false); const [newKeyName, setNewKeyName] = useState(""); const [newKeyExpiry, setNewKeyExpiry] = useState<number | null>(90);
  const [creating, setCreating] = useState(false); const [newRawKey, setNewRawKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false); const [revokeConfirm, setRevokeConfirm] = useState<string | null>(null);
  const [orgSubs, setOrgSubs] = useState<OrgSubscription[]>([]);
  const [selectedSubIds, setSelectedSubIds] = useState<Set<string>>(new Set());
  const [subsLoading, setSubsLoading] = useState(false);

  const fetchKeys = useCallback(async () => {
    if (!orgId) return;
    try { const res = await apiFetch<{ data: ApiKey[] }>(`/v1/orgs/${orgId}/keys`); setKeys(res.data); }
    catch (e: unknown) { toast((e as Error).message ?? "Failed to load keys", "error"); }
    finally { setLoading(false); }
  }, [orgId, toast]);

  useEffect(() => { fetchKeys(); }, [fetchKeys]);

  const fetchSubs = useCallback(async () => {
    if (!orgId) return;
    setSubsLoading(true);
    try {
      const res = await apiFetch<{ data: OrgSubscription[] }>(`/v1/orgs/${orgId}/subscriptions`);
      const active = res.data.filter((s) => s.status === "active");
      setOrgSubs(active);
      setSelectedSubIds(new Set(active.map((s) => s.id)));
    } catch (e: unknown) { toast((e as Error).message ?? "Failed to load subscriptions", "error"); }
    finally { setSubsLoading(false); }
  }, [orgId, toast]);

  function handleOpenCreate() {
    setShowCreate(true);
    fetchSubs();
  }

  function toggleSub(id: string) {
    setSelectedSubIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (selectedSubIds.size === orgSubs.length) setSelectedSubIds(new Set());
    else setSelectedSubIds(new Set(orgSubs.map((s) => s.id)));
  }

  async function handleCreate(e?: React.FormEvent) {
    e?.preventDefault(); if (!newKeyName.trim() || !orgId || selectedSubIds.size === 0) return; setCreating(true);
    try {
      const res = await apiFetch<{ data: ApiKey }>(`/v1/orgs/${orgId}/keys`, { method: "POST", body: JSON.stringify({ name: newKeyName, expires_in_days: newKeyExpiry, subscription_ids: [...selectedSubIds] }) });
      setNewRawKey(res.data.raw_key ?? null); setKeys((p) => [{ ...res.data, raw_key: undefined }, ...p]);
      setShowCreate(false); setNewKeyName(""); toast("API key created");
    } catch (e: unknown) { toast((e as Error).message ?? "Failed to create key", "error"); }
    finally { setCreating(false); }
  }

  async function handleRevoke(keyId: string) {
    if (!orgId) return;
    try {
      await apiFetch(`/v1/orgs/${orgId}/keys/${keyId}/revoke`, { method: "POST" });
      setKeys((p) => p.map((k) => (k.id === keyId ? { ...k, status: "revoked" as const } : k)));
      toast("Key revoked");
    } catch (e: unknown) { toast((e as Error).message ?? "Failed to revoke key", "error"); }
    setRevokeConfirm(null);
  }

  async function handleCopy(text: string) { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }
  function daysUntil(d: string | null) { if (!d) return "Never"; const days = Math.ceil((new Date(d).getTime() - Date.now()) / 86400000); return days < 0 ? "Expired" : `${days}d`; }

  // Build a lookup from subscription ID to display name for key scope tags
  const subNameMap = new Map<string, string>();
  for (const s of orgSubs) subNameMap.set(s.id, subDisplayName(s));

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-[#1B1034]">API Keys</h1>
        <button onClick={handleOpenCreate} className="px-5 py-2.5 text-sm bg-[#1B1034] text-white rounded-none font-medium hover:bg-[#2A1D4E]">+ Create API Key</button>
      </div>
      {newRawKey && (
        <div className="bg-amber-50 border-2 border-amber-400 rounded-none p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-amber-900"><i className="fi fi-ss-lock mr-1.5" />Your new API key</span>
            <button onClick={() => setNewRawKey(null)} className="text-xs text-amber-600 hover:text-amber-800">Dismiss</button>
          </div>
          <div className="flex items-center gap-2 mb-2">
            <code className="text-sm font-mono break-all text-amber-900 flex-1">{newRawKey}</code>
            <button onClick={() => handleCopy(newRawKey)} className="flex-shrink-0 text-xs border border-amber-400 rounded px-3 py-1.5 font-medium hover:bg-amber-100">{copied ? "Copied!" : "Copy"}</button>
          </div>
          <p className="text-xs font-semibold text-amber-800">This key will only be shown once. Copy it now and store it securely — you cannot retrieve it later.</p>
        </div>
      )}
      {showCreate && (
        <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-5 mb-6">
          <form onSubmit={handleCreate} className="space-y-4">
            <input type="text" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} placeholder="Key name" required className={"w-full " + inputCls} />
            <div className="flex gap-2">{EXPIRY_OPTIONS.map((o) => (<button key={o.label} type="button" onClick={() => setNewKeyExpiry(o.days)} className={`px-4 py-2 text-sm rounded-none border ${newKeyExpiry === o.days ? "bg-[#1B1034] text-white border-[#1B1034]" : "border-gray-300 text-gray-500"}`}>{o.label}</button>))}</div>

            {/* Subscription scope checkboxes */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-[#1B1034]">Subscription access</label>
                {orgSubs.length > 1 && (
                  <button type="button" onClick={toggleAll} className="text-xs text-[#834DFB] hover:underline">
                    {selectedSubIds.size === orgSubs.length ? "Deselect all" : "Select all"}
                  </button>
                )}
              </div>
              {subsLoading ? (
                <p className="text-xs text-gray-400 py-2">Loading subscriptions...</p>
              ) : orgSubs.length === 0 ? (
                <p className="text-xs text-gray-400 py-2">No active subscriptions. Subscribe to a domain first.</p>
              ) : (
                <div className="border border-gray-200 rounded-none max-h-48 overflow-y-auto divide-y divide-gray-100">
                  {orgSubs.map((s) => (
                    <label key={s.id} className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={selectedSubIds.has(s.id)}
                        onChange={() => toggleSub(s.id)}
                        className="w-4 h-4 accent-[#834DFB]"
                      />
                      <span className="text-sm text-[#1B1034]">{subDisplayName(s)}</span>
                    </label>
                  ))}
                </div>
              )}
              {orgSubs.length > 0 && selectedSubIds.size === 0 && (
                <p className="text-xs text-red-500 mt-1">Select at least one subscription</p>
              )}
            </div>

            <div className="flex gap-2">
              <button type="button" onClick={() => handleCreate()} disabled={creating || selectedSubIds.size === 0 || orgSubs.length === 0} className="px-5 py-2.5 text-sm bg-[#1B1034] text-white rounded-none font-medium disabled:opacity-50">{creating ? "Creating..." : "Create key"}</button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2.5 text-sm text-gray-400 hover:text-[#834DFB]">Cancel</button>
            </div>
          </form>
        </div>
      )}
      <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none overflow-hidden">
        <table className="w-full">
          <thead><tr className="text-xs text-gray-400 text-left"><th className="px-5 py-3 font-medium">Name</th><th className="px-3 py-3 font-medium">Key</th><th className="px-3 py-3 font-medium">Scope</th><th className="px-3 py-3 font-medium">Status</th><th className="px-3 py-3 font-medium">Expires</th><th className="px-3 py-3 font-medium">Last used</th><th className="px-5 py-3 font-medium text-right"></th></tr></thead>
          <tbody>
            {loading ? <tr><td colSpan={7} className="px-5 py-8 text-center text-sm text-gray-300">Loading...</td></tr>
            : keys.length === 0 ? <tr><td colSpan={7} className="px-5 py-8 text-center text-sm text-gray-300">No API keys yet.</td></tr>
            : keys.map((k) => (
              <tr key={k.id} className="border-t border-[#1B1034] hover:bg-gray-50">
                <td className="px-5 py-4"><p className="text-sm font-medium text-[#1B1034]">{k.name}</p><p className="text-xs text-gray-400">{new Date(k.created_at).toLocaleDateString()}{k.created_by_name ? <span> · <i className="fi fi-ss-user" style={{ fontSize: 10 }} /> {k.created_by_name}</span> : null}</p></td>
                <td className="px-3 py-4"><code className="text-sm font-mono text-gray-400">{k.key_prefix.slice(0, 14)}{"••••••"}</code></td>
                <td className="px-3 py-4">
                  {!k.subscription_ids ? (
                    <span className="text-xs text-gray-400">All</span>
                  ) : (
                    <div className="flex flex-wrap gap-1">
                      {k.subscription_ids.map((sid) => (
                        <span key={sid} className="inline-block px-2 py-0.5 text-xs bg-[#E8E0F0] text-[#1B1034] rounded-sm">{subNameMap.get(sid) || sid.slice(0, 8)}</span>
                      ))}
                    </div>
                  )}
                </td>
                <td className="px-3 py-4"><span className={`text-sm font-medium ${k.status === "active" ? "text-[#834DFB]" : "text-gray-400"}`}>{k.status}</span></td>
                <td className="px-3 py-4 text-sm text-gray-400">{daysUntil(k.expires_at)}</td>
                <td className="px-3 py-4 text-sm text-gray-400">{k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : "Never"}</td>
                <td className="px-5 py-4 text-right">{k.status === "active" && (revokeConfirm === k.id ? <span className="flex gap-2 justify-end"><button onClick={() => handleRevoke(k.id)} className="text-sm text-red-500 font-medium">Yes</button><button onClick={() => setRevokeConfirm(null)} className="text-sm text-gray-400">No</button></span> : <button onClick={() => setRevokeConfirm(k.id)} className="text-sm text-red-500 font-medium">Revoke</button>)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
