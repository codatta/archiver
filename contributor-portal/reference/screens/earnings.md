# Screen: Earnings

> **Route:** `/contribute/earnings`
> **Nav item:** EARNINGS → Earnings
> **Purpose:** Pipeline-aware earnings tracking. Not just "earned / pending" but the full instance-by-instance pipeline position. The contributor's money tracker.

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Earnings                                [This month ▾] [Export]  │
│                                                                  │
│  ┌─ Earnings Summary ────────────────────────────────────────┐   │
│  │                                                            │   │
│  │  $1,240.00          $420.00          $86.50                │   │
│  │  Total earned       Pending          Royalties accrued     │   │
│  │  (all time)         (in pipeline)    (lifetime)            │   │
│  │                                                            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─ Pipeline Breakdown ──────────────────────────────────────┐   │
│  │                                                            │   │
│  │  Per-campaign pipeline position of your submissions:       │   │
│  │                                                            │   │
│  │  NVIDIA — Housekeeping Video ($2.50 fixed)                 │   │
│  │  ┌────────────────────────────────────────────────────┐    │   │
│  │  │  82 total submitted                                │    │   │
│  │  │                                                    │    │   │
│  │  │  ██████████████████████████░░░░░░░░░░░░░░  $155.00│    │   │
│  │  │  62 accepted ($155.00)     20 in review            │    │   │
│  │  │                                                    │    │   │
│  │  │  Rejected: 4 (see feedback)                        │    │   │
│  │  └────────────────────────────────────────────────────┘    │   │
│  │                                                            │   │
│  │  OpenAI — RLHF Quality (royalty est. $1.80/inst)           │   │
│  │  ┌────────────────────────────────────────────────────┐    │   │
│  │  │  50 total submitted                                │    │   │
│  │  │                                                    │    │   │
│  │  │  State breakdown:                                  │    │   │
│  │  │  30 ◆ royalty-eligible        $54.00 earned        │    │   │
│  │  │  12   in labeling             —                    │    │   │
│  │  │   5   in label-validate       —                    │    │   │
│  │  │   3   rejected                $0.00                │    │   │
│  │  │                                                    │    │   │
│  │  │  Pipeline velocity: ~4 hrs supply → labeled         │    │   │
│  │  └────────────────────────────────────────────────────┘    │   │
│  │                                                            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─ Transaction History ─────────────────────────────────────┐   │
│  │  Apr 15  Nvidia HK Video   +$25.00  fixed pay  62 inst   │   │
│  │  Apr 14  OpenAI RLHF       +$14.40  royalty    8 inst     │   │
│  │  Apr 14  Nvidia HK Video   +$30.00  fixed pay  12 inst   │   │
│  │  Apr 13  Nvidia HK Video   +$20.00  fixed pay  8 inst    │   │
│  │  ...                                                      │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Earnings Summary

Three headline numbers at the top:

| Metric | Calculation | Display |
|---|---|---|
| **Total earned** | Sum of all paid amounts (fixed + royalty) | `$1,240.00` |
| **Pending** | Fixed pay submitted but not yet reviewed + royalty-eligible but not yet consumed | `$420.00` |
| **Royalties accrued** | Lifetime royalty earnings specifically | `$86.50` |

---

## Pipeline Breakdown

One block per campaign. Two display modes based on compensation model:

### Fixed Pay Campaign

Simple progress bar: accepted vs. in-review vs. rejected.

```
  82 total submitted

  ██████████████████████████░░░░░░░░░░░░░░  $155.00
  62 accepted ($155.00)     20 in review

  Rejected: 4 (see feedback)
```

### Royalty / Hybrid Campaign

Instance-by-instance pipeline state breakdown.

```
  50 total submitted

  State breakdown:
  30 ◆ royalty-eligible        $54.00 earned
  12   in labeling             —
   5   in label-validate       —
   3   rejected                $0.00

  Pipeline velocity: ~4 hrs supply → labeled
```

**Pipeline state categories:**

| State | Icon | Color | Meaning |
|---|---|---|---|
| Royalty-eligible | ◆ | Green | Completed pipeline, earnings accruing |
| In labeling | — | Gray | Downstream labeling in progress |
| In validation | — | Gray | Downstream validation in progress |
| Accepted (no royalty yet) | ✓ | Blue | Pipeline complete but data not consumed |
| Rejected | ✕ | Red | Failed at some stage |
| Pipeline stalled | ⚠ | Amber | No movement in 5+ days |

**Clicking "Rejected: 4"** expands to show per-instance rejection reasons.

**Pipeline velocity** shows campaign-level average: how long instances take to move through downstream stages. Addresses situation D2 (royalty tracking anxiety).

---

## Stalled Campaign Alert

When a campaign has no pipeline movement for 5+ days:

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠ Pipeline stalled — no movement since Apr 10               │
│                                                              │
│  12 of your instances are waiting for labeling.              │
│  Your pending royalties: ~$21.60                             │
│                                                              │
│  This can happen when a campaign's supply outpaces labeling. │
│  The campaign creator has been notified.                     │
└──────────────────────────────────────────────────────────────┘
```

---

## Transaction History

Chronological list of all earnings events.

| Column | Content |
|---|---|
| Date | Transaction date |
| Campaign | Org + campaign name |
| Amount | `+$25.00` (always positive in this view) |
| Type | `fixed pay` / `royalty` / `bounty` |
| Instances | Count of instances in this batch |

**Filters:** Campaign, type (fixed/royalty/bounty), date range.

**Export:** CSV download of transaction history.

---

## Connection to Payouts

The Earnings screen shows what you've earned. The Payouts screen (future) shows how to withdraw. A banner links between them:

```
  Available for withdrawal: $840.00    [Go to Payouts →]
```
