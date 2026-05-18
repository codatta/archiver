import React, { useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { supabase } from "../../lib/supabase";
import { slugify } from "../../lib/utils";
import { useOrgAvailability } from "../../lib/useOrgAvailability";
import type { FieldStatus } from "../../lib/orgAvailability";

type Props = {
  onCreated: (orgId: string) => void;
  onSkipped: () => void;
};

const inputCls =
  "w-full px-4 py-2.5 bg-white border-[1.5px] border-[#1B1034] rounded-none text-sm placeholder:text-gray-400 focus:outline-none focus:border-[#834DFB] focus:ring-2 focus:ring-[#834DFB]/10";

function AvailabilityBadge({ status }: { status: FieldStatus }) {
  if (status === "idle") return null;
  if (status === "checking")
    return (
      <p className="text-xs text-gray-400 mt-1" aria-live="polite">
        Checking...
      </p>
    );
  if (status === "available")
    return (
      <p className="text-xs text-emerald-600 mt-1" aria-live="polite">
        ✓ Available
      </p>
    );
  return (
    <p className="text-xs text-red-500 mt-1" aria-live="polite">
      Already in use
    </p>
  );
}

export function StepOrgDetails({ onCreated, onSkipped }: Props) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugManual, setSlugManual] = useState(false);
  const [industry, setIndustry] = useState("");
  const [companySize, setCompanySize] = useState("");
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [logoUploading, setLogoUploading] = useState(false);
  const [logoError, setLogoError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [skipping, setSkipping] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { nameStatus, slugStatus } = useOrgAvailability(name, slug);

  const canSubmit =
    !loading &&
    !logoUploading &&
    nameStatus !== "checking" &&
    slugStatus !== "checking" &&
    nameStatus !== "taken" &&
    slugStatus !== "taken";

  async function handleLogoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLogoError("");

    const allowed = ["image/png", "image/jpeg", "image/svg+xml"];
    if (!allowed.includes(file.type)) {
      setLogoError("PNG, JPG, or SVG only.");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setLogoError("File must be under 2 MB.");
      return;
    }

    setLogoUploading(true);
    const path = `${Date.now()}-${file.name.replace(/[^a-zA-Z0-9._-]/g, "_")}`;
    const { error: uploadErr } = await supabase.storage
      .from("org-logos")
      .upload(path, file, { upsert: false });

    if (uploadErr) {
      setLogoError(uploadErr.message);
      setLogoUploading(false);
      return;
    }

    const { data } = supabase.storage.from("org-logos").getPublicUrl(path);
    setLogoUrl(data.publicUrl);
    setLogoUploading(false);
  }

  async function handleSubmit() {
    setError("");
    if (!name.trim()) {
      setError("Organization name is required");
      return;
    }
    if (!slug.trim()) {
      setError("Slug is required");
      return;
    }
    setLoading(true);
    try {
      const r = await apiFetch<{ data: { id: string } }>("/v1/onboarding/org", {
        method: "POST",
        body: JSON.stringify({
          name,
          slug,
          logo_url: logoUrl ?? undefined,
          industry: industry || undefined,
          company_size: companySize || undefined,
        }),
      });
      onCreated(r.data.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function handleSkip() {
    setSkipping(true);
    try {
      await apiFetch("/v1/onboarding/skip", { method: "POST" });
    } catch {
      // Non-fatal: skip even if the request fails — user can always create org later
    } finally {
      setSkipping(false);
      onSkipped();
    }
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        handleSubmit();
      }}
      className="space-y-4"
    >
      {/* Logo upload */}
      <div>
        <label className="block text-sm font-medium text-[#1B1034] mb-1.5">
          Logo
        </label>
        <input
          ref={fileInputRef}
          type="file"
          accept=".png,.jpg,.jpeg,.svg"
          className="hidden"
          onChange={handleLogoChange}
        />
        <div
          onClick={() => !logoUploading && fileInputRef.current?.click()}
          className="w-20 h-20 border border-dashed border-[#1B1034] rounded-none flex flex-col items-center justify-center text-gray-400 text-xs overflow-hidden hover:border-[#834DFB] transition-colors"
          style={{ cursor: logoUploading ? "wait" : "pointer" }}
        >
          {logoUploading ? (
            <span className="text-xs text-gray-400">Uploading…</span>
          ) : logoUrl ? (
            <img src={logoUrl} alt="org logo" className="w-full h-full object-cover" />
          ) : (
            <>
              <span className="text-lg mb-1">&uarr;</span>Upload logo
            </>
          )}
        </div>
        {logoError && <p className="text-xs text-red-500 mt-1">{logoError}</p>}
        {!logoError && (
          <p className="text-xs text-gray-400 mt-1">PNG, JPG, SVG. Max 2MB.</p>
        )}
      </div>

      {/* Organization name */}
      <div>
        <label className="block text-sm font-medium text-[#1B1034] mb-1.5">
          Organization name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            if (!slugManual) setSlug(slugify(e.target.value));
          }}
          placeholder="Acme AI Labs"
          required
          className={inputCls}
        />
        <AvailabilityBadge status={nameStatus} />
      </div>

      {/* Slug */}
      <div>
        <label className="block text-sm font-medium text-[#1B1034] mb-1.5">
          Slug
        </label>
        <div className="flex items-center gap-1">
          <span className="text-sm text-gray-400">humanbased.ai/</span>
          <input
            type="text"
            value={slug}
            onChange={(e) => {
              setSlugManual(true);
              setSlug(e.target.value);
            }}
            placeholder="acme-ai"
            required
            className={inputCls.replace("w-full ", "") + " flex-1"}
          />
        </div>
        <AvailabilityBadge status={slugStatus} />
      </div>

      {/* Industry + size */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-[#1B1034] mb-1.5">
            Industry
          </label>
          <select
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            className={inputCls}
          >
            <option value="">Select...</option>
            <option>AI / Machine Learning</option>
            <option>Fintech</option>
            <option>Crypto / Web3</option>
            <option>E-commerce</option>
            <option>SaaS</option>
            <option>Other</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-[#1B1034] mb-1.5">
            Size
          </label>
          <select
            value={companySize}
            onChange={(e) => setCompanySize(e.target.value)}
            className={inputCls}
          >
            <option value="">Select...</option>
            <option>1-10</option>
            <option>11-50</option>
            <option>51-200</option>
            <option>201-1000</option>
            <option>1000+</option>
          </select>
        </div>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="w-full py-2.5 bg-[#1B1034] text-white rounded-none text-sm font-medium hover:bg-[#2A1D4E] disabled:opacity-50"
      >
        {loading ? "Creating..." : "Continue"}
      </button>

      <div className="text-center">
        <button
          type="button"
          onClick={handleSkip}
          disabled={skipping}
          className="text-sm text-gray-400 hover:text-[#1B1034] underline-offset-2 hover:underline transition-colors"
        >
          {skipping ? "Skipping..." : "Skip for now"}
        </button>
      </div>
    </form>
  );
}
