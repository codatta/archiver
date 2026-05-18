import React, { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useToast } from "../../lib/toast";
import { THEME } from "../../lib/config";

// ── Types ────────────────────────────────────────────────────────────────────

type Balance = {
  balance_available_usd: number;
  balance_frozen_usd: number;
  balance_spent_usd: number;
  balance_earnings_usd: number;
};
type Transaction = {
  id: string;
  type: string;
  amount_usd: number;
  balance_after_usd: number;
  description?: string;
  reference_id?: string;
  created_at: string;
};

const QUICK = [100, 500, 1000, 5000];
const STORAGE_KEY = "hb_pre_checkout_balance";
const PAGE_SIZE = 20;
const TX_TYPES = ["all", "topup", "freeze", "settle", "refund"] as const;

function fmtFull(n: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}

function fmtShort(n: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
  }).format(n);
}

// ── Animated counter ──────────────────────────────────────────────────────────

function useCountUp(to: number, from: number, durationMs: number, run: boolean): number {
  const [val, setVal] = useState(from);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!run) { setVal(to); return; }
    const start = Date.now();
    const diff = to - from;

    function tick() {
      const elapsed = Date.now() - start;
      const t = Math.min(elapsed / durationMs, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setVal(from + diff * eased);
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    }

    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current !== null) cancelAnimationFrame(rafRef.current); };
  }, [to, from, durationMs, run]);

  return val;
}

// ── AnimatedBalance ───────────────────────────────────────────────────────────

function AnimatedBalance({
  target,
  from,
  animate,
}: {
  target: number;
  from: number;
  animate: boolean;
}) {
  const val = useCountUp(target, from, 1800, animate);
  return (
    <span
      style={{
        display: "inline-block",
        transition: animate ? undefined : "none",
        color: animate ? "#16a34a" : THEME.textPrimary,
      }}
    >
      {fmtFull(val)}
    </span>
  );
}

// ── Success banner ────────────────────────────────────────────────────────────

function SuccessBanner({ amount, onDismiss }: { amount: number; onDismiss: () => void }) {
  return (
    <div
      className="flex items-center justify-between px-5 py-3 mb-6 border-[1.5px]"
      style={{ borderColor: "#16a34a", background: "rgba(34,197,94,0.06)" }}
    >
      <div className="flex items-center gap-3">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="8" fill="#22C55E" fillOpacity="0.15"/>
          <path d="M5 9.5L7.5 12L13 6" stroke="#16a34a" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <div>
          <span className="text-sm font-medium" style={{ color: "#15803d" }}>
            Payment successful — {fmtFull(amount)} added to your balance
          </span>
          <span className="text-xs block" style={{ color: "#16a34a" }}>
            Your account has been credited immediately.
          </span>
        </div>
      </div>
      <button onClick={onDismiss} className="w-5 h-5 flex items-center justify-center opacity-50 hover:opacity-100" style={{ color: "#15803d" }}>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <path d="M1 1L11 11M11 1L1 11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
        </svg>
      </button>
    </div>
  );
}

// ── Transaction type badge styles ─────────────────────────────────────────────

const TX_BADGE: Record<string, { background: string; color: string }> = {
  topup:  { background: "rgba(34,197,94,0.1)",  color: "#15803d" },
  freeze: { background: "rgba(245,158,11,0.1)", color: "#B45309" },
  settle: { background: "rgba(139,92,246,0.1)", color: "#7C3AED" },
  refund: { background: "rgba(59,130,246,0.1)", color: "#2563EB" },
};

function txBadgeStyle(type: string): React.CSSProperties {
  return TX_BADGE[type] ?? { background: "rgba(107,114,128,0.1)", color: "#6B7280" };
}

// ── Pagination ────────────────────────────────────────────────────────────────

function Pagination({ page, totalPages, onPageChange }: { page: number; totalPages: number; onPageChange: (p: number) => void }) {
  if (totalPages <= 1) return null;
  return (
    <div className="flex items-center justify-between px-5 py-3" style={{ borderTop: `1.5px solid ${THEME.border}` }}>
      <span className="text-xs" style={{ color: THEME.textMuted }}>
        Page {page} of {totalPages}
      </span>
      <div className="flex gap-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1 text-xs border-[1.5px] disabled:opacity-30"
          style={{ borderColor: THEME.border, color: THEME.textSecondary }}
        >
          Previous
        </button>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1 text-xs border-[1.5px] disabled:opacity-30"
          style={{ borderColor: THEME.border, color: THEME.textSecondary }}
        >
          Next
        </button>
      </div>
    </div>
  );
}

// ── Billing ───────────────────────────────────────────────────────────────────

export function Billing() {
  const { orgId } = useAuth();
  const { toast } = useToast();

  const [balance, setBalance] = useState<Balance | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [amount, setAmount] = useState("1000");
  const [paying, setPaying] = useState(false);
  const [billingMode, setBillingMode] = useState<"test" | "live" | null>(null);

  // Filters and pagination
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [txPage, setTxPage] = useState(1);

  // Post-payment animation state
  const [successAmount, setSuccessAmount] = useState<number | null>(null);
  const [animateFrom, setAnimateFrom] = useState(0);
  const [animating, setAnimating] = useState(false);
  const [showBanner, setShowBanner] = useState(false);

  const fetchData = useCallback(async () => {
    if (!orgId) return;
    try {
      const [b, t] = await Promise.all([
        apiFetch<{ data: Balance }>(`/v1/orgs/${orgId}/billing/balance`),
        apiFetch<{ data: Transaction[] }>(`/v1/orgs/${orgId}/billing/transactions`),
      ]);
      return { balance: b.data, transactions: t.data };
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to load billing data", "error");
      return null;
    }
  }, [orgId, toast]);

  // Fetch billing mode
  useEffect(() => {
    apiFetch<{ environment: "test" | "live" }>("/v1/billing/mode")
      .then((r) => setBillingMode(r.environment))
      .catch(() => {});
  }, []);

  // Initial load + handle ?status=success return from Stripe
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get("status");
    const sessionId = params.get("session_id");

    if (status) {
      const clean = window.location.pathname;
      window.history.replaceState({}, "", clean);
    }

    const prevBalance = parseFloat(sessionStorage.getItem(STORAGE_KEY) ?? "0");
    sessionStorage.removeItem(STORAGE_KEY);

    if (status === "success" && orgId) {
      let knownAmount: number | null = null;

      async function fetchSessionAmount() {
        if (!sessionId) return;
        try {
          const s = await apiFetch<{ data: { amount_usd: number; status: string } }>(
            `/v1/orgs/${orgId}/billing/checkout/${sessionId}`
          );
          if (s.data.amount_usd > 0) knownAmount = s.data.amount_usd;
        } catch {
          // Session lookup failed
        }
      }

      let retries = 0;
      const maxRetries = 4;
      const pollInterval = 1500;
      let verified = false;

      async function verifyAndCredit() {
        if (!sessionId || verified) return;
        verified = true;
        try {
          await apiFetch<{ credited: boolean; amount_usd: number }>(
            `/v1/orgs/${orgId}/billing/verify-session`,
            { method: "POST", body: JSON.stringify({ session_id: sessionId }) }
          );
        } catch {
          // Verification failed — webhook may still process
        }
      }

      async function pollBalance() {
        const data = await fetchData();
        if (!data) return;
        setBalance(data.balance);
        setTransactions(data.transactions);
        setLoading(false);

        const newAvailable = data.balance.balance_available_usd;
        if (newAvailable > prevBalance) {
          const paid = knownAmount ?? (newAvailable - prevBalance);
          setAnimateFrom(prevBalance);
          setAnimating(true);
          setSuccessAmount(paid > 0 ? paid : (knownAmount ?? newAvailable));
          setShowBanner(true);
          setTimeout(() => setAnimating(false), 2200);
        } else if (retries < maxRetries) {
          if (retries === 2) verifyAndCredit();
          retries++;
          setTimeout(pollBalance, pollInterval);
        } else {
          if (knownAmount && knownAmount > 0) {
            setSuccessAmount(knownAmount);
            setShowBanner(true);
          }
        }
      }

      fetchSessionAmount().then(() => pollBalance());
    } else {
      fetchData().then((data) => {
        if (!data) return;
        setBalance(data.balance);
        setTransactions(data.transactions);
        setLoading(false);
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCheckout() {
    if (!orgId) return;
    const cents = Math.round(parseFloat(amount) * 100);
    if (!cents) return;
    sessionStorage.setItem(STORAGE_KEY, String(balance?.balance_available_usd ?? 0));
    setPaying(true);
    try {
      const r = await apiFetch<{ data: { checkout_url: string } }>(
        `/v1/orgs/${orgId}/billing/checkout`,
        { method: "POST", body: JSON.stringify({ amount_cents: cents }) }
      );
      window.location.href = r.data.checkout_url;
    } catch (e: unknown) {
      toast((e as Error).message ?? "Failed to start checkout", "error");
      sessionStorage.removeItem(STORAGE_KEY);
      setPaying(false);
    }
  }

  // Filtered + paginated transactions
  const filteredTx = typeFilter === "all"
    ? transactions
    : transactions.filter((tx) => tx.type === typeFilter);
  const txTotalPages = Math.max(1, Math.ceil(filteredTx.length / PAGE_SIZE));
  const txPageClamped = Math.min(txPage, txTotalPages);
  const pagedTx = filteredTx.slice((txPageClamped - 1) * PAGE_SIZE, txPageClamped * PAGE_SIZE);

  // Reset page when filter changes
  useEffect(() => { setTxPage(1); }, [typeFilter]);

  const availableDisplay = balance?.balance_available_usd ?? 0;
  const frozenDisplay    = balance?.balance_frozen_usd ?? 0;
  const spentDisplay     = balance?.balance_spent_usd ?? 0;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-semibold" style={{ color: THEME.textPrimary }}>Billing</h1>
        {billingMode && (
          <span
            className="text-xs font-medium px-2.5 py-1 uppercase tracking-wide"
            style={{
              background: billingMode === "live" ? "rgba(34,197,94,0.1)" : "rgba(245,158,11,0.12)",
              color: billingMode === "live" ? "#15803d" : "#B45309",
              border: `1px solid ${billingMode === "live" ? "rgba(34,197,94,0.3)" : "rgba(245,158,11,0.3)"}`,
            }}
          >
            {billingMode === "live" ? "Live Mode" : "Test Mode"}
          </span>
        )}
      </div>

      {/* Success banner */}
      {showBanner && successAmount !== null && (
        <SuccessBanner amount={successAmount} onDismiss={() => setShowBanner(false)} />
      )}

      {/* Balance cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6">
          <p className="text-3xl font-bold">
            {animating || (successAmount !== null && animateFrom !== availableDisplay) ? (
              <AnimatedBalance target={availableDisplay} from={animateFrom} animate={animating} />
            ) : (
              <span style={{ color: THEME.textPrimary }}>{fmtFull(availableDisplay)}</span>
            )}
          </p>
          <p className="text-sm mt-1" style={{ color: THEME.textMuted }}>Available</p>
        </div>

        <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6">
          <p className="text-3xl font-bold" style={{ color: "#B45309" }}>{fmtFull(frozenDisplay)}</p>
          <p className="text-sm mt-1" style={{ color: THEME.textMuted }}>Frozen</p>
        </div>

        <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6">
          <p className="text-3xl font-bold" style={{ color: THEME.textPrimary }}>{fmtFull(availableDisplay + frozenDisplay)}</p>
          <p className="text-sm mt-1" style={{ color: THEME.textMuted }}>Total</p>
        </div>

        <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6">
          <p className="text-3xl font-bold" style={{ color: THEME.textMuted }}>{fmtFull(spentDisplay)}</p>
          <p className="text-sm mt-1" style={{ color: THEME.textMuted }}>Spent</p>
        </div>
      </div>

      {/* Add Funds */}
      <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none p-6 mb-8">
        <h2 className="text-base font-semibold mb-4" style={{ color: THEME.textPrimary }}>Add Funds</h2>
        <div className="flex items-center gap-2 flex-wrap">
          {QUICK.map((a) => (
            <button
              key={a}
              onClick={() => setAmount(String(a))}
              className="px-4 py-2 text-sm border-[1.5px]"
              style={{
                background: amount === String(a) ? THEME.btnBg : "white",
                color: amount === String(a) ? "#fff" : THEME.textSecondary,
                borderColor: amount === String(a) ? THEME.btnBg : THEME.border,
                borderRadius: 0,
              }}
            >
              {fmtShort(a)}
            </button>
          ))}
          <div className="flex items-center border-[1.5px] border-[#1B1034] bg-white">
            <span className="px-3 text-sm" style={{ color: THEME.textMuted }}>$</span>
            <input
              type="number"
              min="1"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-24 py-2 pr-3 text-sm bg-transparent focus:outline-none"
              style={{ color: THEME.textPrimary }}
            />
          </div>
          <button
            onClick={handleCheckout}
            disabled={paying || !amount}
            className="px-5 py-2 text-sm text-white font-medium disabled:opacity-50"
            style={{ background: THEME.accent, borderRadius: 0 }}
          >
            {paying ? "Redirecting…" : "Pay with Stripe →"}
          </button>
        </div>
      </div>

      {/* Transactions */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold" style={{ color: THEME.textPrimary }}>Transactions</h2>
        <div className="flex items-center gap-1">
          {TX_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className="px-3 py-1 text-xs capitalize"
              style={{
                background: typeFilter === t ? THEME.btnBg : "transparent",
                color: typeFilter === t ? "#fff" : THEME.textMuted,
                border: `1.5px solid ${typeFilter === t ? THEME.btnBg : "transparent"}`,
              }}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="bg-white border-[1.5px] border-[#1B1034] rounded-none overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="text-xs text-left" style={{ color: THEME.textMuted }}>
              <th className="px-5 py-3 font-medium">Date</th>
              <th className="px-3 py-3 font-medium">Type</th>
              <th className="px-3 py-3 font-medium">Amount</th>
              <th className="px-3 py-3 font-medium">Balance after</th>
              <th className="px-3 py-3 font-medium">Description</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-sm" style={{ color: THEME.textMuted }}>Loading…</td></tr>
            ) : pagedTx.length === 0 ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-sm" style={{ color: THEME.textMuted }}>
                {typeFilter === "all" ? "No transactions yet." : `No ${typeFilter} transactions.`}
              </td></tr>
            ) : pagedTx.map((tx) => (
              <tr key={tx.id} style={{ borderTop: `1.5px solid ${THEME.border}` }}>
                <td className="px-5 py-3 text-xs" style={{ color: THEME.textMuted }}>
                  {new Date(tx.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                  <span className="block" style={{ color: THEME.textMuted }}>
                    {new Date(tx.created_at).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <span
                    className="text-xs px-2 py-0.5 font-medium uppercase tracking-wide"
                    style={txBadgeStyle(tx.type)}
                  >
                    {tx.type}
                  </span>
                </td>
                <td className="px-3 py-3 text-sm font-medium" style={{ color: tx.amount_usd >= 0 ? "#15803d" : THEME.danger }}>
                  {tx.amount_usd >= 0 ? "+" : ""}{fmtFull(tx.amount_usd)}
                </td>
                <td className="px-3 py-3 text-sm" style={{ color: THEME.textSecondary }}>
                  {tx.balance_after_usd != null ? fmtFull(tx.balance_after_usd) : "—"}
                </td>
                <td className="px-3 py-3 text-xs" style={{ color: THEME.textMuted }}>{tx.description ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <Pagination page={txPageClamped} totalPages={txTotalPages} onPageChange={setTxPage} />
      </div>
    </div>
  );
}
