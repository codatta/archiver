# Screen: Task Workspace

> **Route:** `/contribute/campaigns/[id]/tasks/[taskId]`
> **Entry:** "Accept & Start Working" from campaign detail, or "Continue Working" from My Tasks
> **Purpose:** Where contributors do the actual work. Renders the pipeline context bar, upstream context, and the annotation canvas for the current instance.

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Campaign Name                    [Campaign: Nvidia HK Video]  │
│                                                                  │
│  ┌─ Pipeline Context Bar ────────────────────────────────────┐   │
│  │  supply ████│ sup-val ██ │ 🤖▓▓▓░░░░░░░░│  lbl-val  ◆   │   │
│  └────────────────────────────────────────────────────────────┘   │
│  ▾ supply — contributor_8f2a · Apr 10 · score 91                 │
│                                                                  │
│  ┌─ Task Header ─────────────────────────────────────────────┐   │
│  │  🏷 Labeling · Task annotation         12 / 30 completed  │   │
│  │  Instance #247                     [$18.00 earned today]   │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─ Annotation Canvas ───────────────────────────────────────┐   │
│  │                                                            │   │
│  │          (annotation UI rendered here)                     │   │
│  │          (Label Studio iframe / native renderer)           │   │
│  │                                                            │   │
│  │                                                            │   │
│  │                                                            │   │
│  │                                                            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─ Action Bar ──────────────────────────────────────────────┐   │
│  │  [Skip]         [Save Draft]             [Submit ⏎]        │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Context Bar

Rendered at the top. Always visible. Per-instance. See [components/pipeline-context-bar.md](../components/pipeline-context-bar.md) for full spec.

The bar adapts to the current task type:

| Task type | Bar appearance |
|---|---|
| Supply | Current segment fills, all downstream pending |
| Labeling | Upstream filled, current segment has sub-segments (agent + human), downstream pending |
| Validation | All upstream filled, current segment is the last (or second-to-last) |

---

## Task Header

Always visible. Shows the contributor's orientation info.

```
  🏷 Labeling · Task annotation         12 / 30 completed
  Instance #247                     [$18.00 earned today]
```

| Element | Content |
|---|---|
| Task type badge | 📤 / 🏷 / ✅ + label |
| Sub-segment name | Current sub-segment within the task (e.g., "Task annotation") |
| Progress counter | Instances completed / total available this session |
| Instance ID | Current instance identifier |
| Running earnings | Today's earnings from this campaign (accumulates during session) |

**Styling:** `bg-gray-50 border-b border-gray-200 px-6 py-3`

---

## Context Header (below pipeline bar)

Static line showing upstream instance metadata. Rendered by the pipeline context bar component.

**Supply task:** No context header (you're creating the instance).

**Labeling task:**
```
  ▾ supply — contributor_8f2a · Apr 10 · score 91
```

**Validation task:**
```
  ▾ supply — contributor_8f2a · Apr 10 · score 91
  ▾ label  — contributor_3c9b · Apr 13 · 24 annotations
```

---

## Annotation Canvas

The main work area. Renders differently per task type:

### Supply

Blank canvas. Content depends on campaign configuration:
- **Video recording:** Camera / upload UI
- **Text generation:** Text editor with character count
- **Image capture:** Camera / file upload with requirements overlay
- **Structured data:** Form fields defined by campaign schema

### Labeling

Instance renderer + annotation overlay. Powered by the annotation pipeline runtime:
- The instance (image, video, text, audio) is displayed read-only
- Annotation tools overlay based on the Label Studio XML config
- Agent pre-labeling may be pre-filled (contributor adjusts / adds)

### Validation

Instance renderer + existing annotations + verdict controls:
- The instance is displayed read-only
- Existing annotations from the labeler are shown
- Gold standard comparison (if available) is shown alongside
- Verdict buttons: Accept / Reject / Flag for review
- Rejection requires selecting a reason from the rubric

---

## Action Bar

Sticky bottom bar with task actions.

| Button | When shown | Behavior |
|---|---|---|
| **Skip** | Always (if more instances available) | Skips this instance, loads next. No penalty. Limited to 10% of session. |
| **Save Draft** | Supply and Labeling tasks | Saves work-in-progress, does not submit |
| **Submit** | Always | Submits current work for quality review |

**Keyboard shortcuts:**
- `Enter` / `Cmd+Enter` — Submit
- `Tab` — Next annotation field
- `Esc` — Skip (with confirmation if work in progress)

**Styling:**
- Skip: `text-gray-500 text-sm`
- Save Draft: `border border-gray-300 text-gray-700 px-4 py-2 rounded-md`
- Submit: `bg-black text-white px-6 py-2 rounded-md`

---

## Post-Submission Transition

1. Current segment fills solid (200ms)
2. Brief "Submitted ✓" toast (400ms)
3. Crossfade to next instance:
   - Pipeline bar resets for new instance
   - Context header updates with new upstream info
   - Annotation canvas clears / loads new content
4. If no more instances: "No more instances available. [Notify me] or [Browse campaigns]"

---

## Session Quota

When the contributor hits the campaign's per-session cap:

```
┌──────────────────────────────────────────────────────────────┐
│  You've reached today's cap (20/20)                          │
│                                                              │
│  Your submissions are in review. Come back tomorrow.          │
│                                                              │
│  Today's session: 20 submitted · $50.00 est. earnings        │
│                                                              │
│  [Browse Other Campaigns]        [Set Reminder for Tomorrow]  │
└──────────────────────────────────────────────────────────────┘
```

---

## Queue Thin / Empty States

### Thin queue (< 5 remaining)

Yellow banner above the annotation canvas:

```
  ⚠ 3 instances remaining. Supply queue is building.
  New instances typically arrive every ~2 hours.
  [Notify me when 10+ ready]
```

### Empty queue (0 remaining)

Replaces the annotation canvas:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  No instances available right now                            │
│                                                              │
│  This campaign's supply queue is building.                   │
│  Labeling tasks will appear as supply is accepted.           │
│                                                              │
│  [Notify me when queue refills]    [Browse other campaigns]  │
│                                                              │
│  Your session so far: 12 submitted · $18.00 est. earnings    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Instructions Panel

A collapsible panel on first entry to any campaign's workspace.

**First visit:** Expanded by default. Must scroll through to enable Submit button.

**Subsequent visits:** Collapsed. Accessible via `[?]` icon in the task header.

```
┌─ Instructions ─────────────────────────────────────── [✕] ──┐
│                                                              │
│  Record a 30-120 second video of yourself performing a       │
│  household activity. Requirements:                           │
│  • Film in a well-lit indoor space                           │
│  • Keep hands clearly visible throughout                     │
│  • Include at least one object manipulation                  │
│                                                              │
│  ┌─ Sample Submissions ─────────────────────────────────┐    │
│  │  ▶ Sample 1 (✅ Accepted) — good hand visibility      │    │
│  │  ▶ Sample 2 (❌ Rejected) — hands obscured 0:12-0:18  │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Validation-Specific Controls

When the task type is Validation, the action bar changes:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  [Gold Standard]     [Accept ✓]  [Reject ✕]  [Flag 🚩]      │
│                                                              │
│  Rejection reason (required when rejecting):                 │
│  [Select from rubric ▾]                                      │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Optional note for the labeler...                    │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- **Gold Standard:** Opens a side panel showing the reference annotation for comparison
- **Accept:** Passes the instance downstream
- **Reject:** Requires rubric reason + optional note. Routes back to labeling.
- **Flag:** Escalates to adjudication queue
