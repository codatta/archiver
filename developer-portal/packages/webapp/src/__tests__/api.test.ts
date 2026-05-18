import { test, expect, mock, beforeEach } from "bun:test";

// Test the API fetch wrapper logic directly
const API_URL = "http://localhost:8000";

function createApiFetch(getToken: () => string | null) {
  return async function apiFetch<T = unknown>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    const token = getToken();
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error((body as Record<string, string>).detail ?? res.statusText);
    }

    return res.json() as Promise<T>;
  };
}

test("apiFetch adds Authorization header when token exists", async () => {
  const calls: Request[] = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = mock(async (input: any, init: any) => {
    const req = new Request(input, init);
    calls.push(req);
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  }) as any;

  const apiFetch = createApiFetch(() => "my-token");
  await apiFetch("/v1/auth/me");

  expect(calls.length).toBe(1);
  expect(calls[0].headers.get("Authorization")).toBe("Bearer my-token");

  globalThis.fetch = originalFetch;
});

test("apiFetch omits Authorization header when no token", async () => {
  const calls: Request[] = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = mock(async (input: any, init: any) => {
    const req = new Request(input, init);
    calls.push(req);
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  }) as any;

  const apiFetch = createApiFetch(() => null);
  await apiFetch("/v1/auth/signin", { method: "POST", body: "{}" });

  expect(calls.length).toBe(1);
  expect(calls[0].headers.get("Authorization")).toBeNull();

  globalThis.fetch = originalFetch;
});

test("apiFetch throws on non-ok response with detail", async () => {
  const originalFetch = globalThis.fetch;

  globalThis.fetch = mock(async () => {
    return new Response(JSON.stringify({ detail: "Invalid login credentials" }), { status: 401 });
  }) as any;

  const apiFetch = createApiFetch(() => null);

  try {
    await apiFetch("/v1/auth/signin", { method: "POST" });
    expect(true).toBe(false); // should not reach
  } catch (e: any) {
    expect(e.message).toBe("Invalid login credentials");
  }

  globalThis.fetch = originalFetch;
});

test("apiFetch constructs correct URL", async () => {
  const calls: string[] = [];
  const originalFetch = globalThis.fetch;

  globalThis.fetch = mock(async (input: any) => {
    calls.push(typeof input === "string" ? input : input.url);
    return new Response(JSON.stringify({}), { status: 200 });
  }) as any;

  const apiFetch = createApiFetch(() => null);
  await apiFetch("/v1/orgs/123/keys");

  expect(calls[0]).toBe("http://localhost:8000/v1/orgs/123/keys");

  globalThis.fetch = originalFetch;
});
