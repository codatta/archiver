import React, { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useToast } from "../../lib/toast";
import { THEME } from "../../lib/config";
import { navigate } from "../../App";
import { supabase } from "../../lib/supabase";

const inputCls = "w-full px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";

export function OrgSettings() {
  const { orgId } = useAuth();
  const { toast } = useToast();
  const [name, setName] = useState(""); const [slug, setSlug] = useState("");
  const [orgEmail, setOrgEmail] = useState(""); const [backupEmail, setBackupEmail] = useState("");
  const [saving, setSaving] = useState(false); const [saved, setSaved] = useState(false);
  const [orgEmailError, setOrgEmailError] = useState<string | null>(null);
  const [showDelete, setShowDelete] = useState(false);
  const [deleteInput, setDeleteInput] = useState(""); const [deleting, setDeleting] = useState(false);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [logoUploading, setLogoUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchOrg = useCallback(async () => {
    if (!orgId) return;
    try {
      const r = await apiFetch<{ data: { name: string; slug: string; billing_email: string | null; backup_email: string | null; logo_url: string | null } }>(`/v1/orgs/${orgId}`);
      const o = r.data;
      setName(o.name); setSlug(o.slug); setOrgEmail(o.billing_email ?? ""); setBackupEmail(o.backup_email ?? ""); setLogoUrl(o.logo_url ?? null);
    } catch (e: unknown) { toast((e as Error).message ?? "Failed to load org settings", "error"); }
  }, [orgId, toast]);

  useEffect(() => { fetchOrg(); }, [fetchOrg]);

  async function handleLogoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !orgId) return;
    if (file.size > 2 * 1024 * 1024) { toast("Image must be under 2MB", "error"); return; }
    setLogoUploading(true);
    try {
      const ext = file.name.split(".").pop() ?? "png";
      const path = `${orgId}/logo.${ext}`;
      const { error } = await supabase.storage.from("org-logos").upload(path, file, { upsert: true, contentType: file.type });
      if (error) throw new Error(error.message);
      const { data: urlData } = supabase.storage.from("org-logos").getPublicUrl(path);
      const publicUrl = `${urlData.publicUrl}?t=${Date.now()}`;
      await apiFetch(`/v1/orgs/${orgId}`, { method: "PATCH", body: JSON.stringify({ logo_url: publicUrl }) });
      setLogoUrl(publicUrl);
      toast("Logo updated");
    } catch (err: unknown) {
      toast((err as Error).message ?? "Failed to upload logo", "error");
    } finally {
      setLogoUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleSave(e?: React.FormEvent) {
    e?.preventDefault(); if (!orgId) return;

    setOrgEmailError(null);

    // Trim leading/trailing hyphens from slug on save
    const cleanSlug = slug.replace(/^-+|-+$/g, "");
    if (cleanSlug !== slug) setSlug(cleanSlug);

    setSaving(true); setSaved(false);
    try {
      await apiFetch(`/v1/orgs/${orgId}`, { method: "PATCH", body: JSON.stringify({ name, slug: cleanSlug, billing_email: orgEmail || null, backup_email: backupEmail || null }) });
      setSaved(true); setTimeout(() => setSaved(false), 2000); toast("Organization settings saved");
    } catch (e: unknown) { toast((e as Error).message ?? "Failed to save", "error"); }
    finally { setSaving(false); }
  }

  async function handleDelete() {
    if (deleteInput !== name || !orgId) return; setDeleting(true);
    try { await apiFetch(`/v1/orgs/${orgId}`, { method: "DELETE" }); navigate("/"); }
    catch (e: unknown) { toast((e as Error).message ?? "Failed to delete organization", "error"); setDeleting(false); }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6" style={{ color: THEME.textPrimary }}>Organization Settings</h1>

      {/* Logo */}
      <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6 mb-6">
        <h2 className="text-sm font-semibold mb-4" style={{ color: THEME.textPrimary }}>Organization Logo</h2>
        <div className="flex items-center gap-5">
          <div
            className="w-20 h-20 rounded-none border-[1.5px] border-[#1B1034] overflow-hidden flex items-center justify-center"
            style={{ background: THEME.accentLight }}
          >
            {logoUrl ? (
              <img src={logoUrl} alt="Org logo" className="w-full h-full object-cover" />
            ) : (
              <span className="text-2xl font-bold" style={{ color: THEME.accent }}>
                {name ? name[0].toUpperCase() : "?"}
              </span>
            )}
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="hidden"
              onChange={handleLogoUpload}
            />
            <button
              type="button"
              disabled={logoUploading}
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 text-sm text-white rounded-none font-medium disabled:opacity-50"
              style={{ background: THEME.btnBg }}
            >
              {logoUploading ? "Uploading..." : "Upload logo"}
            </button>
            <p className="text-xs mt-1.5" style={{ color: THEME.textMuted }}>JPG, PNG, WebP or GIF — max 2MB</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSave} className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6 mb-6 space-y-5">
        <h2 className="text-sm font-semibold" style={{ color: THEME.textPrimary }}>General</h2>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium mb-1.5" style={{ color: THEME.textPrimary }}>Organization name</label><input type="text" value={name} onChange={(e) => setName(e.target.value)} className={inputCls} /></div>
          <div><label className="block text-sm font-medium mb-1.5" style={{ color: THEME.textPrimary }}>Slug</label><div className="flex items-center gap-1"><span className="text-sm" style={{ color: THEME.textMuted }}>humanbased.ai/</span><input type="text" value={slug} onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))} className={inputCls.replace("w-full ", "") + " flex-1"} /></div></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-sm font-medium mb-1.5" style={{ color: THEME.textPrimary }}>Organization email</label><input type="email" value={orgEmail} onChange={(e) => { setOrgEmail(e.target.value); setOrgEmailError(null); }} placeholder="team@company.com" className={inputCls} />{orgEmailError && <p className="text-xs mt-1 text-red-600">{orgEmailError}</p>}</div>
          <div><label className="block text-sm font-medium mb-1.5" style={{ color: THEME.textPrimary }}>Backup email</label><input type="email" value={backupEmail} onChange={(e) => setBackupEmail(e.target.value)} placeholder="admin@gmail.com" className={inputCls} /><p className="text-xs mt-1" style={{ color: THEME.textMuted }}>Used for important notifications.</p></div>
        </div>

        <button type="button" onClick={() => handleSave()} disabled={saving} className="px-5 py-2.5 text-sm text-white rounded-none font-medium disabled:opacity-50" style={{ background: THEME.btnBg }}>{saving ? "Saving..." : saved ? "Saved!" : "Save changes"}</button>
      </form>

      <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6" style={{ borderColor: "#FCA5A5" }}>
        <h3 className="text-sm font-semibold mb-2" style={{ color: THEME.danger }}>Danger Zone</h3>
        <p className="text-xs mb-3" style={{ color: THEME.textSecondary }}>Delete this organization permanently. All data, keys, and subscriptions will be removed.</p>
        {showDelete ? (
          <div className="space-y-3">
            <p className="text-xs" style={{ color: THEME.danger }}>Type the organization name to confirm:</p>
            <input type="text" value={deleteInput} onChange={(e) => setDeleteInput(e.target.value)} className="w-full px-4 py-2 border border-red-200 rounded-none text-sm" placeholder={name} />
            <div className="flex gap-2">
              <button onClick={handleDelete} disabled={deleting || deleteInput !== name} className="px-4 py-2 text-sm bg-red-600 text-white rounded-none disabled:opacity-50">{deleting ? "Deleting..." : "Delete"}</button>
              <button onClick={() => { setShowDelete(false); setDeleteInput(""); }} className="px-4 py-2 text-sm" style={{ color: THEME.textMuted }}>Cancel</button>
            </div>
          </div>
        ) : <button onClick={() => setShowDelete(true)} className="px-4 py-2 text-sm border border-red-200 rounded-none hover:bg-red-50" style={{ color: THEME.danger }}>Delete organization</button>}
      </div>
    </div>
  );
}
