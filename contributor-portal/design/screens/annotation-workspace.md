# Screen: Annotation Workspace (T3)

## Purpose
The primary contribution surface. Contributors review Vision Engine pre-labels, cull unusable clips, annotate action segments with temporal labels and bounding boxes, add language instructions, and submit. Modeled after Label Studio's annotation UX with a dark canvas to reduce eye strain during extended sessions.

## Phase
V1

## Users
- **Active contributor on a T3 task** — has already enrolled and uploaded a video (T1 done, T2 done); now annotating

## Entry Points
- My Kitchen → T3 task card "Start Task" or "Resume"
- Deep link `/tasks/:instance_id` (from notification, direct link)

## Exit Points
- Submit (all clips annotated) → My Kitchen
- Save + exit (partial progress) → My Kitchen (progress preserved)
- Back breadcrumb → My Kitchen (with unsaved-changes warning if any unsaved changes)

## Devices
- **Desktop only** (min 1024px width). This screen is keyboard-driven and cannot function on touch devices.
- Tablet / Mobile: Show "Use a desktop browser (min 1024px) to annotate tasks."

---

## States

| State | Trigger | What renders |
|---|---|---|
| Loading | Fetching task + clip data | Dark skeleton (shimmer on dark bg `#111827`) |
| Active — clip selected | Default working state | Full 3-panel layout: clip list, canvas, annotation panel |
| Clip culled | Contributor marks clip as "Cull" | Canvas dims; shows "Clip marked for removal" + skip to next |
| Clip complete | All labels for a clip are saved | Green "Done" tag on clip in left panel; advance to next |
| All clips done | Last clip submitted | Submit button activates; summary overlay shows counts |
| Submit confirming | Submit clicked | Confirmation dialog: counts summary + confirm/cancel |
| Submitted | Confirm submit | Success overlay → navigate to My Kitchen |
| Error — load failure | Clips/frames fail to load | Error state with retry option |

---

## User Journey

1. Contributor opens annotation workspace from My Kitchen.
2. Sees dark-themed 3-panel layout: clip list (left), video canvas (center), annotation panel (right).
3. First clip loads automatically. Watches Vision Engine pre-labels (bboxes, keypoints) already rendered.
4. **Cull review:** decides if clip is usable. If blurry or invalid → marks "Cull" → skips to next clip.
5. **Temporal annotation:** plays video, identifies action segments. Draws timeline segments by dragging on Actions track.
6. Selects action label for each segment (e.g., "fold_box", "pick_place") using the action label selector buttons.
7. **Spatial review:** adjusts Vision Engine bboxes/keypoints if wrong (or confirms they're correct).
8. **Language annotation:** types natural language instruction for the clip ("fold the towel on the table").
9. **Task plan:** optionally adds ordered step list.
10. Clicks "Next Clip" — moves to next. Repeats for all clips.
11. When all clips done: clicks "Submit". Confirms in dialog. Returns to My Kitchen.

---

## Behavior

**On load:**
- Fetch task instance: `GET /v1/task-instances/:instance_id`
- Fetch clips: `GET /v1/task-instances/:instance_id/clips` (includes Vision Engine pre-labels per clip)
- Load first clip automatically; restore any saved annotation state for in-progress tasks
- Fetch task LS XML config to parse action labels, keypoint definitions, textarea prompts

**LS XML config parsing:**
- `<TimelineLabels>` → action label buttons with configured colors
- `<Rectangle>` → enable bbox editing mode
- `<KeyPointLabels>` → keypoint labels (left/right arm joints)
- `<TextArea name="language_instruction">` → instruction textarea placeholder
- `<TextArea name="task_plan">` → task plan textarea placeholder

**Auto-save:**
- Save annotation state for current clip every 30 seconds automatically
- Explicit save: "Save" button in top bar → `PUT /v1/clips/:clip_id/annotation`
- Saved state survives navigation away + return (restored on "Resume")

**Clip submission flow:**
- "Next Clip" → save current clip annotation → load next clip
- Last clip's "Next Clip" changes to "Done" → marks all clips saved → activates "Submit"
- Submit: `POST /v1/task-instances/:instance_id/submit` → triggers T4 validation

**Keyboard shortcuts:**
- `Space` — play/pause video
- `←` / `→` — step back/forward 1 frame
- `Shift+←` / `Shift+→` — step back/forward 10 frames
- `C` — mark clip as Cull
- `1–9` — select action label by position
- `N` — advance to next clip (same as "Next Clip")
- `S` — save current clip annotation

**Vision Engine pre-labels:**
- Bboxes rendered as purple `#834DFB` rectangles on video canvas
- Keypoints rendered per LS `<KeyPointLabels>` definition: amber = left arm joints, green = right arm joints
- Contributor can drag to adjust; corrections are stored alongside pre-labels in annotation payload
- Quality signals (blur score, person confidence) shown as progress bars in right panel — read-only

---

## Layout (dark theme: `#111827` base)

### Top bar (48px, `#1B1034`)
- Left: back breadcrumb "← My Kitchen", task label + filename
- Center: clip progress "3 / 12 clips"
- Right: "Save" button (secondary) + "Submit" button (primary, disabled until all done)

### Left panel (200px, `#1F2937`)
- Clip list with thumbnail previews (from Vision Engine frame extraction)
- Active clip: purple border (`#834DFB`)
- Completed clip: green "Done" tag
- Culled clip: gray "Culled" tag, strikethrough
- Scrollable, clips listed in order

### Center canvas (flexible, min 650px)
- Video player with Konva overlay for bbox/keypoint rendering
- Bboxes: purple rectangles, draggable corners
- Keypoints: colored dots per joint definition, draggable
- **Playback controls bar** (56px, `#374151`):
  - Play/pause button, current time / total duration
  - Scrubber with playhead (draggable)
- **Timeline** (148px, `#1F2937`):
  - Actions track: colored segment blocks, drag to create segments
  - Cull state track: Keep / Review toggles per clip
  - Pose confidence track: read-only confidence signal from Vision Engine
  - White vertical cursor line at current playhead position

### Right panel (350px, `#1F2937`)
- Selected segment info (time range, duration)
- **Action label selector**: color-coded buttons per `<TimelineLabels>` config; active = teal highlight
- **Language instruction** textarea (dark input, `#111827`; placeholder from XML config)
- **Task plan** textarea (dark input; placeholder from XML config)
- **Keypoints display**: joint list with detected/undetected status from Vision Engine
- **Quality signals**: blur score + person confidence — thin progress bars, read-only
- Keyboard shortcut reference (collapsible, at bottom)
- "Next Clip" CTA button (purple `#834DFB`, full-width)

---

## Interactions

| Element | Trigger | Response |
|---|---|---|
| Clip in left panel | Click | Load that clip in canvas; save current clip draft first |
| Play/pause button | Click / `Space` | Play or pause video |
| Scrubber | Drag | Seek to time position |
| Action timeline | Click+drag on Actions track | Create new segment; open label selector for it |
| Segment block | Click | Select segment; update right panel with segment info |
| Action label button | Click | Apply label to selected segment |
| Bbox corner handle | Drag | Resize bbox |
| Keypoint dot | Drag | Move keypoint position |
| "Mark as Cull" button | Click | Dim canvas; save cull state; offer "Skip to next" |
| "Save" button (top bar) | Click / `S` | Save current clip annotation to server |
| "Next Clip" button | Click / `N` | Save + advance to next clip |
| "Submit" button | Click | Open confirmation dialog |
| Submit confirm | Click | POST submit; navigate to My Kitchen |

---

## Screen Relationships

| Destination | Trigger | Data passed |
|---|---|---|
| My Kitchen | Submit success | — |
| My Kitchen | Save + exit | — |
| My Kitchen | Back breadcrumb (with warning if unsaved) | — |

---

## Excalidraw Design
Checkpoint: `3d4b4b1e5db140f9a9` (see `design/reference/contributor-kitchen.md`)
