# Screen: Campaign Browse

> **Route:** `/contribute/campaigns`
> **Nav item:** WORK → Campaigns
> **Purpose:** The primary discovery screen. A job board where contributors find campaigns matching their skills and pay expectations.

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Campaigns                                   [Search _________]  │
│  Find work and start earning                                     │
│                                                                  │
│  ┌─ Filter Bar ───────────────────────────────────────────────┐  │
│  │  Frontier: [All ▾]  Pay: [All ▾]  Task type: [All ▾]      │  │
│  │  Qualified: [All ▾]  Sort: [Highest pay ▾]                 │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  18 active campaigns                                             │
│                                                                  │
│  ┌────────────────────────────┐  ┌────────────────────────────┐  │
│  │    Campaign Card            │  │    Campaign Card            │  │
│  │    (see campaign-card.md)   │  │                             │  │
│  └────────────────────────────┘  └────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────┐  ┌────────────────────────────┐  │
│  │    Campaign Card            │  │    Campaign Card            │  │
│  └────────────────────────────┘  └────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

Grid: `grid-cols-2` desktop, `grid-cols-1` mobile.

---

## Filters

| Filter | Options | Default |
|---|---|---|
| **Frontier** | All, Robotics, NLP/LLM, Crypto, Food, Fashion, Medical, ... (multi-select) | All |
| **Pay** | All, Highest first, $5+, $2+, Royalty only | All |
| **Task type** | All, Has supply, Has labeling, Has validation | All |
| **Qualified** | All, Qualified only | All |
| **Sort** | Highest pay, Newest, Most remaining, Ending soon | Highest pay |

Filters are URL-param-based: `/contribute/campaigns?frontier=robotics&task_type=labeling&sort=newest`

**Task type filter** addresses situation A1 — specialists can find campaigns with their preferred task type.

---

## Search

- Searches: campaign name, org name, description, frontier, domain tags
- Debounced 300ms
- Privacy-masked campaigns: search matches the masked description only

---

## Campaign Card

See [components/campaign-card.md](../components/campaign-card.md) for the full card anatomy.

Key elements at a glance:
1. **Org header** — logo, name, trust badge, track record (privacy-adapted)
2. **Campaign body** — name, description, tags, task type breakdown, compensation pill
3. **Footer** — qualification status + primary action

---

## Empty States

### No campaigns match filters

```
No campaigns match your filters.
[Clear all filters] or try a different combination.
```

### No active campaigns platform-wide

```
No active campaigns right now.
New campaigns are posted regularly — check back soon.
[Set up notifications →]
```
