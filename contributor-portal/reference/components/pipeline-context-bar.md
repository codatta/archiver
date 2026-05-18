# Component: Pipeline Context Bar

> A composable, configuration-driven horizontal strip showing one instance's journey through the campaign pipeline. The contributor's primary orientation device.

---

## Design Principles

1. **Composable** — assembled from discrete visual components; new types added without layout changes
2. **Per-instance** — shows the journey of one data point, not campaign aggregate
3. **Linear** — always a single fixed-height horizontal strip; never branches vertically
4. **Extensible** — campaign configuration drives rendering; bar doesn't need to know all stage types

---

## Anatomy

```
┌──────────────────────────────────────────────────────────────────────┐
│  ██████│██████│  🤖▓▓▓░░░░░░░░│░░░░░░░░░│░░░░░░│  ░░░░░░│░░░░░░  ◆│
│   (A)    (B)    (C)     (D)       (E)       (F)     (G)     (H)  (I)│
└──────────────────────────────────────────────────────────────────────┘
  ▾ supply — contributor_8f2a · Apr 10 · score 91                  (J)
```

| Label | Component | Description |
|---|---|---|
| (A) | Completed stage | Upstream stage, filled solid |
| (B) | Completed stage | Another upstream, can have any count |
| (C) | Agent sub-segment | Within current stage: agent's work (solid, distinct) |
| (D) | Human sub-segment | Within current stage: contributor's work (fills progressively) |
| (E) | Multi-label slot | Parallel labeler's slot |
| (F) | Consensus gate | Thin segment resolving multi-label agreement |
| (G) | Pending stage | Downstream, not yet reached |
| (H) | Pending stage | Another downstream |
| (I) | Milestone marker | Overlay indicator (royalty, checkpoint) |
| (J) | Context header | Static line below bar — upstream metadata |

---

## Component Catalog

### Stage

The atomic unit. One task in the pipeline.

```typescript
interface StageConfig {
  id: string;
  label: string;
  state: 'completed' | 'current' | 'pending';
  width_weight?: number;             // default 1, proportional
  sub_segments?: SubSegmentConfig[];
  multi_slots?: { count: number; consensus: ConsensusConfig; };
}
```

| State | Fill | Text color |
|---|---|---|
| `completed` | Solid black | White |
| `current` | Sub-segments fill progressively | — |
| `pending` | Light gray stroke | Gray |

### SubSegment

Internal phase within a stage (e.g., agent pre-labeling → human annotation).

```typescript
interface SubSegmentConfig {
  id: string;
  label: string;
  executor: 'agent' | 'human';
  style: 'solid' | 'gray' | 'hatched';
  width_weight: number;
}
```

| Style | Appearance | Use |
|---|---|---|
| `solid` (black) | Solid fill | Agent pre-labeling, completed human work |
| `gray` | Gray fill | Manual adjustment |
| `hatched` | Diagonal lines on white | Pure human annotation |

### MultiSlot

Horizontal subdivision for parallel independent labelers. Fixed bar height regardless of count.

```typescript
interface MultiSlotConfig {
  slot_index: number;
  total_slots: number;
  state: 'completed' | 'active' | 'pending';
  is_self: boolean;
}
```

Example — 3 labelers, you are L3:
```
  │L1████│L2████│L3░░░░│
  │ done  │ done  │←you  │
```

Min width per slot: 24px. At 10+ slots, collapse to thin ticks.

### ConsensusGate

Thin segment after multi-slots. Resolves when consensus condition passes.

```typescript
interface ConsensusConfig {
  condition: 'majority' | 'unanimous' | '2_of_3' | '3_of_5';
  fallback_stage_id?: string;  // injected on failure
}
```

| State | Appearance |
|---|---|
| `pending` | Thin, dashed border |
| `passed` | Thin, solid, ✓ |
| `failed` | Thin, amber, ⚠ |
| `adjudicating` | Thin, pulsing border, ↻ |

On failure: bar extends with dynamically injected adjudication stage.

### MilestoneMarker

Overlay indicator at a specific position. Zero width.

| Type | Icon | Use |
|---|---|---|
| `royalty` | ◆ | Royalty vesting point |
| `checkpoint` | ● | Custom milestone |

### VelocityHint

Tooltip on hover/tap of pending stages. Shows campaign-level average duration.

```
  ╭──────────────────────────╮
  │ ~3 hrs on this campaign   │
  ╰──────────┬───────────────╯
             │pending stage│
```

### ContextHeader

Static text below the bar. Shows upstream instance metadata.

| Task type | Header content |
|---|---|
| Supply | None |
| Supply-validate | Supply submission info |
| Labeling | Supply submission info |
| Label-validate | Supply info + labeling info |

Format: `▾ supply — contributor_8f2a · Apr 10 · score 91`

---

## Full Configuration Example

```json
{
  "stages": [
    { "id": "supply", "label": "Record Video", "width_weight": 2 },
    { "id": "supply-validate", "label": "Supply QA" },
    {
      "id": "label", "label": "Labeling", "width_weight": 2,
      "sub_segments": [
        { "id": "agent-prelabel", "label": "Pre-labeling by Agent", "executor": "agent", "style": "solid", "width_weight": 1 },
        { "id": "manual-adjust", "label": "Segmentation adjustment", "executor": "human", "style": "gray", "width_weight": 1 },
        { "id": "annotation", "label": "Task annotation", "executor": "human", "style": "hatched", "width_weight": 2 }
      ]
    },
    { "id": "label-validate", "label": "Label QA" }
  ],
  "milestones": [
    { "type": "royalty", "position": "after:label-validate", "label": "Royalty vests here" }
  ]
}
```

---

## State Matrix

**Supply contributor:**
```
  │░░░░░░░░░░░░░░░░░░│  sup-val  │  label  │  lbl-val◆│
```

**Labeling contributor (with agent pre-label):**
```
  │supply████│sup-val██│🤖▓▓▓│░░░░│////░░│  lbl-val◆│
```

**Multi-label (3 labelers, you are L2):**
```
  │supply████│sup-val██│L1██│L2░░│L3  │┊┊│  lbl-val◆│
```

**Consensus failed:**
```
  │supply██│sv██│L1██│L2██│L3██│⚠│adjudication│lbl-val◆│
```

---

## Interaction Rules

| Target | Desktop | Mobile | Effect |
|---|---|---|---|
| Upstream stage | Hover | Tap | Highlight segment + pulse context header |
| Downstream stage | Hover | Tap | VelocityHint tooltip (auto-dismiss 3s) |
| Milestone marker | Hover | Tap | Label tooltip |
| Multi-slot (completed) | Click | Tap | Show labeler info in context header |
| Current segment | None | None | No interaction — fills automatically |

---

## Sizing

| Viewport | Bar height | Context header |
|---|---|---|
| Desktop (≥1024px) | 32px | Full text, 2 lines max |
| Tablet (768–1023px) | 28px | Full text, 2 lines |
| Mobile (<768px) | 24px | Abbreviated, 1 line |

---

## Compact Variant (for My Tasks / Earnings)

16px height, no labels, no context header. Status shown as right-aligned text.

```
  #312  supply██│sv██│label▒▒│lv  ◆   in labeling
```

---

## Post-Submission Transition

1. Current segment fills solid (200ms ease-in)
2. Hold 400ms — contributor sees "done" state
3. Crossfade (150ms) to next instance's bar
4. If no more instances: muted bar + empty queue message
