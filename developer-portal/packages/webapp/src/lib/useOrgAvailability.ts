import { useEffect, useRef, useState } from "react";
import {
  buildCheckUrl,
  parseCheckResponse,
  shouldCheck,
  type FieldStatus,
  type OrgAvailability,
} from "./orgAvailability";
import { apiFetch } from "./api";

const DEBOUNCE_MS = 400;

/**
 * Debounced, race-safe availability check for org name + slug.
 *
 * - Stays "idle" until both inputs have ≥ 2 chars.
 * - Debounces by DEBOUNCE_MS (400ms) — resets timer on each keystroke.
 * - Uses AbortController to cancel any in-flight request when new input arrives.
 * - Returns { nameStatus, slugStatus } — each "idle"|"checking"|"available"|"taken".
 */
export function useOrgAvailability(
  name: string,
  slug: string,
): OrgAvailability {
  const [nameStatus, setNameStatus] = useState<FieldStatus>("idle");
  const [slugStatus, setSlugStatus] = useState<FieldStatus>("idle");
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // Cancel any pending request from a previous render
    abortRef.current?.abort();

    if (!shouldCheck(name, slug)) {
      setNameStatus("idle");
      setSlugStatus("idle");
      return;
    }

    setNameStatus("checking");
    setSlugStatus("checking");

    const controller = new AbortController();
    abortRef.current = controller;

    const timerId = setTimeout(async () => {
      try {
        const url = buildCheckUrl(name, slug);
        const json = await apiFetch<{
          name_available: boolean;
          slug_available: boolean;
        }>(url, { signal: controller.signal });

        const { nameAvailable, slugAvailable } = parseCheckResponse(json);
        setNameStatus(nameAvailable ? "available" : "taken");
        setSlugStatus(slugAvailable ? "available" : "taken");
      } catch (err: unknown) {
        // Ignore abort errors — a new check is already in flight
        if (err instanceof Error && err.name === "AbortError") return;
        // Network/parse error — reset to idle so user can retry
        setNameStatus("idle");
        setSlugStatus("idle");
      }
    }, DEBOUNCE_MS);

    return () => {
      clearTimeout(timerId);
      controller.abort();
    };
  }, [name, slug]);

  return { nameStatus, slugStatus };
}
