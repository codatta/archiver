# Visual Spec — Contributor Portal

> Complete screen inventory, visual hierarchy, and implementation spec.
> Clean-room — no Pencil artifacts. Grounded in `reference/`, `design/system.md`, `design/sample-data.md`, and user wireframes.

### Brand & Logo

- **Logo:** Codatta logomark (square symbol from `codatta/brand-kit`). No wordmark alongside it.
- **Assets:** `public/assets/logos/colored/codatta.png` (black, for light bg), `public/assets/logos/white/codatta.png` (white, for dark bg).
- **Product name:** "Humanbased" — displayed as text next to logomark in sidebar and auth screens.
- **Visual consistency:** Must match `developer.humanbased.ai` — identical tokens, input styles, button styles, auth layout. Both portals are one product.

---

## Screen Inventory

### Primary Tabs (sidebar navigation)

| # | Tab | Route | Purpose |
|---|---|---|---|
| 1 | **Home** | `/contribute` | Dashboard — stats, attention items, quick actions |
| 2 | **Campaigns** | `/contribute/campaigns` | Browse + enrollment lifecycle |
| 2a | — Browse view | `?tab=browse` | Job board grid with filters |
| 2b | — Enrollments view | `?tab=enrollments` | Active/past enrollment management |
| 2c | — Campaign Detail | `/contribute/campaigns/[id]` | Deep-dive: org, task breakdown, qualification, enroll |
| 3 | **Tasks** | `/contribute/tasks` | Recurrent work queue bundled by campaign |
| 4 | **Contributions** | `/contribute/contributions` | Submission ledger — enriched flat table |
| 5 | **Earnings** | `/contribute/earnings` | Pipeline-aware financial tracking |
| 6 | **Profile** | `/contribute/profile` | Identity, credentials, social, settings |

### Annotation Workflow (full-screen, sidebar collapses)

| # | Screen | Route | Purpose |
|---|---|---|---|
| 7 | **Task Workspace** | `/contribute/campaigns/[id]/tasks/[taskId]` | Active annotation — context bar + canvas + action bar |
| 7a | — Supply mode | | Blank form / upload / recording |
| 7b | — Labeling mode | | Instance + annotation tools + agent pre-labels |
| 7c | — Validation mode | | Instance + existing annotations + verdict |

### Auth (no sidebar)

| # | Screen | Route |
|---|---|---|
| 8 | Sign In | `/auth/signin` |
| 9 | Sign Up (3-step) | `/auth/signup` |
| 10 | Onboarding | `/onboarding` |

**Total: 10 screens, 3 sub-views, 3 workspace modes.**

---

## Global Shell

```
┌──────────────────────────────────────────────────────────────────┐
│ Shell (min-h-screen, flex horizontal)                            │
│                                                                  │
│ ┌──────────┐ ┌──────────────────────────────────────────────────┐│
│ │          │ │ Top Bar (h-14)                                   ││
│ │ Sidebar  │ ├──────────────────────────────────────────────────┤│
│ │ w-[220px]│ │                                                  ││
│ │          │ │ Content Area                                     ││
│ │ dark     │ │ (bg-[#FAFAF9], overflow-y-auto)                  ││
│ │ bg-[#111]│ │                                                  ││
│ │          │ │                                                  ││
│ │ collaps- │ │                                                  ││
│ │ ible to  │ │                                                  ││
│ │ 56px     │ │                                                  ││
│ │          │ │                                                  ││
│ └──────────┘ └──────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### Sidebar (expanded: w-[220px])

```
bg-[#111827] text-gray-400 flex-col h-screen sticky top-0

┌────────────────────┐
│ [◆] Humanbased     │  h-14, px-4, flex items-center gap-2.5
│                    │  Codatta logomark (w-7 h-7, white variant for dark bg)
│                    │  + "Humanbased" text-sm font-semibold text-white
├────────────────────┤  border-b border-gray-800
│                    │
│ WORK               │  text-[10px] uppercase tracking-[0.1em] text-gray-500 px-3 pt-4 pb-1
│ ● Campaigns        │  ← active: bg-gray-800 text-white font-medium rounded-md
│ ○ My Tasks         │     px-3 py-2 flex items-center gap-3
│ ○ Contributions    │     2px left accent bar bg-[#834DFB] on active item
│                    │  ← inactive: text-gray-400 hover:text-white hover:bg-gray-800/50
│ EARNINGS           │
│ ○ Earnings         │
│                    │
│ ME                 │
│ ○ Profile          │
│                    │
│                    │  flex-1 (spacer)
│                    │
├────────────────────┤  border-t border-gray-800
│ ● YZ  @yi_zhang   │  avatar w-8 h-8 bg-[#834DFB] rounded-full
│ Expert · 847/1000  │  text-xs text-gray-500
│            [« ▸]   │  collapse toggle
└────────────────────┘
```

### Sidebar (collapsed: w-[56px])

```
┌──────┐
│  ■   │  logomark only, centered
├──────┤
│  ◎   │  icon buttons w-10 h-10, centered
│  ☐   │  tooltip on hover shows label
│  ☐   │  active: bg-gray-800 rounded-md
│  ─   │  section divider: 1px border-gray-800 mx-2
│  ☐   │
│  ─   │
│  ☐   │
│      │
├──────┤
│  ●   │  avatar only
│  [▸] │
└──────┘
```

### Top Bar

```
h-14 px-6 flex items-center justify-between border-b border-[#E5E7EB] bg-white

Left:  breadcrumb (text-sm text-gray-500) or page context
Right: [Sandbox ●─ Production] toggle + "yi@humanbased.io" text-xs text-gray-500
       + avatar w-7 h-7 bg-[#1B1034] rounded-full text-white text-[10px]
```

---

## Screen 1: Home Dashboard

**Route:** `/contribute`  
**Active nav:** (none, or first item)

```
Content (px-10 py-8, max-w-[1200px])
│
│ "Good morning, Yi"
│  text-2xl font-semibold text-[#1B1034]
│
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    grid-cols-4 gap-4
│ │Total    │ │Active   │ │Completed│ │Pending  │
│ │Earned   │ │Campaigns│ │         │ │         │    Each: bg-white border border-[#E5E7EB]
│ │$847.20  │ │3        │ │142      │ │$42.50   │    p-5
│ │         │ │         │ │         │ │(amber)  │    label: text-xs text-gray-500
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘    value: text-3xl font-semibold
│
│ "Needs Attention"  text-sm font-semibold
│ ┌──────────────────────────────────────────────┐    bg-white border border-[#E5E7EB]
│ │ ⏳ 4 labeled instances stuck — Embodiment-X  │    divide-y divide-gray-100
│ │ 🔚 Kitchen Task Recording ending in 3 days   │    each row: px-4 py-3 text-sm
│ │ ✕  T1 upload rejected — Warehouse Nav        │    text-gray-600, icons color-coded
│ └──────────────────────────────────────────────┘
│
│ "Quick Actions"  text-sm font-semibold
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  grid-cols-3 gap-4
│ │Continue      │ │Browse        │ │View          │
│ │Tasks →       │ │Campaigns →   │ │Earnings →    │  bg-white p-5
│ │8 instances   │ │5 new matches │ │$42.50 pending│  border: first=1.5px #1B1034, rest=gray-200
│ └──────────────┘ └──────────────┘ └──────────────┘  hover:border-[#1B1034]
│
│ "Recent Activity"  text-sm font-semibold (below fold)
│ ✓ T3 annotation accepted · Embodiment-X · 2h ago    text-sm text-gray-500
│ $ $12.50 earned · Kitchen Task Recording · 1d ago    divide-y
│ ✕ T1 upload rejected · Warehouse Nav · 2d ago
```

---

## Screen 2a: Campaigns — Browse

**Route:** `/contribute/campaigns`  
**Active nav:** Campaigns

```
Content (px-10 py-8, max-w-[1200px])
│
│ "Campaigns"  text-2xl font-semibold
│ [Browse ▸ | My Enrollments]  tab toggle, text-sm
│   active tab: font-semibold text-[#1B1034] border-b-2 border-[#1B1034] pb-1
│   inactive: text-gray-400 hover:text-[#1B1034]
│
│ Filter Bar (flex gap-3 items-center)
│ [Frontier ▾] [Pay ▾] [Task Type ▾] [Qualified ▾] [Sort ▾]  ←  <Select> rounded-none
│ + Search input w-[260px] right-aligned                         border-[1.5px]
│ "18 campaigns"  text-xs text-gray-400
│
│ Campaign Grid (grid-cols-2 gap-5)
│
│ ┌─ CampaignCard ───────────────────────────────────────────┐
│ │                                                           │
│ │  ┌────┐ NVIDIA PhysicalAI                                 │  Org header
│ │  │logo│ ★ 4.8 · 12 campaigns · Trusted                   │  text-xs text-gray-400
│ │  └────┘                                                   │  logo: w-10 h-10 rounded-lg bg-gray-100
│ │                                                           │
│ │  Kitchen Manipulation                                     │  text-base font-semibold line-clamp-1
│ │  Record and annotate robotics manipulation videos         │  text-sm text-gray-600 line-clamp-2
│ │  for embodied AI training.                                │
│ │                                                           │
│ │  [Robotics] [Video] [Manipulation]                        │  tags: bg-gray-100 text-xs rounded-full
│ │                                                           │        px-2.5 py-0.5 text-gray-700
│ │  📤 Supply ($2.50) · 🏷 Labeling ($1.50) · ✅ Agent      │  task breakdown: text-xs text-gray-600
│ │                                                           │
│ │  ┌──────────────────────────────────────────────────┐     │
│ │  │ 💵 $2.50 / instance · Fixed pay                  │     │  comp pill: border-green-200 bg-green-50
│ │  └──────────────────────────────────────────────────┘     │  text-green-800 text-xs px-3 py-1.5 rounded-lg
│ │                                                           │
│ │  672 / 1,000 instances · 34 days left                     │  text-xs text-gray-400
│ │                                                           │
│ │  ✓ You qualify                     [ View Campaign ]      │  qualification + action
│ │                                                           │
│ └───────────────────────────────────────────────────────────┘
│   Card: bg-white border border-gray-200 p-5
│   hover:border-gray-400 hover:shadow-sm transition
│
│ (4 cards shown: Kitchen Manip, RoboMIND, Egocentric, Humanoid Motion)
│
│ "Show 12 more"  text-sm text-[#834DFB] text-center py-4
```

**Privacy tier adaptation on org header:**

| Tier | Logo | Name shown | Description |
|---|---|---|---|
| Open | Real logo | "NVIDIA PhysicalAI" | Original text |
| Shielded (k≥5) | Badge icon | "Verified AI Company" | AI-masked |
| Guarded (k≥20) | Category icon | "Technology Company" | Abstract |
| Sealed (k=∞) | Lock icon | "Anonymous Employer" | Opaque |

**Qualification footer states:**

| State | Left | Right |
|---|---|---|
| Qualified | `✓ You qualify` text-green-600 | `[View Campaign]` primary btn |
| Partial | `⚠ 1 req not met` text-amber-600 | `[View Requirements]` outline btn |
| Not qualified | `✕ 3 reqs not met` text-gray-400 | text link, card opacity-60 |
| Contributing | `● Contributing · 23/50` text-blue-600 | `[Continue →]` primary btn |

**Compensation pill variants:**

| Model | Content | Colors |
|---|---|---|
| Fixed | `💵 $2.50 / instance · Fixed pay` | border-green-200 bg-green-50 text-green-800 |
| Royalty | `📈 Revenue share · est. $1.80/ea` | border-purple-200 bg-purple-50 text-purple-800 |
| Hybrid | `🔀 $1.00 base + royalty` | border-blue-200 bg-blue-50 text-blue-800 |
| Bounty | `🎯 $5,000 milestone` | border-amber-200 bg-amber-50 text-amber-800 |

---

## Screen 2b: Campaigns — My Enrollments

**Route:** `/contribute/campaigns?tab=enrollments`  
**Active nav:** Campaigns

```
Content (px-10 py-8, max-w-[1200px])
│
│ "Campaigns"  text-2xl font-semibold
│ [Browse | My Enrollments ▸]  tab toggle (enrollments active)
│
│ "Active Enrollments (3)"  text-sm font-semibold
│
│ ┌─ EnrollmentCard ──────────────────────────────────────────┐
│ │ border-[1.5px] border-[#1B1034] bg-white p-5              │
│ │                                                            │
│ │  Kitchen Manipulation                    [Active] green    │  flex justify-between
│ │  text-base font-semibold                 badge             │
│ │                                                            │
│ │  Supply $2.50 · Labeling $1.50 · Fixed                     │  text-xs text-gray-500
│ │  23 submitted · 18 accepted · 5 in review                  │  text-xs text-gray-500
│ │                                                            │
│ │  ████████████████████░░░░░░░░  78% accepted                │  h-1.5 rounded-full
│ │                                                            │  bg-green-500 / bg-gray-200
│ │                         [ Continue Tasks ]  [ Unenroll ]   │
│ │                          primary btn         outline btn    │
│ └────────────────────────────────────────────────────────────┘
│
│ (repeat for each active enrollment)
│
│ "Past Enrollments"  text-sm font-semibold mt-6
│ ┌──────────────────────────────────────────────────────────┐
│ │ Warehouse Navigation · Completed · 47 tasks      [View]  │  bg-white border
│ │ Assembly Line QC · Ended · 12 tasks              [View]  │  divide-y
│ └──────────────────────────────────────────────────────────┘  px-4 py-3 text-sm
│
│ "Popular Right Now"  text-sm font-semibold mt-6
│ (horizontal scroll of 3 mini campaign cards)
```

---

## Screen 2c: Campaign Detail

**Route:** `/contribute/campaigns/[id]`  
**Active nav:** Campaigns

```
Content (px-10 py-8, max-w-[960px])
│
│ ← Back to Campaigns  (text-sm text-gray-500 flex items-center gap-1)
│
│ ┌─ Org Hero Card ─────────────────────────────────────────┐
│ │ bg-white border border-[#E5E7EB] p-6 flex gap-5         │
│ │                                                          │
│ │ ┌──────┐  NVIDIA PhysicalAI                              │  logo: w-14 h-14
│ │ │ logo │  Robotics & AI · Trusted ★4.8                   │  text-base font-semibold
│ │ └──────┘  12 campaigns · 94% on-time                     │  text-xs text-gray-400
│ │           "Building the world's most advanced..."        │  text-sm text-gray-600
│ └──────────────────────────────────────────────────────────┘
│
│ "Kitchen Manipulation"  text-2xl font-semibold mt-6
│ [Robotics] [Video] [Manipulation]  tags
│ 672 / 1,000 instances · 34 days left  text-sm text-gray-500
│
│ "About This Campaign"  text-sm font-semibold mt-6
│ (paragraph text-sm text-gray-600)
│
│ "Task Type Breakdown"  text-sm font-semibold mt-6
│ ┌──────────────────────────────────────────────────────────┐
│ │ bg-white border divide-y                                  │
│ │                                                          │
│ │ 📤 Supply           $2.50/ea   Human    ✓ Qualified      │  each row: px-5 py-3
│ │ 🏷 Labeling          $1.50/ea   Human    ⚠ Need tutorial  │  flex justify-between
│ │ ✅ Validation         —          Agent    (automatic)      │  text-sm
│ └──────────────────────────────────────────────────────────┘
│
│ "How It Works"  text-sm font-semibold mt-6
│ ┌──────────────────────────────────────────────────────────┐
│ │  Supply → Validation → Labeling → Label-Validation       │  pipeline DAG
│ │  [human]   [agent]     [human]    [agent]                │  horizontal flow
│ │                                                          │  nodes connected by arrows
│ │  stage labels below each node                            │  text-xs text-gray-500
│ └──────────────────────────────────────────────────────────┘
│
│ "Compensation"  text-sm font-semibold mt-6
│ ┌──────────────────────────────────────────────────────────┐
│ │ 💵 Fixed pay · $2.50 per accepted supply instance        │  bg-green-50 border-green-200
│ │ $1.50 per accepted labeling instance                     │  p-4 text-sm
│ │ Payout: within 48 hours of acceptance                    │
│ └──────────────────────────────────────────────────────────┘
│
│ "Your Qualifications"  text-sm font-semibold mt-6
│ ┌──────────────────────────────────────────────────────────┐
│ │ ✓ Platform: reputation ≥ 500                 met         │  checklist
│ │ ✓ Domain: robotics experience                met         │  text-sm
│ │ ⚠ Certification: complete tutorial           not met     │  green ✓ / amber ⚠
│ │                                    [ Start Tutorial → ]  │
│ └──────────────────────────────────────────────────────────┘
│
│ ┌──────────────────────────────────────────────────────────┐
│ │ Sticky footer (fixed bottom, bg-white border-t, p-4)     │
│ │                                                          │
│ │ ⚠ 1 requirement not met          [ View Requirements ]   │  if partial
│ │ ✓ You qualify for all tasks       [   Enroll Now    ]     │  if qualified
│ │ ● Already enrolled · 23/50       [   Continue →     ]     │  if enrolled
│ └──────────────────────────────────────────────────────────┘
```

---

## Screen 3: Tasks (Work Queue)

**Route:** `/contribute/tasks`  
**Active nav:** My Tasks

```
Content (px-10 py-8, max-w-[1200px])
│
│ "Tasks"  text-2xl font-semibold
│ "Your work queue across enrolled campaigns"  text-sm text-gray-500
│
│ ┌─ Today Summary ──────────────────────────────────────────┐
│ │ bg-white border border-[#E5E7EB] px-5 py-3               │
│ │ flex gap-8 items-center                                   │
│ │                                                           │
│ │ Today:  7 submitted  $18.50 earned  2 rejected            │
│ │ bold    text-gray-500 text-green-600  text-red-500         │
│ └───────────────────────────────────────────────────────────┘
│
│ ┌─ CampaignBundle: KITCHEN MANIPULATION ────────────────────┐
│ │ border-[1.5px] border-[#1B1034] bg-white                  │
│ │                                                            │
│ │ ┌─ Header ──────────────────────────────────────────────┐  │
│ │ │ KITCHEN MANIPULATION                    [Fixed]       │  │  bg-gray-50 px-5 py-3
│ │ │ text-xs font-semibold tracking-wide      badge gray   │  │  border-b border-gray-200
│ │ └──────────────────────────────────────────────────────┘  │
│ │                                                            │
│ │ ┌─ TaskRow ─────────────────────────────────────────────┐  │
│ │ │ 📤 Supply (3 available)                               │  │  px-5 py-3.5
│ │ │ $2.50/ea · ~15 min each            [ Start Next ]    │  │  border-b border-gray-100
│ │ └──────────────────────────────────────────────────────┘  │
│ │                                                            │
│ │ ┌─ TaskRow ─────────────────────────────────────────────┐  │
│ │ │ 🏷 Labeling (8 available)                             │  │
│ │ │ $1.50/ea · ~45 min                                    │  │
│ │ │ ●●●●●●○○ 6/8 pre-labeled by agent  [ Continue #47 ] │  │
│ │ └──────────────────────────────────────────────────────┘  │
│ │                                                            │
│ │ ┌─ TaskRow (agent, muted) ──────────────────────────────┐  │
│ │ │ ✅ Validation · Agent · no action needed               │  │  text-gray-400
│ │ └──────────────────────────────────────────────────────┘  │
│ └────────────────────────────────────────────────────────────┘
│
│ ┌─ CampaignBundle: ROBOMIND TRAJECTORIES ───────────────────┐
│ │ border border-gray-200 bg-white                            │
│ │ (same structure, Royalty badge, Supply + Labeling rows)     │
│ └────────────────────────────────────────────────────────────┘
│
│ — no more campaigns with available tasks —
│ text-sm text-gray-400 text-center py-6
```

**TaskRow anatomy:**

```
px-5 py-3.5 flex justify-between items-center border-b border-gray-100

Left (flex-col gap-1):
├── Line 1: emoji + " " + type + " (" + count + " available)"  text-sm font-medium
└── Line 2: "$X.XX/ea · ~Nm each"  text-xs text-gray-500
    Optional: "●●●●●●○○ 6/8 pre-labeled"  text-xs text-gray-400 mt-0.5

Right:
└── "Start Next" or "Continue #N"  — <Button> size=sm (h-8 px-4 text-xs)
    Agent rows: no button, entire row text-gray-400
```

---

## Screen 4: Contributions (Enriched Table)

**Route:** `/contribute/contributions`  
**Active nav:** Contributions

```
Content (px-10 py-8)
│
│ "Contributions"  text-2xl font-semibold
│ "147 submissions across 5 campaigns"  text-sm text-gray-500       [ Export CSV ↓ ] outline btn
│
│ Filter Bar (flex gap-3 mt-4)
│ [Campaign ▾] [Task Type ▾] [Status ▾] [Date range] [Search instance...]
│
│ ┌─ Data Table ──────────────────────────────────────────────────────────────┐
│ │ bg-white border border-[#E5E7EB]                                          │
│ │                                                                           │
│ │ Header Row  bg-gray-50 border-b-2 border-gray-200                         │
│ │ Campaign  Type  Instance  Chain ID  Status  Stage  Pay  ▸                 │
│ │ w-[180]   w-80  w-[120]   w-[120]   w-100   w-120  w-80  w-48            │
│ │ text-[11px] font-semibold text-gray-500 uppercase tracking-wide           │
│ │                                                                           │
│ │ Data Rows  border-b border-gray-100 hover:bg-gray-50 cursor-pointer      │
│ │                                                                           │
│ │ Kitchen    🏷 Lab  #inst-4f2a  0xa3..f1  ✓ Accept  ██████  $1.50    ▸    │
│ │ Manip.     purple  mono gray   purple    green     green   bold          │
│ │                                                                           │
│ │ RoboMIND   📤 Sup  #inst-d7e3  0xf4..a2  ✓ Accept  ██████  royalty  ▸    │
│ │                                           green     green   purple        │
│ │                                                                           │
│ │ Xperience  🏷 Lab  #inst-b3c8  —         ● Work   ████░░  —        ▸    │
│ │                     mono gray   gray-300  purple   purple  gray-300       │
│ │                                                                           │
│ │ Bones      🏷 Lab  #inst-8a1f  —         ✕ Reject  ██░░░░  —        ▸    │
│ │ Motion                                    red      red     gray-300       │
│ │                                                                           │
│ └───────────────────────────────────────────────────────────────────────────┘
│
│ "Showing 1–25 of 147"  text-xs text-gray-500
│ [← Prev] [1] [2] [3] ... [6] [Next →]
```

**Column spec:**

| Column | Width | Font | Color rule |
|---|---|---|---|
| Campaign | 180px | text-sm font-medium | text-[#1B1034] |
| Type | 80px | text-xs font-medium | 📤 gray, 🏷 purple, ✅ gray |
| Instance | 120px | text-xs font-mono | text-gray-500 |
| Chain ID | 120px | text-xs font-mono | on-chain: text-[#834DFB], pending: "—" text-gray-300 |
| Status | 100px | text-xs font-medium | ✓ green-600, ◐ amber-600, ● purple, ✕ red-500 |
| Stage | 120px | h-1.5 rounded-full | fill matches status color, track bg-gray-200 |
| Pay | 80px | text-sm font-medium | amount: text-[#1B1034], royalty: text-[#834DFB], pending: "—" gray-300 |
| Expand | 48px | icon chevron-right | text-gray-400 |

**Row click → Detail Drawer** (Sheet, side=right, w-[480px]):

```
┌─────────────────────────────────────────────────┐
│ Instance #inst-4f2a                       [✕]   │  font-semibold
│ Kitchen Manipulation · 🏷 Labeling               │  text-sm text-gray-500
│                                                  │
│ ─── PIPELINE ────────────────────────────────    │
│ [PipelineContextBar, full 32px variant]          │  see Screen 7 spec
│ supply██ → validation██ → labeling██ → lv░░      │
│                                                  │
│ ─── DATA PREVIEW ────────────────────────────    │
│ ┌──────────────────────────────────────────┐     │
│ │  ▶  video player (16:9)                  │     │  <video> element
│ │     00:45 / 01:32                        │     │
│ └──────────────────────────────────────────┘     │
│                                                  │
│ 🎵 audio-clip-03.wav                             │  (conditional by media type)
│ ┌──────────────────────────────────────────┐     │
│ │ ▶ ▁▃▅▇▅▃▁▃▅▇▅▃▁  00:12                 │     │  waveform viz
│ └──────────────────────────────────────────┘     │
│                                                  │
│ 📝 "Fold the towel on the table"                 │  bg-gray-50 p-3 rounded text-sm
│                                                  │
│ ─── DETAILS ─────────────────────────────────    │
│ Submitted    Feb 12, 2025 14:32                  │  key-value grid
│ Status       Accepted                            │  text-sm
│ Quality      Grade A                             │  label: text-gray-500 w-[120px]
│ Reward       $1.50 (Fixed)                       │  value: text-[#1B1034]
│ Chain ID     0xa3b7...c4f1 [copy]                │  purple + copy btn
│ Lifecycle    label_accepted                      │
│ Consensus    2/3 agree                           │
│                                                  │
│ ─── LINEAGE ─────────────────────────────────    │
│ ← Supply by contributor_8f2a                     │  text-gray-500
│ ← Validation (agent) auto-pass                   │
│ ● You: Labeling                                  │  font-semibold text-[#1B1034]
│ → Label-validation pending                       │  text-gray-400
└─────────────────────────────────────────────────┘
```

---

## Screen 5: Earnings

**Route:** `/contribute/earnings`  
**Active nav:** Earnings

```
Content (px-10 py-8, max-w-[1200px])
│
│ "Earnings"  text-2xl font-semibold
│                                          [This month ▾] [Export ↓]
│
│ ┌────────────┐ ┌────────────┐ ┌────────────┐       grid-cols-3 gap-4
│ │Total Earned│ │Pending     │ │Royalties   │
│ │$1,240.00   │ │$420.00     │ │$86.50      │       bg-white border p-5
│ │(all time)  │ │(in pipeline)│ │(lifetime)  │       value: text-3xl font-semibold
│ └────────────┘ └────────────┘ └────────────┘       label: text-xs text-gray-500
│
│ "Pipeline Breakdown"  text-sm font-semibold mt-6
│
│ ┌─ Campaign: Kitchen Manipulation (Fixed) ─────────────────┐
│ │ bg-white border p-5                                       │
│ │                                                           │
│ │ 82 total submitted                                        │  text-sm font-medium
│ │ ██████████████████████████░░░░░░░░░░  $155.00             │  h-2 bg-green-500 / bg-gray-200
│ │ 62 accepted ($155.00)     20 in review                    │  text-xs text-gray-500
│ │ Rejected: 4 (see feedback)                                │  text-xs text-red-500
│ └───────────────────────────────────────────────────────────┘
│
│ ┌─ Campaign: RoboMIND Trajectories (Royalty) ──────────────┐
│ │ bg-white border p-5                                       │
│ │                                                           │
│ │ 50 total submitted                                        │
│ │ State breakdown:                                          │
│ │ 30 ◆ royalty-eligible     $54.00 earned                   │  text-green-600
│ │ 12   in labeling          —                               │  text-gray-500
│ │  5   in label-validate    —                               │
│ │  3   rejected             $0.00                           │  text-red-500
│ │ Pipeline velocity: ~4 hrs supply → labeled                │  text-xs text-gray-400
│ └───────────────────────────────────────────────────────────┘
│
│ ⚠ Stalled: Egocentric Experience — no movement 6 days      │  bg-amber-50 border-amber-200
│   12 instances pending, $8.00 at stake                      │  p-4 text-sm text-amber-800
│
│ "Transaction History"  text-sm font-semibold mt-6
│ ┌──────────────────────────────────────────────────────────┐
│ │ Date         Campaign        Amount   Type     Count     │  bg-white border
│ │ Feb 12       Kitchen Manip.  $12.50   Fixed    5         │  text-sm
│ │ Feb 10       RoboMIND        $8.00    Royalty  3         │  divide-y
│ │ Feb 8        Kitchen Manip.  $7.50    Fixed    3         │
│ │ Feb 5        Bones Motion    bounty   Bounty   10        │  text-[#834DFB]
│ └──────────────────────────────────────────────────────────┘
│
│ ┌──────────────────────────────────────────────────────────┐
│ │ Available for withdrawal: $840.00      [ Go to Payouts → ] │  bg-[#F0EBFF] border-[#834DFB]
│ └──────────────────────────────────────────────────────────┘  p-4 text-sm
```

---

## Screen 6: Profile

**Route:** `/contribute/profile`  
**Active nav:** Profile

```
Content (px-10 py-8, max-w-[1200px])
│
│ "Profile"  text-2xl font-semibold
│
│ Two-Column (flex gap-8)
│
│ ┌─ Left: Profile Card (w-[320px]) ──────────────────┐
│ │ border-[1.5px] border-[#1B1034] bg-white p-6      │
│ │                                                     │
│ │  ┌──────┐                                           │  w-16 h-16 bg-[#1B1034]
│ │  │  YZ  │  rounded-full, text-xl text-white         │  font-semibold
│ │  └──────┘                                           │
│ │                                                     │
│ │  Yi Zhang           text-xl font-semibold           │
│ │  @yi_zhang          text-sm text-[#834DFB]          │
│ │  yi@humanbased.io ✓ text-sm text-gray-500 + green   │
│ │                                                     │
│ │  ─────────────────  border-t my-3                   │
│ │                                                     │
│ │  Reputation         text-xs text-gray-500 uppercase │
│ │  847 / 1,000        text-lg font-semibold           │
│ │  ████████████████░░  h-2 bg-[#834DFB] / bg-gray-200│
│ │                                                     │
│ │  Member since Dec 2024  text-xs text-gray-400       │
│ │                                                     │
│ │  [ Edit Profile ]  outline btn full-width           │
│ └─────────────────────────────────────────────────────┘
│
│ ┌─ Right (flex-1, flex-col gap-6) ────────────────────┐
│ │                                                      │
│ │ "Credentials"  text-sm font-semibold                 │
│ │ ┌──────────────────────────────────────────────────┐ │
│ │ │ Robotics Annotation  [tutorial-passed]  [View]   │ │  bg-white border divide-y
│ │ │ Data Collection      [credential-verified] [View]│ │  px-5 py-3.5
│ │ │ AI/ML Labeling       [unverified]    [Start →]   │ │  flex justify-between
│ │ └──────────────────────────────────────────────────┘ │
│ │                                                      │
│ │ "Earnings"  text-sm font-semibold                    │
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐              │  grid-cols-3 gap-4
│ │ │$847.20   │ │$42.50    │ │$124.00   │              │  bg-white border p-5
│ │ │total     │ │pending   │ │royalties │              │
│ │ │          │ │(amber)   │ │(purple)  │              │
│ │ └──────────┘ └──────────┘ └──────────┘              │
│ │                                                      │
│ │ "Recent Transactions"  text-sm font-semibold         │
│ │ (compact 3-row table: date | campaign | amount)      │
│ └──────────────────────────────────────────────────────┘
```

**Credential tier badges:**

| Tier | Background | Text | Left accent on row |
|---|---|---|---|
| unverified | bg-gray-100 | text-gray-500 | border-l-2 border-gray-300 |
| tutorial-passed | bg-[#F0EBFF] | text-[#834DFB] | border-l-2 border-[#834DFB] |
| credential-verified | bg-green-50 | text-green-700 | border-l-2 border-green-500 |
| expert | bg-amber-50 | text-amber-700 | border-l-2 border-amber-500 |

---

## Screen 7: Task Workspace

**Route:** `/contribute/campaigns/[id]/tasks/[taskId]`  
**Sidebar:** collapsed to 56px icon rail (auto-collapse on entry)  
**Purpose:** Full-screen annotation — pipeline context + canvas + action bar

This is based directly on the user's wireframes.

```
┌──────┬────────────────────────────────────────────────────────────┐
│      │                                                            │
│ icon │  Pipeline Context Bar (h-10, bg-white, border-b)           │
│ rail │  supply ─── validation ─── ▓▓▓▓▓▓▓░░ ─── validation       │
│ 56px │                                                            │
│      ├────────────────────────────────────────────────────────────┤
│      │                                                            │
│      │  Sub-task Breakdown Bar (h-12, flex, gap-0)                │
│      │  ┌──────────────┐┌────────────────────────┐┌─────────────┐│
│      │  │Pre-labeling  ││Segmentation            ││█ Task       ││
│      │  │by Agent      ││manual-adjustment       ││  annotation ││
│      │  │solid black bg││gray bg                 ││hatched bg   ││
│      │  │white text    ││white text              ││current step ││
│      │  └──────────────┘└────────────────────────┘└─────────────┘│
│      │                                                            │
│      ├────────────────────────────────────────────────────────────┤
│      │                                                            │
│      │  ┌──┐ ┌──────────────────────────────────────────────────┐│
│      │  │▲ │ │                                                  ││
│      │  │  │ │              Annotation Canvas                   ││
│      │  │▼ │ │              (iframe or Konva)                    ││
│      │  │  │ │                                                  ││
│      │  │  │ │              bg-[#374151] (dark gray)            ││
│      │  └──┘ │              flex-1                               ││
│      │  nav   │                                                  ││
│      │  40px  │                                                  ││
│      │        │                                                  ││
│      │        └──────────────────────────────────────────────────┘│
│      │                                                            │
│      ├────────────────────────────────────────────────────────────┤
│      │                                                            │
│      │  Action Bar (h-14, bg-[#111827], flex justify-between)     │
│      │                                                            │
│      │  Task time: 5m 45s (Session: 12m35s)    [Prev]  [Next]   │
│      │  text-sm text-gray-400 bg-amber-500/20   outline   primary│
│      │  amber left badge with timer              btn      btn    │
│      │                                                            │
│      └────────────────────────────────────────────────────────────┘
```

### Pipeline Context Bar (full, 32px height)

Based on user's wireframe Image 1. Shows where the current instance is in the full campaign pipeline.

```
h-10 px-6 flex items-center gap-0 bg-white border-b border-[#E5E7EB]

Segments (flex items-center, h-8, gap-[2px]):

┌───────────┬─│─┬──────────┬─│─┬─────────────────────────┬─│─┬──────────┐
│  supply   │ │ │validation│ │ │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░  │ │ │validation│
│           │ │ │          │ │ │ (labeling — current)     │ │ │          │
│ completed │ │ │completed │ │ │ partially filled         │ │ │ pending  │
│ solid blk │ │ │solid blk │ │ │ purple gradient          │ │ │ gray-200 │
└───────────┘ └───────────┘ └─────────────────────────────┘ └──────────┘
                │              │                              │
                gate           gate                           gate
                (solid ✓)      (dashed, pending)              (dashed)

Stage labels below (text-[10px] text-gray-500 flex justify-between mt-1):
"supply"      "validation"    "labeling"                      "validation"
```

**Segment styles:**
- Completed: `bg-[#1B1034]` solid, white text label
- Current: `bg-[#834DFB]` filled portion + `bg-gray-200` remaining
- Pending: `bg-gray-100 border border-gray-300` dashed outline
- Gate (passed): `w-[2px] bg-green-500`
- Gate (pending): `w-[2px] border-l border-dashed border-gray-400`

### Sub-task Breakdown Bar

Shows sub-steps within the current pipeline stage (labeling in this case).

```
h-12 flex gap-0 mx-6 mt-2

┌──────────────────┐┌──────────────────────────────┐┌──────────────────────┐
│ Pre-labeling     ││ Segmentation                 ││█ Task annotation █   │
│ by Agent         ││ manual-adjustment            ││                      │
│                  ││                              ││ (current sub-task)   │
│ bg-[#1B1034]     ││ bg-[#6B7280]                 ││ bg-white             │
│ text-white       ││ text-white                   ││ border-[1.5px]       │
│ text-xs          ││ text-xs                      ││ border-[#1B1034]     │
│                  ││                              ││ diagonal hatching    │
│ flex-[1]         ││ flex-[2]                     ││ pattern              │
│ solid = done     ││ solid gray = done            ││ text-sm font-medium  │
└──────────────────┘└──────────────────────────────┘└──────────────────────┘
```

**Sub-task segment styles (from wireframe):**
- Agent (completed): solid `bg-[#1B1034]` white text — "Pre-labeling by Agent"
- Manual adjustment (completed): solid `bg-gray-500` white text — "Segmentation manual-adjustment"
- Current human task: white bg, `border-[1.5px] border-[#1B1034]`, diagonal hatching pattern — "Task annotation"

### Canvas Area

```
flex-1 flex

Left nav rail (w-10, bg-[#1F2937], flex-col items-center justify-center gap-2):
├── ▲ button (w-8 h-8 bg-[#1B1034] text-white rounded flex items-center justify-center)
├── spacer
└── ▼ button (w-8 h-8 bg-[#1B1034] text-white rounded)

Canvas (flex-1, bg-[#374151]):
└── iframe (annotation runtime) or Konva stage
    Communication via postMessage: load_task, set_mode, request_response
```

### Action Bar

```
h-14 bg-[#111827] px-6 flex items-center justify-between

Left:
└── Timer badge: "Task time: 5m 45s (Session: 12m35s)"
    bg-amber-500/20 text-amber-400 text-sm px-3 py-1.5 rounded

Right (flex gap-3):
├── "Skip" — ghost btn text-gray-400 (10% limit warning tooltip)
├── "Save Draft" — outline btn text-gray-300 border-gray-600
├── "Prev" — outline btn text-white border-gray-600
└── "Next" — primary btn bg-white text-[#1B1034] font-semibold
```

### Workspace modes

| Mode | Canvas content | Action bar |
|---|---|---|
| **Supply** (7a) | Blank form / file upload zone / recorder | Submit only (no Prev/Next) |
| **Labeling** (7b) | Instance data + annotation tools + agent pre-labels | Skip / Save / Prev / Next |
| **Validation** (7c) | Instance + existing annotations + verdict controls (Accept/Reject/Revise) | Skip / Save / Accept / Reject |

---

## Shared Components

### TaskTypeBadge

**Inline:** `📤 Supply ($2.50) · 🏷 Labeling ($1.50) · ✅ Agent`  
Style: `text-xs text-gray-600`  
Agent tasks omit pay rate.

**Pill:** `bg-gray-100 text-gray-700 text-xs px-2.5 py-1 rounded-full font-medium`

### PipelineContextBar — Compact (16px)

Used in: Contributions table Stage column, My Tasks instance rows, Earnings breakdown.

```
h-[6px] w-full rounded-full overflow-hidden flex gap-[1px]

Segments:
├── Completed: bg-[#1B1034] flex-[weight]
├── Current:   bg-[#834DFB] flex-[progress] + bg-gray-200 flex-[remaining]
└── Pending:   bg-gray-200 flex-[weight]
```

No labels, no gates. Pure progress visualization.

### StatusBadge

| Status | Classes |
|---|---|
| ✓ Accepted | `text-green-600 font-medium` |
| ◐ In Review | `text-amber-600 font-medium` |
| ● Working | `text-[#834DFB] font-medium` |
| ✕ Rejected | `text-red-500 font-medium` |
| ◆ Royalty-eligible | `text-green-600 font-medium` |

---

## Implementation Structure

```
src/
├── app/contribute/
│   ├── page.tsx                    # Screen 1: Home Dashboard
│   ├── campaigns/
│   │   ├── page.tsx                # Screen 2a/2b: Browse + Enrollments (tab)
│   │   └── [id]/
│   │       ├── page.tsx            # Screen 2c: Campaign Detail
│   │       └── tasks/[taskId]/
│   │           └── page.tsx        # Screen 7: Task Workspace
│   ├── tasks/page.tsx              # Screen 3: Tasks Queue
│   ├── contributions/page.tsx      # Screen 4: Contributions Table
│   ├── earnings/page.tsx           # Screen 5: Earnings
│   └── profile/page.tsx            # Screen 6: Profile
├── components/
│   ├── shell/
│   │   ├── sidebar.tsx             # Dark sidebar, collapsible
│   │   ├── nav-item.tsx            # Active/inactive with accent bar
│   │   ├── top-bar.tsx
│   │   └── shell.tsx               # Layout wrapper
│   ├── campaign/
│   │   ├── campaign-card.tsx       # 8-section card with privacy tiers
│   │   ├── enrollment-card.tsx     # Progress bar + Continue/Unenroll
│   │   ├── campaign-bundle.tsx     # Task queue: header + task rows
│   │   └── campaign-detail.tsx     # Full detail page sections
│   ├── workspace/
│   │   ├── pipeline-bar.tsx        # Full 32px + compact 6px variants
│   │   ├── subtask-bar.tsx         # Sub-step breakdown with hatching
│   │   ├── canvas.tsx              # iframe/Konva wrapper
│   │   ├── action-bar.tsx          # Timer + Skip/Save/Prev/Next
│   │   └── nav-rail.tsx            # ▲/▼ clip navigation
│   ├── contributions/
│   │   ├── contributions-table.tsx
│   │   └── detail-drawer.tsx       # Sheet with media preview + lineage
│   ├── earnings/
│   │   ├── pipeline-breakdown.tsx  # Per-campaign earnings viz
│   │   └── transaction-table.tsx
│   └── shared/
│       ├── summary-card.tsx        # Label + big number
│       ├── status-badge.tsx        # Color-coded status text
│       ├── task-type-badge.tsx     # Inline/pill/icon variants
│       ├── compensation-pill.tsx   # Fixed/Royalty/Hybrid/Bounty
│       ├── credential-row.tsx      # Skill + tier badge + action
│       └── pipeline-bar-compact.tsx
├── app/auth/
│   ├── signin/page.tsx             # Screen 8: Sign In
│   ├── signup/page.tsx             # Screen 9: Sign Up (3-step)
│   └── callback/page.tsx           # OAuth callback handler
├── app/onboarding/
│   └── page.tsx                    # Screen 10: Onboarding (3-step)
├── components/auth/
│   ├── oauth-buttons.tsx           # 4 provider buttons
│   ├── otp-input.tsx               # 6-digit code entry
│   ├── password-input.tsx          # With strength meter
│   └── step-indicator.tsx          # Numbered progress dots
└── lib/
    └── theme.ts                    # Token constants
```

---

## Screen 8: Sign In

**Route:** `/auth/signin`  
**Shell:** none — full-page centered layout, no sidebar  
**Purpose:** Returning contributor authentication  
**Consistency:** Matches developer portal auth UX (same token system, same layout pattern)

```
Full page: min-h-screen bg-[#FAFAF9] flex items-center justify-center

┌─ Auth Container (w-[420px]) ────────────────────────────────┐
│ bg-white border-[1.5px] border-[#1B1034] p-10               │
│                                                              │
│  [Codatta logomark] Humanbased                               │  logomark w-8 h-8 (black variant)
│                                                              │  + "Humanbased" text-lg font-semibold text-[#1B1034]
│                                                              │
│  Sign in                                                     │  text-2xl font-semibold text-[#1B1034] mt-6
│  Welcome back to Humanbased                                  │  text-sm text-gray-500 mt-1
│                                                              │
│  ┌─ OAuth Buttons (flex-col gap-3, mt-8) ─────────────────┐ │
│  │                                                         │ │
│  │  [ G  Continue with Google    ]                         │ │  w-full h-11
│  │  [ in Continue with LinkedIn  ]                         │ │  bg-white border-[1.5px] border-[#1B1034]
│  │  [ 🤗 Continue with Hugging Face ]                      │ │  rounded-none
│  │  [ GH Continue with GitHub    ]                         │ │  text-sm font-medium text-[#1B1034]
│  │                                                         │ │  hover:bg-gray-50
│  │  Each button:                                           │ │  flex items-center justify-center gap-3
│  │  icon w-5 h-5 (provider logo) + text                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ──────────── or ────────────                                │  flex items-center gap-4
│  border-t text-xs text-gray-400                              │  <div className="flex-1 h-px bg-gray-200" />
│                                                              │
│  Email                                                       │  <Label> text-sm font-medium
│  ┌──────────────────────────────────────────────────────┐    │
│  │ you@example.com                                      │    │  <Input> h-11 border-[1.5px] border-[#1B1034]
│  └──────────────────────────────────────────────────────┘    │  rounded-none focus:border-[#834DFB]
│                                                              │  focus:ring-2 focus:ring-[#834DFB]/10
│  Password                                                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ••••••••                                        [👁]  │    │  same input style + eye toggle
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  [ Forgot password? ]                                        │  text-sm text-[#834DFB] hover:underline
│                                                              │  text-right
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                    Sign in                           │    │  <Button> w-full h-11
│  └──────────────────────────────────────────────────────┘    │  bg-[#1B1034] text-white rounded-none
│                                                              │  font-medium hover:bg-[#2D2250]
│                                                              │
│  Don't have an account?  Sign up                             │  text-sm text-gray-500
│                          text-[#834DFB] hover:underline      │  "Sign up" is a link
│                                                              │
└──────────────────────────────────────────────────────────────┘

Footer below card:
"© 2025 Humanbased · Privacy · Terms"  text-xs text-gray-400 mt-6
```

### OAuth Button Anatomy

```
h-11 w-full flex items-center justify-center gap-3
border-[1.5px] border-[#1B1034] rounded-none bg-white
hover:bg-gray-50 transition
text-sm font-medium text-[#1B1034]

┌──────────────────────────────────────────┐
│  [icon]  Continue with [Provider Name]   │
└──────────────────────────────────────────┘

Icons (w-5 h-5, inline SVG):
├── Google:       multi-color G logo
├── LinkedIn:     #0A66C2 "in" logo
├── Hugging Face: 🤗 emoji or HF logo
└── GitHub:       black octocat
```

### Error States

```
Field error:    border-red-500 + "Invalid email address" text-xs text-red-500 mt-1
Auth error:     red banner above form: bg-red-50 border border-red-200 p-3
                text-sm text-red-800 "Invalid credentials. Please try again."
Rate limited:   amber banner: "Too many attempts. Try again in 60 seconds."
```

---

## Screen 9: Sign Up (3-Step Flow)

**Route:** `/auth/signup`  
**Shell:** none — full-page centered  
**Purpose:** New contributor registration  
**Flow:** Email → OTP verify → Password + name

### Step Indicator (shared across steps)

```
flex items-center justify-center gap-0 mb-8

Step 1        Step 2        Step 3
  ●─────────────○─────────────○       (future steps dimmed)
  
Active:   w-8 h-8 bg-[#1B1034] text-white rounded-full flex items-center justify-center
          text-sm font-semibold
Completed: w-8 h-8 bg-[#834DFB] text-white rounded-full + ✓ checkmark
Pending:  w-8 h-8 bg-gray-200 text-gray-500 rounded-full
Line:     h-[2px] w-16 bg-[#1B1034] (completed) or bg-gray-200 (pending)
```

### Step 1: Email Entry

```
┌─ Auth Container (w-[420px]) ────────────────────────────────┐
│ bg-white border-[1.5px] border-[#1B1034] p-10               │
│                                                              │
│  [Codatta logomark]                                                │
│                                                              │
│  Create your account                                         │  text-2xl font-semibold
│  Join thousands of data contributors                         │  text-sm text-gray-500
│                                                              │
│  [Step indicator: ●───○───○ ]                                │
│                                                              │
│  ┌─ OAuth Buttons ────────────────────────────────────────┐  │
│  │  [ G  Sign up with Google    ]                         │  │  same 4 buttons as sign-in
│  │  [ in Sign up with LinkedIn  ]                         │  │
│  │  [ 🤗 Sign up with Hugging Face ]                      │  │
│  │  [ GH Sign up with GitHub    ]                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ──────────── or ────────────                                │
│                                                              │
│  Email                                                       │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ you@example.com                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │               Send verification code                 │    │  primary btn full-width
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  Already have an account?  Sign in                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Step 2: OTP Verification

```
┌─ Auth Container (w-[420px]) ────────────────────────────────┐
│ bg-white border-[1.5px] border-[#1B1034] p-10               │
│                                                              │
│  [Codatta logomark]                                                │
│                                                              │
│  Check your email                                            │  text-2xl font-semibold
│  We sent a code to yi@example.com                            │  text-sm text-gray-500
│                                                              │
│  [Step indicator: ✓───●───○ ]                                │
│                                                              │
│  Verification code                                           │  text-sm font-medium
│                                                              │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                 │  6 individual inputs
│  │  4 │ │  8 │ │  2 │ │  7 │ │    │ │    │                 │  w-12 h-14 each
│  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘                 │  text-2xl text-center font-mono
│                                                              │  border-[1.5px] border-[#1B1034]
│  flex items-center justify-center gap-2                      │  focus:border-[#834DFB]
│                                                              │  auto-advance on digit entry
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                  Verify code                         │    │  primary btn (disabled until 6 digits)
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  Didn't receive it?                                          │  text-sm text-gray-500
│  Resend code (47s)                                           │  text-[#834DFB] disabled with countdown
│                                                              │  enabled after 60s, then "Resend code"
│  Wrong email? Go back                                        │  text-sm text-[#834DFB]
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Step 3: Profile Setup

```
┌─ Auth Container (w-[420px]) ────────────────────────────────┐
│ bg-white border-[1.5px] border-[#1B1034] p-10               │
│                                                              │
│  [Codatta logomark]                                                │
│                                                              │
│  Set up your profile                                         │  text-2xl font-semibold
│  Almost there — just a few details                           │  text-sm text-gray-500
│                                                              │
│  [Step indicator: ✓───✓───● ]                                │
│                                                              │
│  Full name                                                   │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Yi Zhang                                             │    │  standard input
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  Username                                                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ @yi_zhang                                            │    │  prefix "@" inside input
│  └──────────────────────────────────────────────────────┘    │  + availability check (✓ available / ✕ taken)
│  ✓ Available  text-xs text-green-600                         │  real-time check with debounce
│                                                              │
│  Password                                                    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ••••••••••                                      [👁]  │    │  password input + eye toggle
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  Password strength:                                          │
│  ┌───────┐┌───────┐┌───────┐┌───────┐                       │  4-segment bar
│  │███████││███████││███████││░░░░░░░│                       │  h-1 flex gap-1
│  └───────┘└───────┘└───────┘└───────┘                       │
│  Good                                  text-xs text-amber-500│
│                                                              │
│  ✓ At least 8 characters                                    │  text-xs
│  ✓ One uppercase letter                                     │  met: text-green-600
│  ✕ One number                                               │  unmet: text-gray-400
│  ✓ One special character                                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │               Create account                         │    │  primary btn
│  └──────────────────────────────────────────────────────┘    │  disabled until all rules met
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Password Strength Meter

```
4 segments, h-1, flex gap-1, w-full

Segment fill logic:
├── 0 rules met:  all gray-200                 label: (none)
├── 1 rule met:   seg1 red-500, rest gray-200  label: "Weak" text-red-500
├── 2 rules met:  seg1-2 amber-500             label: "Fair" text-amber-500
├── 3 rules met:  seg1-3 amber-400             label: "Good" text-amber-500
└── 4 rules met:  all green-500                label: "Strong" text-green-600

Rules:
├── ≥ 8 characters
├── One uppercase letter
├── One number
└── One special character (!@#$%...)
```

---

## Screen 10: Onboarding (3-Step)

**Route:** `/onboarding`  
**Shell:** none — full-page centered, wider container  
**Purpose:** Post-signup profile enrichment — collect data needed before first contribution  
**Trigger:** Redirected here after successful sign-up or first OAuth sign-in

### Step Indicator (same component as sign-up, reused)

```
Step 1: Skills     Step 2: Interests     Step 3: Ready
  ●──────────────────○──────────────────○
```

### Step 1: Declare Skills

```
Full page: min-h-screen bg-[#FAFAF9] flex items-center justify-center

┌─ Onboarding Container (w-[560px]) ──────────────────────────┐
│ bg-white border-[1.5px] border-[#1B1034] p-10               │
│                                                              │
│  [Codatta logomark]                                                │
│                                                              │
│  What are you good at?                                       │  text-2xl font-semibold
│  Select skills relevant to data contribution work.           │  text-sm text-gray-500
│  You can update these later.                                 │
│                                                              │
│  [Step indicator: ●───○───○ ]                                │
│                                                              │
│  ┌─ Skill Grid (grid-cols-2 gap-3) ──────────────────────┐  │
│  │                                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐             │  │
│  │  │ ✓ Robotics      │  │   NLP / LLM     │             │  │
│  │  │   Annotation    │  │   Evaluation    │             │  │
│  │  └─────────────────┘  └─────────────────┘             │  │
│  │                                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐             │  │
│  │  │   Computer      │  │ ✓ Data          │             │  │
│  │  │   Vision        │  │   Collection    │             │  │
│  │  └─────────────────┘  └─────────────────┘             │  │
│  │                                                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐             │  │
│  │  │   Audio         │  │   Medical       │             │  │
│  │  │   Transcription │  │   Imaging       │             │  │
│  │  └─────────────────┘  └─────────────────┘             │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Each skill tile:                                            │
│  Unselected: border border-gray-200 p-4 rounded-none        │
│              text-sm font-medium text-gray-700               │
│              hover:border-[#1B1034]                           │
│  Selected:   border-[1.5px] border-[#1B1034] bg-[#F0EBFF]   │
│              text-sm font-medium text-[#1B1034]              │
│              ✓ checkmark top-right                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                    Continue                          │    │  primary btn
│  └──────────────────────────────────────────────────────┘    │  disabled until ≥1 selected
│                                                              │
│  [ Skip for now ]  text-sm text-gray-400 hover:text-gray-600│
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Step 2: Contribution Interests

```
┌─ Onboarding Container (w-[560px]) ──────────────────────────┐
│ bg-white border-[1.5px] border-[#1B1034] p-10               │
│                                                              │
│  [Codatta logomark]                                                │
│                                                              │
│  What kind of work interests you?                            │  text-2xl font-semibold
│  This helps us recommend campaigns.                          │  text-sm text-gray-500
│                                                              │
│  [Step indicator: ✓───●───○ ]                                │
│                                                              │
│  Preferred task types                                        │  text-sm font-medium
│                                                              │
│  ┌─ Option List (flex-col gap-2) ─────────────────────────┐  │
│  │                                                         │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ ✓ 📤 Supply — Create data from scratch           │   │  │  selectable rows
│  │  │   Record videos, upload files, capture data       │   │  │  same selected/unselected
│  │  └──────────────────────────────────────────────────┘   │  │  style as skill tiles
│  │                                                         │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │   🏷 Labeling — Annotate existing data            │   │  │
│  │  │   Review AI outputs, label segments, add text     │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  │                                                         │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │   ✅ Validation — Review others' work             │   │  │
│  │  │   Grade quality, verify accuracy, approve/reject  │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                              │
│  How much time per week?                                     │  text-sm font-medium mt-4
│  ┌──────────────────────────────────────────────────────┐    │
│  │ [ < 5 hrs ] [ 5–15 hrs ] [ 15–30 hrs ] [ 30+ hrs ] │    │  segmented control
│  └──────────────────────────────────────────────────────┘    │  active: bg-[#1B1034] text-white
│                                                              │  inactive: bg-white border text-gray-600
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                    Continue                          │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  [ Skip for now ]                                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Step 3: Ready to Contribute

```
┌─ Onboarding Container (w-[560px]) ──────────────────────────┐
│ bg-white border-[1.5px] border-[#1B1034] p-10               │
│ text-center                                                  │
│                                                              │
│  [Codatta logomark]                                                │
│                                                              │
│  You're all set!                                             │  text-2xl font-semibold
│  Your profile is ready. Start exploring campaigns.           │  text-sm text-gray-500
│                                                              │
│  [Step indicator: ✓───✓───● ]                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                                                      │    │
│  │  ┌──────┐                                            │    │  avatar w-20 h-20
│  │  │  YZ  │                                            │    │  bg-[#1B1034] rounded-full
│  │  └──────┘                                            │    │  text-2xl text-white
│  │                                                      │    │
│  │  Yi Zhang                                            │    │  text-xl font-semibold
│  │  @yi_zhang                                           │    │  text-sm text-[#834DFB]
│  │                                                      │    │
│  │  Skills: Robotics, Data Collection                   │    │  text-sm text-gray-500
│  │  Interests: Supply, Labeling · 5–15 hrs/week        │    │
│  │                                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  What to do next:                                            │  text-sm font-semibold mt-6
│                                                              │  text-left
│  1. Browse campaigns and find work that fits your skills     │  text-sm text-gray-600
│  2. Enroll in a campaign to start receiving tasks            │  ordered list, pl-5
│  3. Complete tasks to earn and build reputation              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              Browse Campaigns →                      │    │  primary btn
│  └──────────────────────────────────────────────────────┘    │  → navigates to /contribute/campaigns
│                                                              │
│  [ Go to Dashboard ]  text-sm text-[#834DFB]                 │  → navigates to /contribute
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Auth Flow Summary

```
                    ┌──────────────┐
                    │   Landing    │
                    │   /          │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼─────────┐    ┌─────────▼────────┐
     │   Sign In (8)    │    │   Sign Up (9)    │
     │                  │    │   Step 1: Email   │
     │  OAuth (4 prov)  │    │   Step 2: OTP     │
     │  — or —          │    │   Step 3: Profile  │
     │  Email+Password  │    │                    │
     └────────┬─────────┘    └─────────┬──────────┘
              │                        │
              │              ┌─────────▼──────────┐
              │              │  Onboarding (10)   │
              │              │  Step 1: Skills    │
              │              │  Step 2: Interests │
              │              │  Step 3: Ready     │
              │              └─────────┬──────────┘
              │                        │
              └────────────┬───────────┘
                           │
                  ┌────────▼─────────┐
                  │   Dashboard (1)  │
                  │   /contribute    │
                  └──────────────────┘

OAuth callback handling:
├── Existing user → Sign In → Dashboard
├── New user → auto-create account → Onboarding
└── Error → Sign In with error message
```

### OAuth Provider Config

| Provider | Client ID env var | Scope | Notes |
|---|---|---|---|
| Google | `GOOGLE_CLIENT_ID` | email, profile | Most common, default first |
| LinkedIn | `LINKEDIN_CLIENT_ID` | r_emailaddress, r_liteprofile | Professional context |
| Hugging Face | `HF_CLIENT_ID` | read | ML community, signals expertise |
| GitHub | `GITHUB_CLIENT_ID` | read:user, user:email | Developer background |

### Supabase Auth Integration

```ts
// OAuth sign-in
supabase.auth.signInWithOAuth({
  provider: 'google' | 'linkedin_oidc' | 'github',
  options: { redirectTo: `${origin}/auth/callback` }
})

// HuggingFace (custom provider via Supabase edge function)
// POST /auth/huggingface → redirect to HF OAuth → callback → exchange token

// Email OTP
supabase.auth.signInWithOtp({ email })

// Verify OTP
supabase.auth.verifyOtp({ email, token, type: 'signup' })

// Set password (after OTP verification)
supabase.auth.updateUser({ password })
```
