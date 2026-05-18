import { readConfig, getApiUrl } from "./config";

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const config = await readConfig();
  if (!config.api_key) {
    console.error("No API key configured. Run: hb auth set-key <your-key>");
    process.exit(1);
  }

  const url = getApiUrl(config);
  const res = await fetch(`${url}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${config.api_key}`,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = (body as Record<string, string>).detail ?? res.statusText;
    console.error(`Error: ${msg}`);
    process.exit(1);
  }

  return res.json() as Promise<T>;
}

/** Fetch without API key (public endpoints) */
export async function publicFetch<T = unknown>(path: string): Promise<T> {
  const config = await readConfig();
  const url = getApiUrl(config);
  const res = await fetch(`${url}${path}`);
  if (!res.ok) {
    console.error(`Error: ${res.statusText}`);
    process.exit(1);
  }
  return res.json() as Promise<T>;
}
