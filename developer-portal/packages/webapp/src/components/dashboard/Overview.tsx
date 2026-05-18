import React, { useCallback, useEffect, useRef, useState } from "react";
import type { AnnotationItem } from "@humanbased/shared";
import { supabase } from "../../lib/supabase";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { THEME } from "../../lib/config";
import { StatCards } from "./StatCards";
import { WaffleChart, type WaffleBlock } from "./WaffleChart";
import { LiveStream } from "./LiveStream";
import { DisputePool } from "./DisputePool";
import { ConfirmModal } from "./ConfirmModal";
import { DataSourceModal, DisconnectModal } from "./DataSourceModal";
import { useFakeProgress, progressLabel } from "../../lib/useFakeProgress";
import { useSandboxSubscriptions, useSandboxApiKeys } from "../../lib/useSandboxState";

// ── Vertical meta ─────────────────────────────────────────────────────────────

export type VerticalMeta = { id: string; slug: string; name: string; icon: string };

const VERTICAL_ICON_MAP: Record<string, string> = {
  crypto_account_annotation: "🏦",
  fashion_item_annotation:   "👕",
  food_product_intelligence: "🍲",
};

// ── Realistic mock payload generators per vertical ───────────────────────────

function mockCryptoPayload() {
  const chains    = ["ethereum", "base", "polygon", "arbitrum", "bsc", "optimism", "solana"];
  const categories = ["dex", "cex", "staking", "bridge", "mixer", "scam", "mev_bot", "vault", "lending", "nft", "cold_storage"];
  const entities  = ["Uniswap", "Coinbase", "Lido", "Stargate", "Unknown", "Binance", "Aave", "Curve"];
  const sources   = ["ground_truth", "machine_learning", "research", "heuristic"];
  const cat = categories[Math.floor(Math.random() * categories.length)];
  const ent = entities[Math.floor(Math.random() * entities.length)];
  const chain = chains[Math.floor(Math.random() * chains.length)];
  return {
    address: `0x${Array.from({ length: 40 }, () => Math.floor(Math.random() * 16).toString(16)).join("")}`,
    chain,
    category: cat,
    entity: `${ent}_${cat}`.toLowerCase().replace(/ /g, "_"),
    source: sources[Math.floor(Math.random() * sources.length)],
    description: `${ent} ${cat} contract on ${chain}`,
  };
}

function mockFashionPayload() {
  const brands      = ["Nike", "Adidas", "Patagonia", "Zara", "Levi's", "Arc'teryx", "Louis Vuitton", "H&M"];
  const categories  = ["sneakers", "jacket", "jeans", "dress", "bag", "coat", "t_shirt", "boots", "activewear"];
  const materials   = ["cotton", "polyester", "leather", "nylon", "recycled_polyester", "denim", "wool", "silk"];
  const tiers       = ["budget", "mid_range", "premium", "luxury", "ultra_luxury"];
  const sustain     = ["A", "B", "C", "D"];
  const brand = brands[Math.floor(Math.random() * brands.length)];
  const cat   = categories[Math.floor(Math.random() * categories.length)];
  return {
    brand,
    product_name: `${brand} ${cat.replace(/_/g, " ")}`,
    category: cat,
    material: materials[Math.floor(Math.random() * materials.length)],
    price_tier: tiers[Math.floor(Math.random() * tiers.length)],
    sustainability_tier: sustain[Math.floor(Math.random() * sustain.length)],
    condition: "new",
  };
}

function mockFoodPayload() {
  const brands      = ["Oatly", "Chobani", "KIND", "Nestle", "Bob's Red Mill", "Organic Valley", "Kellogg's"];
  const categories  = ["dairy", "snacks", "beverages", "pasta_grains", "fresh_produce", "bakery", "sweets", "health_food"];
  const nutriscores = ["A", "B", "C", "D", "E"];
  const brand = brands[Math.floor(Math.random() * brands.length)];
  const cat   = categories[Math.floor(Math.random() * categories.length)];
  return {
    brand,
    product_name: `${brand} ${cat.replace(/_/g, " ")}`,
    category: cat,
    nutriscore: nutriscores[Math.floor(Math.random() * nutriscores.length)],
    nova_group: Math.ceil(Math.random() * 4),
    ingredients_count: Math.floor(Math.random() * 20) + 1,
  };
}

const MOCK_PAYLOAD_BY_SLUG: Record<string, () => Record<string, unknown>> = {
  crypto_account_annotation: mockCryptoPayload,
  fashion_item_annotation:   mockFashionPayload,
  food_product_intelligence: mockFoodPayload,
};

// ── Sample-based simulator ───────────────────────────────────────────────────

type SampleItem = {
  payload: Record<string, unknown>;
  quality_score: number;
  quality_method: string;
  validator_count: number;
  consensus_ratio: number;
  unit_price_usd: number;
};

function mockItemForVertical(v: VerticalMeta, samples?: SampleItem[]): AnnotationItem {
  // Use a real sample if available, otherwise fall back to mock generators
  if (samples && samples.length > 0) {
    const sample = samples[Math.floor(Math.random() * samples.length)];
    return {
      id: crypto.randomUUID(),
      delivery_id: null,
      vertical_id: v.id,
      topic_id: null,
      payload: sample.payload,
      quality_score: sample.quality_score,
      quality_method: sample.quality_method,
      validator_count: sample.validator_count,
      consensus_ratio: sample.consensus_ratio,
      unit_price_usd: sample.unit_price_usd,
      task_id: null,
      cf_id: null,
      created_at: new Date().toISOString(),
      vertical_slug: v.slug,
      topic_name: v.name,
      status: "pending",
    };
  }
  const payloadFn = MOCK_PAYLOAD_BY_SLUG[v.slug] ?? mockCryptoPayload;
  return {
    id: crypto.randomUUID(),
    delivery_id: null,
    vertical_id: v.id,
    topic_id: null,
    payload: payloadFn(),
    quality_score: 0.70 + Math.random() * 0.30,
    quality_method: ["consensus", "expert_review", "single_review"][Math.floor(Math.random() * 3)],
    validator_count: Math.floor(Math.random() * 4) + 1,
    consensus_ratio: 0.70 + Math.random() * 0.30,
    unit_price_usd: Math.random() * 0.08 + 0.01,
    task_id: null,
    cf_id: null,
    created_at: new Date().toISOString(),
    vertical_slug: v.slug,
    topic_name: v.name,
    status: "pending",
  };
}

// ── Block helper ─────────────────────────────────────────────────────────────

function itemToBlock(item: AnnotationItem, verticals: VerticalMeta[]): WaffleBlock {
  const vi = verticals.findIndex((v) => v.slug === item.vertical_slug || v.id === item.vertical_id);
  return {
    id: item.id,
    vertical: vi >= 0 ? vi : 0,
    status: item.status === "accepted" ? "adopted" : item.status === "rejected" ? "disputed" : "pending",
    timestamp: new Date(item.created_at).getTime(),
  };
}

// ── Types ─────────────────────────────────────────────────────────────────────

type DataSource = "simulator" | "production";
type ModalState = { open: false } | { open: true; action: "adopt" | "dispute"; item: AnnotationItem };

// ── DataSourceToggle ──────────────────────────────────────────────────────────

function DataSourceToggle({
  source,
  onRequestSwitch,
}: {
  source: DataSource;
  onRequestSwitch: (to: DataSource) => void;
}) {
  const isProduction = source === "production";
  return (
    <div className="flex items-center gap-2">
      <div
        className="inline-flex border-[1.5px] border-[#1B1034] text-xs font-medium overflow-hidden select-none"
        style={{ borderRadius: 0 }}
      >
        <button
          className="px-3 py-1.5"
          style={{
            background: !isProduction ? THEME.btnBg : "transparent",
            color: !isProduction ? "#fff" : THEME.textSecondary,
            cursor: "default",
          }}
        >
          <i className="fi fi-ss-bolt" /> Simulator
        </button>
        <div style={{ width: 1, background: "#1B1034", opacity: 0.3 }} />
        <button
          onClick={() => !isProduction && onRequestSwitch("production")}
          className="px-3 py-1.5 transition-colors duration-200"
          style={{
            background: isProduction ? THEME.accent : "transparent",
            color: isProduction ? "#fff" : THEME.textSecondary,
            cursor: !isProduction ? "pointer" : "default",
          }}
        >
          🔴 Production
        </button>
      </div>

      {/* Explicit disconnect button — only visible when live */}
      {isProduction && (
        <button
          onClick={() => onRequestSwitch("simulator")}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border-[1.5px] transition-colors hover:bg-red-50"
          style={{ borderColor: THEME.danger, color: THEME.danger, borderRadius: 0 }}
        >
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M1 1L9 9M9 1L1 9" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
          Disconnect
        </button>
      )}

      <style>{`
        @keyframes livePulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
          60%       { box-shadow: 0 0 0 5px rgba(34,197,94,0); }
        }
      `}</style>
    </div>
  );
}

// ── Empty subscriptions nudge ─────────────────────────────────────────────────

function NoSubscriptionsNotice() {
  return (
    <div
      className="flex flex-col items-center justify-center py-16 border-[1.5px] border-dashed"
      style={{ borderColor: THEME.textMuted, color: THEME.textMuted }}
    >
      <i className="fi fi-ss-inbox text-3xl mb-3" style={{ color: THEME.textMuted }} />
      <p className="text-sm font-medium mb-1" style={{ color: THEME.textPrimary }}>No active subscriptions</p>
      <p className="text-xs text-center max-w-xs">
        Go to the <strong>Subscriptions</strong> tab to subscribe to a data vertical.
        Once subscribed, data will flow here automatically.
      </p>
    </div>
  );
}

// ── Overview ──────────────────────────────────────────────────────────────────

export function Overview({ mode = "simulation" }: { mode?: "production" | "simulation" }) {
  const { orgId } = useAuth();
  const sandboxSubs = useSandboxSubscriptions();
  const sandboxKeys = useSandboxApiKeys();
  const isSandboxNoOrg = mode === "simulation" && !orgId;

  // Subscribed verticals (drives everything)
  const [activeVerticals, setActiveVerticals] = useState<VerticalMeta[]>([]);
  const [subCount, setSubCount] = useState(0);
  const [loadingVerticals, setLoadingVerticals] = useState(true);
  const loadProgress = useFakeProgress(!loadingVerticals, 2500);
  const verticalByIdRef = useRef<Map<string, VerticalMeta>>(new Map());

  // Stat card data
  const [balance, setBalance] = useState<string>("$—");
  const [activeKeyCount, setActiveKeyCount] = useState<number | null>(null);
  const [apiKeys, setApiKeys] = useState<{ id: string; name: string; key_prefix: string }[]>([]);

  // Data source: driven by top-bar toggle
  const dataSource: DataSource = mode === "production" ? "production" : "simulator";
  const setDataSource = (_v: DataSource) => {}; // no-op, driven by prop
  const [dsModalOpen, setDsModalOpen] = useState(false);
  const [disconnectModalOpen, setDisconnectModalOpen] = useState(false);
  const [pendingTarget, setPendingTarget] = useState<DataSource | null>(null);

  // Stream state
  const [pendingItems, setPendingItems] = useState<AnnotationItem[]>([]);
  const [disputedItems, setDisputedItems] = useState<AnnotationItem[]>([]);
  const [waffleBlocks, setWaffleBlocks] = useState<WaffleBlock[]>([]);
  const [modal, setModal] = useState<ModalState>({ open: false });
  const [transitioningId, setTransitioningId] = useState<string | null>(null);
  const [newestDisputeId, setNewestDisputeId] = useState<string | null>(null);
  const realtimeChannelRef = useRef<ReturnType<typeof supabase.channel> | null>(null);

  // Sample data for simulator (fetched from real production data)
  const [samplesByVertical, setSamplesByVertical] = useState<Map<string, SampleItem[]>>(new Map());

  // Org settings (auto-adopt hours)
  const [autoAdoptHours, setAutoAdoptHours] = useState(48);
  useEffect(() => {
    if (!orgId) return;
    apiFetch<{ data: { auto_adopt_hours: number } }>(`/v1/orgs/${orgId}/settings`)
      .then((r) => setAutoAdoptHours(r.data.auto_adopt_hours))
      .catch(() => {});
  }, [orgId]);

  // ── Sandbox without org: load verticals from API, use localStorage subs ────
  useEffect(() => {
    if (!isSandboxNoOrg) return;
    setLoadingVerticals(true);

    apiFetch<{ data: { id: string; slug: string; name: string }[] }>("/v1/verticals")
      .then((vRes) => {
        const allVerticals = vRes.data.map((v) => ({
          id: v.id, slug: v.slug, name: v.name,
          icon: VERTICAL_ICON_MAP[v.slug] ?? "📦",
        }));

        // If user has sandbox subscriptions, filter; otherwise show all
        const subSet = new Set(sandboxSubs.subs);
        const active = subSet.size > 0
          ? allVerticals.filter((v) => subSet.has(v.id))
          : allVerticals;

        setActiveVerticals(active);
        setSubCount(active.length);
        verticalByIdRef.current = new Map(active.map((v) => [v.id, v]));

        // Demo stat cards
        setBalance("$50.00");
        setActiveKeyCount(sandboxKeys.keys.length);
        setApiKeys([]);
      })
      .catch(() => {
        // Fallback: hardcoded demo verticals
        const demo: VerticalMeta[] = [
          { id: "demo-crypto", slug: "crypto_account_annotation", name: "Crypto Account Annotation", icon: "fi fi-ss-wallet" },
          { id: "demo-fashion", slug: "fashion_item_annotation", name: "Fashion Item Annotation", icon: "fi fi-ss-shirt" },
          { id: "demo-food", slug: "food_product_intelligence", name: "Food Product Intelligence", icon: "fi fi-ss-plate-utensils" },
        ];
        setActiveVerticals(demo);
        setSubCount(demo.length);
        verticalByIdRef.current = new Map(demo.map((v) => [v.id, v]));
        setBalance("$50.00");
        setActiveKeyCount(0);
        setApiKeys([]);
      })
      .finally(() => setLoadingVerticals(false));
  }, [isSandboxNoOrg, sandboxSubs.subs, sandboxKeys.keys.length]);

  // ── Fetch subscribed verticals (org mode) ─────────────────────────────────
  useEffect(() => {
    if (!orgId || isSandboxNoOrg) return;
    setLoadingVerticals(true);

    Promise.all([
      apiFetch<{ data: { id: string; slug: string; name: string }[] }>("/v1/verticals"),
      apiFetch<{ data: { id: string; vertical_id: string; status: string }[] }>(`/v1/orgs/${orgId}/subscriptions`),
      apiFetch<{ data: { id: string; name: string; key_prefix: string; status: string }[] }>(`/v1/orgs/${orgId}/keys`),
      apiFetch<{ data: { balance_available_usd: number } }>(`/v1/orgs/${orgId}/billing/balance`).catch(() => null),
    ])
      .then(([vRes, sRes, kRes, bRes]) => {
        const verticalMap = new Map(vRes.data.map((v) => [v.id, v]));
        const active = sRes.data
          .filter((s) => s.status === "active")
          .map((s) => {
            const v = verticalMap.get(s.vertical_id);
            if (!v) return null;
            return { id: v.id, slug: v.slug, name: v.name, icon: VERTICAL_ICON_MAP[v.slug] ?? "📦" } satisfies VerticalMeta;
          })
          .filter((v): v is VerticalMeta => v !== null);

        setActiveVerticals(active);
        setSubCount(active.length);
        verticalByIdRef.current = new Map(active.map((v) => [v.id, v]));

        const activeKeys = kRes.data.filter((k) => k.status === "active");
        setActiveKeyCount(activeKeys.length);
        setApiKeys(activeKeys.map((k) => ({ id: k.id, name: k.name, key_prefix: k.key_prefix })));

        if (bRes?.data) {
          const bal = bRes.data.balance_available_usd;
          setBalance(`$${Number(bal).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
        }
      })
      .catch(() => {
        setActiveVerticals([]);
        setSubCount(0);
        setActiveKeyCount(0);
        setApiKeys([]);
        setBalance("$0.00");
      })
      .finally(() => setLoadingVerticals(false));
  }, [orgId, isSandboxNoOrg]);

  // ── Fetch sample data for simulator ────────────────────────────────────────
  useEffect(() => {
    if (activeVerticals.length === 0) return;
    const fetches = activeVerticals.map((v) =>
      apiFetch<{ data: SampleItem[] }>(`/v1/verticals/${v.id}/sample-items?limit=50`)
        .then((res) => [v.id, res.data] as const)
        .catch(() => [v.id, []] as const)
    );
    Promise.all(fetches).then((results) => {
      setSamplesByVertical(new Map(results));
    });
  }, [activeVerticals]);

  // ── addItem ────────────────────────────────────────────────────────────────
  const addItem = useCallback(
    (item: AnnotationItem) => {
      setPendingItems((prev) => [item, ...prev].slice(0, 200));
      setWaffleBlocks((prev) => [...prev, itemToBlock(item, activeVerticals)].slice(-500));
    },
    [activeVerticals],
  );

  // ── Supabase Realtime (production only) ────────────────────────────────────
  useEffect(() => {
    if (dataSource !== "production") {
      if (realtimeChannelRef.current) {
        supabase.removeChannel(realtimeChannelRef.current);
        realtimeChannelRef.current = null;
      }
      return;
    }
    const channel = supabase
      .channel("delivery_items_live")
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "delivery_items" }, (payload) => {
        const raw = payload.new as AnnotationItem;
        // Only process items for this org's subscribed verticals
        if (!verticalByIdRef.current.has(raw.vertical_id)) return;
        // Enrich with vertical slug/name since Realtime only sends the UUID
        const v = verticalByIdRef.current.get(raw.vertical_id);
        const enriched: AnnotationItem = {
          ...raw,
          vertical_slug: v?.slug ?? raw.vertical_slug,
          topic_name: raw.topic_name ?? v?.name,
        };
        addItem(enriched);
      })
      .subscribe();
    realtimeChannelRef.current = channel;
    return () => {
      supabase.removeChannel(channel);
      realtimeChannelRef.current = null;
    };
  }, [dataSource, addItem]);

  // ── Mock simulator (simulator only) — writes to test DB if org, else client-only
  useEffect(() => {
    if (dataSource !== "simulator" || activeVerticals.length === 0) return;
    const interval = setInterval(async () => {
      const v = activeVerticals[Math.floor(Math.random() * activeVerticals.length)];
      const samples = samplesByVertical.get(v.id);
      const mock = mockItemForVertical(v, samples);

      // With org: write to test DB via API
      if (orgId) {
        try {
          const res = await apiFetch<{ data: AnnotationItem; underfunded: boolean }>(
            `/v1/orgs/${orgId}/data/simulate-receive`,
            {
              method: "POST",
              body: JSON.stringify({
                vertical_id: mock.vertical_id,
                payload: mock.payload,
                quality_score: mock.quality_score,
                quality_method: mock.quality_method,
                validator_count: mock.validator_count,
                consensus_ratio: mock.consensus_ratio,
                unit_price_usd: mock.unit_price_usd,
                vertical_slug: mock.vertical_slug,
              }),
            },
          );
          const item: AnnotationItem = {
            ...res.data,
            vertical_slug: v.slug,
            topic_name: v.name,
            status: "pending",
          };
          addItem(item);
        } catch {
          addItem(mock);
        }
      } else {
        // No org: pure client-side mock
        addItem(mock);
      }
    }, 2000 + Math.random() * 3000);
    return () => clearInterval(interval);
  }, [dataSource, activeVerticals, addItem, samplesByVertical, orgId]);

  // ── Data source switch handlers ────────────────────────────────────────────
  function handleRequestSwitch(to: DataSource) {
    if (to === "production") {
      setPendingTarget("production");
      setDsModalOpen(true);
    } else {
      setDisconnectModalOpen(true);
    }
  }

  function handleDsConfirm() {
    setDsModalOpen(false);
    setPendingItems([]);
    setWaffleBlocks([]);
    setDataSource(pendingTarget ?? "production");
    setPendingTarget(null);
  }

  function handleDsCancel() {
    setDsModalOpen(false);
    setPendingTarget(null);
  }

  // ── Adopt / Dispute ────────────────────────────────────────────────────────
  function requestAdopt(id: string) {
    const item = pendingItems.find((i) => i.id === id);
    if (item) setModal({ open: true, action: "adopt", item });
  }
  function requestDispute(id: string) {
    const item = pendingItems.find((i) => i.id === id);
    if (item) setModal({ open: true, action: "dispute", item });
  }
  function closeModal() { setModal({ open: false }); }

  async function confirmAction() {
    if (!modal.open) return;
    const { action, item } = modal;
    closeModal();

    // Call backend if user has an org (items have real DB IDs)
    if (orgId) {
      try {
        const endpoint = action === "adopt"
          ? `/v1/orgs/${orgId}/data/items/${item.id}/adopt`
          : `/v1/orgs/${orgId}/data/items/${item.id}/dispute`;
        await apiFetch(endpoint, { method: "POST" });

        apiFetch<{ data: { balance_available_usd: number } }>(`/v1/orgs/${orgId}/billing/balance`)
          .then((r) => {
            const bal = r.data.balance_available_usd;
            setBalance(`$${Number(bal).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
          })
          .catch(() => {});
      } catch {
        // Best-effort — update UI regardless
      }
    }
    // No org (sandbox): just update UI locally — no backend call

    setTransitioningId(item.id);
    setTimeout(() => {
      setTransitioningId(null);
      if (action === "adopt") {
        setPendingItems((prev) => prev.filter((i) => i.id !== item.id));
        setWaffleBlocks((prev) => prev.map((b) => b.id === item.id ? { ...b, status: "adopted" as const } : b));
      } else {
        setPendingItems((prev) => prev.filter((i) => i.id !== item.id));
        setDisputedItems((prev) => [{ ...item, status: "rejected" as const }, ...prev]);
        setNewestDisputeId(item.id);
        setWaffleBlocks((prev) => prev.map((b) => b.id === item.id ? { ...b, status: "disputed" as const } : b));
        setTimeout(() => setNewestDisputeId(null), 400);
      }
    }, 300);
  }

  const modalItem = modal.open ? modal.item : null;
  const verticalNames = activeVerticals.map((v) => v.name);

  if (loadProgress < 100) {
    return (
      <div className="py-16 px-4 flex justify-center">
        <div className="w-full max-w-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-medium" style={{ color: THEME.textSecondary }}>
              {progressLabel(loadProgress, !loadingVerticals)}
            </span>
            <span className="text-[11px] font-mono" style={{ color: THEME.textMuted }}>
              {Math.round(loadProgress)}%
            </span>
          </div>
          <div className="w-full h-1 bg-[#E8E5ED] overflow-hidden">
            <div
              className="h-full"
              style={{
                width: `${loadProgress}%`,
                background: THEME.btnBg,
                transition: loadProgress >= 100 ? "width 0.3s ease" : "none",
              }}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: "#1B1034" }}>Overview</h1>
          <p className="text-xs mt-0.5" style={{ color: THEME.textMuted }}>
            {dataSource === "simulator"
              ? "Sandbox mode — simulated data, no charges"
              : "Production mode — live data"}
          </p>
        </div>
      </div>

      <StatCards stats={[
        { label: "Balance", value: balance },
        { label: "Active Keys", value: activeKeyCount === null ? "—" : String(activeKeyCount) },
        { label: "Subscriptions", value: String(subCount) },
      ]} />

      {/* No subscriptions nudge */}
      {activeVerticals.length === 0 ? (
        <NoSubscriptionsNotice />
      ) : (
        <>
          {/* Subscribed verticals pill row */}
          {activeVerticals.length > 0 && (
            <div className="flex items-center gap-2 mb-4 flex-wrap">
              <span className="text-xs" style={{ color: THEME.textMuted }}>Streaming:</span>
              {activeVerticals.map((v) => (
                <span
                  key={v.id}
                  className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium"
                  style={{ background: THEME.accentLight, color: THEME.accent, border: `1px solid ${THEME.accent}22` }}
                >
                  {v.icon} {v.name}
                </span>
              ))}
            </div>
          )}

          <div className="mb-6">
            <WaffleChart
              blocks={waffleBlocks}
              verticalNames={verticalNames.length > 0 ? verticalNames : ["—"]}
              bucketMs={10000}
            />
          </div>
          <div className="space-y-4">
            <LiveStream
              items={pendingItems}
              verticals={activeVerticals}
              onAdopt={requestAdopt}
              onDispute={requestDispute}
              transitioningId={transitioningId}
              autoAdoptHours={autoAdoptHours}
            />
            <DisputePool items={disputedItems} newestId={newestDisputeId} />
          </div>
        </>
      )}

      <ConfirmModal
        open={modal.open}
        title={modal.open && modal.action === "adopt" ? "Adopt this item?" : "Dispute this item?"}
        body={
          modal.open && modal.action === "adopt"
            ? <span><strong>${modalItem?.unit_price_usd.toFixed(3)}</strong> will be settled from your frozen balance.</span>
            : <span>This item will be flagged for admin review. Funds stay frozen until resolved.</span>
        }
        confirmLabel={modal.open && modal.action === "adopt" ? "Adopt" : "Dispute"}
        confirmDanger={modal.open && modal.action === "dispute"}
        onConfirm={confirmAction}
        onCancel={closeModal}
      />

      <DataSourceModal
        open={dsModalOpen}
        apiKeys={apiKeys}
        onConfirm={handleDsConfirm}
        onCancel={handleDsCancel}
      />

      <DisconnectModal
        open={disconnectModalOpen}
        onConfirm={() => {
          setDisconnectModalOpen(false);
          setDataSource("simulator");
          setPendingItems([]);
          setWaffleBlocks([]);
        }}
        onCancel={() => setDisconnectModalOpen(false)}
      />
    </div>
  );
}
