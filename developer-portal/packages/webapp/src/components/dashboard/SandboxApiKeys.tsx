import React, { useState } from "react";
import { useSandboxApiKeys } from "../../lib/useSandboxState";
import { THEME } from "../../lib/config";

const inputCls = "px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";

export function SandboxApiKeys() {
  const { keys, createKey, revokeKey } = useSandboxApiKeys();
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newRawKey, setNewRawKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [revokeConfirm, setRevokeConfirm] = useState<string | null>(null);

  function handleCreate(e?: React.FormEvent) {
    e?.preventDefault();
    if (!newKeyName.trim()) return;
    const created = createKey(newKeyName.trim());
    setNewRawKey(created.key);
    setShowCreate(false);
    setNewKeyName("");
  }

  async function handleCopy(text: string) {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleRevoke(id: string) {
    revokeKey(id);
    setRevokeConfirm(null);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-[#1B1034]">API Keys</h1>
        <button onClick={() => setShowCreate(true)} className="px-5 py-2.5 text-sm bg-[#1B1034] text-white rounded-none font-medium hover:bg-[#2A1D4E]">+ Create Sandbox Key</button>
      </div>

      {/* Sandbox banner */}
      <div className="flex items-center gap-2 px-4 py-2.5 mb-6 border-[1.5px]" style={{ borderColor: THEME.accent, background: THEME.accentLight }}>
        <i className="fi fi-ss-flask text-sm" style={{ color: THEME.accent }} />
        <span className="text-xs" style={{ color: THEME.accent }}>
          Sandbox keys are for testing only. They return simulated data and do not authenticate against the production API.
        </span>
      </div>

      {/* New key reveal */}
      {newRawKey && (
        <div className="bg-amber-50 border-2 border-amber-400 rounded-none p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-amber-900"><i className="fi fi-ss-lock mr-1.5" />Your new sandbox key</span>
            <button onClick={() => setNewRawKey(null)} className="text-xs text-amber-600 hover:text-amber-800">Dismiss</button>
          </div>
          <div className="flex items-center gap-2 mb-2">
            <code className="text-sm font-mono break-all text-amber-900 flex-1">{newRawKey}</code>
            <button onClick={() => handleCopy(newRawKey)} className="flex-shrink-0 text-xs border border-amber-400 rounded px-3 py-1.5 font-medium hover:bg-amber-100">{copied ? "Copied!" : "Copy"}</button>
          </div>
          <p className="text-xs font-semibold text-amber-800">Copy this key now — you won't see it again.</p>
        </div>
      )}

      {/* Create form */}
      {showCreate && (
        <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-5 mb-6">
          <form onSubmit={handleCreate} className="space-y-4">
            <input type="text" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} placeholder="Key name (e.g. my-app)" required className={"w-full " + inputCls} />
            <p className="text-xs" style={{ color: THEME.textMuted }}>Key will be named "{newKeyName ? `${newKeyName}-sandbox` : "...-sandbox"}"</p>
            <div className="flex gap-2">
              <button type="button" onClick={() => handleCreate()} className="px-5 py-2.5 text-sm bg-[#1B1034] text-white rounded-none font-medium">Create key</button>
              <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2.5 text-sm text-gray-400 hover:text-[#834DFB]">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Key table */}
      <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="text-xs text-gray-400 text-left">
              <th className="px-5 py-3 font-medium">Name</th>
              <th className="px-3 py-3 font-medium">Key</th>
              <th className="px-3 py-3 font-medium">Created</th>
              <th className="px-5 py-3 font-medium text-right"></th>
            </tr>
          </thead>
          <tbody>
            {keys.length === 0 ? (
              <tr><td colSpan={4} className="px-5 py-8 text-center text-sm text-gray-300">No sandbox keys yet.</td></tr>
            ) : keys.map((k) => (
              <tr key={k.id} className="border-t border-[#1B1034] hover:bg-gray-50">
                <td className="px-5 py-4">
                  <p className="text-sm font-medium text-[#1B1034]">{k.name}</p>
                </td>
                <td className="px-3 py-4">
                  <code className="text-sm font-mono text-gray-400">{k.key.slice(0, 18)}{"••••••"}</code>
                </td>
                <td className="px-3 py-4 text-sm text-gray-400">
                  {new Date(k.created_at).toLocaleDateString()}
                </td>
                <td className="px-5 py-4 text-right">
                  {revokeConfirm === k.id ? (
                    <span className="flex gap-2 justify-end">
                      <button onClick={() => handleRevoke(k.id)} className="text-sm text-red-500 font-medium">Yes</button>
                      <button onClick={() => setRevokeConfirm(null)} className="text-sm text-gray-400">No</button>
                    </span>
                  ) : (
                    <button onClick={() => setRevokeConfirm(k.id)} className="text-sm text-red-500 font-medium">Revoke</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
