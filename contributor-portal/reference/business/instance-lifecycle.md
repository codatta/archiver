# Instance Lifecycle

> An instance is one data point traversing the campaign's task pipeline. This doc defines the states an instance passes through, the transitions between them, and the multi-label consensus model.

---

## The Complete Sequence

A campaign defines a pipeline. The canonical full sequence is:

```
supply ──▶ [supply-validate] ──▶ label ──▶ label-validate
```

Brackets indicate optional stages. Not all campaigns include every stage. The pipeline configuration drives what stages exist.

One campaign = many instances, each traversing this pipeline independently.

---

## Instance States

```
                           ┌──────────────────────────────────────┐
                           │          Per-Instance States          │
                           └──────────────────────────────────────┘

  created ──▶ supply_pending ──▶ supply_submitted ──▶ supply_accepted
                                       │                     │
                                       ▼                     ▼
                              supply_rejected       [supply_validate_pending]
                                                            │
                                                            ▼
                                                   [supply_validate_passed]
                                                            │
                                                            ▼
                                                   label_pending ──▶ label_submitted
                                                                          │
                                                           ┌──────────────┤
                                                           ▼              ▼
                                                   label_rejected   label_accepted
                                                                          │
                                                                          ▼
                                                               label_validate_pending
                                                                          │
                                                           ┌──────────────┤
                                                           ▼              ▼
                                                   label_val_rejected  label_val_passed
                                                                          │
                                                                          ▼
                                                                     completed ──▶ royalty_eligible
```

---

## State Definitions

| State | Description | Who acts next |
|---|---|---|
| `created` | Instance record exists; no work started | System assigns to supply contributor |
| `supply_pending` | Assigned to a supply contributor; awaiting submission | Supply contributor |
| `supply_submitted` | Contributor submitted; awaiting review | Quality gate (agent or human) |
| `supply_accepted` | Supply passed quality gate | System routes to next stage |
| `supply_rejected` | Supply failed quality gate | Contributor sees rejection reason |
| `supply_validate_pending` | Queued for supply validation | Validation contributor |
| `supply_validate_passed` | Supply validation approved | System routes to labeling |
| `label_pending` | Queued for labeling | Labeling contributor(s) |
| `label_submitted` | Labels submitted; awaiting validation | Quality gate or consensus |
| `label_accepted` | Labels passed quality gate / consensus | System routes to label-validate |
| `label_rejected` | Labels failed; may route back for re-labeling | Labeling contributor or adjudicator |
| `label_validate_pending` | Queued for final validation | Validation contributor |
| `label_val_passed` | All stages complete | System marks complete |
| `label_val_rejected` | Final validation failed | Routes to re-labeling or discard |
| `completed` | All pipeline stages passed | Data enters the marketplace |
| `royalty_eligible` | Completed + used by org downstream | Royalty payments triggered |

---

## Multi-Label Consensus

A labeling stage can require **multiple independent labelers** working on the same instance. The consensus gate determines the outcome.

### Configuration

```typescript
interface MultiLabelConfig {
  count: number;                      // 2, 3, or 5 typically
  consensus: {
    condition: 'majority' | 'unanimous' | '2_of_3' | '3_of_5';
    fallback: 'adjudication' | 'discard' | 're_label';
  };
}
```

### Flow

```
instance arrives at labeling stage
         │
         ▼
  ┌─── slot 1 (contributor A) ───┐
  │    slot 2 (contributor B)    │── all slots complete ──▶ consensus check
  │    slot 3 (contributor C)    │
  └──────────────────────────────┘
                                            │
                              ┌─────────────┴─────────────┐
                              ▼                           ▼
                       consensus passed              consensus failed
                              │                           │
                              ▼                           ▼
                     label_accepted              fallback action
                                                 (adjudicate / discard / re-label)
```

### Slot States

Each slot tracks independently:

| Slot state | Meaning |
|---|---|
| `pending` | Not yet assigned to a contributor |
| `assigned` | A contributor has been assigned |
| `submitted` | Contributor submitted their labels |
| `completed` | Slot finished (labels are final for this contributor) |

The consensus gate evaluates only after ALL slots reach `completed`.

### Adjudication

When consensus fails and the fallback is `adjudication`:
1. A new stage is dynamically injected into the instance's pipeline
2. An adjudicator (human or agent) reviews all label sets
3. The adjudicator produces a resolved label set
4. The instance proceeds to label-validate with the resolved labels

---

## Instance in the Context Bar

The pipeline context bar renders per-instance state. See [components/pipeline-context-bar.md](../components/pipeline-context-bar.md) for the visual spec. The bar shows:

- Completed stages (solid fill, left side)
- Current stage (filling progressively)
- Multi-label slots (subdivisions within a stage)
- Consensus gate (thin segment after multi-label slots)
- Pending stages (gray, right side)
- Milestone markers (royalty vesting point)

---

## Rejection and Re-entry

When an instance is rejected at any stage:

| Rejection point | Default behavior | Contributor sees |
|---|---|---|
| Supply quality gate | Instance discarded; contributor sees rejection reason | "Rejected: [specific reason]" |
| Supply-validate | Routes back to supply contributor for revision | "Revision requested: [feedback]" |
| Label quality gate | Routes back to labeling queue | "Re-label: [feedback]" |
| Label-validate | Routes back to labeling with validator's notes | "Revision: [validator notes]" |

Rejected instances retain their full history — each attempt is recorded for audit and reputation scoring.
