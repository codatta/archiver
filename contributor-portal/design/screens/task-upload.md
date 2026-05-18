# Screen: Task Upload (T1)

## Purpose
The data capture screen for T1 tasks. Contributors upload a robotics video (or ZIP of frames), configure a detection preset, and submit. Designed to be frictionless for a one-take video — most contributors will submit a single MP4. The preset configuration is the only non-trivial decision; defaults should cover 80% of cases.

## Phase
V1

## Users
- **New contributor** — first-time upload; needs guidance on what to upload and how to configure the preset
- **Returning contributor** — familiar with the flow; wants to upload fast with minimal friction

## Entry Points
- My Kitchen → T1 task card "Start Task" / "Resume"
- Deep link `/tasks/:instance_id` (direct link from notification)

## Exit Points
- Submit success → My Kitchen (with toast "Uploaded! Vision processing has started.")
- Cancel / back → My Kitchen (draft preserved if mid-upload)
- Sidebar nav items → other screens (with unsaved-changes warning)

## Devices
- Desktop (primary): 2-panel layout (upload left, configuration right)
- Tablet (≥768px): stacked (upload → configuration → submit)
- Mobile (<768px): Not supported. Show "Use a desktop browser to upload tasks." prompt.

---

## States

| State | Trigger | What renders |
|---|---|---|
| Loading | Fetching task config | Skeleton for upload panel + preset panel |
| Ready — no file | Default state | Upload drop zone + preset configuration (defaults applied) |
| File selected | User selects or drops a file | File preview panel (thumbnail + metadata) replaces drop zone; preset configuration remains |
| Uploading | Submit clicked | Progress bar with percentage; submit button disabled; cancel option |
| Upload complete | Upload finishes | Success illustration + "Processing started" message + "Back to My Kitchen" button |
| Validation error | File fails client-side checks | Inline error below drop zone (file too large, wrong format, too short, etc.) |
| Upload error | Network or server error | Error toast + retry button; file not lost |

---

## User Journey

1. Contributor opens task upload from My Kitchen.
2. Reads task brief: what kind of video to capture, length requirements, what the Vision Engine will extract.
3. Drops or selects their video file. Sees thumbnail preview + duration/size.
4. Reviews detection preset — in most cases, keeps the default ("All: Object + Pose + Optical Flow").
5. Adds optional clip notes (free text) for context.
6. Clicks "Submit". Sees upload progress bar.
7. On completion: returns to My Kitchen. Sees T2 processing indicator in Kitchen.

---

## Behavior

**On load:**
- Fetch task instance: `GET /v1/task-instances/:instance_id`
- Fetch task config (LS XML for T1) to extract requirements: accepted formats, min/max duration, file size limit
- Apply default detection preset from campaign config (`campaign.params.default_detection_preset`)

**File validation (client-side before upload):**
- Accepted formats: MP4, MOV, AVI, ZIP (of frames)
- Min duration: from campaign config (default 30s)
- Max duration: from campaign config (default 120s)
- Max file size: 2GB
- If ZIP: must contain ≥30 frames, common image formats

**Detection preset:**
- Preset controls which Vision Engine models run on the video in T2
- Options derived from campaign config; each preset is a named combination of detection modules:
  - Object Detection (YOLO): detects objects, bounding boxes
  - Human Pose (ViT/OpenPose): arm keypoints, body joints
  - Optical Flow: motion vectors for action segmentation
- Default preset is campaign-configurable; shown pre-selected on load
- Contributor can change preset if they know their video has specific characteristics

**Upload:**
- Resumable upload via Supabase Storage (TUS protocol)
- Progress reported in real-time via upload progress events
- On complete: `POST /v1/task-instances/:instance_id/submit` with `{ storage_path, detection_preset, notes }`
- Backend triggers T2 processing asynchronously

**Draft preservation:**
- If contributor navigates away mid-configuration (no file yet): no warning, nothing to lose
- If file is selected but not submitted: warn on navigation "You have an unsaved upload. Leave anyway?"
- In-progress uploads: cancel → file removed from storage

---

## Interactions

| Element | Trigger | Response |
|---|---|---|
| Drop zone | Drag and drop file | Validate file; show preview on success or error on failure |
| "Browse files" button | Click | Open OS file picker (accepts configured formats) |
| Detection preset selector | Change | Update active preset; show description of what will be detected |
| "Submit" button | Click | Validate → start upload → show progress |
| "Cancel upload" | Click during upload | Confirm dialog → cancel upload → return to Ready state |
| "Back to My Kitchen" button (post-success) | Click | Navigate to My Kitchen |
| Breadcrumb / back | Click (pre-submit) | If file selected: warn dialog; else navigate back |

No keyboard shortcuts on this screen.

---

## Upload Panel

- Drop zone: dashed border (`#9890A8`), centered icon + "Drag your video here" text + "Browse files" button
- On file selected:
  - Video thumbnail (first frame, if MP4/MOV) or generic file icon (ZIP)
  - File name + size + detected duration
  - "Remove" link to reset

## Configuration Panel

- **Detection preset selector** (radio group or segmented control):
  - Label: "Detection preset"
  - Each option: preset name + one-line description of what it detects
  - Active selection: border `#834DFB`, background `#F0EBFF`
- **Clip notes** (optional textarea):
  - Label: "Notes for reviewers" (optional)
  - Placeholder: "Describe anything unusual about this video..."
  - Max 500 characters
- **Task brief** (collapsible, open by default):
  - What the campaign needs in this video (from task config)
  - Accepted formats + duration range

## Submit Row

- "Submit" primary button (disabled until file selected and valid)
- Helper text: "Submitting starts automated processing. You'll be notified when annotation is ready."

---

## Screen Relationships

| Destination | Trigger | Data passed |
|---|---|---|
| My Kitchen | Submit success / post-success button | — |
| My Kitchen | Back / cancel (pre-submit) | — |

---

## Excalidraw Design
Not yet designed. Run Pencil with spec from this file when ready.
