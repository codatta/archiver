# PRD — Contributor Portal

## Vision

The supply-side web portal for the Humanbased platform. Campaign annotation UIs are defined by **Label Studio XML configs**. Agent processing (Vision Engine) integrates via the **ML Backend protocol**. All data lives in the **shared Supabase instance** with the developer portal.

The V1 campaign is **robotics video collection** (Embodiment-X): upload video → vision processing (YOLO/Pose/optical flow) → human annotation (temporal segments, action labels, bounding boxes, language instructions, task plan) → validation. Existing `labeling-*` repos are logic reference, not code to port.

## Product Identity

| | |
|---|---|
| **Platform name** | Humanbased |
| **Supply-side portal** | **Contributor Kitchen** — where contributors upload, process, and annotate data. "Kitchen" = craft space; contributors are chefs, raw footage is the ingredient, campaigns are recipes. Casual, warm, human. |
| **Demand-side portal** | **Builder Studio** — where campaign builders configure annotation schemas, set quality gates, and consume labeled data. "Studio" = professional craft space; builders are directors, campaigns are productions. |
| **Logo** | Codatta logomark (square symbol) only — never with wordmark text. Light bg: `public/assets/logos/colored/codatta.png`. Dark bg: `public/assets/logos/white/codatta.png`. |
| **Brand voice** | Contributor Kitchen: warm, approachable, empowering. Builder Studio: capable, precise, productive. Platform-level: human-first, lineage-credible, technically rigorous. |

---

## Target Users

| User | Job to be done |
|---|---|
| **Contributor (human)** | Discover campaigns worth joining, execute annotation tasks, track earnings and reputation, verify quality of their own output |
| **Vision Engine (ML Backend)** | Motion detection, person detection, scene segmentation via LS protocol |
| **Campaign Builder (via Builder Studio)** | Configure campaigns using LS XML configs, set quality gates, publish usage disclosure for royalty contributors |

## Capability Scope

Version labels: **V1** (current build queue) · **V2** · **V3** · **LT** (long-term/chain layer)

### 1 — Campaign Discovery & Enrollment
| Capability | Version |
|---|---|
| Browse and filter campaigns (frontier, compensation type, status, payout level) | V1 |
| Campaign detail: task DAG, estimated time, quality requirements | V1 |
| **Compensation breakdown** — type (instant / royalty / mix), schedule, minimum guarantee, royalty basis | V1 |
| **Builder credibility panel** — verified org, LinkedIn, HuggingFace, GitHub, publications, past campaigns, completion rate | V1 — display only; data written by Builder Studio |
| Enrollment with qualification gate check (tutorials passed, exams passed) | V1 |
| Campaign matching — "recommended for you" based on past contributions and qualifications | V2 |

### 2 — Contribution Workflow
| Capability | Version |
|---|---|
| My Tasks / Work Queue — enrolled campaigns → pending tasks | V1 |
| Task execution — LS XML-driven UI per task type | V1 |
| **Contribution history table** — all instances across campaigns; sortable by campaign, status, quality grade, earnings | V1 |
| Rework queue — evaluation feedback, revise and resubmit | V1 |
| **Dispute resolution** — contributor challenges evaluation; dispute becomes a peer-review task pushed to other qualified contributors in the campaign; quorum + timeout window configurable at platform level, overridable per campaign | V2 |

### 3 — Lineage & Downstream Progress
| Capability | Version |
|---|---|
| Per-instance lifecycle: T1→T2→T3→T4 status chain with timestamps | V1 |
| Campaign-level progress: my instance count vs. campaign target | V1 |
| Downstream view: contribution included in export batch, validation status | V1 — up to validation boundary |
| **Usage disclosure**: contribution used in a model training run (published by builder) | V2 — see Policy Decisions |

### 4 — Trust, Identity & Skills
| Capability | Version |
|---|---|
| Profile: display name, bio, location | V1 |
| Email verification | V1 |
| **Skills inventory on profile** — list of skills with verification level per skill: `unverified` → `tutorial-passed` → `credential-verified` → `expert` | V1 |
| **Training materials** — platform-curated content (video, docs, interactive exercises) per skill; materials are publicly disclosed before enrollment so contributors can evaluate effort and fit before committing | V1 |
| **Tutorial completion + quiz** — complete training material, pass quiz → skill moves to `tutorial-passed` | V1 |
| Reputation score (composite: quality grades, completion rate, rework rate, dispute outcomes) | V1 |
| Badges (milestone achievements + skill certifications earned per verification path) | V1 |
| **Credential submission** — contributor uploads proof of past experience: degree / diploma, professional license (CPA, PE, medical, etc.), industry certification; platform reviews and approves → skill moves to `credential-verified` | V2 |
| **Campaign skill gates** — campaign specifies required skill + minimum verification level; enrollment blocked if unmet; contributor shown which training to complete to qualify | V2 |
| **KYC tier** — dynamic threshold set by campaign type and owner; KYC'd contributors qualify for higher-rate campaigns | V2 |
| **AI interview** — video call conducted by AI to assess domain expertise; evaluates response quality, depth, accuracy; produces score + summary; borderline cases escalate to human review → grants `expert` tier | V3 |

### 5 — Earnings & Attribution
| Capability | Version |
|---|---|
| Earnings ledger — per-instance and cumulative, compensation type, pending vs. confirmed | V1 (data model + read-only display) |
| Instant payout tracking and history | V2 |
| Royalty accrual display with estimates | V2 |
| Payout / withdrawal settings (wallet address, bank, threshold triggers) | V2 |

### 6 — Notifications
| Capability | Version |
|---|---|
| In-app (bell): evaluation results, rework requests, new matched campaigns, payout events, dispute outcomes | V1 |
| Email: same event set | V1 |
| SMS / text message: same event set | V2 |

### Future Capabilities
| Capability | Version |
|---|---|
| **Teams** — form a team on a campaign, shared contribution, split earnings, team reputation | V3 |
| **Ownership marketplace** — buy / sell / stake data ownership tokens | LT |

---

## Policy Decisions

| Decision | Policy |
|---|---|
| **Downstream usage disclosure** | Opted-in by default. **Required** for royalty-compensating campaigns — contributors must see the usage basis for their royalties. **Optional** for instant-payout campaigns. |
| **Dispute resolution** | Dispute converts to a peer-review task assigned to qualified contributors in the same campaign. Timeout window and quorum are platform-level defaults; campaign owners can override both per campaign. |
| **KYC threshold** | Dynamic — set by campaign type and campaign owner configuration. Higher KYC level unlocks higher-rate campaigns. Platform manages KYC provider integration. Compensation to KYC'd contributors is typically higher; builders pay a premium for verified contributions. |
| **Compensation payouts** | V1: track and display earnings only. V2: actual payouts, withdrawal, royalty distribution. |
| **Notifications V1** | In-app + email. SMS in V2. |
| **Skill verification hierarchy** | `unverified` (self-declared) < `tutorial-passed` (quiz) < `credential-verified` (document proof) < `expert` (AI interview). Campaigns specify required skill + minimum level. Training materials are always publicly disclosed pre-enrollment. |

---

## Success Criteria

- [ ] End-to-end campaign: upload → vision processing → cull/slice → annotate (temporal + spatial + language) → validate → export
- [ ] Campaign annotation config is Label Studio XML, customizable per campaign
- [ ] Vision Engine wrapped as ML Backend (`/predict`, `/setup`, `/webhook`), any LS-compatible model is drop-in
- [ ] All state in shared Supabase — persistent, multi-user, lineage-tracked
- [ ] Every instance has correct `parent_instances[]` through T1→T2→T3→T4
- [ ] Mock AttemptIndex and attribution hooks with stable interfaces
- [ ] Developer portal can customize campaign config (action vocabulary, detection presets, quality thresholds)

## Non-Goals

- Porting labeling-* code — rewrite fresh, reference for logic only
- Vision Engine modifications — external service, wrapped by adapter
- Native mobile apps — web-only for V1
- Real on-chain writes — mocked with staging Postgres
- Compensation payouts — V1 tracks and displays earnings only; actual payouts, withdrawal, and royalty distribution are V2
- Full DAG orchestration — linear pipeline for V1
- Multi-campaign types in V1 — robotics video collection only

---

## Tasks View — Design Decision (v2)

**Source:** User wireframes (5-panel progressive interaction sketch, 2026-04-16).

### Five Progressive Views

The Tasks screen is a single page with multiple interaction states that reveal themselves through scrolling and clicking. No page navigation required.

**View 1 — Default state:**
```
┌──────────────────────────────────────────────────┐
│ My Tasks                                          │
│                                                   │
│ ┌───────────────────────────┐                     │
│ │ Today:  7 submitted       │                     │
│ └───────────────────────────┘                     │
│                                                   │
│ Priority Items                                    │
│ ┌──────────┐ ┌──────────────┐ ┌──────────┐       │
│ │ Resume 3 │ │ Expiring Soon│ │In Dispute │       │
│ └──────────┘ └──────────────┘ └──────────┘       │
│                                                   │
│ [campaign 01] [campaign 02] [campaign 03]         │  ← campaign tab bar
│                                                   │
│ ● campaign 01                                     │
│ ┌──────┐ ┌──────┐ ┌──────┐                       │
│ │ Task │ │ Task │ │ Task │                       │  ← 3-col grid
│ └──────┘ └──────┘ └──────┘                       │  inside bordered
│ ┌──────┐ ┌──────┐                                │  campaign container
│ │ Task │ │ Task │                                │
│ └──────┘ └──────┘                                │
│                                                   │
│ ● campaign 02                                     │
│ ┌──────┐ ┌──────┐ ┌──────┐                       │
│ │ Task │ │ Task │ │ Task │                       │
│ └──────┘ └──────┘ └──────┘                       │
│ ┌──────┐                                          │
│ │ Task │                                          │
│ └──────┘                                          │
│                                                   │
│ ● campaign 03                                     │
│ ┌──────┐ ┌──────┐ ┌──────┐                       │
│ ...                                               │
└──────────────────────────────────────────────────┘
```

**View 2 — Priority Items expanded:**
Clicking a priority pill (e.g. "Resume 3") expands the section inline to show a **horizontal scrollable carousel** of the actual task cards:

```
Priority Items
┌──────────┐ ┌──────────────┐ ┌──────────┐
│ Resume 3 │ │ Expiring Soon│ │In Dispute │     ← pills (Resume is active)
└──────────┘ └──────────────┘ └──────────┘

┌────────────────────────────────────────── ▸     ← horizontal scroll
│ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ │Task Card │ │Task Card │ │Task Card │         ← actual instance cards
│ │  01      │ │  02      │ │  03      │         (same card component as grid)
│ └──────────┘ └──────────┘ └──────────┘
└──────────────────────────────────────────

[campaign 01] [campaign 02] [campaign 03]
```

The carousel shows the instances matching the selected priority category. Clicking another pill switches the carousel content. Clicking the same pill again collapses it.

**Views 3–4 — Magnetic sticky campaign tab bar:**
As the user scrolls down and the campaign tab bar reaches the top navbar:

```
Step 1: User scrolls down, campaign tabs approach top navbar
┌─────────────────────────────────────┐  ← top navbar (fixed)
│ [◆]  │  Sandbox ●─ Prod │ Yi Z ● │
├─────────────────────────────────────┤
│ [campaign 01][campaign 02][camp 03] │  ← tabs scrolling up...
├─────────────────────────────────────┤
│ ● campaign 01                       │
│ ┌──────┐ ┌──────┐ ┌──────┐        │
│ ...                                 │

Step 2: Tabs "magnetically" dock to the top navbar
┌─────────────────────────────────────┐  ← top navbar (fixed)
│ [◆]  │  Sandbox ●─ Prod │ Yi Z ● │
│ [campaign 01][campaign 02][camp 03] │  ← DOCKED (sticky, z-index above content)
├─────────────────────────────────────┤
│ ● campaign 01                       │
│ ┌──────┐ ┌──────┐ ┌──────┐        │
│ ...                                 │

Step 3: User scrolls back up — tabs decouple
When scrolling upward, once the original position of the tab bar
comes back into view, the tabs smoothly detach from the navbar
and return to their natural flow position.
```

**CSS implementation:**
```css
/* Campaign tab bar uses position: sticky with top offset matching navbar height */
.campaign-tabs {
  position: sticky;
  top: 56px; /* height of top navbar (h-14) */
  z-index: 10;
  background: white;
  border-bottom: 1.5px solid #1B1034;
  transition: box-shadow 0.2s ease;
}

/* When docked, add subtle shadow to indicate stickiness */
.campaign-tabs.is-stuck {
  box-shadow: 0 2px 8px rgba(27, 16, 52, 0.08);
}
```

**View 5 — Campaign tab clicked (scroll-to-group):**
Clicking a campaign tab smooth-scrolls to that campaign's task group section:

```
[campaign 01] [campaign 02●] [campaign 03]    ← campaign 02 is active (filled)
                                                 
● campaign 02                                  ← scrolled into view
┌──────────────────────────────────────┐
│ ┌──────┐ ┌──────┐ ┌──────┐          │       ← campaign container has
│ │ Task │ │ Task │ │ Task │          │          its own border
│ └──────┘ └──────┘ └──────┘          │
│ ┌──────┐                             │
│ │ Task │                             │
│ └──────┘                             │
└──────────────────────────────────────┘
```

### Campaign Tab Hover Animation

Campaign tabs show **abbreviated names** in their default state to save space. On hover, a tab **expands horizontally** with a smooth animation to reveal the full campaign name:

```
Default:   [Kitchen] [RoboM] [Xper]
                 ↓ hover on RoboM
Expanded:  [Kitchen] [RoboMIND Trajectories ●12] [Xper]
```

**Implementation:**
```css
.campaign-tab {
  max-width: 100px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  transition: max-width 0.25s ease, padding 0.15s ease;
}

.campaign-tab:hover {
  max-width: 300px;  /* expand to show full name */
  z-index: 20;       /* sit above siblings */
}
```

- Default: truncated with ellipsis, fixed ~100px max-width
- Hover: expands to fit full text (up to 300px), overlaps neighbors if needed via z-index
- Active tab (clicked): always shows full name, stays expanded
- Badge (instance count) always visible: `●12` at the end

### Priority Items — Three Categories

| Category | Content | Color accent |
|---|---|---|
| **Resume** | In-progress instances (started but not submitted) | `#1B1034` (black — most urgent) |
| **Expiring Soon** | Instances from campaigns ending within 3 days | `#F59E0B` (amber — time pressure) |
| **In Dispute** | Instances with quality disputes pending your response | `#EF4444` (red — needs resolution) |

Each pill shows a count badge. Click expands/collapses the horizontal carousel below.

### Campaign Task Groups

Each campaign section is a **self-contained bordered region** (card principle):

```
● campaign name                    ← bullet + name header outside the container
┌──────────────────────────────────────┐
│ ┌──────┐ ┌──────┐ ┌──────┐          │  ← border-[1.5px] border-[#1B1034]
│ │ Task │ │ Task │ │ Task │          │     contains 3-col grid of instance cards
│ └──────┘ └──────┘ └──────┘          │
│ ┌──────┐ ┌──────┐                    │
│ │ Task │ │ Task │                    │
│ └──────┘ └──────┘                    │
└──────────────────────────────────────┘
```

- Container has `border-[1.5px] border-[#1B1034]` + internal `p-4`
- Cards inside use `border-[1.5px] border-[#1B1034]` (cards within cards)
- 3-column grid with `gap-4`
- Bullet `●` uses campaign accent color or black
- The container allows vertical endless scroll — all campaigns stack vertically

### Task Card — Design Principles

1. **Fixed dimensions** — ALL task cards are the **same height and width**. No variation. This creates a clean, predictable grid. Cards never stretch or shrink to fit content — content adapts to the card.

2. **Content hierarchy** — Each card provides enough information for a contributor to decide "should I work on this?":

```
┌──────────────────────────────┐
│ ┌──────────────────────────┐ │
│ │                          │ │  ← Creative image / thumbnail
│ │   instance-specific      │ │     Video frame, data preview, or
│ │   visual preview         │ │     generated abstract pattern
│ │                          │ │     Fills top ~50% of card
│ └──────────────────────────┘ │
│                              │
│ Review 12 clips from...     │  ← Task description (1-2 lines, clamp)
│                              │
│ 🏷 Labeling · ~45 min       │  ← Task type + estimated time
│ $1.50 · Kitchen Manip.      │  ← Pay + campaign name
│                              │
│ ● In Progress                │  ← Status (if applicable)
│                              │
└──────────────────────────────┘

Height: 260px — fixed, never varies
Width:  320px — fixed, never varies (see fluid layout below)
Border: 1.5px solid #1B1034
Background: white
```

**Gold standard**: 3 columns of 320px cards on a MacBook Air 15" (1440px viewport).
With sidebar expanded (220px) + padding (64px): 1440 - 220 - 64 = 1156px available.
3 × 320 + 2 × 24 = 1008px → fits with 148px margin. Clean.

3. **Visual identity per instance** — The top image area distinguishes instances from each other. Even within the same campaign, each instance shows its own data preview (specific video frame, audio waveform, text snippet). If no preview exists, show a generated pattern using the task-type color.

4. **Status indicators** — Cards show status when relevant:
   - `● In Progress` — black dot, for resume items
   - `⚠ Expiring` — amber, for time-sensitive items
   - `✕ Disputed` — red, for items needing response
   - No status shown on fresh available tasks

5. **Same card everywhere** — The identical card component is used in:
   - Priority carousel (on black canvas, horizontal scroll)
   - Campaign grid sections (on white canvas, column grid)
   - Anywhere a task instance needs to be shown
   - Same 320×260px dimensions in ALL contexts

### Fluid Layout — Task Card Grid

**Principle: card width is FIXED. Adjust layout columns first. Change card width LAST.**

The responsive cascade:

```
Step 1: Reduce columns (card stays 320px)
  ≥1008px available → 3 columns (gold standard for MacBook Air 15")
  ≥664px available  → 2 columns
  ≥320px available  → 1 column

Step 2: Only shrink card width when 1 column doesn't fit
  <320px available  → card width = 100% of container
```

**Implementation:**
```css
.task-card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.task-card {
  width: 320px;   /* fixed — never changes unless viewport < 320px */
  height: 260px;  /* fixed — never changes */
}

/* Only at very small screens: card fills container */
@media (max-width: 400px) {
  .task-card { width: 100%; }
}
```

**Why fixed width, not responsive width:**
- Contributors develop muscle memory for card size — scanning speed improves
- Fixed cards = predictable grid = faster visual parsing
- Column reduction is visible and understandable (3→2→1)
- Card shrinking is disorienting — content reflows, proportions break

**Priority carousel uses the same 320×260 card** in a horizontal scroll container.
Cards are `shrink-0` to maintain width inside `overflow-x-auto`.

**Campaign sections use the same 320×260 card** in a `flex-wrap` layout.
Cards maintain width; when they don't fit in the row, they wrap to the next line.

### Three-Section Layout

The Tasks page is divided into **three visually distinct sections** separated by `border-t-[1.5px] border-[#1B1034]`:

```
┌── Top Navbar (fixed) ──────────────────────────────────┐
│ [◆]                               Sandbox│Prod  Yi Z ● │
╞════════════════════════════════════════════════════════╡
│                                                        │
│  SECTION 1: TODAY'S MESSAGE                            │
│  ─────────────────────────                             │
│  My Tasks                                              │
│  ┌────────────────────────────────────────────────┐    │
│  │ Today: 7 submitted · $18.50 earned · 2 rejected│    │
│  └────────────────────────────────────────────────┘    │
│                                                        │
╞══ 1.5px black line ═══════════════════════════════════╡
│                                                        │
│  SECTION 2: PRIORITY ITEMS                             │
│  ─────────────────────────                             │
│  Priority Items                                        │
│  ┌────────┐ ┌──────────────┐ ┌──────────┐             │
│  │Resume  │ │Expiring Soon │ │In Dispute│             │
│  │   3    │ │      5       │ │    2     │             │
│  └────────┘ └──────────────┘ └──────────┘             │
│       █                                                │  ← connector
│  ┌████████████████████████████████████████████████▸    │  ← carousel
│  │ [Card] [Card] [Card]                          │    │
│  └────────────────────────────────────────────────    │
│                                                        │
╞══ 1.5px black line ═══════════════════════════════════╡
│                                                        │
│  SECTION 3: ENROLLED CAMPAIGN TASKS                    │
│  ──────────────────────────────────                    │
│  [Kitchen][RoboM][Xper] ← campaign selector            │  ← sticky on scroll
│     (horizontal, overlapping, truncated → expand hover) │
│                                                        │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (gray bg)   │
│  │ ● Kitchen Manipulation    View details →            │
│  │   [Card] [Card] [Card]                              │
│  │   [Card] [Card]                                     │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░               │
│                                           (white bg)    │
│  │ ● RoboMIND Trajectories  View details →             │
│  │   [Card] [Card] [Card] [Card]                       │
│                                                        │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  (gray bg)   │
│  │ ● Egocentric Experience   View details →            │
│  │   [Card] [Card] [Card]                              │
│  │   [Card] [Card] [Card] [Card]                       │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░               │
│                                                        │
│  — no more tasks —                                     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Section separation:** 1.5px solid `#1B1034` horizontal lines between sections. Each section has its own internal padding. Sections are visually self-contained.

**Campaign selector behavior:**
- **Horizontal bar** at the top of Section 3 (not vertical/floating)
- Tabs are **overlapping** (negative margin `-ml-[1.5px]`) like a segmented control
- Default: truncated campaign names (~100px max-width)
- Hover: tab expands to show full name (260px, 0.25s ease)
- Active: filled black, synced with scroll position via IntersectionObserver
- **Sticky**: when scrolling, selector sticks below the top navbar
- Positioned **tight to the campaign content** — minimal gap between selector and first campaign group

### Animation: Priority Section Expand/Collapse

When a priority pill is clicked:

1. **Below-content slides down** — the campaign tabs and card grid smoothly translate downward to make room (`transition: transform 0.3s ease, height 0.3s ease`)
2. **Carousel snaps in** — the expanded card row pops up from behind (scale 0.95 → 1.0 + opacity 0 → 1, `0.25s ease-out` with 100ms delay after the slide starts)
3. **Collapse reversal** — cards fade + scale down first, then content slides back up

```css
/* Expandable priority section */
.priority-carousel-enter {
  opacity: 0;
  transform: scale(0.95) translateY(-8px);
}
.priority-carousel-enter-active {
  opacity: 1;
  transform: scale(1) translateY(0);
  transition: opacity 0.25s ease-out 0.1s, transform 0.25s ease-out 0.1s;
}

/* Below-content displacement */
.tasks-content-shift {
  transition: transform 0.3s ease;
}
.tasks-content-shift.expanded {
  transform: translateY(var(--carousel-height));
}
```

### Animation: Responsive Fluid Layout

Task cards have a **fixed minimum width** and never squeeze. The grid column count reduces fluidly as viewport narrows:

| Viewport | Columns | Card behavior |
|---|---|---|
| ≥1024px | 3 columns | Full grid, standard gap |
| 768–1023px | 2 columns | Cards maintain width, gap preserved |
| <768px | 1 column | Single card per row, linear stack, full-width |

**Implementation:** CSS Grid with `auto-fill` and fixed `minmax`:

```css
.task-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
```

This means:
- Cards never go below 260px wide
- At 1200px content width: fits 3 cards (3 × 260 + 2 × 16 = 812, room for 3)
- At 800px: fits 2 cards
- At 500px: fits 1 card
- **No breakpoints needed** — purely fluid, cards maintain their size and readability
- On mobile (single column), each card is the full-width task unit — ready for touch interaction

The campaign container border stretches to fill available width. Cards inside it reflow without shrinking.

---

## Enrollments View — Design Decision

### Enrollment Card Content (Human-first)

Each active enrollment card shows contributor's own stats prominently:

```
┌─────────────────────────────────────────────────────┐
│ Kitchen Manipulation              [Active · 34d left]│
│ 48 contributors enrolled                            │
├─────────────────────────────────────────────────────┤
│ Your Earnings   Submitted   Accepted   Rank          │  ← primary: YOUR stats
│ $34.50          23          18         Top 15%       │
├─────────────────────────────────────────────────────┤
│ Supply $2.50 · Labeling $1.50 · Fixed               │  ← secondary: campaign info
│ ████████████████████░░░░  78% accepted               │
├─────────────────────────────────────────────────────┤
│                    [Continue Tasks]  [Unenroll]       │
└─────────────────────────────────────────────────────┘
```

Click card body → navigates to campaign detail.

### Continue Tasks Behavior

"Continue Tasks" links to `/contribute/tasks#cg-{campaign-name}` — navigates to My Tasks and scrolls directly to the campaign's task group.

### Unenroll Flow

Clicking "Unenroll" opens a **confirmation modal** explaining:
1. No new tasks will be assigned from this campaign
2. **In-progress tasks remain visible** in My Tasks until completed or cancelled
3. Completed tasks and earnings are preserved
4. Once all claimed tasks are resolved, campaign moves to Past

In My Tasks, an unenrolled campaign's section shows a visual marker (e.g., strikethrough or "Unenrolling" badge) to indicate the contributor is winding down, not actively enrolled. Tasks disappear from the campaign group only when:
- The contributor completes the task, OR
- The contributor cancels the in-progress task

### Past Enrollments

Past enrollments show: campaign name, status (Completed/Ended), task count, and total earned. Clickable → campaign detail page.

---

## Sidebar Navigation — Rationale

**Decision:** Break "Campaigns" into two top-level nav items: **Discover** and **Enrollments**, and reorder sidebar as:

```
WORK
  Tasks          ← #1 daily action
  Discover       ← #2 find new work
  Enrollments    ← #3 manage commitments
  Contributions  ← #4 review history

EARNINGS
  Earnings
```

**Reasoning — Action frequency optimization:**

1. **Tasks first** — A returning contributor's primary intent is to continue working. Available task instances generate revenue. Putting this first reduces clicks-to-value to zero.
2. **Discover second** — When the task queue is thin or a contributor wants variety, browsing campaigns is the natural next action. This feeds the enrollment pipeline.
3. **Enrollments third** — Enrollment is a commitment management screen (enroll once, work many times). It's infrequent — most contributors don't unenroll daily. Separating it from Discover removes the tab toggle cognitive load and gives it proper URL-addressable state.
4. **Contributions fourth** — Retrospective review of submission history. Important for trust (on-chain fingerprints, lineage) but not a daily-driver screen.

**Why separate Discover from Enrollments (not tabs):**
- Each serves a distinct intent: "find new" vs "manage existing"
- Each deserves its own URL (`/discover` vs `/enrollments`) for deep-linking from notifications
- Removes the tab toggle — one click, one screen, one purpose
- Matches the "progressive disclosure" principle — new contributors see Discover first, active contributors live in Tasks

**Design principles applied:**
- Human > Data > Developer info priority on campaign cards
- Flat design: white bg, solid borders, no shadows
- Sharp geometry: all rectangular corners
- Minimal color: black/white dominant, color only for status

---

## Architecture

### Label Studio XML as Campaign Config

Every task in a campaign has an XML config defining its annotation UI. This is the annotation-pipeline spec's core decision (§4.1). The XML uses Label Studio's tag library:

**T1 (Data Supply):** Minimal — file upload metadata fields
```xml
<View>
  <Header value="Upload Robotics Video"/>
  <TextArea name="device" placeholder="Recording device..." rows="1"/>
  <TextArea name="environment" placeholder="Environment description..." rows="1"/>
  <Choices name="camera_setup" choice="single">
    <Choice value="single_camera"/><Choice value="dual_camera"/><Choice value="multi_view"/>
  </Choices>
</View>
```

**T2 (Vision Processing):** ML Backend config — no human UI
```xml
<View>
  <Header value="Automated Vision Processing"/>
  <!-- This task is served by ML Backend, not rendered to humans -->
  <!-- Config defines what the ML Backend should produce -->
  <Video name="vid" value="$video_url"/>
  <Rectangle name="person_bbox" toName="vid"/>
  <KeyPointLabels name="pose" toName="vid">
    <Label value="left_shoulder"/><Label value="left_elbow"/><Label value="left_wrist"/>
    <Label value="right_shoulder"/><Label value="right_elbow"/><Label value="right_wrist"/>
  </KeyPointLabels>
  <TimelineLabels name="motion_segment" toName="vid">
    <Label value="keep"/><Label value="review"/>
    <Label value="culled_motion"/><Label value="culled_low_action"/><Label value="culled_person"/>
  </TimelineLabels>
</View>
```

**T3 (Human Annotation):** Full Embodiment-X schema
```xml
<View>
  <Header value="Embodiment-X: Robotics Action Annotation"/>
  <Video name="vid" value="$video_url"/>
  <TimelineLabels name="action" toName="vid">
    <Label value="fold_box" background="#FF6B6B"/>
    <Label value="fold_textile" background="#4ECDC4"/>
    <Label value="packing" background="#45B7D1"/>
    <Label value="pick_place" background="#96CEB4"/>
    <Label value="other_valid" background="#FFEAA7"/>
  </TimelineLabels>
  <Rectangle name="bbox" toName="vid" strokeWidth="2"/>
  <KeyPointLabels name="arm_kp" toName="vid">
    <Label value="left_shoulder"/><Label value="left_elbow"/><Label value="left_wrist"/>
    <Label value="right_shoulder"/><Label value="right_elbow"/><Label value="right_wrist"/>
  </KeyPointLabels>
  <TextArea name="language_instruction" toName="vid"
            placeholder="Describe what the person is doing..." rows="2"/>
  <TextArea name="task_plan" toName="vid"
            placeholder="Steps: 1) pick up towel 2) fold 3) place on shelf" rows="3"/>
</View>
```

**T4 (Validation):** Quality gate config
```xml
<View>
  <Header value="Validation Review"/>
  <Video name="vid" value="$video_url"/>
  <Choices name="quality_decision" choice="single">
    <Choice value="approve"/><Choice value="reject"/><Choice value="needs_revision"/>
  </Choices>
  <Rating name="quality_score" toName="vid" maxRating="5"/>
  <TextArea name="rejection_reason" toName="vid"
            placeholder="If rejecting, explain why..." rows="2" whenChoiceValue="reject"/>
</View>
```

### ML Backend Adapter (Vision Engine)

The Vision Engine (GPU server) is wrapped in a thin adapter that speaks the LS ML Backend protocol. This is the **only** code that knows Vision Engine internals.

```
Contributor Portal API
  │
  │  POST /ml-backend/predict  (LS format: task with video URL)
  │
  ▼
ML Backend Adapter (this repo)
  │
  │  Translates LS request → Vision Engine native API
  │  Translates Vision Engine response → LS predictions (regions)
  │
  ▼
labeling-vision-engine (external GPU server)
  │
  │  POST /tasks/process  (native: file + params → callback)
  │  GET  /tasks/:id/progress
  │  POST /tasks/annotate-frame
  │
  └── Returns: clips, segments, bboxes, keypoints, action segments
```

**Why adapter, not rewrite:** The Vision Engine is stateless, GPU-optimized, and deployed. Rewriting it gains nothing. The adapter makes it LS-compatible so any future ML model (SAM2, GroundingDINO, etc.) can replace or supplement it using the same protocol.

### Native Re-implementation (not iframe)

**Decision (2026-04-16):** The existing labeling tool at `labeling.codatta.io` will NOT be embedded via iframe. The contribution pipeline is re-implemented natively in Contributor Kitchen.

**Reference URLs and their mapping:**

| Production URL | Step | Native route |
|---|---|---|
| `labeling.codatta.io/web` | Supply (upload + detection config) | `/workspace/[campaignId]/[taskId]/supply` |
| `labeling.codatta.io/web/annotate/:id/filter` | AI pre-label review (cull uninformative segments) | `/workspace/[campaignId]/[taskId]/review` |
| `labeling.codatta.io/web/annotate/:id/slice` | Human segmentation + action labeling | `/workspace/[campaignId]/[taskId]/annotate` |

**Why not iframe:**
1. Auth isolation — labeling.codatta.io has its own auth; Supabase sessions don't cross origin
2. Lineage gap — T1→T2→T3→T4 instance chain lives in shared Supabase; the labeling app writes to its own API
3. Brand break — old codatta chrome, not Humanbased Contributor Kitchen
4. State handoff fragility — URL params or postMessage for job_id/campaign_id breaks silently on upstream changes
5. Dead end — labeling-* repos are designated reference-only; taking a runtime dependency locks us to code we plan to abandon

**Reference repos:** `codatta/labeling-website` (UX patterns, component breakdown), `codatta/labeling-api` (VE communication, data structures). Code is rewritten fresh; only logic and UX patterns are carried forward.

### Workspace Routing — Per-Step Routes

**Decision (2026-04-16):** The annotation workspace uses explicit per-step routes, not a single URL with step state.

```
/workspace/[campaignId]/[taskId]/supply    — T1: upload + detection preset config
/workspace/[campaignId]/[taskId]/review    — T3a: cull review (filter uninformative segments)
/workspace/[campaignId]/[taskId]/annotate  — T3b: slice, action label, spatial, language, task plan
/workspace/[campaignId]/[taskId]/export    — T3c: review + submit annotation
```

**Why per-step routes over single URL:**
- Resumability — contributor closes tab mid-annotation, reopens at `/review` exactly where they left off
- Deep-linkable — notifications can link directly to the step that needs attention
- Matches the labeling.codatta.io URL pattern that already validates this approach
- Each step has distinct layout, keyboard shortcuts, and data requirements

### Detection Presets

Campaign-level detection presets stored in `campaigns.params.detection_presets`. Contributor selects one during T1 supply step.

| Preset | Key params |
|---|---|
| Universal | Default YOLO params, no filtering |
| YOLO Human Filter | `filter_humans=true, require_center=true` |
| Workstation | `workstation_mode=true, arm_conf_threshold=0.6` |
| Workstation + Pose | Above + `pose_estimation=true, full_body=true` |

Presets are campaign-configurable (developer portal writes to `campaigns.params`). The contributor portal reads and renders the selector. Custom parameter tuning is available as an "Advanced" toggle below the preset selector.

### Shared Supabase Instance

Same project as developer-portal (`uxafdddzhgdhsabkwmgw`). Contributor-portal adds tables to the `public` schema. Migrations must be additive and non-breaking.

**Existing tables (developer-portal, do NOT modify):**
- `organizations`, `users`, `org_memberships`, `org_invitations`, `org_settings`
- `accounts`, `transactions`
- `api_keys`, `key_cursors`
- `subscriptions`, `verticals`, `topics`
- `deliveries`, `delivery_items`, `consumer_feedback`
- `pricing_schedule`, `access_log`, `usage_daily`, `usage_meter`
- `supply.cfp_frontier`, `supply.cfp_frontier_task`, `supply.cfp_task_submission`, `supply.cfp_task_audit_record`

**New tables (contributor-portal adds):**

```sql
-- ═══════════════════════════════════════════════════════════════
-- Campaign framework (shared contract between both portals)
-- Developer portal writes config; contributor portal writes instances
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE campaigns (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id          uuid REFERENCES organizations(id),
  frontier_id     text NOT NULL,           -- 'robotics' for V1
  template_id     text NOT NULL,           -- 'robotics_video_collection'
  name            text NOT NULL,
  status          text NOT NULL DEFAULT 'draft',
  annotation_config text,                  -- Label Studio XML (per-campaign override)
  params          jsonb DEFAULT '{}',      -- target_quantity, quality_threshold, etc.
  created_at      timestamptz DEFAULT now()
);

CREATE TABLE tasks (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id     uuid REFERENCES campaigns(id) ON DELETE CASCADE,
  task_key        text NOT NULL,            -- 'data_supply', 'vision_processing', etc.
  name            text NOT NULL,
  origin          text NOT NULL,            -- 'manual' | 'auto_generated'
  execution       text NOT NULL,            -- 'human' | 'agent'
  annotation_config text,                   -- Label Studio XML for this task
  ml_backend_url  text,                     -- ML Backend endpoint (for agent tasks)
  config          jsonb DEFAULT '{}',       -- task-specific params
  depends_on      uuid[],                   -- parent task IDs in DAG
  position        int NOT NULL,
  UNIQUE (campaign_id, task_key)
);

CREATE TABLE task_instances (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id         uuid REFERENCES tasks(id),
  campaign_id     uuid REFERENCES campaigns(id),
  parent_instances uuid[],                  -- lineage: upstream instance IDs
  content_hash    text,                     -- SHA-256 of canonicalized payload
  annotation_config_ver text,               -- 'embodiment_x_v1.0.0'
  contributor_id  uuid,
  quality_grade   text,                     -- S|A|B|C|D
  status          text NOT NULL DEFAULT 'pending',
  payload         jsonb,                    -- task-specific output
  submitted_at    timestamptz,
  validated_at    timestamptz,
  created_at      timestamptz DEFAULT now()
);
CREATE INDEX idx_instances_parent ON task_instances USING GIN (parent_instances);
CREATE INDEX idx_instances_campaign ON task_instances (campaign_id, status);
CREATE INDEX idx_instances_hash ON task_instances (content_hash);

-- ═══════════════════════════════════════════════════════════════
-- Vision processing workflow
-- Bridges Vision Engine results to campaign instances
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE processing_jobs (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  t1_instance_id  uuid REFERENCES task_instances(id),
  campaign_id     uuid REFERENCES campaigns(id),
  filename        text NOT NULL,
  task_name       text,
  scenario_code   text DEFAULT 'SCENE_01',
  status          text NOT NULL DEFAULT 'processing',
  step            text DEFAULT 'upload',
  step_pct        int DEFAULT 0,
  input_type      text,                     -- 'video' | 'sequence'
  file_hash       text,
  compress_px     int DEFAULT 0,
  detection_params jsonb,                   -- params sent to Vision Engine
  result          jsonb,                    -- raw Vision Engine callback result
  created_at      timestamptz DEFAULT now()
);

CREATE TABLE clips (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id          uuid REFERENCES processing_jobs(id) ON DELETE CASCADE,
  t2_instance_id  uuid REFERENCES task_instances(id),
  start_idx       int, end_idx int,
  start_ms        int, end_ms int,
  start_ns        bigint, end_ns bigint,
  fps             float,
  thumb_url       text,
  blur_score      float,
  brightness      float,
  frame_count     int,
  actions         jsonb                     -- action segments from Vision Engine
);

CREATE TABLE clip_frames (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clip_id         uuid REFERENCES clips(id) ON DELETE CASCADE,
  frame_idx       int NOT NULL,
  file_url        text NOT NULL,
  timestamp_ns    bigint,
  motion_score    float,
  person_detected boolean,
  person_bbox     jsonb,
  arm_keypoints   jsonb,
  hand_activity_score float,
  blur_score      float,
  brightness      float
);
CREATE INDEX idx_frames_clip ON clip_frames (clip_id, frame_idx);

CREATE TABLE segments (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id          uuid REFERENCES processing_jobs(id) ON DELETE CASCADE,
  state           text NOT NULL,            -- keep|review|culled_motion|culled_low_action|culled_person
  start_idx       int, end_idx int,
  frame_count     int,
  duration_ms     int,
  thumb_url       text,
  cull_reason     text,
  is_reviewed     boolean DEFAULT false,
  review_decision text                      -- valid|invalid (set during cull review)
);

-- ═══════════════════════════════════════════════════════════════
-- Annotation output (Embodiment-X schema)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE annotations (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  t3_instance_id  uuid REFERENCES task_instances(id),
  job_id          uuid REFERENCES processing_jobs(id),
  temporal        jsonb NOT NULL,           -- segments: [{start_ns, end_ns, action_label, language_instruction, task_plan[]}]
  spatial         jsonb,                    -- frames: [{frame_idx, bounding_boxes[], keypoints[]}]
  quality_metadata jsonb,                   -- {blur_score, brightness, person_detected, hand_activity_score}
  created_at      timestamptz DEFAULT now()
);

-- ═══════════════════════════════════════════════════════════════
-- Contributors + mock lineage
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE contributors (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name    text,
  email           text,
  wallet_address  text,
  reputation_score float DEFAULT 0,
  created_at      timestamptz DEFAULT now()
);

CREATE TABLE lineage_staging (
  instance_id     uuid PRIMARY KEY REFERENCES task_instances(id),
  contributor_did text,
  campaign_id     uuid,
  task_id         uuid,
  frontier_id     text,
  parent_instances uuid[],
  content_hash    text,
  annotation_config_ver text,
  compensation_model text DEFAULT 'fixed',
  upstream_shares jsonb,
  quality_grade   text,
  staged_at       timestamptz DEFAULT now(),
  staging_status  text DEFAULT 'mock_committed'
);
```

---

## Iteration Strategy

Each iteration delivers a working vertical slice. Labeling-* repos are logic reference — we implement fresh using LS XML configs, ML Backend protocol, and shared Supabase.

### Iteration 0 — Foundation
Project scaffold, domain types, DB schema, campaign template with LS XML configs.

### Iteration 1 — Vision Processing Pipeline
ML Backend adapter wrapping Vision Engine. Upload → process → results stored in Supabase. T1 and T2 instances created with lineage.

### Iteration 2 — Annotation Workflow
Human annotation UI: cull review, slice, action labeling. Reference labeling-website for UX patterns. T3 instances with lineage.

### Iteration 3 — Embodiment-X Extensions
Spatial annotation (bbox editing from ML Backend pre-labels), language instructions, task plan. Full annotation schema.

### Iteration 4 — Campaign Framework & Lineage
Campaign discovery, task DAG visualization, instance lineage tracking, content hashing. Developer portal integration.

### Iteration 5 — Validation & Mocks
T4 quality gates, mock AttemptIndex, mock attribution hooks. Export with lineage metadata.

---

## Infrastructure Architecture

### Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
├──────────────┬──────────────┬──────────────┬────────────────┤
│              │              │              │                │
│   Vercel     │ Google Cloud │  Supabase    │  HuggingFace   │
│   (Frontend) │ Run (API)    │  (DB+Auth+   │  (Test data    │
│              │              │   Storage)   │   + campaigns) │
│   Next.js 16 │ FastAPI      │              │                │
│   Static +   │ Python 3.13  │  Postgres    │  Datasets API  │
│   SSR        │ + MCP (V2)   │  Auth        │  for seeding   │
│              │              │  Storage     │                │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

| Layer | Service | Deploy | Notes |
|---|---|---|---|
| **Frontend** | Vercel | `vercel deploy` | Next.js 16 App Router. Preview + production. |
| **API** | Google Cloud Run | `gcloud run deploy` | FastAPI. Serves webapp + future CLI + MCP (V2). |
| **Database** | Supabase (shared) | Managed | Same project as developer portal. Shared `auth.users`. |
| **Storage** | Supabase Storage | Managed | Video uploads, processed frames, avatars. |
| **Auth** | Supabase Auth | Managed | OAuth (Google, LinkedIn, HuggingFace, GitHub) + email OTP. |
| **Docs** | Separate build | TBD | Merges with docs.humanbased.ai eventually. |

### Service URLs

Contributor portal adopts the nested-namespace pattern so `api.humanbased.ai` (already claimed by the developer portal) remains untouched, and contributor-owned services are scoped under `contributor.*`.

| Service | Production | Staging |
|---|---|---|
| Frontend (Vercel) | `contributor.humanbased.ai` | `staging.contributor.humanbased.ai` |
| API (Cloud Run, `asia-northeast1`) | `api.contributor.humanbased.ai` | `staging.api.contributor.humanbased.ai` |
| Docs | (merges into `docs.humanbased.ai`) | — |

**Temporary treatment — main-only, everything to staging:**
During V1 rapid iteration, only the two **staging** URLs are registered and receiving deploys. Production DNS records (`contributor.humanbased.ai`, `api.contributor.humanbased.ai`) are reserved but left unconfigured. Main pushes build Vercel Previews aliased to the staging URL; Cloud Run deploys target `contributor-api-staging` only. Exit trigger: `I4-1` ships → flip Vercel production branch, provision `contributor-api` prod service, register the prod CNAMEs.

**Long-term convergence — unified API surface:**
The `api.contributor.humanbased.ai` split is a V1 engineering convenience, not a user-facing product boundary. End users (developers consuming the platform API, AI agents consuming the MCP surface, CLIs) should see **one** unified API origin. The directional goal is to collapse `api.humanbased.ai` and `api.contributor.humanbased.ai` into a single gateway that routes internally based on scope/role, so consumers experience the platform as one product regardless of which portal the data flowed through. Tracking this is a separate initiative — the split API is a temporary stage, not the destination.

### Database Strategy — Shared Supabase, Two Environments, Branching on Staging

**Decision:** Both portals (developer + contributor) co-live on **two shared Supabase projects** — staging and production. Git-like **branching is used on staging only** for isolating concurrent schema work. Production is never branched.

```
Supabase STAGING project  (shared: dev portal + contributor portal)
│                         active development target
│
├── main (default staging state)
│   ├── Developer portal tables
│   ├── Contributor portal tables
│   └── auth.users (shared)
│
├── branch: feat/contributor-xyz   ← per-feature isolation
├── branch: feat/dev-abc            ← per-feature isolation
└── merge branch → main             ← applies migration to staging main
                                       validate → manually promote to production

Supabase PRODUCTION project  (shared: dev portal + contributor portal)
│                            release target, NEVER branched
│
├── Developer portal tables
├── Contributor portal tables
└── auth.users (shared)
```

**Why this setup:**

1. **Shared DBs, not separate** — One `auth.users` per environment means role switching ("Switch to Developer") is an RLS change, not cross-project auth. The `campaigns` table is the shared contract (developer portal writes config, contributor portal reads + writes instances).

2. **Staging + Production, not one environment** — Staging isolates active development from release. Migrations are validated on staging before promotion to production.

3. **Branch staging, never production** — Branching exists to isolate concurrent schema work. That risk lives in active dev (staging), not release (production). Branching production would turn the source of truth into a dev target — unacceptable.

**Development workflow:**

```
Feature development:
  1. Create Supabase branch off staging/main  (e.g. `feat/instance-claim-flow`)
  2. Apply schema changes + develop + test against the branch
  3. PR review (code + migration SQL)
  4. Merge branch → staging/main  (applies migration to staging)
  5. Validate in staging
  6. Manually promote migration SQL to production
     (same SQL, run against production Supabase URL)

Env wiring:
  .env.local (local dev)        → staging branch URL + key
  Vercel preview deploys        → staging main URL + key
  Vercel production             → production URL + key
  packages/api (Cloud Run)      → production URL + key
```

**Safety rules — migration hygiene:**
- All DDL uses `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`
- Never `DROP TABLE` on shared DBs without explicit sign-off from both portal teams
- Never branch production — staging only
- New columns use defaults (no backfill required)
- RLS policies scope access per contributor — can only see/modify own rows
- Contributor portal routes only write to contributor tables, never developer portal tables
- Test destructive queries on an isolated branch first, not directly on staging/main

**Joint adoption — critical:**
Supabase branching on shared projects must be coordinated with the **developer portal team**. Branches affect DB state both teams share at merge time. Both portals agree on:
- Branch naming conventions (`feat/portal-feature-name`)
- Who can create/merge branches
- How long branches live (days, not weeks)
- Review protocol before merge to staging/main

**Table Ownership Map — who owns what in the shared DBs**

Each table has a single **owning portal**. The owner is the only system permitted to run DDL against it or write via server-role keys. The non-owner may *read* via RLS-scoped queries and may *write instance rows* to the shared-contract tables through the owner's API boundary.

| Table | Owner | Contributor portal access | Developer portal access |
|---|---|---|---|
| `organizations`, `accounts`, `api_keys`, `subscriptions`, `deliveries`, `delivery_items`, `charges`, `org_*`, `usage_meter`, `webhook_endpoints`, `consumer_feedback`, `key_cursors`, `api_key_daily_usage`, `verticals`, `topics` | **Developer portal** | none | full |
| `users` (shared identity) | **Developer portal** | read-only (lookup by id) | full |
| `auth.*` (Supabase Auth) | Supabase | read own session | read own session |
| `campaigns`, `tasks` (**shared contract — config**) | **Developer portal** | read-only | full |
| `task_instances`, `enrollments`, `contributions`, `lineage_records` (**shared contract — execution**) | **Contributor portal** | full | read-only |
| `contributors`, `credentials` | **Contributor portal** | full | read-only (lookup) |

**Enforcement mechanisms:**

1. **Postgres roles** — Each portal uses a dedicated service role whose grants match the ownership map. Contributor portal's service role has no `INSERT/UPDATE/DELETE` on developer-owned tables. Cross-portal writes fail at the DB layer, not at the application layer.
2. **RLS policies** — Every shared-contract table has policies keyed off `auth.uid()` + portal role, verified in migration tests.
3. **Migration namespacing** — Migrations live in each repo's own `sql-query/migrations/` directory. A migration that touches a table the repo does *not* own requires a cross-repo PR reference in the migration header comment.
4. **Code-level guard** — Both repos' DB clients wrap the Supabase client with a table-allowlist that matches the ownership map. Attempting to mutate a disallowed table throws before the network call.

**Environment Guards — seed scripts and destructive operations**

Any script that writes bulk data (seed campaigns, backfill contributors, fixture loading) must:

1. Read `SUPABASE_URL` from env — **never hardcoded**
2. Print the target URL + DB name and require an interactive `y/N` confirmation before proceeding
3. Refuse to run against production unless **both** conditions hold: `NODE_ENV=production` (or `ENV=production`) is set AND a `--confirm-production` flag is passed
4. Log every insert to a run-report file (for rollback)
5. Stamp inserted rows with `seed_run_id` (UUID per script invocation) so seed data can be deleted cleanly

**Migration authorship — runtime ownership vs. DDL authorship (separated)**

Strict runtime ownership (runtime service roles cannot write cross-portal) does not require strict DDL authorship. During rapid V1 iteration, the contributor portal often needs to evolve the shared-contract tables (`campaigns`, `tasks`) without a repo context switch. We allow this under a **phased DDL exception**:

| Phase | DDL authorship on `campaigns`/`tasks` | Runtime writes on `campaigns`/`tasks` |
|---|---|---|
| **V1 build (now)** — schema still in flux | Either portal may author. Filename must start with `shared_`. Migration header comment must link to a companion notify-PR (or Linear ticket) in the sibling repo so the dev-portal team is aware before staging merge. | Dev portal only (runtime roles unchanged). |
| **Post-V1 stabilization** — trigger: `I4-1` ships | Dev portal only. Contributor portal raises a change request in the dev-portal repo. | Dev portal only. |

**Why this split works:**
- Runtime traffic is always protected by Postgres grants — the shared-infra safety guarantee holds end-to-end regardless of who authored the DDL.
- DDL happens infrequently and only via reviewed migration files, so "who holds the pen" is a cadence question, not a security one.
- The V1 exception has a named exit criterion (`I4-1`), so it won't silently become permanent.

**Concrete DDL roles:**
- `migration_role` — full DDL + DML grants; only loaded by the migration runner (CI or `supabase db push`), never by application servers.
- `contributor_portal_role` / `developer_portal_role` — runtime roles, grants per ownership map. Loaded by the app servers via `SUPABASE_SECRET_KEY`.

**Authorship diagrams — phase × environment**

The grant matrix below is the single source of truth. Staging and Production share the same matrix within a phase; the difference between environments is *branching and promotion*, not grants. The difference between phases is *who may author DDL on shared-contract tables*.

```
┌── V1 PHASE — STAGING ────────────────────────────────────────────┐
│                                                                   │
│  Shared-contract      Contributor-owned       Others              │
│  campaigns, tasks     task_instances,         organizations,      │
│                       enrollments,            accounts,           │
│                       contributions,          api_keys,           │
│                       lineage_records,        subscriptions,      │
│                       contributors,           deliveries, charges,│
│                       credentials             users, …            │
│  ───────────────────  ──────────────────────  ──────────────────  │
│  DDL authorship       DDL authorship          DDL authorship      │
│    dev     ✓            dev     ✗               dev     ✓         │
│    contrib ✓ *          contrib ✓               contrib ✗         │
│                                                                   │
│  Runtime writes       Runtime writes          Runtime writes      │
│    dev     ✓            dev     ✗ (RO)          dev     ✓         │
│    contrib ✗ (RO)       contrib ✓               contrib ✗ (none) │
│                                                                   │
│  * `shared_` filename prefix + notify-PR to developer-portal      │
│  Branching: allowed (feature branches off staging/main)           │
└───────────────────────────────────────────────────────────────────┘

┌── V1 PHASE — PRODUCTION ─────────────────────────────────────────┐
│                                                                   │
│  Grant matrix: IDENTICAL to V1 staging above.                     │
│                                                                   │
│  Environment differences:                                         │
│    • No branching — direct push from owning-repo's main           │
│    • Migration promoted only after 24h staging bake               │
│    • Same SQL file that ran on staging-main runs here             │
│    • Reviewer approval gate on the workflow_dispatch job          │
└───────────────────────────────────────────────────────────────────┘

┌── POST-V1 CONVERGENCE — STAGING & PRODUCTION ────────────────────┐
│       (trigger: I4-1 ships → exception auto-expires)              │
│                                                                   │
│  Shared-contract      Contributor-owned       Others              │
│  campaigns, tasks     task_instances, …       organizations, …    │
│  ───────────────────  ──────────────────────  ──────────────────  │
│  DDL authorship       DDL authorship          DDL authorship      │
│    dev     ✓            dev     ✗               dev     ✓         │
│    contrib ✗            contrib ✓               contrib ✗         │
│                                                                   │
│  Runtime writes       Runtime writes          Runtime writes      │
│    dev     ✓            dev     ✗ (RO)          dev     ✓         │
│    contrib ✗ (RO)       contrib ✓               contrib ✗         │
│                                                                   │
│  V1 exception is gone. Contributor portal raises DDL change       │
│  requests via the developer-portal repo. Runtime grants unchanged │
│  (they were always strict). Branching rule unchanged (staging-    │
│  only). Promotion protocol unchanged.                             │
└───────────────────────────────────────────────────────────────────┘
```

**Long-term convergence** — the `I4-1` trigger is the point at which the contributor portal stops authoring DDL against shared-contract tables. Post-V1 matches the steady-state we want forever: strict ownership everywhere, one repo holds the pen per table, runtime grants remain the enforcement floor.

**Promotion protocol — staging → production**

1. Migration SQL is written and applied on a Supabase branch off staging/main
2. PR opened; migration SQL reviewed by both portal teams if it touches shared-contract tables
3. Branch merged → staging/main. Staging validation runs (smoke tests, RLS assertions, ownership-grant tests)
4. After at least 24 hours of staging bake-in without regression, the **same migration file** is applied to production via a manual `supabase db push --linked` against the production project
5. Production migration is announced in a shared #db-migrations channel before and after the run
6. Production never runs migrations from a branch — only from main of the owning repo

**Existing tables in the shared DBs:**

*Developer portal:* `organizations`, `accounts`, `transactions`, `api_keys`, `verticals`, `topics`, `subscriptions`, `deliveries`, `delivery_items`, `charges`, `users`, `org_memberships`, `org_invitations`, `org_settings`, `consumer_feedback`, `webhook_endpoints`, `usage_meter`, `api_key_daily_usage`, `key_cursors`

*Contributor portal (added):* `contributors`, `campaigns`, `tasks`, `task_instances`, `enrollments`, `contributions`, `lineage_records`, `credentials`

> **Correction (2026-04-17):** `campaigns` and `tasks` are *developer-portal owned* (the developer portal writes campaign config). The contributor portal reads config and writes execution-side rows only (`task_instances`, `enrollments`, `contributions`, `lineage_records`). The ownership map above is the authoritative reference — any earlier lines suggesting otherwise are superseded.

### MVP Build Order

```
Phase 1: Foundation (current → functional)
  1. Supabase project + schema migration
  2. Auth (OAuth + email OTP)  
  3. API scaffold (FastAPI on Cloud Run)
  4. Connect frontend to real auth
  5. Connect frontend to real data

Phase 2: Campaigns + Tasks
  6. Seed real campaigns from HuggingFace datasets
  7. Campaign CRUD API
  8. Task instance lifecycle API
  9. Enrollment API

Phase 3: Workspace + Contributions
  10. Annotation workspace (iframe integration)
  11. Submission API
  12. Contributions tracking
  13. Earnings calculation

Phase 4: Extensions
  14. CLI tool
  15. MCP server for AI agent access
  16. On-chain lineage (mock → real)
  17. Docs site
```

---

## Data Model

### Schema Overview

```
contributors ←──── enrollments ────→ campaigns
     │                                    │
     │                                    ├── tasks (types within campaign)
     │                                    │
     └── contributions ←── task_instances ─┘
              │
              └── lineage_records
              
contributors ←── credentials (skill verification)
```

### Table: `contributors`

```sql
CREATE TABLE contributors (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_id       UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  username      TEXT UNIQUE NOT NULL,
  display_name  TEXT NOT NULL,
  email         TEXT UNIQUE NOT NULL,
  avatar_url    TEXT,
  reputation    INTEGER DEFAULT 0 CHECK (reputation >= 0 AND reputation <= 1000),
  tier          TEXT DEFAULT 'contributor' CHECK (tier IN ('contributor', 'expert', 'admin')),
  skills        JSONB DEFAULT '[]',       -- ["Robotics Annotation", "Data Collection"]
  preferences   JSONB DEFAULT '{}',       -- {task_types: [], time_commitment: "5-15"}
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now()
);
```

### Table: `campaigns`

```sql
CREATE TABLE campaigns (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id            UUID,                   -- references orgs table (shared with dev portal)
  title             TEXT NOT NULL,
  description       TEXT,
  banner_url        TEXT,                   -- campaign banner image
  frontier          TEXT NOT NULL,          -- "Robotics", "NLP", "Vision", etc.
  tags              TEXT[] DEFAULT '{}',
  compensation_model TEXT NOT NULL CHECK (compensation_model IN ('fixed', 'royalty', 'hybrid', 'bounty')),
  compensation_config JSONB NOT NULL,       -- {supply_rate: 2.50, labeling_rate: 1.50, ...}
  annotation_config  TEXT,                  -- Label Studio XML config
  privacy_tier      TEXT DEFAULT 'open' CHECK (privacy_tier IN ('open', 'shielded', 'guarded', 'sealed')),
  status            TEXT DEFAULT 'active' CHECK (status IN ('draft', 'active', 'paused', 'ended', 'completed')),
  target_instances  INTEGER NOT NULL,
  current_instances INTEGER DEFAULT 0,
  starts_at         TIMESTAMPTZ,
  ends_at           TIMESTAMPTZ,
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);
```

### Table: `tasks`

Task types within a campaign (Supply, Labeling, Validation). Defines the pipeline DAG.

```sql
CREATE TABLE tasks (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id     UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  type            TEXT NOT NULL CHECK (type IN ('supply', 'labeling', 'validation')),
  executor        TEXT NOT NULL CHECK (executor IN ('human', 'agent')),
  title           TEXT NOT NULL,
  description     TEXT,
  pay_rate        DECIMAL(10,2),          -- NULL for agent tasks or royalty
  estimated_time  INTEGER,                -- minutes
  position        INTEGER NOT NULL,       -- order in pipeline DAG
  depends_on      UUID[],                 -- task IDs this depends on
  qualification_requirements JSONB DEFAULT '{}',
  config          JSONB DEFAULT '{}',     -- task-specific config
  created_at      TIMESTAMPTZ DEFAULT now()
);
```

### Table: `task_instances`

Individual work items — what contributors see as cards.

```sql
CREATE TABLE task_instances (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id         UUID REFERENCES tasks(id) ON DELETE CASCADE,
  campaign_id     UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  contributor_id  UUID REFERENCES contributors(id),
  status          TEXT DEFAULT 'available' CHECK (status IN (
    'available', 'claimed', 'in_progress', 'submitted',
    'in_review', 'accepted', 'rejected', 'disputed', 'cancelled'
  )),
  priority        TEXT CHECK (priority IN ('resume', 'expiring', 'dispute')),
  data_url        TEXT,                   -- source data (video, image, etc.)
  thumbnail_url   TEXT,                   -- preview image for card
  annotation_data JSONB,                  -- submitted annotation payload
  quality_grade   TEXT,                   -- A/B/C/D/F
  pay_amount      DECIMAL(10,2),
  parent_instances UUID[],                -- lineage: what this was derived from
  content_hash    TEXT,                   -- for on-chain attribution
  claimed_at      TIMESTAMPTZ,
  submitted_at    TIMESTAMPTZ,
  reviewed_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);
```

### Table: `enrollments`

Contributor ↔ Campaign relationship.

```sql
CREATE TABLE enrollments (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contributor_id  UUID REFERENCES contributors(id) ON DELETE CASCADE,
  campaign_id     UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  status          TEXT DEFAULT 'active' CHECK (status IN ('active', 'unenrolling', 'completed', 'ended')),
  enrolled_at     TIMESTAMPTZ DEFAULT now(),
  unenrolled_at   TIMESTAMPTZ,
  total_submitted INTEGER DEFAULT 0,
  total_accepted  INTEGER DEFAULT 0,
  total_rejected  INTEGER DEFAULT 0,
  total_earned    DECIMAL(10,2) DEFAULT 0,
  UNIQUE(contributor_id, campaign_id)
);
```

### Table: `contributions`

Completed work record — the ledger.

```sql
CREATE TABLE contributions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  instance_id     UUID REFERENCES task_instances(id) ON DELETE CASCADE,
  contributor_id  UUID REFERENCES contributors(id) ON DELETE CASCADE,
  campaign_id     UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  task_type       TEXT NOT NULL,
  status          TEXT NOT NULL CHECK (status IN ('accepted', 'rejected', 'in_review', 'disputed')),
  quality_grade   TEXT,
  pay_amount      DECIMAL(10,2),
  pay_type        TEXT CHECK (pay_type IN ('fixed', 'royalty', 'bounty')),
  chain_id        TEXT,                   -- on-chain fingerprint hash
  submitted_at    TIMESTAMPTZ NOT NULL,
  reviewed_at     TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT now()
);
```

### Table: `lineage_records`

On-chain data attribution tracking (mock in V1, real in V3).

```sql
CREATE TABLE lineage_records (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  instance_id     UUID REFERENCES task_instances(id) ON DELETE CASCADE,
  contributor_id  UUID REFERENCES contributors(id),
  content_hash    TEXT NOT NULL,
  parent_hashes   TEXT[],                 -- upstream data this derives from
  chain_tx_hash   TEXT,                   -- blockchain transaction hash
  status          TEXT DEFAULT 'mock_committed' CHECK (status IN ('mock_committed', 'pending', 'committed', 'failed')),
  metadata        JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ DEFAULT now()
);
```

### Table: `credentials`

Skill verification tiers for contributors.

```sql
CREATE TABLE credentials (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contributor_id  UUID REFERENCES contributors(id) ON DELETE CASCADE,
  skill           TEXT NOT NULL,
  tier            TEXT DEFAULT 'unverified' CHECK (tier IN ('unverified', 'tutorial_passed', 'credential_verified', 'expert')),
  verified_at     TIMESTAMPTZ,
  document_url    TEXT,                   -- uploaded credential
  metadata        JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE(contributor_id, skill)
);
```

### Indexes

```sql
CREATE INDEX idx_instances_campaign ON task_instances(campaign_id);
CREATE INDEX idx_instances_contributor ON task_instances(contributor_id);
CREATE INDEX idx_instances_status ON task_instances(status);
CREATE INDEX idx_enrollments_contributor ON enrollments(contributor_id);
CREATE INDEX idx_contributions_contributor ON contributions(contributor_id);
CREATE INDEX idx_contributions_campaign ON contributions(campaign_id);
CREATE INDEX idx_lineage_instance ON lineage_records(instance_id);
CREATE INDEX idx_credentials_contributor ON credentials(contributor_id);
```

---

## Test Campaign Seeding — HuggingFace Datasets

Create real-world campaigns with actual data from HuggingFace to test the full system. Each campaign includes: tutorial, training requirements, annotation schema (LS XML), and seeded task instances.

### Seed Campaigns

| Campaign | HuggingFace Source | Compensation | Instances to Seed |
|---|---|---|---|
| Kitchen Manipulation | nvidia/PhysicalAI-Robotics-Manipulation-Kitchen | Fixed ($2.50/$1.50) | 50 |
| RoboMIND Trajectories | x-humanoid-robomind/RoboMIND | Royalty | 100 |
| Egocentric Experience | ropedia-ai/xperience-10m | Hybrid ($1.00 + royalty) | 200 |
| Humanoid Motion Library | bones-studio/seed | Bounty ($5,000/10K) | 50 |
| VLA Community | HuggingFaceVLA/community_dataset_v1 | Fixed ($0.75/$1.25) | 100 |

### Seeding Script

```python
# packages/api/scripts/seed_campaigns.py
# 1. Create campaigns in Supabase from design/sample-data.md specs
# 2. Download sample data from HuggingFace datasets API
# 3. Upload to Supabase Storage
# 4. Create task definitions (Supply → Labeling → Validation pipeline)
# 5. Create task_instances with real thumbnails/previews
# 6. Create tutorial/qualification requirements per campaign
```

Each seeded campaign includes:
- **Tutorial**: Markdown + quiz questions stored in campaign config
- **Training requirements**: Qualification rules in `tasks.qualification_requirements`
- **Annotation schema**: Label Studio XML in `campaigns.annotation_config`
- **Real data**: Video frames/images from HuggingFace as task instance thumbnails

---

## Build Queue

### 🔜 Next Up

- [ ] **U1-1: Auth Polish — OAuth Fold + OTP Login & Password Reset** — Tighten sign-in/sign-up UX during the OAuth-disabled window
  - **User:** Contributors (signed-out), including returning users who forgot their password
  - **Acceptance Criteria:**
    - **OAuth fold + temporary disable:**
      - Primary providers visible by default: Google, LinkedIn
      - Secondary providers folded behind a "Show more sign-in options" toggle: GitHub, HuggingFace
      - All four OAuth buttons rendered in a disabled/greyed state — cursor `not-allowed`, `aria-disabled="true"`, click short-circuits with no network call
      - Small caption under the OAuth block: "OAuth sign-in is temporarily unavailable. Use email below." — no modal, no alert
      - Disabled state driven by env flag `NEXT_PUBLIC_OAUTH_ENABLED` (default `false`); flipping the flag re-enables all four without code change
    - **Password sign-in (default tab):** Email + password form — behavior unchanged from current implementation
    - **OTP sign-in (new tab on `/auth/signin`):** Tab/segmented toggle — "Password" | "Email code"
      - Email input → "Send code" → 6-digit OTP input (reuses `components/auth/otp-input.tsx`) → redirect to `/contribute`
      - `supabase.auth.signInWithOtp({ email, options: { shouldCreateUser: false } })` + `verifyOtp({ email, token, type: 'email' })`
      - Resend button disabled with visible countdown for 60s after each send
      - Error surfaces for: invalid code, expired code, rate-limited, unknown email (generic copy to prevent enumeration)
    - **Password reset via OTP (new route `/auth/reset-password`):** Linked from signin via "Forgot password?"
      - Step 1: email input → send OTP (`signInWithOtp`, `shouldCreateUser: false`)
      - Step 2: 6-digit OTP input → `verifyOtp({ type: 'email' })` establishes session
      - Step 3: new password + confirm → `supabase.auth.updateUser({ password })` → auto-signed-in redirect to `/contribute`
      - 3-step progress indicator reuses `components/auth/step-indicator.tsx`
      - Generic success copy on step 1 ("If an account exists, we sent a code.") regardless of email validity
    - **Signup flow — dual mode:** Signup page gets a matching "Password" | "Email code" tab toggle
      - **Password tab (new):** email + password (+ name + username) → `supabase.auth.signUp({ email, password, options: { data: { full_name, username } } })` → redirect to `/onboarding` (Supabase's own email-confirmation email is sent in background; product treats signup as complete on success)
      - **Email code tab:** current 3-step flow (email → OTP → profile + password) preserved unchanged
      - Tab selection persists only during the session — no cookie
      - Primary CTA copy adapts per mode ("Create account" vs. "Send verification code")
    - **Layout + brand tokens:** Reuses `app/auth/layout.tsx`, existing colors/borders/typography — no new design tokens introduced
  - **Technical Notes:**
    - Components to reuse: `components/auth/oauth-buttons.tsx`, `otp-input.tsx`, `password-input.tsx`, `step-indicator.tsx`
    - New route files: `src/app/auth/reset-password/page.tsx` (and a sub-step state machine inside that page)
    - `oauth-buttons.tsx` changes: split providers into `primary` + `secondary`; add `showMore` local state; accept `disabled` prop driven by env flag; retain provider order Google → LinkedIn → GitHub → HuggingFace
    - Signin page state machine: `mode: 'password' | 'otp'`; OTP sub-states `idle → code_sent → verifying → error`
    - Reset-password page state machine: `step: 'email' | 'otp' | 'new_password'`
    - **Verify against current Supabase JS SDK docs before coding** — `signInWithOtp`, `verifyOtp`, `updateUser` signatures may have shifted; do not trust cached API knowledge
    - Email enumeration: Supabase already returns generic success on unknown emails; no extra handling needed, just match copy
    - Rate-limit: Supabase default cooldown ~60s per email; countdown uses client timer (no server round-trip)
  - **Tests Required:**
    - OAuth buttons render disabled when flag is off; clickable when flag is on; "Show more" toggle reveals GitHub + HuggingFace
    - Password sign-in regression: valid creds → redirect; invalid creds → error surface
    - OTP sign-in: send → verify → redirect; invalid code → error; resend disabled during 60s countdown
    - Password reset: unknown email → generic success copy; known email → OTP works → new password set → user is signed in with new password
    - Accessibility: keyboard tab order on signin form, `aria-disabled` on OAuth buttons, focus management on OTP inputs, form labels announced by screen readers
  - **Solution approach:**
    1. **Env flag + copy** — add `NEXT_PUBLIC_OAUTH_ENABLED=false` to `.env.example`; add microcopy strings to a small `auth/copy.ts` helper to keep page files lean
    2. **Refactor `oauth-buttons.tsx`** — split providers array, add `showMore` local state + "Show more" text button, add `disabled` prop driven by env flag, render disabled visual style (muted border, `cursor-not-allowed`, `aria-disabled`)
    3. **Signin page** — wrap current form in a `Tabs`-style toggle (plain React state, no new UI lib); OTP branch uses `otp-input.tsx`; "Forgot password?" link sits below the password field, routes to `/auth/reset-password`
    4. **Reset-password route** — new `src/app/auth/reset-password/page.tsx`; 3-step wizard driven by local state + `step-indicator.tsx`; on step 3 success, use `window.location.href = '/contribute'` for a full reload so server-side auth state re-reads cleanly
    5. **Error + countdown helpers** — small `useResendCooldown(seconds)` hook returns `{ remaining, start }`; error strings funnel through a mapper to generic user-facing copy
    6. **Tests** — component-level tests with React Testing Library (Vitest) for state machines and a11y; manual end-to-end smoke against staging Supabase before merge
  - **Non-goals for this item:**
    - Bringing HuggingFace OAuth online (requires custom OIDC bridge — separate spike)
    - OTP-based signup / wallet connect / magic-link (non-OTP) flows
    - New visual design tokens — reuses existing auth layout

- [ ] **I0-3: Staging + Production Supabase Environments & Shared-Infra Safety** — Split envs and enforce ownership boundary
  - **User:** Engineers (both portals)
  - **Acceptance Criteria:**
    - **Link the two existing Supabase projects** (Inductive Network org): staging + production. No new project creation — reuse what the developer-portal team already provisioned. Confirm project IDs with the dev-portal team and record them in `docs/infrastructure.md`.
    - **`.env.example` updated** with a single `SUPABASE_URL` / `SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_SECRET_KEY` pair resolved per environment by `ENV=local|staging|production`. Default for `local` is the staging project. Production values live only in Vercel/Cloud Run env, never on disk.
    - **Vercel env vars wired** via `vercel env add`: Preview → staging, Production → production.
    - **Cloud Run env vars wired** for `packages/api`: staging service → staging DB, production service → production DB.
    - **Postgres roles created in each Supabase project** (aligned with the Migration-Authorship split in `### Database Strategy`):
      - `migration_role` — full DDL + DML grants; used only by the migration runner (CI / `supabase db push`).
      - `contributor_portal_role` — runtime role. `SELECT` on all tables; `INSERT/UPDATE/DELETE` only on contributor-owned tables (`contributors`, `credentials`, `task_instances`, `enrollments`, `contributions`, `lineage_records`).
      - `developer_portal_role` — runtime role. Mirror grants for developer-owned tables + DDL authorship over `campaigns`/`tasks` post-V1.
      - Assertion test: runtime role attempting a cross-portal write returns a permission error.
    - **Phased DDL authorship enabled for V1** — migrations in `sql-query/migrations/` touching shared-contract tables (`campaigns`, `tasks`) must use filename prefix `shared_` and include a header comment linking to a notify-PR or Linear ticket in the developer-portal repo. CI check enforces the prefix convention. This exception auto-expires when `I4-1` ships (tracked as part of `I4-1`'s Done criteria).
    - **Seed scripts safety wrapper** (`packages/api/scripts/_env_guard.py`):
      - Reads `SUPABASE_URL` from env; refuses to run without it.
      - Prints target URL + project name; requires interactive confirmation.
      - Refuses production unless `ENV=production` AND `--confirm-production` flag passed.
      - Stamps inserted rows with `seed_run_id` UUID for rollback.
      - Writes run-report file to `packages/api/.seed-runs/<run_id>.json`.
    - **DB client allowlist wrapper** — `packages/api/app/db/client.py` wraps `supabase-py` with a table-name allowlist matching the runtime ownership map; mutations outside the list raise `OwnershipViolation` before the network call. Same pattern mirrored in the webapp's server-side Supabase client.
    - **CI guard** — GitHub Action runs migrations against a throwaway Supabase branch off staging and asserts (a) shared_-prefix convention for cross-portal DDL, (b) runtime roles cannot write cross-portal. Production promotion is a separate manual `workflow_dispatch` job gated on a reviewer approval.
    - **Docs** — `docs/infrastructure.md` (new) documents: project IDs (staging + production), env resolution order, how to switch local dev between staging/prod, migration-authorship phase rules, promotion protocol, on-call escalation for a cross-portal conflict.
  - **Technical Notes:**
    - **Existing Supabase projects** — confirm IDs with developer-portal team before starting. Do NOT create new projects.
    - **Supabase MCP** — `mcp__supabase-inductive` tooling can inspect the existing projects; authenticate via `mcp__supabase-inductive__authenticate` at the start of the task.
    - Supabase branching remains a staging-only mechanism (per `### Database Strategy`). This item adds the *environment split itself*, not the branching workflow.
    - **Phased authorship is the core dev-cadence concession** — lets contributor-portal evolve `campaigns`/`tasks` during V1 without repo context-switch, while runtime grants still enforce ownership. The phase exits at `I4-1`.
    - Existing `.env.example` line `SUPABASE_URL=https://uxafdddzhgdhsabkwmgw.supabase.co` is *production* — after this item lands, `.env.example` points local/staging at the staging project and production values live only in deploy envs.
  - **Blocks:** I0-4 (Apply DB Migration & Wire API). Migrations land on staging first, validated, then promoted to production.
  - **Tests Required:**
    - Seed script refuses without env; refuses production without flag; stamps seed_run_id; rollback via seed_run_id works
    - Runtime role attempting cross-portal write returns permission error
    - Migration role succeeds on cross-portal DDL (V1 phase)
    - DB client wrapper throws `OwnershipViolation` on disallowed table mutation
    - Env resolution: `ENV=local` → staging, `ENV=staging` → staging, `ENV=production` → production
    - CI workflow rejects a PR with a cross-portal migration missing the `shared_` prefix or notify link

- [ ] **I0-4: Apply DB Migration & Wire API to Supabase** — Connect API to real database
  - **User:** Engineers
  - **Acceptance Criteria:**
    - `001_contribution_schema.sql` applied to Supabase instance
    - API routes use real Supabase queries (replace in-memory `_campaigns`/`_tasks` dicts)
    - `POST /v1/campaigns/seed` writes to DB; `GET /v1/campaigns` reads from DB
    - Data survives API restart
    - RLS policies: contributors read own instances; campaigns public for active status
  - **Technical Notes:** Migration is additive to existing dev-portal tables. Use `supabase-py` async client. Transition pattern: replace dict lookups with `supabase.table('campaigns').select()`.
  - **Tests Required:** Seed persists across restart; concurrent reads; RLS blocks cross-contributor access

- [ ] **I1-1: ML Backend Adapter** — Vision Engine wrapped in LS ML Backend protocol
  - **User:** Engineers (infrastructure)
  - **Acceptance Criteria:**
    - FastAPI service implementing: `POST /predict`, `POST /setup`, `GET /health`
    - `/predict` accepts LS task format (video URL), submits to Vision Engine, returns LS predictions
    - Predictions include: timeline labels (motion segments), bounding boxes (person detection), keypoints (pose)
    - `/setup` validates Vision Engine availability
    - `/health` proxies to Vision Engine health check (ffmpeg + yolo status)
    - Supports both video and ZIP-of-sequences input types
    - Handles Vision Engine's async callback pattern: submit → poll/callback → translate response
    - Detection params configurable per prediction request (preset or custom)
  - **Technical Notes:** Reference `labeling-api/worker_client.py` for Vision Engine communication protocol and `labeling-vision-engine/main.py` for request/response shapes. The adapter converts VE's native output (clips_data, culled_segments, all_segments) into LS region format. This is the ONLY code that knows VE internals.
  - **Tests Required:** /predict returns LS-format regions; handles video + sequence input; handles VE timeout; handles VE down; detection params passed through; /health reflects VE status

- [ ] **I1-2: Upload & Processing Flow** — Video/ZIP upload → Vision Engine → results in Supabase
  - **User:** Contributors
  - **Acceptance Criteria:**
    - Route: `/workspace/[campaignId]/[taskId]/supply` (per-step routing decision)
    - Upload page: file picker (video/ZIP), detection preset selector, task name, scenario code
    - **Detection preset selector:** reads presets from `campaigns.params.detection_presets` (Universal, YOLO Human Filter, Workstation, Workstation+Pose); "Advanced" toggle shows individual VE params
    - Upload creates T1 instance (`parent_instances: []`) + processing_job in Supabase
    - File stored in Supabase Storage
    - ML Backend adapter called with LS /predict; results written to clips, clip_frames, segments tables
    - T2 instance created on processing complete (`parent_instances: [T1.id]`, `contributor_id: ml_backend_adapter`)
    - Processing status page: poll status with progress display, navigate to `/review` on complete
    - Handles: corrupt video, empty frames, VE failure
  - **Technical Notes:** Reference `labeling.codatta.io/web` for UX. Reference labeling-website UploadPage for preset UX and labeling-api POST /process for upload logic. Client-side ZIP compression for large sequence archives (reference `compress-zip.ts`). Content hash (SHA-256) computed for T1 instance.
  - **Tests Required:** Upload creates T1 + job; VE callback writes clips/segments to DB; T2 instance has correct parent; handles failure; data survives API restart

- [ ] **I2-1: Cull Review UI** — Review auto-detected segments, mark valid/invalid
  - **User:** Contributors
  - **Acceptance Criteria:**
    - Route: `/workspace/[campaignId]/[taskId]/review` (maps to `labeling.codatta.io/web/annotate/:id/filter`)
    - Segment timeline showing all segments with state badges (keep/review/culled_motion/culled_low_action/culled_person)
    - Frame-by-frame playback with Konva canvas (person detection bounding box overlay from clip_frames)
    - Keyboard-driven review: Y=keep, N=cull, arrow keys=next/prev, M=merge segments
    - "Finalize Review" persists decisions to segments table, advances to `/annotate` step
    - Valid segments advance to slicing step
  - **Technical Notes:** Reference `labeling.codatta.io/web/annotate/:id/filter` for UX. Reference labeling-website CullReviewTab for component breakdown and keyboard patterns. Reference FramePlayer for Konva rendering with bbox overlay. Data comes from Supabase (clips, clip_frames, segments tables), not localStorage.
  - **Tests Required:** Renders segments with correct states; keyboard review works; finalize updates DB; valid segments identified

- [ ] **I2-2: Slice & Action Label UI** — Fine-cut segments into sub-clips, assign action labels
  - **User:** Contributors
  - **Acceptance Criteria:**
    - Route: `/workspace/[campaignId]/[taskId]/annotate` (maps to `labeling.codatta.io/web/annotate/:id/slice`)
    - Valid segments displayed for fine-cutting with keyframe markers
    - Drag-to-split via filmstrip scrubber (FilmstripScrubber component)
    - Sub-clips labeled as "annotate" or "invalid"
    - Action label assignment from vocabulary (keyboard shortcuts 1-5)
    - Label dictionary customizable per campaign (from `campaigns.params`)
    - Undo/redo support
    - Save creates annotation records in DB
  - **Technical Notes:** Reference `labeling.codatta.io/web/annotate/:id/slice` for UX. Reference labeling-website SliceTab + AnnotateTab for component breakdown. Reference FilmstripScrubber for drag-to-split interaction. Action vocabulary comes from campaign config (stored in DB), not hardcoded.
  - **Tests Required:** Keyframe split works; label assignment with shortcuts; custom vocabulary from campaign; undo/redo; saves to annotations table

- [ ] **I3-1: Spatial Annotation** — Edit Vision Engine bounding box pre-labels
  - **User:** Contributors
  - **Acceptance Criteria:**
    - In annotation view, frames show person bounding boxes from clip_frames as editable overlays
    - Object label selector: person, hand, towel, box, furniture, tool, other
    - Arm keypoints (from Pose detection) displayed as reference points
    - Contributor can: accept bbox, adjust position/size, delete false positive, add new bbox
    - Spatial data saved in `annotations.spatial` JSONB per frame
    - Pre-labels are LS "suggestions" — agent-produced with score and provenance
  - **Technical Notes:** Konva canvas for bbox editing (reference FramePlayer for base rendering). Pre-labels come from clip_frames table (populated by ML Backend during T2). This follows the Argilla-style suggestions model from annotation-pipeline spec §4.2.
  - **Tests Required:** Pre-labels rendered; bbox drag-resize; new bbox creation; delete; data saved; handles frames with no pre-labels

- [ ] **I3-2: Language Instruction & Task Plan** — Semantic annotation per action segment
  - **User:** Contributors
  - **Acceptance Criteria:**
    - Each action segment has text input for language instruction
    - Task plan input: ordered list of high-level steps (add/remove/reorder)
    - Saved in annotations.temporal: `segments[].language_instruction` and `segments[].task_plan[]`
    - Completes the Embodiment-X schema (temporal + spatial + semantic)
  - **Technical Notes:** Two TextArea fields matching the LS XML config. Language instruction is free-text. Task plan is ordered string array.
  - **Tests Required:** Language saved per segment; task plan CRUD; export includes both fields

- [ ] **I3-3: Annotation Submit & T3 Instance** — Create T3 instance with full Embodiment-X payload
  - **User:** Contributors
  - **Acceptance Criteria:**
    - "Submit" aggregates temporal + spatial + language + quality metadata into Embodiment-X payload
    - T3 instance created: `parent_instances: [T2.id]`, `content_hash: SHA-256(canonical payload)`, `annotation_config_ver: 'embodiment_x_v1.0.0'`
    - Payload stored in `task_instances.payload` JSONB
    - Export page: stats, label distribution, JSON download (both legacy `labeling_meta.json` format AND Embodiment-X format)
  - **Technical Notes:** Content hash must be deterministic: canonical JSON serialization (sorted keys, no whitespace) → SHA-256. The export supports backward compatibility with existing `labeling_meta.json` consumers.
  - **Tests Required:** T3 instance has correct parent; content hash deterministic; payload matches Embodiment-X schema; export works in both formats

- [ ] **I4-1: Campaign Discovery & Task DAG** — Browse campaigns, view task pipeline
  - **User:** Contributors
  - **Acceptance Criteria:**
    - `/campaigns` lists live campaigns as cards (name, frontier, progress)
    - `/campaigns/{id}` shows task DAG (T1→T2→T3→T4) with status per task
    - "Start Contributing" links to upload page scoped to campaign
    - Campaign status (live/paused/completed) reflected
    - Progress bar (instances submitted / target quantity)
    - **Phase-exit:** closes the V1 DDL-authorship exception for `campaigns`/`tasks` introduced in `I0-3`. After this item ships, contributor-portal no longer authors migrations against those tables — changes go through the developer-portal repo. Update `docs/infrastructure.md` to reflect the post-V1 rule and remove the `shared_` filename allowance from the contributor-portal CI guard.
  - **Technical Notes:** Campaign data from shared Supabase. Developer portal writes campaign config; this portal reads and renders.
  - **Tests Required:** Renders campaigns; DAG correct; navigation; progress calculation; contributor-portal CI rejects any new `shared_` prefixed migration

- [ ] **I4-2: Instance Lineage API** — Query lineage chain through the DAG
  - **User:** Engineers + both portals
  - **Acceptance Criteria:**
    - `GET /v1/instances/{id}/lineage` returns full parent chain as tree
    - Lineage walks `parent_instances[]` recursively (depth-bounded at 5)
    - Each node includes: instance_id, task_key, contributor_id, content_hash, quality_grade, status
    - Lineage visualization on campaign detail page (which T1 video → which T2 processing → which T3 annotation)
  - **Technical Notes:** Recursive CTE in Postgres for efficient lineage walking. Same query shape that the developer portal will use for `GET /v1/live/pull?include_lineage=true`.
  - **Tests Required:** Full chain T1→T2→T3→T4; depth bound at 5; handles orphans; CTE performance on 1000+ instances

- [ ] **I5-1: Validation (T4) & Quality Gates** — Auto-generated quality scoring
  - **User:** Automated + platform
  - **Acceptance Criteria:**
    - T3 submit triggers T4 validation (sample 10%)
    - Checks: annotation completeness, spatial coverage, language instruction present, action label consistency
    - Quality grade: S/A/B/C/D
    - T4 instance: `parent_instances: [T3.id]`
    - On pass: MockAttributionHooks writes full chain to lineage_staging
    - `upstream_shares` uses protocol defaults (60% self, 5% platform, 35% parents weighted by depth)
  - **Technical Notes:** Rule-based validation. Scoring weights: temporal completeness 30%, spatial presence 25%, language quality 20%, label consistency 15%, quality metadata 10%.
  - **Tests Required:** Sample selection; grade calculation; attribution hooks; lineage_staging correct; upstream_shares sum to 10000

- [ ] **I5-2: Mock AttemptIndex & Attribution Hooks** — Search + lineage staging
  - **User:** Engineers + both portals
  - **Acceptance Criteria:**
    - `GET /v1/attempts/search` with filters; `GET /v1/attempts/{id}/lineage`; `POST /v1/attempts/bulk-query`
    - `MockAttributionHooks` writes InstanceRecord to lineage_staging on validation
    - All mock responses include `X-Mock: true` header
  - **Technical Notes:** Postgres queries against task_instances. Same interface for future search/chain backends.
  - **Tests Required:** Filters work; lineage walks; content_hash deterministic; mock status correct

- [ ] **I5-3: Developer Portal Integration** — Campaign config from shared Supabase
  - **User:** Developers
  - **Acceptance Criteria:**
    - Developer portal writes campaign config (LS XML, action vocabulary, quality thresholds) to shared Supabase
    - Contributor portal reads and renders
    - Config changes reflected within 30 seconds (Supabase Realtime)
    - Feature flag `CAMPAIGN_SOURCE=mock|supabase`
  - **Technical Notes:** Both portals share Supabase. Campaign tables are the contract. Mock seed provides same interface for standalone development.
  - **Tests Required:** Config read from shared DB; changes propagate; feature flag toggles

### 🧪 In Progress

<!-- Move an item here once work has started. Only one at a time. -->

### ✅ Done

<!-- Completed items with commit hash, newest on top -->

- [x] **U1-1: Auth Polish — OAuth Fold + OTP Login & Password Reset** — `2984ec5` (main impl), `d36bf03` (screenshots), `1c1d96e` → `4a784d0` (toggle polish); PR #14
  - `oauth-buttons.tsx`: primary (Google, LinkedIn) always visible; secondary (GitHub, HuggingFace) behind "Show more" toggle with rotating `▾` chevron; all disabled/`aria-disabled` when `NEXT_PUBLIC_OAUTH_ENABLED=false`; toggle uses `textSecondary→textPrimary` color shift on hover (no underline — per design system)
  - `signin/page.tsx`: Password | Email code tabs; OTP sub-flow (idle → code_sent → verifying); "Forgot password?" link
  - `signup/page.tsx`: Password | Email code tabs; Password tab = direct `signUp`; Email code tab = existing 3-step OTP flow preserved
  - `reset-password/page.tsx`: 3-step wizard (email → OTP → new password) with `step-indicator.tsx`; generic copy on step 1 (anti-enumeration)
  - `src/hooks/useResendCooldown.ts`: 60s countdown hook
  - `src/lib/auth/copy.ts`: all microcopy strings + `mapOtpError` mapper
  - `.env.example`: added `NEXT_PUBLIC_OAUTH_ENABLED=false`
  - `e2e/auth.spec.ts`: updated stale tests; added OAuth toggle, disabled state, OTP signin, reset-password, resend cooldown, and ARIA tests
  - `e2e/ux-journey-screenshots.spec.ts`: 5 new auth screens (signin tabs, OAuth expanded, signup tabs, reset-password steps); 27/27 passing; PNGs committed to `tests/v1/ux-tests/` and embedded in PR description

- [x] **I1-0: Workspace Route Structure & Mock Data** — 2026-04-17 (commit pending)
  - Layout extracted to `workspace/[campaignId]/[taskId]/layout.tsx`: step-aware pipeline bar, sub-task bar (4 navigable step links), action bar with step-specific primary CTAs
  - Root page redirects to `/supply`; four sub-routes built: `supply/`, `review/`, `annotate/`, `export/`
  - Mock data module `src/lib/mock/workspace.ts` with Supabase-shaped types: `Segment`, `ClipFrame`, `ProcessingJob`, `ActionSegmentDraft`, `CampaignConfig`, `DetectionPreset`, `ActionLabel`. 8 mock segments spanning keep/review/culled states; 4 draft action segments.
  - Supply page: drag-and-drop file picker, 4 detection preset cards with Advanced param toggle, task name + scenario code inputs, next-steps banner
  - Review page: FramePlayer (Konva canvas with bbox + arm keypoint overlays), segment info panel with metrics, keyboard review (Y/N/←→), segment timeline with state coloring and decision badges
  - Annotate page: draft segments list (left), FramePlayer + language instruction textarea + task plan editor (center), action label palette with 1–5 keyboard shortcuts (right), FilmstripScrubber (bottom)
  - Export page: completion checklist, label distribution bars, instance fingerprint preview (content_hash placeholder), submit CTA gated on completeness
  - FramePlayer uses dynamic `import("konva")` inside `useEffect` to avoid SSR hydration mismatch with React 19 + Next 16 App Router
  - `bun run typecheck` + `bun run build` pass; all 5 routes return 200 (root 307 → supply); dev server clean
  - Follow-up work threaded into I1-2 (supply → real upload), I2-1 (review → real segments from Supabase), I2-2 (annotate → real action labels + bbox editing), I3-3 (export → real content_hash + T3 instance)

- [x] **I0-3: Campaign Template with LS XML Configs** — `4a26a62`
  - `templates/robotics_video_collection/` with campaign.yaml + 4 LS XML configs (t1–t4)
  - `POST /v1/campaigns/seed` and `GET /v1/campaigns/{id}/tasks/{task_id}/config` implemented (in-memory store)
  - Template loader service parses YAML + XML

- [x] **I0-2: Domain Types & Database Migration** — `4a26a62`
  - SQL migration: `sql-query/migrations/001_contribution_schema.sql` (all tables defined, not yet applied to Supabase)
  - Pydantic models: `packages/api/app/models/domain.py` + `enums.py`
  - Note: migration written but not applied; API uses in-memory store, not real Supabase queries yet

- [x] **I0-1: Project Scaffold** — `4a26a62`
  - Next.js 16 + React 19 + Tailwind v4 + shadcn/ui + Konva installed
  - FastAPI + uv + Pydantic + Supabase SDK
  - Auth UI (signin/signup with Supabase OAuth + email)
  - Shell layout (sidebar, topbar, nav), all page routes scaffolded
  - Supabase client configured (SSR + browser)

### 🧊 Backlog / Ideas

#### V2 — Planned Next

- [ ] **Contributor Auth** — Supabase Auth, email + optional wallet connect
- [ ] **Contributor Dashboard** — Earnings, tasks, reputation, campaigns
- [ ] **Dispute Resolution** — Dispute task type: contributor challenges evaluation → peer-review task assigned to qualified campaign contributors; platform-level timeout + quorum defaults, per-campaign overrides; resolution upholds or overturns evaluation grade
- [ ] **Downstream Usage Disclosure** — Builder publishes model training runs to Supabase; Contributor Kitchen displays per-instance and campaign-level usage; required for royalty campaigns, optional for instant-payout; opted-in by default
- [ ] **Campaign Matching** — Recommend campaigns based on contributor qualifications, past contributions, frontier history; V1 filter/search, V2 ML-based ranking
- [ ] **Credential Submission & Review** — Contributor uploads education/professional proof (diploma, CPA license, domain certifications); admin/AI-assisted review workflow; approved credentials elevate skill to `credential-verified`; rejected with reason
- [ ] **Campaign Skill Gates** — Campaign specifies required skills + minimum verification level; enrollment blocked if unmet; contributor shown path to qualify (which training to complete)
- [ ] **KYC Tier** — Dynamic threshold configured per campaign and campaign owner; platform manages KYC provider (Persona or equivalent); KYC'd contributors unlock higher-rate campaigns
- [ ] **Payouts & Withdrawal** — Instant payout disbursement, royalty distribution, withdrawal settings (wallet address, bank, threshold triggers); follows lineage upstream_shares model from lineage spec
- [ ] **SMS Notifications** — Same event set as V1 in-app + email: evaluation results, rework, new campaigns, payout events, dispute outcomes

#### V3

- [ ] **AI Interview** — Video call interview conducted by AI to verify domain expertise; evaluates response quality, depth, accuracy; produces score + written summary; borderline cases escalate to human review; grants `expert` skill tier
- [ ] **Teams** — Form a team on a campaign: shared contributions, split earnings (configurable share), team-level reputation and badges; requires team identity, conflict resolution mechanism
- [ ] **Campaign Template: `video_supply_annotation`** — Unitree footage (Supply → Annotate → Validate)
- [ ] **LS Playground Iframe Embed** — Per annotation-pipeline spec §4.1 item 3, embed LS playground for richer annotation UI
- [ ] **Pre-labeling Suggestions UI** — Argilla-style: agent suggestions with score/provenance
- [ ] **Inter-Annotator Agreement (IAA)** — Multiple contributors, agreement metrics
- [ ] **Gold Standard Injection** — Known-correct items, accuracy tracking
- [ ] **Qualification Gates** — Tutorial/test before campaign access
- [ ] **Extended Action Taxonomy** — Hierarchical labels, campaign-specific vocabularies
- [ ] **Multi-Camera/Multi-View** — ROS bag correspondence, synchronized annotation
- [ ] **Additional ML Backends** — SAM2, GroundingDINO, LLM agents — all drop-in via LS protocol
- [ ] **Real AttemptIndex** — Elasticsearch/Typesense
- [ ] **Real Attribution Hooks** — Merkle batching, L2 writes
- [ ] **Native iOS/Android** — XML config interpreter + native renderer
- [ ] **Annotation Runtime Extraction** — Move to annotation-pipeline repo
- [ ] **Full DAG Orchestration** — Vercel Workflow DevKit or Temporal
- [ ] **Compensation** — Wallet, escrow, token distribution
- [ ] **Formalize Frontier Standard** — Add `frontier-robotics/` to codatta-frontier-standards

---

## Appendix: Key References

| Document | Location | Relevance |
|---|---|---|
| Annotation Pipeline Spec | `huge_leap/docs/specs/annotation-pipeline.md` | LS XML config decision, ML Backend protocol, repo architecture |
| Data Lineage Spec | `huge_leap/docs/specs/data-lineage.md` | InstanceRecord schema, upstream_shares, royalty walk |
| Domain Model | `huge_leap/docs/model/prd.md` | Frontier/Campaign/Task/Instance hierarchy |
| Campaign Launch Roadmap | `developer-portal/campaign-launch-roadmap.md` | Phase 0-6, template formats, lineage enrichment |
| labeling-website | `codatta/labeling-website` (GitHub) | UX reference: annotation flow, keyboard patterns, presets |
| labeling-api | `codatta/labeling-api` (GitHub) | Logic reference: VE communication, frame organization, export |
| labeling-vision-engine | `codatta/labeling-vision-engine` (GitHub) | External service API contract |
| Open X-Embodiment | `annotation-pipeline/research/04-multimodal-datasets.md` | Benchmark dataset format |
| Frontier Standards | `codatta-frontier-standards/` | Schema pattern (robotics TBD) |
