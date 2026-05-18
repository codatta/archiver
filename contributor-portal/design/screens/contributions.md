# Screen: Contributions

## Purpose
The contributor's ledger and lineage view. Shows all submitted task instances across campaigns — what was submitted, when, quality outcome, and (V2) downstream usage. Contributors use this to track their work history, monitor quality evaluations, and (V2) initiate disputes on unfair grades.

## Phase
V1 (history table + mock lineage); V2 (dispute action + downstream usage disclosure)

## Users
- **Active contributor** — reviewing submission history and quality grades
- **Contributor with a disputed evaluation** (V2) — initiating or tracking a dispute

## Entry Points
- Sidebar "Contributions" nav item
- My Kitchen → notification about a completed T4 evaluation → deep links to specific row
- Direct link `/contributions/:instance_id` (from notification: "Your annotation was graded")

## Exit Points
- "Dispute" action (V2) → Dispute Review screen
- Campaign name link → Campaign Detail
- Sidebar nav items → other screens

## Devices
- Desktop (primary): full data table with all columns visible
- Tablet (≥768px): horizontal scroll; pinned campaign + task columns
- Mobile (<768px): horizontal scroll; pinned campaign + task columns; reduced visible columns

---

## States

| State | Trigger | What renders |
|---|---|---|
| Loading | Initial fetch | Table skeleton (shimmer rows) |
| Empty | No submissions ever | "No contributions yet" illustration + "Go to My Kitchen" CTA |
| Populated | Submissions exist | Filter/sort row + contributions table |
| Row highlighted | Arrived via `#<instance_id>` anchor | Scroll to row; brief highlight animation |
| Lineage expanded | Row expand trigger | Inline lineage DAG: T1→T2→T3→T4 with status per step |

---

## User Journey

1. Contributor opens Contributions from sidebar.
2. Sees a table of past submissions sorted by date (newest first).
3. Each row: campaign name, task type, submission date, status, quality grade (when evaluated).
4. Clicks a row to expand inline lineage: sees the full T1→T2→T3→T4 pipeline status for that instance.
5. (V2) Sees a quality grade of "Needs revision" or "D" → clicks "Dispute" → navigates to Dispute Review.
6. (V2) Sees "Used in training run #12" downstream usage note on royalty-campaign rows.

---

## Behavior

**On load:**
- Fetch contribution history: `GET /v1/contributions?contributor_id=me` (paginated, 50 per page)
- Sort: newest first by default
- If `#<instance_id>` anchor: scroll to that row and highlight

**Table columns (V1):**
| Column | Content |
|---|---|
| Campaign | Campaign name (linked to Campaign Detail) |
| Task | T1 / T3 (task type) |
| Submitted | Submission timestamp |
| Status | Processing / Graded / Rejected |
| Quality | Grade A–F (shown when T4 evaluation complete; pending otherwise) |
| Lineage | Expand trigger (chevron icon) |

**Table columns added in V2:**
| Column | Content |
|---|---|
| Downstream Usage | "Used in Model Run #N" or "—" for instant-payout campaigns |
| Dispute | "Dispute" button if grade is disputable (quality grade D or below, within dispute window) |
| Earnings | Payout amount or royalty accrual status |

**Lineage expansion:**
- Expands inline below the row (not a modal)
- Shows the T1→T2→T3→T4 DAG for this specific instance:
  - T1: uploaded (timestamp, file name, storage path link)
  - T2: processing status (duration, Vision Engine output summary: clips found, frames processed)
  - T3: annotation submitted (timestamp, action labels used, clip count)
  - T4: evaluation result (grade, evaluator type: auto / peer, feedback note if any)
- Mock lineage: all statuses available; `lineage_staging` table data

**Filtering + sorting:**
- Filter by: campaign (multi-select), status, quality grade range
- Sort by: submission date (default), quality grade, campaign name
- Applied client-side against fetched page in V1

**Pagination:**
- "Load more" button at bottom (not infinite scroll — avoids accidental triggering)
- Shows "Showing 1–50 of 147 contributions" count

---

## Interactions

| Element | Trigger | Response |
|---|---|---|
| Row chevron | Click | Expand inline lineage for that instance |
| Campaign name | Click | Navigate to Campaign Detail |
| Filter by campaign | Change | Filter table client-side |
| Sort selector | Change | Re-sort table |
| "Dispute" button (V2) | Click | Navigate to Dispute Review for that instance |
| "Load more" | Click | Fetch next page, append to table |
| Notification link | Navigate | Scroll to highlighted row |

No keyboard shortcuts on this screen.

---

## Quality Grades

| Grade | Meaning | Action available |
|---|---|---|
| Pending | T4 evaluation not yet complete | — |
| A / B | High quality | None needed |
| C | Acceptable | Optional dispute (V2) |
| D | Needs revision — significant issues | Dispute (V2) or re-annotate |
| F | Rejected | Dispute (V2) |

---

## Downstream Usage (V2)

- For royalty campaigns: when a builder publishes a training run event that references this instance's annotation, show "Used in [Builder name] Model Training Run #N"
- Data written to `lineage_staging` from builder webhook
- Contributor sees royalty status update: Pending → Confirmed

---

## Screen Relationships

| Destination | Trigger | Data passed |
|---|---|---|
| Dispute Review (V2) | "Dispute" button | `instance_id` via URL param |
| Campaign Detail | Campaign name link | `campaign.id` via URL param |

---

## Pencil Design
Designed in `design/source/contributor-portal.pen` — Screen 9: Contributions (node `6vXnv`, x=12800, y=0).

Key design decisions recorded:
- Single-column full-width list (original 2-column campaign grid collapsed; right column deleted, cards moved left)
- Row visual pattern: purple icon for T3 annotation tasks (`clapperboard`), gray upload icon for T1 tasks
- Grade displayed inline in footer: green `#22C55E` for A/B, default gray for C; "Processing…" shown as plain text for in-progress rows
- V1 uses card shape (not true table rows) for compatibility with Pencil copy-based constraint
