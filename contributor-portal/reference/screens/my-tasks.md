# Screen: My Tasks

> **Route:** `/contribute/tasks`
> **Nav item:** WORK → My Tasks
> **Purpose:** Cross-campaign view of all enrolled campaigns, in-progress tasks, and submitted instances with live pipeline status. The contributor's operations dashboard.

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  My Tasks                                [Filter: All ▾] [⚙]    │
│                                                                  │
│  ┌─ Summary Bar ─────────────────────────────────────────────┐   │
│  │  3 campaigns enrolled · 47 submitted today · $82.50 earned │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─ Campaign Section ────────────────────────────────────────┐   │
│  │  NVIDIA — Housekeeping Video Collection                    │   │
│  │  📤 Supply · Fixed $2.50/inst · 12 submitted · 8 accepted │   │
│  │                                              [Continue →]  │   │
│  │                                                            │   │
│  │  Recent submissions:                                       │   │
│  │  ┌────────────────────────────────────────────────────┐    │   │
│  │  │  #312  supply██│sv██│label▒▒│lv  ◆  in labeling   │    │   │
│  │  │  #311  supply██│sv██│label██│lv██◆  royalty-eligible│    │   │
│  │  │  #310  supply██│sv██│label▒▒│lv     in labeling   │    │   │
│  │  │  #308  supply██│sv✕ │                rejected      │    │   │
│  │  └────────────────────────────────────────────────────┘    │   │
│  │  [Show all 12 →]                                           │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─ Campaign Section ────────────────────────────────────────┐   │
│  │  OpenAI — RLHF Response Quality                            │   │
│  │  🏷 Labeling · Royalty est. $1.80/inst · 35 submitted      │   │
│  │                                              [Continue →]  │   │
│  │  ...                                                       │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Summary Bar

Aggregate stats across all enrolled campaigns.

```
3 campaigns enrolled · 47 submitted today · $82.50 earned
```

| Metric | Source |
|---|---|
| Campaigns enrolled | Count of campaigns with `status=active` enrollment |
| Submitted today | Today's submissions across all campaigns |
| Earned today | Sum of fixed pay accepted + royalties triggered today |

---

## Campaign Sections

One section per enrolled campaign. Sorted by most recently worked (not enrollment date).

### Section Header

```
  NVIDIA — Housekeeping Video Collection
  📤 Supply · Fixed $2.50/inst · 12 submitted · 8 accepted
                                                [Continue →]
```

| Element | Content |
|---|---|
| Org + campaign name | Org name (privacy-adapted) + campaign name |
| Task type badge | Primary task type the contributor has been doing |
| Compensation model | Fixed / Royalty / Hybrid + rate |
| Submission count | Total submitted in this campaign |
| Accepted count | Total accepted |
| Continue button | Navigates to task workspace |

### Instance List — Compact Pipeline Bars

Each row shows one submitted instance with a compact pipeline context bar.

```
  #312  supply██│sv██│label▒▒│lv  ◆    in labeling
  #311  supply██│sv██│label██│lv██◆    royalty-eligible
  #310  supply██│sv██│label▒▒│lv        in labeling
  #308  supply██│sv✕ │                  rejected
```

| Element | Rendering |
|---|---|
| Instance ID | `#312` — truncated hash or sequential ID |
| Compact bar | Same component as full bar, but at 16px height, no labels, no context header |
| Status text | Current state in plain text (right-aligned) |
| Rejected indicator | `✕` mark on the stage that rejected, red-tinted |

**Clicking an instance row** expands it to show:
- Full-height pipeline bar with context header
- Rejection reason (if rejected)
- Submission timestamp
- Per-stage timestamps

---

## Filters

| Filter | Options | Default |
|---|---|---|
| Campaign | All, specific campaign names | All |
| Status | All, In progress, Accepted, Rejected, Royalty-eligible | All |
| Task type | All, Supply, Labeling, Validation | All |
| Time range | Today, This week, This month, All time | This week |

---

## Notification Badges

Campaign sections show notification badges for actionable events:

```
  NVIDIA — Housekeeping Video Collection          🔴 3 rejections
```

| Event | Badge |
|---|---|
| New rejections (with feedback) | Red dot + count |
| Royalty unlocked | Green dot + amount |
| Queue refilled (after subscribing) | Blue dot |
| Campaign ending soon | Amber dot |

---

## Empty States

### No enrolled campaigns

```
You haven't enrolled in any campaigns yet.

[Browse Campaigns →]
```

### Campaign with no recent activity

```
No recent submissions. Your last submission was 5 days ago.

[Continue Working →]    [Unenroll from campaign]
```
