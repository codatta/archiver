# Screen: Earnings

## Purpose
The contributor's financial dashboard. Shows pending and confirmed earnings across all campaigns — royalty accrual, instant payouts, and attribution share. Contributors use this to understand how much they've earned, when they'll be paid, and initiate withdrawals.

## Phase
V2

## Users
- **Royalty contributor** — monitoring accrued royalties from downstream model usage
- **Instant-payout contributor** — checking payout history and pending payments
- **Any contributor** — reviewing total lifetime earnings, KYC status for withdrawal

## Entry Points
- Sidebar "Earnings" nav item (visible in V2+)
- Notification: "Your royalty was confirmed" → deep links to specific row

## Exit Points
- "Request Payout" button → payout flow (V2 modal)
- Transaction row → Contributions screen (linked instance)
- Sidebar nav items → other screens

## Devices
- Desktop (primary): 2-column (summary/stats left, transaction ledger right) or top-summary + full-width table
- Tablet (≥768px): responsive single column
- Mobile (<768px): 1-column; horizontal scroll on ledger

---

## States

| State | Trigger | What renders |
|---|---|---|
| Loading | Initial fetch | Skeleton cards + table shimmer |
| No earnings | First-time or no confirmed payouts | "No earnings yet" with explanation of when royalties confirm |
| Earnings present | Transactions exist | Summary cards + ledger table |
| KYC required | Withdrawal threshold reached but KYC not complete | Warning banner: "Complete identity verification to withdraw" |
| Payout in progress | Withdrawal submitted | Status row in ledger: "Processing" |

---

## Behavior

**On load:**
- Fetch earnings summary: `GET /v1/contributors/me/earnings`
- Fetch transaction ledger: `GET /v1/contributors/me/transactions` (paginated)

**Earnings types:**
| Type | How earned | When confirmed |
|---|---|---|
| Royalty | 60% of campaign royalty pool, pro-rated by contribution | When builder publishes training run event |
| Instant | Fixed rate per task | When T4 evaluation passes (grade A–C) |
| Attribution share | Upstream contributor's 35% share, distributed by lineage depth | When downstream royalty confirms |

**Royalty accrual flow:**
- Submission accepted (T4 pass) → status: `Pending royalty`
- Builder uses annotation in training run → status: `Confirmed`
- Withdrawal threshold met + KYC done → status: `Withdrawable`
- Withdrawal requested → status: `Processing`
- Payout settled → status: `Paid`

**Withdrawal:**
- V2: minimum threshold (platform-configurable, e.g., $50)
- KYC required above a campaign-specific threshold (campaign owner sets)
- Payout methods: crypto wallet, bank transfer (V2 scope determined by legal/compliance)

---

## Layout

### Summary cards (top row)
- Total earned (lifetime, all types)
- Pending (not yet confirmed)
- Confirmed (confirmed, not yet withdrawn)
- Withdrawn (total paid out)

### Earnings ledger table

| Column | Content |
|---|---|
| Date | Confirmation or credit date |
| Campaign | Campaign name (linked to Campaign Detail) |
| Type | Royalty / Instant / Attribution |
| Instance | Contribution link → Contributions screen |
| Amount | Dollar amount or "Pending" |
| Status | Pending / Confirmed / Processing / Paid |

- Sort: date (default), amount, status
- Filter: by type, by campaign, by status

### Withdrawal panel (desktop sidebar or bottom section)
- Available balance (confirmed, withdrawable amount)
- "Request Payout" button (disabled if KYC incomplete or below threshold)
- KYC status indicator + link to complete KYC if needed

---

## Interactions

| Element | Trigger | Response |
|---|---|---|
| "Request Payout" button | Click | Open payout modal (amount, method) |
| Transaction row | Click | Expand or navigate to linked contribution |
| KYC banner link | Click | Navigate to KYC verification flow (V2) |
| Filter/sort controls | Change | Filter/sort ledger client-side |
| "Load more" | Click | Fetch next page |

---

## Screen Relationships

| Destination | Trigger | Data passed |
|---|---|---|
| Contributions | Transaction row instance link | `instance_id` |
| Campaign Detail | Campaign name link | `campaign.id` |
| KYC flow (V2) | KYC banner CTA | — |

---

## Excalidraw Design
Not yet designed. Run Pencil with spec from this file when ready.
