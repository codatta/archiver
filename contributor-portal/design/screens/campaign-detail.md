# Screen: Campaign Detail

## Purpose
The decision screen. Contributors evaluate a campaign's full scope — task pipeline, compensation structure, builder credibility, and qualification requirements — before enrolling. Must give enough information to earn trust without overwhelming.

## Phase
V1

## Users
- **Prospective contributor** — evaluating whether this campaign is worth their time and effort
- **Locked contributor** — viewing requirements they must satisfy to qualify; may be redirected here after clicking "View + Qualify"

## Entry Points
- Campaign Discovery card — "View Campaign" button or card click → lands at top
- Campaign Discovery card — "View + Qualify" → lands with `#qualify` anchor section highlighted
- Campaign Detail (self) after completing qualification in Skills & Profile — returning to enroll

## Exit Points
- "Enroll" button → My Kitchen (post-enrollment task queue)
- "Complete qualification" link → Skills & Profile (for tutorial or credential)
- Breadcrumb / back → Campaign Discovery
- Sidebar nav items → other screens

## Devices
- Desktop (primary): 2-column layout (task DAG left, metadata cards right)
- Tablet (≥768px): stacked single column (hero → DAG → cards)
- Mobile (<768px): stacked, scrollable; enroll button pinned to bottom bar

---

## States

| State | Trigger | What renders |
|---|---|---|
| Loading | Initial fetch | Hero skeleton + shimmer placeholders for DAG and right-column cards |
| Qualified | Contributor meets all skill requirements | Enroll card shows green qualification badge + primary "Enroll" button |
| Partially qualified | Some skills met, others not | Enroll card lists met ✓ and unmet ✗ requirements; "Complete qualification" per unmet |
| Unqualified | No requirements met | Enroll card shows lock icon + "Start qualification" CTA; section highlighted if `#qualify` anchor |
| Already enrolled | Contributor already active in campaign | Enroll card replaced with "Go to My Kitchen" button; enrollment date shown |
| Quota reached | Campaign task instances at capacity | Enrollment CTA hidden; "Quota reached — check back later" notice shown |
| Error | Fetch failure | Toast error + retry button |

---

## User Journey

1. Contributor arrives from Campaign Discovery (either direct click or "View + Qualify").
2. Reads hero: campaign name, frontier tag, compensation badge, one-line description.
3. Scrolls down into the 2-column layout:
   - Left: reviews the T1→T2→T3→T4 task DAG. Understands what they'll do (T1, T3), what's automated (T2), what's quality control (T4).
   - Right: reads compensation breakdown (type, share percentages, royalty note if applicable).
4. Checks builder credibility card — org name, verified badge, completed campaigns, satisfaction score.
5. Scrolls to enroll card — sees qualification status.
   - If qualified: clicks "Enroll". Navigated to My Kitchen.
   - If not qualified: clicks "Complete qualification" → Skills & Profile for that skill.
6. Returns to this screen after qualification → qualification status updated → enrolls.

---

## Behavior

**On load:**
- Fetch campaign detail from `GET /v1/campaigns/:id`
- Fetch contributor qualification status from profile (compared against `campaign.requirements`)
- Qualification check runs client-side against fetched data

**Qualification check:**
- For each skill in `campaign.requirements`: compare against contributor's `skills[]` tier
- Requirement tiers: `tutorial-passed`, `credential-verified`, `expert` — must meet or exceed
- All requirements must be met to enable enrollment

**Enroll action:**
- `POST /v1/campaigns/:id/enroll` — creates enrollment record and triggers T1 task instance creation
- On success: navigate to My Kitchen, show success toast "Enrolled! Your first task is ready."
- On error (race: quota reached): show "Campaign is now full" inline in enroll card

**`#qualify` anchor:**
- If URL contains `#qualify`, scroll to the enroll card on load and briefly pulse its border (`#834DFB`)

**Progress bar:**
- Same calculation as Campaign Discovery: `task_instances count / campaign.params.target_quantity`, capped at 100%

---

## Interactions

| Element | Trigger | Response |
|---|---|---|
| "Enroll" button | Click | POST enroll → navigate to My Kitchen |
| "Complete qualification" link (per unmet skill) | Click | Navigate to `/skills#<skill_id>` |
| "Go to My Kitchen" button (already enrolled) | Click | Navigate to My Kitchen |
| Breadcrumb / back link | Click | Navigate back to Campaign Discovery |
| Task DAG node | Click | Expand inline detail for that task step (V2 — no-op in V1) |
| Builder org link chips (LinkedIn, HuggingFace, GitHub) | Click | Open external URL in new tab |
| Sidebar nav | Click | Navigate to respective screen |

No keyboard shortcuts on this screen.

---

## Layout Detail

### Hero (full-width, `#1B1034` dark background)
- Campaign name (32px semibold, white)
- Frontier tag (color-coded, white border)
- Compensation badge (right-aligned)
- One-line subtitle / campaign description (white, 80% opacity)
- Progress bar (white on `#834DFB` on dark track) + contribution count

### Left column — Task DAG (540px, desktop)
- Vertical pipeline: T1 → T2 → T3 → T4
- Each task card: colored left accent bar + task label + role indicator (human / agent / auto)
  - T1: purple accent — "Data Supply — You upload"
  - T2: cyan accent — "Vision Processing — Automated agent"
  - T3: purple accent — "Human Annotation — You annotate" (highlighted "You are here" entry point)
  - T4: gray accent — "Validation — 10% sample, auto + human"
- Arrow connectors between cards

### Right column (400px, desktop) — 3 stacked cards

**Compensation card:**
- Compensation type badge (Royalty / Instant / Mix)
- For royalty: share breakdown table (Contributor 60%, Upstream 35%, Platform 5%)
- Downstream usage disclosure note (amber callout for royalty)
- For instant: flat rate per task, payout schedule

**Builder credibility card:**
- Org logo circle + org name + verified badge
- Completed campaigns count + satisfaction score (stars or percentage)
- Link chips: LinkedIn, HuggingFace, GitHub (only shown if set)

**Enroll card (id="qualify"):**
- Qualification status section (one row per requirement)
  - Met: green checkmark + skill name + current tier
  - Unmet: red X + skill name + required tier + "Complete qualification →" link
- Enrollment CTA or status

---

## Screen Relationships

| Destination | Trigger | Data passed |
|---|---|---|
| My Kitchen | Successful enrollment | — (enrollment record created server-side) |
| Skills & Profile | "Complete qualification" per unmet skill | `skill_id` via URL param → `#<skill_id>` |
| Campaign Discovery | Breadcrumb / back | — |

---

## Excalidraw Design
Checkpoint: `a24a121714b24d579e` (see `design/reference/contributor-kitchen.md`)
