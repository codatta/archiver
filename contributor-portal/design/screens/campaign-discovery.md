# Screen: Campaign Discovery

## Purpose
The primary entry point for contributors exploring available campaigns. Contributors browse, filter, and evaluate campaigns to decide which ones to pursue. Designed for quick scanning — a contributor should be able to assess a campaign's fit within 10 seconds from the card alone.

## Phase
V1

## Users
- **New contributor** — first time exploring; doesn't know what campaigns exist or what they require
- **Returning contributor** — checking for new campaigns that match their existing qualifications

## Entry Points
- App root `/` redirects here if not enrolled in any campaign
- "Discover" sidebar nav item
- "Find more campaigns" CTA from My Kitchen when task queue is empty

## Exit Points
- Campaign card "View Campaign" → Campaign Detail
- Campaign card "View + Qualify" → Campaign Detail (scrolled to qualification section)
- Sidebar nav items → other screens

## Devices
- Desktop (primary): 3-column campaign card grid
- Tablet (≥768px): 2-column grid
- Mobile (<768px): 1-column, vertical scroll

---

## States

| State | Trigger | What renders |
|---|---|---|
| Loading | Initial page load | 3 skeleton campaign cards (shimmer) |
| Empty | No campaigns match active filters | "No campaigns match your filters" + reset filters link |
| No campaigns exist | Platform has zero live campaigns | "No campaigns are live yet — check back soon" |
| Populated | Campaigns fetched | Filter row + campaign card grid |

---

## User Journey

1. Contributor opens the Discover page.
2. Sees a grid of campaign cards with frontier tags (Robotics, Medical, Language) and compensation badges (Royalty, Instant, Mix).
3. Optionally filters by frontier type and/or compensation type using pill filters.
4. Reads each card: campaign name, builder org, contribution progress, time estimate, pay rate.
5. Notices lock badges on campaigns they don't qualify for yet.
6. Clicks "View Campaign" on a card they want → navigates to Campaign Detail.
7. Clicks "View + Qualify" on a locked campaign → navigates to Campaign Detail with qualification section highlighted.

---

## Behavior

**On load:**
- Fetch live campaigns from `GET /v1/campaigns?status=live`
- Fetch contributor's current qualifications from profile (used to determine lock state per card)
- Show skeleton cards during fetch

**Filtering:**
- Frontier filter and compensation filter are additive (AND)
- Filters are applied client-side against the already-fetched campaign list
- Active filter chips highlighted in `#F0EBFF` / `#834DFB`; inactive in gray
- Filter state is not persisted to URL in V1 (V2: query params for shareability)

**Campaign card lock badge:**
- If campaign requires a skill tier the contributor doesn't have → show red-tint "Credential required" / "Tutorial required" badge
- CTA changes to "View + Qualify" (outline button) instead of "View Campaign" (dark button)
- Locked cards are still visible and clickable — locking only blocks enrollment, not viewing

**Progress bar:**
- Fetched from campaign aggregate: `task_instances count / campaign.params.target_quantity`
- Capped at 100% — campaigns at quota show "Quota reached" and hide enrollment CTA

---

## Interactions

| Element | Trigger | Response |
|---|---|---|
| Frontier filter pill | Click | Toggle; re-filters card list client-side |
| Compensation filter pill | Click | Toggle; re-filters card list client-side |
| "View Campaign" button | Click | Navigate to `/campaigns/:id` |
| "View + Qualify" button | Click | Navigate to `/campaigns/:id#qualify` |
| Campaign card (anywhere except button) | Click | Same as "View Campaign" |
| Sort selector | Change | Re-sorts card list (Newest / Most Progress / Payout) |

No keyboard shortcuts on this screen.

---

## Screen Relationships

| Destination | Trigger | Data passed |
|---|---|---|
| Campaign Detail | Card click / "View Campaign" | `campaign.id` via URL param |
| Campaign Detail #qualify | "View + Qualify" | `campaign.id` + scroll anchor |
| My Kitchen | Sidebar nav | — |
| Skills & Profile | Sidebar nav | — |

---

## Excalidraw Design
Checkpoint: `8c65b2e5ec6b494887` (see `design/reference/contributor-kitchen.md`)
