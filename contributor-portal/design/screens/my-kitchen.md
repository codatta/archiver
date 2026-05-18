# Screen: My Kitchen

## Purpose
The operational home for enrolled contributors. Surfaces pending tasks across all active campaigns so contributors can immediately start working. Returning contributors land here directly. Designed to minimize decision fatigue — the most actionable task is always front and center.

## Phase
V1

## Users
- **Active contributor** — enrolled in at least one campaign, checking what work is available
- **Returning contributor** — daily re-entry; expects to find new tasks ready to pick up

## Entry Points
- Sidebar "My Kitchen" nav item (returning users' primary home)
- Post-enrollment redirect from Campaign Detail ("Enrolled! Your first task is ready.")
- Post-submission redirect from Task Upload or Annotation Workspace
- App root `/` redirects here if contributor is enrolled in at least one campaign

## Exit Points
- Task card "Start Task" → Task Upload (T1) or Annotation Workspace (T3) depending on task type
- "Find more campaigns" CTA (empty state) → Campaign Discovery
- Sidebar nav items → other screens

## Devices
- Desktop (primary): task card list with sidebar stats panel
- Tablet (≥768px): responsive single column, stats collapsed into top summary bar
- Mobile (<768px): 1-column card list, stats in collapsible top bar

---

## States

| State | Trigger | What renders |
|---|---|---|
| Loading | Initial fetch | 3 skeleton task cards (shimmer) |
| Empty — no pending tasks | All tasks submitted, none ready yet | "No tasks pending" illustration + "Find more campaigns" CTA + enrolled campaigns list |
| Empty — not enrolled | Contributor has no campaign enrollments | "You haven't enrolled in any campaigns yet" + "Discover Campaigns" primary CTA |
| Active tasks | Pending task instances exist | Task card list, grouped by campaign |
| Mixed (some done today) | Contributor completed tasks today | Completed count badge in header; remaining tasks shown |

---

## User Journey

1. Returning contributor opens the app → lands on My Kitchen.
2. Sees task cards grouped by campaign. Each card shows: campaign name, task type (T1 Upload / T3 Annotate), deadline (if any), estimated time, pay rate.
3. Picks a task card and clicks "Start Task" → navigates to the appropriate task screen.
4. Completes the task → lands back on My Kitchen.
5. If no more tasks remain: sees "No tasks pending — check back later" and optionally explores new campaigns.

---

## Behavior

**On load:**
- Fetch pending task instances for contributor: `GET /v1/my-kitchen/tasks` (returns instances with status `pending` or `in_progress`)
- Sort: In-progress first (resumed), then by campaign, then by oldest assigned
- Fetch enrollment summary: campaigns enrolled, tasks completed today

**Task types shown:**
- T1 (Data Supply): contributor uploads video/data. Shows "Upload" task type tag.
- T3 (Human Annotation): contributor annotates clips. Shows "Annotate" task type tag.
- T2 and T4 are automated — not shown as actionable cards. If T2 is processing, show progress indicator on the campaign row.

**In-progress tasks:**
- If contributor started a task but didn't submit, show it with "Resume" CTA instead of "Start"
- In-progress tasks float to the top of their campaign group

**Task grouping:**
- Cards grouped by campaign name (collapsible group header in V2; flat list in V1)
- Within a campaign, T1 tasks shown before T3 tasks if both pending

**Automated task processing (T2):**
- While T2 is running for a campaign, show a passive progress row: "Vision processing in progress — your annotation task will appear here when ready"
- No action required; auto-refreshes every 30 seconds via polling in V1 (V2: websocket)

---

## Interactions

| Element | Trigger | Response |
|---|---|---|
| "Start Task" button | Click | Navigate to Task Upload (T1) or Annotation Workspace (T3) |
| "Resume" button (in-progress task) | Click | Navigate to task screen, restoring saved state |
| "Find more campaigns" CTA | Click | Navigate to Campaign Discovery |
| "Discover Campaigns" CTA (not enrolled state) | Click | Navigate to Campaign Discovery |
| Campaign group header (V2) | Click | Collapse / expand campaign's task list |
| Notification bell | Click | Open notifications panel (in-app notifications) |

No keyboard shortcuts on this screen.

---

## Task Card Anatomy

Each task card contains:
- **Campaign name** (linked to Campaign Detail)
- **Task type tag** — "Upload" (T1) or "Annotate" (T3), color-coded (purple)
- **Task description** — one-line from task config (e.g., "Upload a 30–120s robotics video")
- **Estimated time** — from task definition (e.g., "~15 min")
- **Pay rate** — per-task rate or royalty indicator
- **Status** — "Ready" (new) or "In Progress" (resumed)
- **CTA button** — "Start Task" or "Resume"

---

## Stats Summary (Desktop sidebar / Mobile top bar)

- Total tasks completed (lifetime)
- Tasks completed today
- Active campaigns count
- Pending tasks count
- Reputation score (links to Skills & Profile)

---

## Screen Relationships

| Destination | Trigger | Data passed |
|---|---|---|
| Task Upload (T1) | "Start Task" / "Resume" on T1 task card | `instance_id` via URL param |
| Annotation Workspace (T3) | "Start Task" / "Resume" on T3 task card | `instance_id` via URL param |
| Campaign Discovery | "Find more campaigns" CTA | — |
| Campaign Detail | Campaign name link on task card | `campaign.id` via URL param |
| Skills & Profile | Stats reputation score link | — |

---

## Pencil Design
Designed in `design/source/contributor-portal.pen` — Screen 7: My Kitchen (node `1zWJe`, x=9600, y=0).

Key design decisions recorded:
- Task cards use copy-then-update pattern (C() from existing Screen 1 cards) due to Pencil I() rendering constraint
- Active task card has `stroke:#000 1.5px`; pending card has `stroke:#E5E7EB 1.5px`
- Task type badges: purple `#F0EBFF` bg for Annotate, yellow `#FEF9C3` for Upload
- T2 processing banner deferred (C() appends-to-end only; banner needs position 1 insertion)
