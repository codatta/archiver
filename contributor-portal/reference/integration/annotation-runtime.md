# Integration: Annotation Runtime

> How the contributor portal consumes the annotation pipeline — the shared module that defines annotation schemas, renders annotation UIs, and captures responses.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Contributor Portal (this repo)                              │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Task Workspace screen                               │    │
│  │                                                      │    │
│  │  ┌─ Pipeline Context Bar ───────────────────────┐    │    │
│  │  │  (rendered by portal)                        │    │    │
│  │  └──────────────────────────────────────────────┘    │    │
│  │                                                      │    │
│  │  ┌─ Annotation Canvas ──────────────────────────┐    │    │
│  │  │  (rendered by annotation runtime)            │    │    │
│  │  │  iframe / embedded component                 │    │    │
│  │  └──────────────────────────────────────────────┘    │    │
│  │                                                      │    │
│  │  ┌─ Action Bar ─────────────────────────────────┐    │    │
│  │  │  (rendered by portal)                        │    │    │
│  │  └──────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Communication: postMessage API                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │
         │  HTTP / postMessage
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Annotation Pipeline (separate repo)                         │
│  humanbased/annotation-pipeline                              │
│                                                              │
│  Provides:                                                   │
│  • XML config parser + validator                             │
│  • Annotation renderer (Label Studio playground / custom)    │
│  • ML Backend protocol (pre-labeling by agent)               │
│  • Response schema (annotations → structured data)           │
│  • Template library (80+ annotation UIs)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## What the Portal Controls

| Responsibility | Owner |
|---|---|
| Pipeline context bar | Portal |
| Task header (type badge, progress, earnings) | Portal |
| Context header (upstream metadata) | Portal |
| Instance fetching and routing | Portal |
| Action bar (submit, skip, save draft) | Portal |
| Qualification gating | Portal |
| Compensation display | Portal |

## What the Annotation Runtime Controls

| Responsibility | Owner |
|---|---|
| Annotation canvas rendering | Runtime |
| XML config interpretation | Runtime |
| Annotation tool interactions (draw, select, label) | Runtime |
| Agent pre-labeling (ML Backend protocol) | Runtime |
| Response serialization (annotations → JSON) | Runtime |
| Template library | Runtime |

---

## Communication Protocol

### Portal → Runtime

| Message | Payload | When |
|---|---|---|
| `load_task` | `{ xml_config, instance_data, suggestions?, mode }` | New instance loaded |
| `set_mode` | `{ mode: 'annotate' \| 'review' \| 'readonly' }` | Task type changes rendering mode |
| `request_response` | `{}` | User clicks Submit — portal asks runtime for annotation data |

### Runtime → Portal

| Message | Payload | When |
|---|---|---|
| `ready` | `{ version }` | Runtime loaded and ready |
| `response` | `{ annotations, metadata }` | In response to `request_response` |
| `dirty` | `{ has_changes: boolean }` | User made/undid changes (for save draft) |
| `error` | `{ code, message }` | Rendering or validation failure |

---

## Rendering Modes

| Mode | Task type | Behavior |
|---|---|---|
| `annotate` | Supply, Labeling | Full annotation tools enabled; contributor creates/modifies annotations |
| `review` | Validation | Annotations shown read-only; verdict controls shown by portal |
| `readonly` | Preview (campaign detail) | Everything read-only; no tools, no submission |

---

## Instance Data Shape

The portal fetches instance data from the API and passes it to the runtime:

```typescript
interface InstancePayload {
  id: string;
  data: Record<string, any>;           // Instance fields (image URL, text, video URL, etc.)
  suggestions?: Annotation[];           // Agent pre-labeling results
  previous_annotations?: Annotation[];  // For validation: labeler's annotations
  gold_standard?: Annotation[];         // For validation: reference annotations
}
```

---

## Template Library

The annotation runtime ships ~80 pre-built templates covering:

| Category | Examples |
|---|---|
| Image | Bounding box, polygon, keypoints, brush/segmentation, classification |
| Video | Timeline annotation, video rectangles |
| Audio | Waveform labeling, timeline labels |
| Text | Classification, NER/spans, generation, ranking |
| Multi-modal | Pairwise comparison (RLHF), chat rating, taxonomy |

Templates are selected during campaign creation (Step 3) and stored as XML config. The contributor portal does not need to know the template vocabulary — it passes the XML config to the runtime, which handles rendering.
