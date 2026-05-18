import { readConfig, writeConfig } from "./config";
import { apiFetch, publicFetch } from "./api";

// ─── Auth ────────────────────────────────────────────

export async function authSetKey(key: string) {
  if (!key.startsWith("hb_live_sk_")) {
    console.error("Invalid key format. Keys start with hb_live_sk_");
    process.exit(1);
  }
  const config = await readConfig();
  config.api_key = key;
  await writeConfig(config);
  console.log("API key saved to ~/.humanbased/config.json");
}

export async function authWhoami() {
  const data = await apiFetch<{ org_id: string; key_name: string }>("/v1/auth/verify-key", { method: "POST" });
  console.log(`  Org:  ${data.org_id}`);
  console.log(`  Key:  ${data.key_name}`);
}

// ─── Verticals ───────────────────────────────────────

export async function verticalsList() {
  const res = await publicFetch<{ data: { slug: string; name: string; description: string; base_price_usd: number }[] }>("/v1/data/verticals");
  if (res.data.length === 0) {
    console.log("No verticals available.");
    return;
  }
  console.log("");
  for (const v of res.data) {
    console.log(`  ${v.name}`);
    console.log(`    slug: ${v.slug}  |  price: $${v.base_price_usd}/item`);
    console.log(`    ${v.description}`);
    console.log("");
  }
}

export async function verticalTopics(slug: string) {
  // First get vertical ID from slug
  const vRes = await publicFetch<{ data: { id: string; slug: string }[] }>("/v1/data/verticals");
  const vertical = vRes.data.find((v) => v.slug === slug);
  if (!vertical) {
    console.error(`Vertical "${slug}" not found.`);
    process.exit(1);
  }
  const res = await publicFetch<{ data: { slug: string; name: string; description: string }[] }>(`/v1/verticals/${vertical.id}/topics`);
  if (res.data.length === 0) {
    console.log("No topics in this vertical.");
    return;
  }
  console.log("");
  for (const t of res.data) {
    console.log(`  ${t.name}  (${t.slug})`);
    console.log(`    ${t.description}`);
    console.log("");
  }
}

// ─── Subscriptions ───────────────────────────────────

export async function subscriptionsList() {
  // Uses the dashboard API (needs JWT), but for CLI we use key-based
  // For now, list deliveries as a proxy
  const res = await apiFetch<{ data: { id: string; status: string; total_items: number; created_at: string }[] }>("/v1/data/deliveries");
  if (res.data.length === 0) {
    console.log("No deliveries found.");
    return;
  }
  console.log("");
  for (const d of res.data) {
    console.log(`  ${d.id}  status:${d.status}  items:${d.total_items}  ${d.created_at}`);
  }
  console.log("");
}

// ─── Data ────────────────────────────────────────────

export async function dataPull(subscriptionId: string, limit: number) {
  const res = await apiFetch<{ data: Record<string, unknown>[]; count: number }>(`/v1/data/pull?subscription_id=${subscriptionId}&limit=${limit}`);
  console.log(JSON.stringify(res.data, null, 2));
  console.error(`\n  ${res.count} items returned.`);
}

export async function dataAdopt(itemId: string) {
  const res = await apiFetch<{ ok: boolean; status: string }>(`/v1/data/items/${itemId}/adopt`, { method: "POST" });
  console.log(`  Item ${itemId}: ${res.status}`);
}

export async function dataDispute(itemId: string) {
  const res = await apiFetch<{ ok: boolean; status: string }>(`/v1/data/items/${itemId}/dispute`, { method: "POST" });
  console.log(`  Item ${itemId}: ${res.status}`);
}

// ─── Frontiers (live production data) ────────────────

type FrontierSummary = {
  frontier_id: string;
  title: string;
  status: string;
  task_count: number;
  total_submissions: number;
};

type TaskSummary = {
  task_id: string;
  name: string;
  task_type: string;
  status: string;
  submission_count: number;
};

export async function frontiersList(status: string) {
  const res = await publicFetch<{ data: FrontierSummary[] }>(`/v1/frontiers?status=${status}`);
  if (res.data.length === 0) {
    console.log("No frontiers found.");
    return;
  }
  console.log("");
  for (const f of res.data) {
    const badge = f.status === "ONLINE" ? "[LIVE]" : "[HIST]";
    console.log(`  ${badge} ${f.title}`);
    console.log(`    id: ${f.frontier_id}  |  tasks: ${f.task_count}  |  submissions: ${formatNumber(f.total_submissions)}`);
    console.log("");
  }
}

export async function frontierTasks(frontierId: string) {
  const res = await publicFetch<{ data: TaskSummary[] }>(`/v1/frontiers/${frontierId}/tasks`);
  if (res.data.length === 0) {
    console.log("No tasks found for this frontier.");
    return;
  }
  console.log("");
  for (const t of res.data) {
    console.log(`  ${t.name}  (${t.task_type})`);
    console.log(`    id: ${t.task_id}  |  status: ${t.status}  |  submissions: ${formatNumber(t.submission_count)}`);
    console.log("");
  }
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

// ─── Live Data ───────────────────────────────────────

type LiveSubmission = {
  submission_id: string;
  task_id: string;
  data: unknown;
  quality_score: number;
  quality_grade: string;
  source: string;
  created_at: string | null;
  consumer_feedback: string | null;
};

export async function livePull(subscriptionId: string, limit: number, cursor?: string) {
  let url = `/v1/live/pull?subscription_id=${subscriptionId}&limit=${limit}`;
  if (cursor) url += `&cursor=${cursor}`;
  const res = await apiFetch<{ data: LiveSubmission[]; next_cursor: string; has_more: boolean; count: number }>(url);
  console.log(JSON.stringify(res.data, null, 2));
  console.error(`\n  ${res.count} items returned. has_more: ${res.has_more}. next_cursor: ${res.next_cursor}`);
}

export async function liveAdopt(submissionId: string, subscriptionId: string) {
  const res = await apiFetch<{ ok: boolean; submission_id: string; feedback: string }>(
    `/v1/live/items/${submissionId}/adopt`,
    { method: "POST", body: JSON.stringify({ subscription_id: subscriptionId }) },
  );
  console.log(`  ${res.submission_id}: ${res.feedback}`);
}

export async function liveDispute(submissionId: string, subscriptionId: string, reason?: string) {
  const res = await apiFetch<{ ok: boolean; submission_id: string; feedback: string }>(
    `/v1/live/items/${submissionId}/dispute`,
    { method: "POST", body: JSON.stringify({ subscription_id: subscriptionId, reason }) },
  );
  console.log(`  ${res.submission_id}: ${res.feedback}`);
}

// ─── Billing ─────────────────────────────────────────

export async function billingBalance() {
  console.log("  Balance check requires the dashboard. Visit: https://developer.humanbased.ai");
}
