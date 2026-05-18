# Contributor Kitchen — UI Design

Designed using the shared Humanbased design system from `developer-portal/packages/webapp/design_system.md`.
Label Studio annotation workspace patterns applied to T3 task UI.

## Excalidraw Checkpoints

| Screen | Description | Checkpoint ID |
|---|---|---|
| Screen 1 | Campaign Discovery | `8c65b2e5ec6b494887` |
| Screen 2 | Campaign Detail | `a24a121714b24d579e` |
| Screen 3 | Annotation Workspace (T3) | `3d4b4b1e5db140f9a9` |
| Screen 4 | Skills & Profile | `5fc61f139ed148dc94` |

To restore any screen in Excalidraw MCP, start elements array with:
`{"type":"restoreCheckpoint","id":"<checkpoint_id>"}`

---

## Design System Applied

Inherits directly from `developer-portal` design system. No divergence from shared tokens.

| Token | Value | Usage |
|---|---|---|
| `textPrimary` | `#1B1034` | All headings, borders, dark buttons |
| `textSecondary` | `#5C5470` | Body text, descriptions |
| `textMuted` | `#9890A8` | Meta, labels, placeholders |
| `accent` | `#834DFB` | Active nav, CTA buttons, active labels |
| `accentLight` | `#F0EBFF` | Active filter chips, skill tier badges |
| Font | DM Sans | All text |

**Contributor Kitchen only:** dark annotation workspace (`#111827` / `#1F2937`) for the T3 task screen — consistent with Label Studio dark canvas convention. All other screens remain on white canvas.

---

## Screen 1 — Campaign Discovery

**Shell:** Left sidebar (220px, `#1B1034`) + white content area. Sidebar carries logo, nav items, profile footer. Active nav item has purple left-bar indicator + light purple background.

**Top bar:** 56px, page title left, notification bell + avatar right. `border-b #E5E7EB`.

**Filters:** Horizontal pill row — frontier type + compensation type. Active pill: `bg #F0EBFF, border #834DFB`. Inactive: `bg transparent, border #9890A8`.

**Campaign cards:** 3-column grid, `rounded-xl`, `border-[1.5px] border-[#1B1034]`. Each card:
- Frontier tag (color-coded by domain) + compensation badge (right)
- Campaign title (20px semibold)
- Builder row: logo circle + org name
- Progress bar (purple fill on gray track) + "X / Y contributions"
- Meta: tasks / time estimate / rate
- Lock badge if credential required (red tint)
- Primary CTA: dark button ("View Campaign") or outline ("View + Qualify")

---

## Screen 2 — Campaign Detail

**Hero:** Full-width dark (`#1B1034`) header with campaign name, frontier tag, compensation badge, subtitle.

**Two-column layout:**
- Left (540px): Task DAG — T1→T2→T3→T4 as vertical pipeline. Each task card has colored left accent bar (T1=purple, T2=cyan, T3=purple active, T4=gray). T3 highlighted as "You are here" entry point.
- Right (400px): Three stacked cards:
  1. **Compensation card** — type badge + royalty breakdown (your share 60%, upstream 35%, platform 5%) + usage disclosure note
  2. **Builder credibility card** — org logo, name, verified badge, completed campaigns count, satisfaction score, link chips (LinkedIn, HuggingFace, GitHub)
  3. **Enroll card** — qualification status + primary enroll button

---

## Screen 3 — Annotation Workspace (T3 Task)

Label Studio-inspired layout. Dark theme throughout (`#111827` base).

**Top bar (48px, `#1B1034`):**
- Back breadcrumb, task label + filename, progress bar (clips done / total), Save + Submit buttons

**Left panel (200px):** Clip list with thumbnail previews. Active clip highlighted with purple border. Completed clips show green "Done" tag.

**Center canvas (650px wide):**
- Video player with bounding box overlay (purple `#834DFB` border) + keypoints (amber = left arm, green = right arm)
- Playback controls bar (56px): play button, scrubber with playhead
- **Timeline** (148px): three tracks — Actions (colored segment blocks by label), Cull state (keep / review), Pose confidence. White vertical cursor line at current time.

**Right panel (350px):**
- Selected segment info (time range, duration)
- Action label selector (color-coded buttons, active = teal)
- Language instruction textarea (dark input `#111827`)
- Task plan (ordered list textarea)
- Keypoints display (from Vision Engine pre-labels, green = detected)
- Quality signals (blur + person confidence progress bars)
- Keyboard shortcut reference at bottom
- "Next Clip" CTA button (purple)

---

## Screen 4 — Skills & Profile

**Profile card:** Avatar + name + email verification badge + reputation score (847/1000) with progress bar.

**Badges row:** 4 badge tiles — Annotator (milestone), Robotics Pro (campaign), ID Verified (KYC), Expert (locked).

**Skills table:** Each skill is a row with:
- Left accent bar (color = verification tier: purple=tutorial, green=credential, gray=unverified)
- Skill name + description
- Tier badge: `tutorial-passed` / `credential-verified` / `unverified`
- Action button: "View Training" / "View Credential" / "Start Training"

**Verification tiers** (per design system status badge colors):
| Tier | Color | Meaning |
|---|---|---|
| `unverified` | `#9890A8` gray | Self-declared |
| `tutorial-passed` | `#834DFB` purple | Quiz passed |
| `credential-verified` | `#22C55E` green | Document approved |
| `expert` | `#F59E0B` amber | AI interview passed |

**Credential submission form:**
- Skill selector + credential type selector (inputs: `rounded-none`, `border-[1.5px] border-[#1B1034]`)
- Upload drop zone (dashed border, accepts PDF/image)
- Info callout (amber tint): "Reviewed by platform AI within 24-48 hours. Borderline cases → human review."
- Submit button

---

## Widget Inventory

Reusable components designed across these screens:

| Widget | Used in | Notes |
|---|---|---|
| `CampaignCard` | S1 | Frontier tag, comp badge, progress, builder row, CTA |
| `TaskPipelineDAG` | S2 | T1-T4 vertical flow with accent bars and status |
| `CompensationBreakdown` | S2 | Type badge + share table + disclosure note |
| `BuilderCredibilityPanel` | S2 | Logo, verified badge, stats, link chips |
| `AnnotationCanvas` | S3 | Konva video + bbox + keypoints overlay |
| `TimelineTrack` | S3 | Multi-row timeline (actions, cull, pose) |
| `ActionLabelSelector` | S3 | Color-coded button grid from LS XML config |
| `SkillRow` | S4 | Tier badge, training/credential action |
| `CredentialUploadForm` | S4 | Drop zone + type selector + review callout |
| `ReputationMeter` | S4 | Score + progress bar |
| `BadgeTile` | S4 | Icon + label + locked state |
