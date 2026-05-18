# Contributor Kitchen — Implementation Docs

> **What this is:** A self-contained spec package for building the Contributor Portal (a.k.a. Contributor Kitchen) — the supply-side product where contributors find campaigns, complete tasks, earn compensation, and build reputation.
>
> **Audience:** Engineers implementing the contributor portal. Every file is designed to be read independently.
>
> **Origin:** Distilled from the design system in `huge_leap/ux-design/` (2026-04-15). This copy is the implementation reference; the source repo retains the design rationale and iteration history.

---

## Architecture at a Glance

The contributor portal is one of two products sharing a single authentication system and data lineage ledger. Contributors never see the developer portal. The two products share the annotation runtime and the on-chain attribution layer but have completely separate navigation, data contexts, and design goals.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Humanbased Platform                          │
│                                                                     │
│  ┌─────────────────────┐              ┌─────────────────────────┐   │
│  │  Developer Portal    │              │  Contributor Kitchen     │   │
│  │  (demand side)       │              │  (supply side)           │   │
│  │                      │              │                          │   │
│  │  Launch campaigns    │──  shared  ──│  Find campaigns          │   │
│  │  Consume data        │   runtime    │  Complete tasks           │   │
│  │  Deploy agents       │   + ledger   │  Earn compensation       │   │
│  │  Manage billing      │              │  Build reputation        │   │
│  └─────────────────────┘              └─────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Shared: Annotation Pipeline · Data Lineage · Auth          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Doc Map

### Business Logic — Rules that drive behavior

| Doc | What it defines |
|---|---|
| [business/task-types.md](business/task-types.md) | Supply, Labeling, Validation taxonomy; DAG rules; executor types |
| [business/instance-lifecycle.md](business/instance-lifecycle.md) | One data point's journey: states, transitions, multi-label consensus |
| [business/compensation.md](business/compensation.md) | Fixed, Bounty, Hybrid, Royalty rules; escrow; payout triggers |
| [business/qualification.md](business/qualification.md) | Per-task-type requirements; pool estimation; certification paths |
| [business/privacy-tiers.md](business/privacy-tiers.md) | Open / Shielded / Guarded / Sealed; UI adaptation rules |

### User Journeys — Who uses this and how

| Doc | What it defines |
|---|---|
| [journeys/archetypes.md](journeys/archetypes.md) | 4 contributor profiles: Supply, Labeling, Validation specialist, Generalist |
| [journeys/situations.md](journeys/situations.md) | 25+ named situations across 5 phases (explore, enroll, work, track, specialize) |
| [journeys/navigation.md](journeys/navigation.md) | Sidebar, routing, screen map, role switch |

### Screens — Page-level specs

| Doc | Route | Status |
|---|---|---|
| [screens/campaign-browse.md](screens/campaign-browse.md) | `/contribute/campaigns` | Designed |
| [screens/campaign-detail.md](screens/campaign-detail.md) | `/contribute/campaigns/[id]` | Designed |
| [screens/task-workspace.md](screens/task-workspace.md) | `/contribute/campaigns/[id]/tasks/[taskId]` | New |
| [screens/my-tasks.md](screens/my-tasks.md) | `/contribute/tasks` | New |
| [screens/earnings.md](screens/earnings.md) | `/contribute/earnings` | New |

### Components — Reusable UI building blocks

| Doc | Where used |
|---|---|
| [components/pipeline-context-bar.md](components/pipeline-context-bar.md) | Task workspace, My Tasks, Earnings |
| [components/campaign-card.md](components/campaign-card.md) | Campaign Browse |
| [components/org-card.md](components/org-card.md) | Campaign Browse, Campaign Detail |
| [components/task-type-badge.md](components/task-type-badge.md) | Campaign Card, Task Workspace, My Tasks |

### Integration — Backend contracts

| Doc | What it defines |
|---|---|
| [integration/annotation-runtime.md](integration/annotation-runtime.md) | How the portal consumes the annotation pipeline |
| [integration/api-surface.md](integration/api-surface.md) | Required API endpoints with request/response shapes |

---

## Key Terminology

| Term | Meaning | Don't use |
|---|---|---|
| contributor | Person or agent who does work | worker, annotator, labeler |
| campaign | Scoped work request from an org | project, task batch, job |
| frontier | Knowledge area / data category | vertical, domain |
| instance | One data point traversing the pipeline | record, item, sample |
| task | One step in the pipeline (supply, label, validate) | stage, phase |
| executor | Who performs the task (human or agent) | performer, operator |

---

## Brand

The platform is **Humanbased** — single word, capital `H`, lowercase `b`. No exceptions in UI strings, docs, or code comments.
