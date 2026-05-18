import React, { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";

type Props = { orgId: string; onDone: () => void };

export function StepApiKey({ orgId, onDone }: Props) {
  const [rawKey, setRawKey] = useState<string | null>(null); const [copied, setCopied] = useState(false);
  const [error, setError] = useState(""); const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<{ data: { raw_key: string } }>(`/v1/onboarding/api-key?org_id=${orgId}`, { method: "POST" })
      .then((r) => { setRawKey(r.data.raw_key); setLoading(false); }).catch((e) => { setError(e.message); setLoading(false); });
  }, [orgId]);

  if (loading) return <div className="bg-white rounded-none p-6 text-center text-sm text-gray-300">Generating your API key...</div>;
  if (error) return <div className="space-y-4"><p className="text-sm text-red-500">{error}</p><button onClick={onDone} className="px-5 py-2.5 bg-[#1B1034] text-white rounded-none text-sm font-medium">Continue to Dashboard</button></div>;

  return (
    <div className="space-y-4">
      <div className="bg-amber-50 border-2 border-amber-400 rounded-none p-4">
        <div className="flex items-center gap-2 mb-2">
          <code className="text-sm font-mono break-all text-amber-900 flex-1">{rawKey}</code>
          <button onClick={async () => { if (rawKey) { await navigator.clipboard.writeText(rawKey); setCopied(true); setTimeout(() => setCopied(false), 2000); } }} className="flex-shrink-0 px-3 py-1.5 text-xs font-medium border border-amber-400 rounded hover:bg-amber-100">{copied ? "Copied!" : "Copy"}</button>
        </div>
        <p className="text-xs font-semibold text-amber-800">This key will only be shown once. Copy it now and store it securely — you cannot retrieve it later.</p>
      </div>
      <div className="bg-[#1B1034] text-gray-100 rounded-none p-4 text-xs font-mono space-y-1">
        <p className="text-gray-500"># Quick start</p><p>npm install -g @codatta/cli</p><p>hb auth set-key {rawKey?.slice(0, 20)}...</p><p>hb verticals list</p>
      </div>
      <button onClick={onDone} className="w-full py-2.5 bg-[#1B1034] text-white rounded-none text-sm font-medium hover:bg-[#2A1D4E]">Go to Dashboard</button>
    </div>
  );
}
