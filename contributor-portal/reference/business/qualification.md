# Qualification Gating

> Campaign creators define who can contribute. Requirements can differ per task type within the same campaign. Contributors who don't fully qualify can still see the campaign — with a clear path to qualifying.

---

## Requirement Types

### Platform Requirements

| Requirement | Type | Example |
|---|---|---|
| Reputation score | Numeric threshold | ≥ 70 / 100 |
| Completed tasks | Numeric threshold | ≥ 10 tasks |
| Account age | Duration threshold | ≥ 30 days |
| Verification level | Enum | Email verified, ID verified |

### Domain Requirements

| Requirement | Type | Example |
|---|---|---|
| Domain experience | Boolean + evidence | Video recording experience |
| Language proficiency | Enum | English (native), Mandarin (fluent) |
| Geographic location | Region filter | US, EU, APAC |
| Equipment | Self-declared | Smartphone with 1080p+ video |
| Frontier specialization | Prior work in frontier | 20+ completed robotics tasks |

### Certification

| Requirement | Type | Example |
|---|---|---|
| Domain certification test | Pass/fail assessment | Pass a 10-question labeling test |
| Practice task set | Scored dry-run | Complete 5 sample tasks with ≥ 80% accuracy |

---

## Per-Task-Type Qualification

A single campaign can have different requirements for different task types:

```json
{
  "qualifications": {
    "supply": {
      "reputation_min": 50,
      "completed_tasks_min": 5,
      "domain_requirements": ["video_recording_experience"],
      "equipment": ["smartphone_1080p"]
    },
    "labeling": {
      "reputation_min": 70,
      "completed_tasks_min": 20,
      "domain_requirements": ["video_recording_experience", "annotation_experience"],
      "certification": "robotics_labeling_test_v1"
    },
    "validation": {
      "reputation_min": 85,
      "completed_tasks_min": 50,
      "domain_requirements": ["annotation_experience"],
      "certification": "robotics_validation_test_v1"
    }
  }
}
```

A contributor may qualify for supply tasks but not labeling — this is surfaced in the UI:

```
YOUR QUALIFICATIONS

Supply tasks:     ✓ You qualify (all 4 requirements met)
Labeling tasks:   ⚠ 1 requirement not met (needs: annotation experience)
Validation tasks: ✕ 2 requirements not met
```

---

## Pool Estimation

The platform estimates the available contributor pool based on qualification filters:

```typescript
interface PoolEstimate {
  total_pool: number;              // All active contributors
  qualified_pool: number;          // Contributors who meet all requirements
  qualified_pct: number;           // qualified / total
  estimated_delivery_weeks: number; // Based on qualified_pool × avg throughput
  warning?: string;                // If qualified_pool < 2× target volume
}
```

This is shown to campaign creators at build time (Step 4 of Campaign Builder) and is NOT shown to contributors.

---

## Qualification Check Display (Campaign Detail)

Real-time evaluation when a contributor views a campaign:

```
┌──────────────────────────────────────────────────────┐
│  ✅  Platform reputation ≥ 70                        │
│      Your score: 84                                  │
├──────────────────────────────────────────────────────┤
│  ✅  10+ completed tasks                              │
│      Your count: 142                                  │
├──────────────────────────────────────────────────────┤
│  ❌  Depth sensor equipment required                  │
│      You don't have this credential                   │
│      [How to qualify →]                               │
└──────────────────────────────────────────────────────┘
```

**Styling:**
- Met: `bg-green-50 border-l-4 border-green-400`
- Not met: `bg-red-50 border-l-4 border-red-400` + "[How to qualify →]" link

---

## "How to Qualify" Paths

Each unmet requirement links to a resolution:

| Requirement type | Resolution path |
|---|---|
| Reputation score too low | Link to reputation screen with improvement tips |
| Not enough completed tasks | Link to beginner-friendly campaigns |
| Missing domain experience | Link to qualification test |
| Missing equipment | Self-declaration form |
| Missing certification | Link to practice task set |
