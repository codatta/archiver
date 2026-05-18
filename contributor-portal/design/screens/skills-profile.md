# Screen: Skills & Profile

## Purpose
Contributors manage their identity and qualifications. They can view and progress their skill verification tiers — from self-declared through tutorial, credential submission, and eventually AI interview. The profile card provides reputation context. This screen is the qualification gateway for gated campaigns.

## Phase
V1 (tutorial-passed tier); V2 (credential submission); V3 (AI interview / expert tier)

## Users
- **New contributor** — completing a tutorial to qualify for their first campaign
- **Experienced contributor** — submitting credentials to access higher-tier campaigns
- **Returning contributor** — checking verification status after credential review

## Entry Points
- Sidebar "Skills" nav item
- Campaign Detail → "Complete qualification" link (anchored to specific skill `#<skill_id>`)
- Campaign Discovery → locked campaign "View + Qualify" → Campaign Detail → here
- Direct link `/skills#<skill_id>` (from notification: "Your credential was approved")

## Exit Points
- Training material link → external tutorial (opens new tab)
- Credential submission confirmation → stays on screen with status updated
- Back to Campaign Detail (if arrived via qualification flow) — breadcrumb or browser back
- Sidebar nav items → other screens

## Devices
- Desktop (primary): 2-column layout (profile card left, skills + badges right) or full-width table
- Tablet (≥768px): responsive single column (profile card → badges → skills table → credential form)
- Mobile (<768px): 1-column; credential upload not optimized but functional

---

## States

| State | Trigger | What renders |
|---|---|---|
| Loading | Initial fetch | Skeleton for profile card + skill rows |
| Populated | Data fetched | Profile card + badges + skills table |
| Skill highlighted | Arrived via `#<skill_id>` anchor | Scroll to skill row; brief border pulse |
| Credential pending review | Contributor submitted credential, awaiting review | Skill row shows "Under review" badge; action button disabled |
| Credential approved | Review completed, credential-verified | Skill row updates to green "credential-verified" tier |
| Credential rejected | Review completed, not approved | Skill row shows rejection notice + "Resubmit" option |
| Error | Fetch or submission failure | Toast error |

---

## User Journey

### Tutorial qualification flow
1. Contributor arrives from Campaign Detail (unqualified, "Complete qualification" clicked).
2. Finds the relevant skill row highlighted.
3. Sees current tier is `unverified`. Clicks "Start Training".
4. Navigates to external training material (new tab). Completes tutorial + quiz.
5. System updates skill tier to `tutorial-passed` (webhook or polling).
6. Returns to Skills & Profile — sees updated green progress. Navigates back to Campaign Detail to enroll.

### Credential submission flow
1. Contributor sees a skill requiring `credential-verified` tier.
2. Clicks "Submit Credential" on that skill row.
3. Credential submission form expands (or modal opens).
4. Selects credential type (diploma, professional license, certification).
5. Uploads credential document (PDF or image).
6. Submits. Sees "Under review" status. Amber callout: "Reviewed within 24-48 hours."
7. Receives in-app notification when approved. Returns to see `credential-verified` badge.

---

## Behavior

**On load:**
- Fetch contributor profile: `GET /v1/contributors/me`
- Fetch skills + verification tiers: `GET /v1/contributors/me/skills`
- Fetch badges earned: `GET /v1/contributors/me/badges`
- If `#<skill_id>` anchor: scroll to that row and pulse border

**Skill tier hierarchy:**
| Tier | Color | Meaning | How to reach |
|---|---|---|---|
| `unverified` | `#9890A8` gray | Self-declared | Default |
| `tutorial-passed` | `#834DFB` purple | Tutorial completed | Complete training material + quiz (V1) |
| `credential-verified` | `#22C55E` green | Document approved | Submit diploma/license → platform review (V2) |
| `expert` | `#F59E0B` amber | AI interview passed | Scheduled video interview with AI (V3) |

**Credential submission:**
- V1: form present but submission routes to "Coming in V2" notice
- V2: `POST /v1/contributors/me/skills/:skill_id/credential` (multipart: `credential_type`, `file`)
- Backend: stores in Supabase Storage, triggers AI review pipeline; sets status `pending_review`
- AI review result (approved/rejected) arrives via webhook → updates skill tier

**Training material link:**
- URL from skill config in campaign requirements
- Opens in new tab
- Quiz result fed back via webhook from training platform (or manual verification in V1)

---

## Layout

### Profile card (left on desktop, top on mobile)
- Avatar (initials placeholder if no photo)
- Contributor name
- Email + verification badge (verified / unverified)
- **Reputation score**: `847 / 1000` with progress bar (purple fill)
- Member since date
- Edit profile link (V2)

### Badges row
- 4 badge tiles in a row (scrollable on mobile)
- Each tile: icon + label + locked/unlocked state
- Examples: "Annotator" (milestone), "Robotics Pro" (campaign badge), "ID Verified" (KYC), "Expert" (locked)
- Locked badges show gray overlay + lock icon

### Skills table
Each skill is a row with:
- **Left accent bar** (color = verification tier: purple/green/gray/amber)
- **Skill name** + short description
- **Tier badge**: pill badge in tier color
- **Action button**:
  - `unverified` → "Start Training" (primary outline)
  - `tutorial-passed` → "View Training" (ghost) — no further action needed for this tier
  - pending review → "Under Review" (disabled)
  - `credential-verified` → "View Credential" (ghost)
  - `expert` → "View Interview" (ghost)

### Credential submission form (V2, below skills table or in expandable panel)
- Skill selector (pre-filled if arrived from skill row)
- Credential type selector (diploma, professional license, certification, other)
- Upload drop zone (dashed border; accepts PDF, JPG, PNG)
- Amber info callout: "Reviewed by platform AI within 24-48 hours. Borderline cases may require human review."
- Submit button (disabled if no file)

---

## Interactions

| Element | Trigger | Response |
|---|---|---|
| "Start Training" button | Click | Open external training URL in new tab |
| "Submit Credential" button | Click | Expand credential form (or open modal) for that skill |
| Credential type selector | Change | Update form; update accepted file types hint |
| Credential drop zone | Drop/click | Select and preview file |
| Credential submit button | Click | POST credential → show "Under review" status |
| Badge tile | Click | Show badge detail tooltip (unlock criteria, date earned) |
| Edit profile link (V2) | Click | Open profile edit form / modal |
| Anchor link `#<skill_id>` | Load | Scroll to skill row + pulse |

No keyboard shortcuts on this screen.

---

## Screen Relationships

| Destination | Trigger | Data passed |
|---|---|---|
| Campaign Detail | Breadcrumb (if arrived via qualification flow) | — |
| External training material | "Start Training" button | Opens new tab |

---

## Pencil Design
Designed in `design/source/contributor-portal.pen` — Screen 8: Skills & Profile (node `vQae6`, x=11200, y=0).

Key design decisions recorded:
- 2-column layout: profile card (left, equal width) + skills table (right, equal width)
- Profile card: black 48px avatar circle with "YZ" initials, reputation score, member since date
- Skill tier visual language: purple `#F0EBFF` bg + `#834DFB` badge for tutorial-passed; green `#DCFCE7` + `#22C55E` badge for credential-verified; gray for unverified
- Green card border (`stroke:#22C55E 1.5px`) on credential-verified skill row
- Active nav uses `LqMhf`/`tUrgC` descendant IDs for RiXIX component (not `Vcbq6`/`3rUC3`)
