# Task Types

> Every task in a campaign belongs to one of three types. Task type determines the contributor's experience: what they see, what they do, and how their submission is evaluated.

---

## The Three Types

### Supply

The contributor **generates data from scratch**. No pre-existing instance is needed.

| Attribute | Value |
|---|---|
| Instance required? | No — the submission IS the instance |
| Instance source | N/A |
| Output | New instance (enters the pipeline) |
| UI pattern | Blank canvas: recorder, upload zone, text editor, structured form |
| Executor | Human or Agent |
| Examples | Record a video, write text, photograph an object, fill a structured form |

### Labeling

The contributor **annotates an existing instance**. Cannot start without an input instance.

| Attribute | Value |
|---|---|
| Instance required? | Yes |
| Instance source | Campaign-creator upload OR prior task output |
| Output | Annotated instance (annotations attached) |
| UI pattern | Instance renderer + annotation overlay (Label Studio XML config) |
| Executor | Human or Agent |
| Examples | Draw bounding boxes, classify text, tag entities, transcribe audio, rank outputs |

### Validation

The contributor **reviews a labeled instance**. Input is always a labeled instance from a prior task.

| Attribute | Value |
|---|---|
| Instance required? | Yes — a labeled instance |
| Instance source | Always prior task output |
| Output | Quality verdict (accept / reject / flag), optionally amended annotations |
| UI pattern | Instance renderer + annotation viewer + verdict controls |
| Executor | Human or Agent |
| Examples | Approve/reject annotations, rate quality, resolve disagreements, spot-check gold standards |

---

## Instance Dependency Matrix

| Task Type | Instance required? | Instance source |
|---|---|---|
| Supply | No | N/A |
| Labeling | Yes | Campaign-creator upload OR prior task output |
| Validation | Yes | Always prior task output |

---

## DAG Rules

Valid edges in the campaign task pipeline:

| From → To | Valid? | Notes |
|---|---|---|
| Supply → Labeling | Yes | Supply output becomes labeling input |
| Labeling → Validation | Yes | Labeled instance passes to validator |
| Supply → Validation | No | Cannot validate un-labeled content |
| Anything → Supply | No | Supply tasks don't consume instances |
| Labeling → Labeling | Yes | Multi-pass annotation (e.g., first bbox, then classification) |
| Validation → Labeling | Yes | Failed validation routes back for re-labeling |

---

## Executor Is Orthogonal

`executor: human | agent` is independent of task type.

| Combination | Use case |
|---|---|
| Agent + Supply | Synthetic data generation |
| Agent + Labeling | Pre-labeling before human review |
| Agent + Validation | Automated QA / gold-standard scoring |
| Human + Supply | Original data from human experience |
| Human + Labeling | Ground-truth annotation |
| Human + Validation | Final adjudication |

---

## Sub-segments Within a Task

A task can have internal phases (sub-segments). Common pattern for labeling tasks:

| Sub-segment | Executor | Visual style | Description |
|---|---|---|---|
| Pre-labeling by Agent | Agent | Solid black | Agent runs first, produces initial annotations |
| Segmentation manual-adjustment | Human | Solid gray | Human refines agent output |
| Task annotation | Human | Hatched (diagonal lines) | Human annotates from scratch |

Sub-segments are defined in the campaign configuration and rendered in the pipeline context bar.

---

## Data Model

```typescript
type TaskType = 'supply' | 'labeling' | 'validation';
type Executor = 'human' | 'agent';

interface TaskDefinition {
  id: string;
  name: string;
  type: TaskType;
  executor: Executor;
  instructions: string;               // Markdown
  instance_source?: 'campaign_upload' | 'prior_task';
  depends_on?: string[];              // IDs of upstream tasks
  sub_segments?: SubSegment[];
  quality_gate: QualityGate;
}

interface SubSegment {
  id: string;
  label: string;
  executor: Executor;
  style: 'solid' | 'gray' | 'hatched';
  width_weight: number;
}

interface QualityGate {
  acceptance_threshold: number;       // 0.70–0.95
  review_method: 'manual' | 'agent_auto' | 'iaa_consensus';
  gold_standard_pct?: number;         // 0–20%
}
```
