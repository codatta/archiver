# Navigation

> Sidebar structure, routing, and screen map for the contributor portal.

---

## Sidebar

```
■ humanbased

WORK
● Campaigns              /contribute/campaigns
○ My Tasks               /contribute/tasks

EARNINGS
○ Earnings               /contribute/earnings
○ Payouts                /contribute/payouts

PROFILE
○ Reputation             /contribute/reputation
○ Credentials            /contribute/credentials
○ Settings               /contribute/settings

─────────────────
contributor_8f2a          Contributor handle
Tier: Expert              Current tier badge
84 / 100 rep              Reputation score
─────────────────
◇ Switch to Developer     If user has dual role
◇ Sign out
```

**Styling:**
- Active item: `font-semibold text-white bg-gray-800 rounded-md` with `●` marker
- Inactive: `text-gray-400 hover:text-white` with `○` marker
- Section headers: `text-xs text-gray-500 uppercase tracking-wider`
- Footer (profile): `border-t border-gray-700 pt-4`
- Sidebar background: `bg-gray-900`

---

## Route Map

| Route | Screen | Status | Doc |
|---|---|---|---|
| `/contribute/campaigns` | Campaign Browse | Designed | [campaign-browse.md](../screens/campaign-browse.md) |
| `/contribute/campaigns/[id]` | Campaign Detail | Designed | [campaign-detail.md](../screens/campaign-detail.md) |
| `/contribute/campaigns/[id]/tasks/[taskId]` | Task Workspace | New | [task-workspace.md](../screens/task-workspace.md) |
| `/contribute/tasks` | My Tasks | New | [my-tasks.md](../screens/my-tasks.md) |
| `/contribute/earnings` | Earnings | New | [earnings.md](../screens/earnings.md) |
| `/contribute/payouts` | Payouts | Future | — |
| `/contribute/reputation` | Reputation | Future | — |
| `/contribute/credentials` | Credentials | Future | — |
| `/contribute/settings` | Settings | Future | — |

---

## Screen → Situation Map

| Screen | Primary situations served |
|---|---|
| Campaign Browse | A1, A2, A3, A5 |
| Campaign Detail | A1, A4, B1, B2, B3 |
| Task Workspace | C1–C7 |
| My Tasks | C6, D2, D5, D6, E3 |
| Earnings | D1–D6 |
| Reputation | E1, E2 |

---

## Navigation Flows

### Discovery → Work

```
Campaign Browse ──▶ Campaign Detail ──▶ Accept ──▶ Task Workspace
       │                    │
       │              (sticky footer)
       │
  Filter / Search
```

### Active Work

```
Task Workspace ──▶ Submit ──▶ Next Instance (same task)
       │                          │
       │                    (auto-transition)
       │
  Pipeline Context Bar (always visible)
```

### Cross-Campaign

```
My Tasks ──▶ Pick any enrolled campaign ──▶ Task Workspace
   │
   └── Shows all campaigns, all task types, all states
```

### Tracking

```
My Tasks ──▶ Instance detail (pipeline status per submission)
   │
Earnings ──▶ Aggregate view (pipeline breakdown per campaign)
```

---

## Role Switch

A user can hold both contributor and developer roles. When switching:
- The sidebar rebuilds completely (different nav items)
- The URL prefix changes (`/contribute/*` → `/*`)
- No shared state between views
- Switch via the footer toggle: `◇ Switch to Developer`
