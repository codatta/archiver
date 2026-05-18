# Screen: Campaign Detail

> **Route:** `/contribute/campaigns/[id]`
> **Entry:** Click "View Campaign" on any campaign card
> **Purpose:** Campaign landing page. Everything a contributor needs to decide whether to accept: who, what, pay, qualifications, and how the pipeline works.

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ← All Campaigns                                                 │
│                                                                  │
│  ┌─ Org Card (hero) ─────────────────────────────────────────┐   │
│  │  [Logo]  ORG NAME              Trust badge                │   │
│  │          Industry                                         │   │
│  │          Description (or masked)           [View Profile]  │   │
│  │  4.9★ · 12 campaigns · 100% on-time · $284K paid          │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─ Campaign Header ─────────────────────────────────────────┐   │
│  │  Campaign Name                                             │   │
│  │  🤖 Frontier  📹 Modality  🏠 Domain                       │   │
│  │  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐                  │   │
│  │  │ $2.50 │ │ 3     │ │ 360   │ │ ~2wks │                  │   │
│  │  │ /inst │ │ tasks │ │ left  │ │ left  │                  │   │
│  │  └───────┘ └───────┘ └───────┘ └───────┘                  │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  § ABOUT THIS CAMPAIGN                                           │
│  § TASK TYPE BREAKDOWN                                           │
│  § HOW IT WORKS (pipeline)                                       │
│  § COMPENSATION                                                  │
│  § YOUR QUALIFICATIONS                                           │
│  § TASK INSTRUCTIONS (preview)                                   │
│                                                                  │
│  ┌─ Sticky Footer ───────────────────────────────────────────┐   │
│  │  ✓ You qualify · $2.50/inst · 360 remaining               │   │
│  │                                   [Accept & Start Working] │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Section: Task Type Breakdown

**New section** addressing situations A1 and A4. Shows what task types exist in this campaign with per-type pay and qualification status.

```
┌──────────────────────────────────────────────────────────────┐
│  TASK TYPE BREAKDOWN                                         │
│                                                              │
│  📤 Supply — Record Video                                    │
│     $2.50 / accepted instance · ✓ You qualify                │
│                                                              │
│  🏷 Labeling — Annotate key frames                           │
│     $1.50 / accepted instance · ⚠ Needs annotation cert     │
│                                                              │
│  ✅ Validation — Auto QA (agent only)                        │
│     🤖 Handled by AI agent — no contributor action needed    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

For each task type:
- Task type badge + task name
- Per-type pay rate
- Per-type qualification status (✓ / ⚠ / ✕ / 🤖 agent)

---

## Section: How It Works (Pipeline)

Contributor-friendly view of the campaign's task DAG. No technical jargon.

```
┌──────────────────────────────────────────────────────────────┐
│  HOW IT WORKS                                                │
│                                                              │
│  This campaign has 3 tasks. You'll work on human tasks;      │
│  AI agents handle the rest automatically.                    │
│                                                              │
│  ┌─────────────────┐                                         │
│  │  ① Record Video  │  ← 👤 You do this                      │
│  │  📤 Supply        │  360 remaining · $2.50/accepted        │
│  └────────┬─────────┘                                        │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │  ② Auto Pre-label│  ← 🤖 AI agent (automatic)             │
│  │  🏷 Labeling      │  You don't need to do anything         │
│  └────────┬─────────┘                                        │
│           ▼                                                  │
│  ┌─────────────────┐                                         │
│  │  ③ Verify Labels │  ← 👤 You may do this                  │
│  │  ✅ Validation    │  Assigned based on availability        │
│  └─────────────────┘                                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Styling:**
- Human tasks: `border-l-4 border-black bg-white rounded-lg p-4`
- Agent tasks: `border-l-4 border-gray-300 bg-gray-50 rounded-lg p-4`
- Task type badge inline with each step

---

## Section: Compensation

```
┌──────────────────────────────────────────────────────────────┐
│  COMPENSATION                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  💵  $2.50 per accepted instance (supply)             │    │
│  │  💵  $1.50 per accepted instance (labeling)           │    │
│  │                                                      │    │
│  │  Model: Fixed pay                                    │    │
│  │  Payment: Within 48 hours of acceptance              │    │
│  │  Escrow: Funds held by platform (guaranteed)         │    │
│  │                                                      │    │
│  │  Estimated earnings (supply tasks):                  │    │
│  │  • 10 instances/day → $25/day → $175/week            │    │
│  │  • Top contributors average 15 inst/day → $262/week  │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

**Compensation card styling:** `border border-green-200 bg-green-50 rounded-lg p-4`

---

## Section: Your Qualifications

Per-task-type qualification check (see [business/qualification.md](../business/qualification.md) for rules).

```
┌──────────────────────────────────────────────────────────────┐
│  YOUR QUALIFICATIONS                                         │
│                                                              │
│  Supply tasks:                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  ✅  Reputation ≥ 50         Your score: 84          │    │
│  │  ✅  5+ completed tasks      Your count: 142         │    │
│  │  ✅  Video recording exp     Verified Mar 2026       │    │
│  │  ✅  Smartphone 1080p+       Self-declared           │    │
│  └──────────────────────────────────────────────────────┘    │
│  ✓ You meet all supply requirements                          │
│                                                              │
│  Labeling tasks:                                             │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  ✅  Reputation ≥ 70         Your score: 84          │    │
│  │  ✅  20+ completed tasks     Your count: 142         │    │
│  │  ❌  Annotation experience   Not verified            │    │
│  │      [How to qualify →]                               │    │
│  └──────────────────────────────────────────────────────┘    │
│  ⚠ 1 requirement not met for labeling                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Enrollment Flow

**Sticky footer button states:**

| State | Button | Style |
|---|---|---|
| Qualified (all types) | `[Accept & Start Working]` | `bg-black text-white` |
| Qualified (some types) | `[Accept Supply Tasks]` | `bg-black text-white` — specifies which types |
| Not qualified | `[View Requirements]` | `bg-gray-100 text-gray-500` |
| Already enrolled | `[Continue Working →]` | `bg-black text-white` |
| Campaign full | `[Join Waitlist]` | `border border-gray-300` |

**Acceptance dialog:**

```
┌──────────────────────────────────────┐
│  Accept Campaign Tasks?              │
│                                      │
│  You qualify for: Supply tasks       │
│  Not yet qualified: Labeling         │
│                                      │
│  By accepting, you agree to:         │
│  • Follow task instructions          │
│  • Submit original work only         │
│  • Maintain quality standards        │
│                                      │
│  You can stop contributing at any    │
│  time. Completed work will still     │
│  be paid.                            │
│                                      │
│  [Cancel]         [Accept & Start]   │
└──────────────────────────────────────┘
```

After acceptance → navigate to task workspace.

---

## Privacy Adaptation

The entire page adapts per privacy tier. See [business/privacy-tiers.md](../business/privacy-tiers.md) for full rules.

---

## Mobile (<768px)

- Org logo: `w-12 h-12` (smaller)
- Stats bar wraps to 2 rows
- Pipeline visualization: vertical list (no arrows, numbered steps)
- Sticky footer: full-width bottom bar
