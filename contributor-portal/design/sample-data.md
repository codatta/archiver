# Sample Campaigns, Tasks & Instances

> Grounded in real HuggingFace datasets. Used for UI design mocks and development fixtures.

---

## Campaign 1: Kitchen Manipulation

**Inspired by**: [nvidia/PhysicalAI-Robotics-Manipulation-Kitchen](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-Manipulation-Kitchen)

| Field | Value |
|---|---|
| ID | `camp-k1m` |
| Org | NVIDIA PhysicalAI (Open tier) |
| Frontier | Embodied AI / Robotics |
| Compensation | **Fixed** — per accepted instance |
| Status | Active — 672 / 1,000 instances |
| Time left | 34 days |

### Tasks

| Task | Type | Executor | Pay | Description |
|---|---|---|---|---|
| T1 | Supply | Human | $2.50 | Record 30-120s kitchen manipulation video (stacking, folding, pick-place) |
| T2 | Labeling | Agent | — | Vision Engine: YOLO object detection + OpenPose keypoints + optical flow |
| T3 | Labeling | Human | $1.50 | Review pre-labels, annotate action segments, add language instructions |
| T4 | Validation | Agent | — | Auto quality gate: blur, completeness, label consistency check |

### Sample Instances

| Instance ID | Task | Status | Stage | Chain ID | Pay |
|---|---|---|---|---|---|
| `#inst-4f2a` | T3 Lab | Accepted | ██████ complete | `0xa3b7..c4f1` | $1.50 |
| `#inst-8b1c` | T1 Sup | Accepted | ████░░ in validation | `0xb7e2..91d3` | $2.50 |
| `#inst-c3d9` | T1 Sup | In Review | ███░░░ in labeling | — | — |
| `#inst-1e7f` | T3 Lab | In Review | ██░░░░ agent pre-label | — | — |
| `#inst-a2b4` | T1 Sup | Rejected | ██░░░░ quality fail | — | — |

---

## Campaign 2: RoboMIND Trajectories

**Inspired by**: [x-humanoid-robomind/RoboMIND](https://huggingface.co/datasets/x-humanoid-robomind/RoboMIND) — 107K real-world trajectories, 479 tasks, 96 object classes

| Field | Value |
|---|---|
| ID | `camp-rmnd` |
| Org | X-Humanoid Lab (Shielded tier — "Verified AI Company") |
| Frontier | Embodied AI / Humanoid |
| Compensation | **Royalty** — revenue share on downstream model training |
| Status | Active — 23,400 / 107,000 instances |
| Time left | 186 days |

### Tasks

| Task | Type | Executor | Pay | Description |
|---|---|---|---|---|
| T1 | Supply | Human | royalty | Record humanoid manipulation demo: drawer open, object grasp, tool use |
| T2 | Labeling | Human | royalty | Classify task type (479 categories), tag object classes (96 types) |
| T3 | Validation | Human | royalty | Peer review: verify trajectory matches claimed task type |

### Sample Instances

| Instance ID | Task | Status | Stage | Chain ID | Pay |
|---|---|---|---|---|---|
| `#inst-d7e3` | T2 Lab | Accepted | ██████ | `0xf491..a2c7` | royalty |
| `#inst-f8a1` | T1 Sup | Accepted | █████░ | `0x8c3d..e5b2` | royalty |
| `#inst-2b9c` | T3 Val | Working | ████░░ | — | — |
| `#inst-6e4d` | T2 Lab | In Review | ███░░░ | — | — |

---

## Campaign 3: Egocentric Experience

**Inspired by**: [ropedia-ai/xperience-10m](https://huggingface.co/datasets/ropedia-ai/xperience-10m) — 10M experiences, 10K hours, 6 video streams + audio + depth + mocap

| Field | Value |
|---|---|
| ID | `camp-xp10` |
| Org | Ropedia AI (Open tier) |
| Frontier | Embodied AI / Egocentric Vision |
| Compensation | **Hybrid** — $1.00 base + royalty on model usage |
| Status | Active — 1,240,000 / 10,000,000 instances |
| Time left | 365 days |

### Tasks

| Task | Type | Executor | Pay | Description |
|---|---|---|---|---|
| T1 | Supply | Human | $1.00 + royalty | Wear headset, record 15-min daily activity (cooking, cleaning, crafting) |
| T2 | Labeling | Agent | — | Stereo depth estimation + hand mocap extraction + camera pose |
| T3 | Labeling | Human | $0.50 + royalty | Hierarchical language annotation: activity → action → sub-action |
| T4 | Labeling | Human | $0.75 + royalty | Temporal segmentation: mark boundaries between primitive skills |
| T5 | Validation | Human | $0.25 + royalty | Verify language descriptions match video, check segment boundaries |

### Sample Instances

| Instance ID | Task | Status | Stage | Chain ID | Pay |
|---|---|---|---|---|---|
| `#inst-9a2f` | T3 Lab | Accepted | ██████ | `0x2d8f..7b41` | $0.50 + royalty |
| `#inst-b3c8` | T4 Lab | Working | ████░░ | — | — |
| `#inst-e1d5` | T1 Sup | Accepted | ██████ | `0x6e9a..c3f8` | $1.00 + royalty |
| `#inst-7f6a` | T5 Val | In Review | █████░ | — | — |

---

## Campaign 4: Humanoid Motion Library

**Inspired by**: [bones-studio/seed](https://huggingface.co/datasets/bones-studio/seed) — 142K annotated human motion animations for humanoid robotics

| Field | Value |
|---|---|
| ID | `camp-bone` |
| Org | Bones Studio (Guarded tier — "Technology Company") |
| Frontier | Humanoid Robotics / Motion |
| Compensation | **Bounty** — $5,000 per 10K accepted animations |
| Status | Active — 89,400 / 142,220 instances |
| Time left | 62 days |

### Tasks

| Task | Type | Executor | Pay | Description |
|---|---|---|---|---|
| T1 | Supply | Human | bounty | Upload mocap recording (SOMA format), min 10s sequence |
| T2 | Labeling | Agent | — | Auto-retarget to Unitree G1 skeleton + extract skeletal metadata |
| T3 | Labeling | Human | bounty | Write natural language description ("person picks up box and walks to shelf") |
| T4 | Labeling | Human | bounty | Temporal segmentation: mark start/end of each primitive motion |
| T5 | Validation | Agent | — | Physics plausibility check on retargeted motion |

### Sample Instances

| Instance ID | Task | Status | Stage | Chain ID | Pay |
|---|---|---|---|---|---|
| `#inst-3c7b` | T3 Lab | Accepted | ██████ | `0xa1c4..d9e2` | bounty share |
| `#inst-5d9e` | T4 Lab | Accepted | ██████ | `0xb8f3..e7a1` | bounty share |
| `#inst-8a1f` | T1 Sup | In Review | ███░░░ | — | — |

---

## Campaign 5: VLA Community Collection

**Inspired by**: [HuggingFaceVLA/community_dataset_v1](https://huggingface.co/datasets/HuggingFaceVLA/community_dataset_v1) — 128 datasets from 55 contributors, vision-language-action learning

| Field | Value |
|---|---|
| ID | `camp-vla` |
| Org | HuggingFace VLA (Open tier) |
| Frontier | Foundation Models / VLA |
| Compensation | **Fixed** — per accepted instance |
| Status | Active — 312,000 / 970,000 instances |
| Time left | 240 days |

### Tasks

| Task | Type | Executor | Pay | Description |
|---|---|---|---|---|
| T1 | Supply | Human | $0.75 | Submit robot manipulation episode (any platform: Franka, UR5, xArm) |
| T2 | Labeling | Agent | — | Auto-extract: camera extrinsics, proprioception, action space normalization |
| T3 | Labeling | Human | $1.25 | Language instruction annotation: describe what the robot does in natural language |
| T4 | Validation | Human | $0.50 | Cross-platform consistency: verify action labels match across robot types |

### Sample Instances

| Instance ID | Task | Status | Stage | Chain ID | Pay |
|---|---|---|---|---|---|
| `#inst-c4e8` | T3 Lab | Accepted | ██████ | `0xd2f7..a8b3` | $1.25 |
| `#inst-a7b2` | T1 Sup | Accepted | █████░ | `0xe5c1..f4d9` | $0.75 |
| `#inst-f9d1` | T4 Val | Working | ████░░ | — | — |
| `#inst-b2e6` | T3 Lab | Rejected | ██░░░░ | — | — |

---

## Summary for UI Design

### Campaign Card Variety

| Campaign | Org Privacy | Compensation | Task Types | Scale |
|---|---|---|---|---|
| Kitchen Manipulation | Open | Fixed | Sup + Lab(A) + Lab(H) + Val(A) | 1K |
| RoboMIND Trajectories | Shielded | Royalty | Sup + Lab + Val | 107K |
| Egocentric Experience | Open | Hybrid | Sup + Lab(A) + Lab(H)×2 + Val | 10M |
| Humanoid Motion | Guarded | Bounty | Sup + Lab(A) + Lab(H)×2 + Val(A) | 142K |
| VLA Community | Open | Fixed | Sup + Lab(A) + Lab(H) + Val | 970K |

### Status Distribution for Table Mocks

| Status | Color | Count | Use in |
|---|---|---|---|
| ✓ Accepted | `#22C55E` green | ~60% | Table, earnings |
| ◐ In Review | `#F59E0B` amber | ~20% | Table, pending |
| ● Working | `#834DFB` purple | ~10% | Table, tasks |
| ✕ Rejected | `#EF4444` red | ~10% | Table, attention items |

### Media Types for Detail Popup

| Campaign | Primary Media | Popup Preview |
|---|---|---|
| Kitchen Manipulation | Video (MP4) | Video player + frame scrubber |
| RoboMIND Trajectories | Video + Sensor data | Video player + trajectory viz |
| Egocentric Experience | Multi-stream video + Audio | Video grid + audio waveform |
| Humanoid Motion | Motion capture (SOMA) | 3D skeleton viewer + timeline |
| VLA Community | Video + Proprioception | Video player + action chart |
