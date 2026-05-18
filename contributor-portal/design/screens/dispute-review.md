# Screen: Dispute Review

## Purpose
The dispute initiation and resolution screen. When a contributor receives a quality grade they believe is unfair, they can dispute it here. The dispute converts to a peer-review task distributed to qualified campaign contributors. This screen serves both the disputing contributor (viewing dispute status) and peer reviewers (completing the review task).

## Phase
V2

## Users
- **Disputing contributor** — initiating a dispute on their own evaluation; tracking outcome
- **Peer reviewer** — a qualified campaign contributor assigned to review the dispute as a task

## Entry Points
- Contributions screen → "Dispute" button on a graded row → `/disputes/new?instance_id=<id>`
- My Kitchen → dispute review task card (peer reviewer flow) → `/disputes/:dispute_id/review`
- Notification: "Your dispute was resolved" → `/disputes/:dispute_id`

## Exit Points
- Submit dispute → back to Contributions (with "Dispute submitted" toast)
- Complete peer review → back to My Kitchen (with "Review submitted" toast)
- Cancel → back to Contributions or My Kitchen

## Devices
- Desktop (primary): 2-column (annotation preview left, dispute form/decision right)
- Tablet (≥768px): stacked single column
- Mobile (<768px): 1-column; annotation preview collapsed by default

---

## States

### Disputing contributor view

| State | Trigger | What renders |
|---|---|---|
| New dispute form | Arrived from Contributions "Dispute" | Annotation preview + dispute reason form |
| Submitted — pending | Dispute submitted, awaiting peer review | Status: "Dispute under peer review" + estimated resolution |
| Resolved — upheld | Peer review quorum upheld original grade | Original grade shown; dispute closed message |
| Resolved — overturned | Peer review quorum overturned grade | New grade shown; earnings updated |
| Timeout — no quorum | Not enough reviewers responded in time | Default outcome shown (platform-configured: uphold or overturn) |

### Peer reviewer view

| State | Trigger | What renders |
|---|---|---|
| Review task loaded | Peer reviewer opens from My Kitchen | Annotation to review + original grade + dispute reason |
| Decision submitted | Reviewer submits uphold/overturn | Success state; back to My Kitchen |

---

## Behavior

**Dispute eligibility:**
- Eligible: quality grade D or F (or grade C, platform-configurable)
- Within dispute window: default 7 days from evaluation (platform-configurable per campaign)
- One dispute per instance (no re-dispute if upheld)

**Dispute submission:**
- `POST /v1/disputes` with `{ instance_id, reason_text, evidence_note }`
- Backend: creates dispute record; generates peer-review task instances for qualified contributors on that campaign
- Peer reviewer count: platform-configured (default: 3 reviewers)
- Timeout: platform-configured (default: 72 hours)

**Peer review task:**
- Appears in peer reviewer's My Kitchen as a "Dispute Review" task
- Reviewer sees: the original annotation (read-only), the original grade + rationale, the dispute reason
- Reviewer decision: "Uphold original grade" or "Overturn — suggest grade: [A/B/C]"
- Decision submitted: `POST /v1/disputes/:dispute_id/reviews` with `{ decision, suggested_grade, note }`

**Resolution:**
- When quorum reached (≥50% of reviewer count + 1 vote in agreement) before timeout → outcome applied immediately
- At timeout: if quorum reached → apply; if not → apply platform default
- Outcome: `upheld` (original grade stands) or `overturned` (grade updated to reviewer suggestion median)
- Disputing contributor and all peer reviewers notified of outcome

**Peer reviewer incentive:**
- Peer reviewers earn a small flat fee per review (from platform fee pool)
- Shown in their earnings ledger as "Dispute review fee"

---

## Layout

### Disputing contributor — new dispute form

**Left panel:** Annotation preview (read-only replay of the submitted annotation)
- Video player (read-only), timeline with their submitted segments, keypoints rendered
- Original grade badge + T4 evaluation feedback note

**Right panel:** Dispute form
- Instance summary (campaign, task type, submission date, grade received)
- Dispute reason textarea: "Explain why you believe this grade is incorrect" (required, max 1000 chars)
- Evidence note textarea: optional — "Describe any relevant context" (optional, max 500 chars)
- Submit button + Cancel link

### Disputing contributor — status view

**Status card:**
- Dispute ID + submission date
- Current status: "Under review by peers" / "Resolved: Overturned" / "Resolved: Upheld"
- Reviewer count: "2 of 3 reviews received"
- Estimated resolution (from timeout window)
- Outcome (when resolved): new grade, earnings update note

### Peer reviewer — review task

**Left panel:** Annotation to review (same read-only annotation player)
- Original grade badge prominently shown
- T4 evaluator feedback note

**Right panel:** Review decision form
- Dispute reason (from disputing contributor, quoted)
- Decision selector: "Uphold original grade" / "Overturn — assign grade:"
  - If overturn: grade selector A / B / C
- Note textarea: optional explanation (max 500 chars)
- Submit review button

---

## Interactions

| Element | Trigger | Response |
|---|---|---|
| Dispute reason textarea | Type | Character counter; enable submit at 10+ chars |
| Submit dispute | Click | POST dispute; show submitted status |
| Cancel | Click | Navigate back to Contributions |
| Peer: decision selector | Click | Toggle uphold/overturn; show grade selector if overturn |
| Peer: submit review | Click | POST review; navigate to My Kitchen |

---

## Screen Relationships

| Destination | Trigger | Data passed |
|---|---|---|
| Contributions | Cancel or post-submit | — |
| My Kitchen | Peer reviewer post-submit | — |
| Contributions | Notification link "Your dispute was resolved" | `dispute_id` → highlight relevant row |

---

## Excalidraw Design
Not yet designed. Run Pencil with spec from this file when ready.
