/**
 * Pure helpers for org name/slug availability checking.
 * Exported so they can be unit tested independently of the hook.
 */

/** Build the query URL for the availability endpoint. */
export function buildCheckUrl(name: string, slug: string): string {
  const params = new URLSearchParams({
    name: name.trim(),
    slug: slug.trim(),
  });
  return `/v1/onboarding/org/check?${params.toString()}`;
}

/** Parse the raw API JSON into a typed result. */
export function parseCheckResponse(json: {
  name_available: boolean;
  slug_available: boolean;
}): { nameAvailable: boolean; slugAvailable: boolean } {
  return {
    nameAvailable: json.name_available,
    slugAvailable: json.slug_available,
  };
}

/**
 * Guard: only trigger a check when both inputs have meaningful length.
 * Prevents a network call on every keystroke at the start of typing.
 */
export function shouldCheck(name: string, slug: string): boolean {
  return name.trim().length >= 2 && slug.trim().length >= 2;
}

// ── Status types ───────────────────────────────────────────────────────────

export type FieldStatus = "idle" | "checking" | "available" | "taken";

export interface OrgAvailability {
  nameStatus: FieldStatus;
  slugStatus: FieldStatus;
}
