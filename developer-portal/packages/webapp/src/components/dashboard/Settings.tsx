import React, { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useToast } from "../../lib/toast";
import { navigate } from "../../App";

type Org = { id: string; name: string; slug: string; business_url: string | null; industry: string | null; company_size: string | null; billing_email: string | null };
const inputCls = "w-full px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";

export function Settings() {
  const { orgId } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false); const [saved, setSaved] = useState(false);
  const [name, setName] = useState(""); const [slug, setSlug] = useState(""); const [website, setWebsite] = useState("");
  const [industry, setIndustry] = useState(""); const [companySize, setCompanySize] = useState(""); const [billingEmail, setBillingEmail] = useState("");
  const [org, setOrg] = useState<Org | null>(null); const [showDelete, setShowDelete] = useState(false); const [deleteInput, setDeleteInput] = useState(""); const [deleting, setDeleting] = useState(false);

  const fetchOrg = useCallback(async () => {
    if (!orgId) return;
    try {
      const r = await apiFetch<{ data: Org }>(`/v1/orgs/${orgId}`);
      const o = r.data; setOrg(o); setName(o.name); setSlug(o.slug); setWebsite(o.business_url ?? ""); setIndustry(o.industry ?? ""); setCompanySize(o.company_size ?? ""); setBillingEmail(o.billing_email ?? "");
    } catch (e: unknown) { toast((e as Error).message ?? "Failed to load settings", "error"); }
    finally { setLoading(false); }
  }, [orgId, toast]);

  useEffect(() => { fetchOrg(); }, [fetchOrg]);

  async function handleSave(e?: React.FormEvent) {
    e?.preventDefault(); if (!orgId) return; setSaving(true); setSaved(false);
    try {
      await apiFetch(`/v1/orgs/${orgId}`, { method: "PATCH", body: JSON.stringify({ name, slug, business_url: website || null, industry: industry || null, company_size: companySize || null, billing_email: billingEmail || null }) });
      setSaved(true); setTimeout(() => setSaved(false), 2000); toast("Settings saved");
    } catch (e: unknown) { toast((e as Error).message ?? "Failed to save", "error"); }
    finally { setSaving(false); }
  }

  async function handleDelete() {
    if (deleteInput !== org?.name || !orgId) return; setDeleting(true);
    try { await apiFetch(`/v1/orgs/${orgId}`, { method: "DELETE" }); navigate("/"); }
    catch (e: unknown) { toast((e as Error).message ?? "Failed to delete organization", "error"); setDeleting(false); }
  }

  if (loading) return <div className="text-sm text-gray-300">Loading...</div>;

  return (
    <div>
      <h1 className="text-2xl font-semibold text-[#1B1034] mb-6">Settings</h1>
      <form onSubmit={handleSave} className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6 mb-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-[#1B1034] mb-1.5">Name</label><input type="text" value={name} onChange={(e) => setName(e.target.value)} required className={inputCls} /></div>
          <div><label className="block text-sm font-medium text-[#1B1034] mb-1.5">Slug</label><div className="flex items-center gap-1"><span className="text-sm text-gray-400">humanbased.ai/</span><input type="text" value={slug} onChange={(e) => setSlug(e.target.value)} required className={inputCls.replace("w-full ", "") + " flex-1"} /></div></div>
        </div>
        <div><label className="block text-sm font-medium text-[#1B1034] mb-1.5">Website</label><input type="url" value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://" className={inputCls} /></div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium text-[#1B1034] mb-1.5">Industry</label><select value={industry} onChange={(e) => setIndustry(e.target.value)} className={inputCls}><option value="">Select...</option><option>AI / Machine Learning</option><option>Fintech</option><option>Crypto / Web3</option><option>E-commerce</option><option>SaaS</option><option>Other</option></select></div>
          <div><label className="block text-sm font-medium text-[#1B1034] mb-1.5">Size</label><select value={companySize} onChange={(e) => setCompanySize(e.target.value)} className={inputCls}><option value="">Select...</option><option>1-10</option><option>11-50</option><option>51-200</option><option>201-1000</option><option>1000+</option></select></div>
        </div>
        <div><label className="block text-sm font-medium text-[#1B1034] mb-1.5">Billing email</label><input type="email" value={billingEmail} onChange={(e) => setBillingEmail(e.target.value)} className={inputCls} /></div>
        <button type="button" onClick={() => handleSave()} disabled={saving} className="px-5 py-2.5 text-sm bg-[#1B1034] text-white rounded-none font-medium hover:bg-[#2A1D4E] disabled:opacity-50">{saving ? "Saving..." : saved ? "Saved!" : "Save changes"}</button>
      </form>
      <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6 border border-red-100">
        <h3 className="text-sm font-semibold text-red-600 mb-2">Danger Zone</h3>
        <p className="text-xs text-gray-500 mb-3">Delete this organization permanently.</p>
        {showDelete ? (
          <div className="space-y-3"><p className="text-xs text-red-600">Type <strong>{org?.name}</strong> to confirm:</p><input type="text" value={deleteInput} onChange={(e) => setDeleteInput(e.target.value)} className="w-full px-4 py-2 border border-red-200 rounded-none text-sm" placeholder={org?.name} /><div className="flex gap-2"><button onClick={handleDelete} disabled={deleting || deleteInput !== org?.name} className="px-4 py-2 text-sm bg-red-600 text-white rounded-none disabled:opacity-50">{deleting ? "Deleting..." : "Delete"}</button><button onClick={() => { setShowDelete(false); setDeleteInput(""); }} className="px-4 py-2 text-sm text-gray-400">Cancel</button></div></div>
        ) : <button onClick={() => setShowDelete(true)} className="px-4 py-2 text-sm border border-red-200 text-red-600 rounded-none hover:bg-red-50">Delete organization</button>}
      </div>
    </div>
  );
}
