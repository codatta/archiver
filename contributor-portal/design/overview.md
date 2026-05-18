# Contributor Kitchen — Design Overview

> Tier 1 of the `design/` documentation. Covers the phase-level roadmap, user journeys, use cases, and screen inventory.
> Per-screen detail (states, behavior, interactions, devices) lives in the individual `design/<screen>.md` files.

---

## Product Purpose

Contributor Kitchen is the supply-side portal of the Humanbased platform. Contributors capture, process, and annotate training data for AI systems. The V1 focus is robotics video (Embodiment-X campaign type). The portal handles the full lifecycle: discovery → qualification → enrollment → task execution → lineage tracking.

---

## Phase Roadmap

### V1 — End-to-end contribution (current build target)

**Goal:** A contributor can find the Embodiment-X campaign, qualify, enroll, upload a video, annotate it, and see their contribution tracked in the lineage. No payment, no dispute, no teams — just a complete working pipeline.

**Screens shipped:** Campaign Discovery, Campaign Detail, My Kitchen (task queue), Task Upload (T1), Annotation Workspace (T3), Skills & Profile (basic), Contributions table
**Backend shipped:** ML Backend adapter, upload pipeline, annotation storage, mock lineage

### V2 — Full contributor lifecycle

**Goal:** Contributors have visibility into earnings, can dispute unfair evaluations, can submit professional credentials for higher-tier campaigns, and receive meaningful downstream usage disclosure for royalty campaigns.

**Additions:** Earnings ledger + payout tracking, Dispute Review workflow, Credential submission + AI review, Downstream usage disclosure, Campaign recommendations, KYC tier, SMS notifications

### V3 — Social and teams

**Goal:** Contributors can form teams on campaigns to collaborate, split earnings, and build team reputation.

**Additions:** Team creation and management, team-level reputation and badges

### Long-term

Ownership marketplace — buy/sell/stake data ownership tokens (requires chain layer).

---

## User Journeys

### Journey 1 — New contributor, first contribution

```
[Campaign Discovery]
  ↓ Finds Embodiment-X, reads card
[Campaign Detail]
  ↓ Reviews task DAG, compensation (royalty), builder credibility
  ↓ Sees "Tutorial required"
[Skills & Profile]
  ↓ Completes training material, passes quiz → tutorial-passed
[Campaign Detail]
  ↓ Qualification met → clicks "Enroll"
[My Kitchen]
  ↓ Sees T1 task assigned
[Task Upload]
  ↓ Uploads video, selects detection preset, submits
  ↓ T2 processes automatically (ML Backend)
[My Kitchen]
  ↓ T2 complete → T3 task available
[Annotation Workspace]
  ↓ Reviews clips, annotates segments, submits
[Contributions]
  ↓ Sees T3 instance in history → T4 validation pending
```

### Journey 2 — Returning contributor, daily work

```
[My Kitchen] (entry point for returning users)
  ↓ Sees pending T3 tasks across enrolled campaigns
[Annotation Workspace]
  ↓ Annotates, saves, submits
[My Kitchen]
  ↓ Picks next task or checks earnings
[Earnings] (V2)
  ↓ Views pending royalty accrual
```

### Journey 3 — Skill qualification for gated campaign

```
[Campaign Discovery]
  ↓ Finds medical imaging campaign — sees lock badge "Credential required"
[Campaign Detail]
  ↓ Views requirements: credential-verified for Medical Imaging skill
[Skills & Profile]
  ↓ Sees Medical Imaging skill is "unverified"
  ↓ Option A: completes training material + quiz → tutorial-passed (not enough for this campaign)
  ↓ Option B: uploads medical degree / certification → submitted for review
  ↓ Platform reviews (AI + human fallback) within 24-48h → credential-verified
[Campaign Discovery / Detail]
  ↓ Notified (in-app + email) → now qualified → enrolls
```

### Journey 4 — Dispute an evaluation (V2)

```
[My Kitchen or Contributions]
  ↓ Notification: T3 evaluation — "needs revision" (quality grade C)
  ↓ Views evaluation feedback
  ↓ Option A: accepts, reworks annotation, resubmits
  ↓ Option B: disputes — submits reason
[System]
  ↓ Dispute becomes peer-review task for other qualified campaign contributors
  ↓ Timeout window expires → quorum decision: uphold or overturn
[My Kitchen / Contributions]
  ↓ Contributor notified of outcome
```

### Journey 5 — Builder watches downstream usage (V2)

```
[Builder Studio — campaign published]
  ↓ Builder exports annotations, uses in model training
  ↓ Builder publishes "training run" event to shared Supabase
[Contributor Kitchen — Contributions]
  ↓ Contributor sees "Your clip contributed to Model Training Run #12"
  ↓ Royalty accrual updated (pending → confirmed)
```

---

## Use Cases

| ID | Use case | Phase | Screen(s) |
|---|---|---|---|
| UC-01 | Browse and filter campaigns by frontier and compensation type | V1 | Campaign Discovery |
| UC-02 | Evaluate a campaign's task pipeline, pay, and builder credibility before enrolling | V1 | Campaign Detail |
| UC-03 | Complete a training tutorial to qualify for a campaign | V1 | Skills & Profile |
| UC-04 | Upload a robotics video with detection preset configuration | V1 | Task Upload |
| UC-05 | Annotate action segments with temporal labels, bounding boxes, language instructions | V1 | Annotation Workspace |
| UC-06 | Review Vision Engine pre-labels (bboxes, keypoints) and correct errors | V1 | Annotation Workspace |
| UC-07 | Track contribution lineage (T1→T2→T3→T4) across campaigns | V1 | Contributions |
| UC-08 | View and manage skills, track verification tier per skill | V1 | Skills & Profile |
| UC-09 | Submit professional credential (diploma, license) for credential-verified tier | V2 | Skills & Profile |
| UC-10 | Dispute a quality evaluation — trigger peer review | V2 | Contributions / Dispute Review |
| UC-11 | View earnings ledger: pending royalties, instant payouts, attribution share | V2 | Earnings |
| UC-12 | See downstream usage: which model training runs used my contributions | V2 | Contributions |

---

## Screen Inventory

### V1 screens

| Screen | File | Entry point | Primary action |
|---|---|---|---|
| Campaign Discovery | `campaign-discovery.md` | App root / Discover nav | Browse and filter campaigns |
| Campaign Detail | `campaign-detail.md` | Campaign card "View Campaign" | Enroll in campaign |
| My Kitchen | `my-kitchen.md` | "My Kitchen" nav (returning users' home) | Open a pending task |
| Task Upload (T1) | `task-upload.md` | My Kitchen → T1 task | Upload video/ZIP + detection preset |
| Annotation Workspace | `annotation-workspace.md` | My Kitchen → T3 task | Annotate clips, submit |
| Skills & Profile | `skills-profile.md` | "Skills" nav | Complete training, submit credential |
| Contributions | `contributions.md` | "Contributions" nav | View history, track lineage |

### V2 screens

| Screen | File | Entry point | Primary action |
|---|---|---|---|
| Earnings | `earnings.md` | "Earnings" nav | View ledger, check payout status |
| Dispute Review | `dispute-review.md` | Notification → Contributions | Submit or review a dispute |

---

## Navigation Map

```
Sidebar:
  Discover          → Campaign Discovery
  My Kitchen        → My Kitchen (task queue)
  Contributions     → Contributions table
  Skills            → Skills & Profile
  Earnings          → Earnings (V2)

Campaign Discovery  → Campaign Detail (card click)
Campaign Detail     → Skills & Profile (if not qualified)
Campaign Detail     → My Kitchen (after enroll)
My Kitchen          → Task Upload (T1 task)
My Kitchen          → Annotation Workspace (T3 task)
Task Upload         → My Kitchen (after submit)
Annotation Workspace→ My Kitchen (after submit, or back)
Contributions       → Dispute Review (V2, dispute action)
```

---

## Device Strategy

| Screen | Desktop | Tablet | Mobile |
|---|---|---|---|
| Campaign Discovery | Primary — 3-col grid | 2-col grid | 1-col, scrollable |
| Campaign Detail | Primary — 2-col layout | Stacked | Stacked, scrollable |
| My Kitchen | Primary | Responsive | 1-col card list |
| Task Upload | Primary | Supported | Not supported |
| Annotation Workspace | **Desktop only** (min 1024px) | Not supported | Not supported |
| Skills & Profile | Primary | Responsive | 1-col |
| Contributions | Primary | Horizontal scroll | Horizontal scroll, pinned columns |
| Earnings | Primary | Responsive | 1-col |

Annotation Workspace is keyboard-driven and cannot function usefully on touch devices. Show a "use a desktop browser" prompt below 1024px width.

---

## Excalidraw Designs

Initial designs for 4 key screens are in `ui-designs/contributor-kitchen.md`:

| Screen | Checkpoint |
|---|---|
| Campaign Discovery | `8c65b2e5ec6b494887` |
| Campaign Detail | `a24a121714b24d579e` |
| Annotation Workspace | `3d4b4b1e5db140f9a9` |
| Skills & Profile | `5fc61f139ed148dc94` |
