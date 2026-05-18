# contributor-portal — Project Instructions

> Project-specific guidance for Claude Code. Global preferences live in `~/CLAUDE.md`.

## Project Overview

- **What it is:** Supply-side web portal for data contributors within the Humanbased campaign framework. Campaign configuration uses **Label Studio XML** as the canonical annotation schema. Vision processing agents integrate via the **Label Studio ML Backend protocol** (`/predict`, `/setup`, `/webhook`). All data lives in the **shared Supabase instance** (`uxafdddzhgdhsabkwmgw`) alongside the developer portal.
- **Primary users:** Data contributors (human), AI agents (ML backend services), developers who configure campaigns via the developer portal.
- **Core problem it solves:** End-to-end contribution flow — from raw data capture through agentic processing to annotated, quality-gated output — with lineage tracking suitable for future on-chain attribution.

## prd.md — Source of Truth

`prd.md` is the **canonical record for everything about this product** — what to build, why, how, and what was built. No feature exists until it is in `prd.md`.

### What prd.md governs

- **Capability scope** — V1/V2/V3/LT items with acceptance criteria and non-goals
- **Architecture decisions** — non-negotiable choices that every implementation must follow
- **Data model and migrations** — table schemas, constraints, RLS policies
- **Build plan** — solution approach recorded before implementation begins
- **History** — completed items with commit hashes; decisions that were changed and why

### Default behaviors (always enforce)

1. **Before writing any code:** Move the build queue item to `### 🧪 In Progress`. Add a "Solution approach" sub-bullet under the item describing the technical plan. Only then begin implementation.
2. **If the approach changes mid-implementation:** Update prd.md first. Never let code diverge silently from the recorded plan.
3. **After completing a feature:** Mark the item `✅ Done` with commit hash. Add any follow-on bugs or discovered work to `### 🧊 Backlog / Ideas`.
4. **Architecture decisions:** Any non-trivial architectural choice goes into the `## Architecture` section of prd.md before it is implemented. If it conflicts with an existing decision, stop and discuss.
5. **Features not in prd.md:** If the user asks for something not yet in prd.md, add it to the Build Queue and confirm the entry before starting. Never invent and implement in one step.

### What does NOT go in prd.md

UI/UX screen-level detail (interactions, states, device behavior) lives in `design/screens/<screen>.md`. Pencil design source lives in `design/source/`. Exported PNGs live in `design/exports/`. prd.md references these files but does not duplicate their content.

---

## Reference Implementations

Three existing repos serve as **context and logic reference** (not code to port). We rewrite from scratch following the architecture decisions from the annotation-pipeline spec.

| Repo | What to learn from it | What NOT to carry forward |
|---|---|---|
| `codatta/labeling-website` | Annotation UX flow (cull → slice → annotate), FramePlayer rendering, detection preset UX, keyboard-driven review patterns | localStorage state, hardcoded API URLs, monolithic 1400-line components, Vite SPA architecture |
| `codatta/labeling-api` | Vision Engine communication protocol, frame organization logic, export format, job lifecycle | In-memory state (no DB!), single-file architecture, no campaign/lineage concept |
| `codatta/labeling-vision-engine` | Processing pipeline (YOLO/Pose/optical flow), three-class cascade, ROS bag parsing, action segmentation | Nothing — it stays as an external service, wrapped in an ML Backend adapter |

## Architecture Decisions (from annotation-pipeline spec)

These are non-negotiable. Every implementation choice follows from these research conclusions:

### 1. Label Studio XML Config = Campaign Annotation Schema

Per annotation-pipeline spec §4.1: the XML Labeling Config DSL is the canonical way to define what contributors see and capture. Stored as `campaigns.annotation_config` in Supabase. The template library from Label Studio is seed data. Every campaign task has an XML config that defines its annotation UI.

```xml
<!-- Example: Embodiment-X robotics annotation config for T3 (human annotation task) -->
<View>
  <Header value="Embodiment-X: Robotics Action Annotation"/>
  <Video name="vid" value="$video_url"/>
  <TimelineLabels name="action" toName="vid">
    <Label value="fold_box" background="#FF6B6B"/>
    <Label value="fold_textile" background="#4ECDC4"/>
    <Label value="packing" background="#45B7D1"/>
    <Label value="pick_place" background="#96CEB4"/>
    <Label value="other_valid" background="#FFEAA7"/>
  </TimelineLabels>
  <Rectangle name="bbox" toName="vid" strokeWidth="2"/>
  <KeyPointLabels name="arm_kp" toName="vid">
    <Label value="left_shoulder"/><Label value="left_elbow"/><Label value="left_wrist"/>
    <Label value="right_shoulder"/><Label value="right_elbow"/><Label value="right_wrist"/>
  </KeyPointLabels>
  <TextArea name="language_instruction" toName="vid"
            placeholder="Describe what the person is doing..." rows="2"/>
  <TextArea name="task_plan" toName="vid"
            placeholder="High-level steps: 1) pick up towel 2) fold 3) place" rows="3"/>
</View>
```

### 2. ML Backend Protocol = Agent Integration Standard

Per annotation-pipeline spec §4.1 item 2: the `label-studio-ml-backend` HTTP protocol is how all agents (including our Vision Engine) integrate. This makes every LS-compatible model (SAM2, YOLO, GroundingDINO, LLM agents, Adala) drop-in compatible.

**Protocol surface:**

```
POST /predict     — given task data, return predictions (regions, labels, scores)
POST /setup       — initialize model with project config
POST /webhook     — receive lifecycle notifications
GET  /health      — readiness check
```

**Vision Engine ML Backend Adapter:**

The existing `labeling-vision-engine` (GPU server) does NOT speak this protocol natively. We write a thin adapter service that:
1. Accepts `/predict` requests with video/image input in LS format
2. Translates to Vision Engine native API (submit + callback)
3. Converts Vision Engine output (clips, segments, bboxes, keypoints) to LS prediction format (regions with labels)
4. Returns LS-compatible response

This adapter is the **only** code that knows about Vision Engine internals. Everything else in the system talks to it via the standard ML Backend protocol.

```python
# Adapter translates between LS ML Backend protocol and Vision Engine native API
class VisionEngineMLBackend:
    """
    LS ML Backend adapter wrapping labeling-vision-engine.
    Accepts: LS /predict request (task data with video URL)
    Returns: LS prediction response (regions: bboxes, keypoints, timeline labels)
    """
    vision_engine_url: str  # http://47.84.74.124:8001

    async def predict(self, tasks: list[dict], **kwargs) -> list[dict]:
        # 1. Extract video/image source from LS task format
        # 2. Submit to Vision Engine native API
        # 3. Poll/await callback for processing results
        # 4. Convert clips/segments/bboxes to LS region format
        # 5. Return LS-compatible predictions

    async def setup(self, project: dict) -> dict:
        # Validate Vision Engine is available, models loaded

    def health(self) -> dict:
        # Proxy to Vision Engine /health
```

### 3. Shared Supabase Instance

Both portals share a single Supabase project (`uxafdddzhgdhsabkwmgw`). PostgreSQL scales horizontally. One database, clear schema boundaries.

**Existing schemas (developer-portal):**
- `public` — 19 demand-side tables: organizations, users, api_keys, subscriptions, accounts, transactions, deliveries, delivery_items, consumer_feedback, pricing_schedule, access_log, usage_daily, etc.
- `supply` — 4 legacy tables mirrored from AliCloud: cfp_frontier, cfp_frontier_task, cfp_task_submission, cfp_task_audit_record
- `auth` — Supabase built-in auth

**New schema (contributor-portal adds to `public`):**
- Campaign tables: `campaigns`, `tasks`, `task_instances` — the shared contract between both portals
- Contribution workflow: `jobs`, `clips`, `clip_frames`, `segments`, `annotations`
- Identity: `contributors`
- Mock lineage: `lineage_staging`

**Convention:** Contributor-portal tables use descriptive names that don't collide with existing tables. Campaign/task/instance tables are the shared contract — developer portal writes campaign config, contributor portal writes instances.

## Ecosystem Context

```
developer-portal (demand side)
  │ writes: campaigns, tasks config, quality gates
  │ reads: task_instances, lineage, quality scores
  │
  └──── Shared Supabase (uxafdddzhgdhsabkwmgw) ────┐
         │                                           │
         │  public.*  (demand + supply + campaign)   │
         │  supply.*  (legacy AliCloud mirror)       │
         │  auth.*    (Supabase built-in)            │
         │                                           │
  ┌──────┘                                           │
  │                                                  │
contributor-portal (supply side — THIS REPO)         │
  │ writes: task_instances, annotations, lineage     │
  │ reads: campaigns, tasks config                   │
  │                                                  │
  ├── ML Backend Adapter ──► labeling-vision-engine  │
  │   (speaks LS protocol)    (GPU, external)        │
  │                                                  │
  └──────────────────────────────────────────────────┘
```

### Sibling repos

| Repo | Location | Relationship |
|---|---|---|
| `huge_leap` | `/in/huge_leap/` | Authoritative specs: annotation-pipeline, data-lineage, domain model |
| `developer-portal` | `/in/developer-portal/` | Shared Supabase, demand-side API, campaign-launch-roadmap |
| `labeling-website` | GitHub `codatta/labeling-website` | UX reference: annotation flow, detection presets, keyboard patterns |
| `labeling-api` | GitHub `codatta/labeling-api` | Logic reference: Vision Engine communication, frame organization |
| `labeling-vision-engine` | GitHub `codatta/labeling-vision-engine` | External service (GPU), wrapped by ML Backend adapter |
| `annotation-pipeline` | `/in/annotation-pipeline/` | Future extraction target for shared runtime code |
| `codatta-frontier-standards` | `/projects/codatta-frontier-standards/` | Frontier schema pattern (robotics not yet formalized) |

## Domain Model

From `huge_leap/docs/model/prd.md`:

- **Frontier** — platform-level bounded knowledge area (e.g., robotics = "Embodiment data")
- **Campaign** — scoped work request. Each task has a **Label Studio XML config** defining its annotation UI.
- **Task** — work specification. Origin: manual/auto-generated. Execution: human/agent. Tasks form a DAG. Agent tasks are served by **ML Backend** services.
- **Instance** — atomic contribution. Each has `parent_instances[]` for lineage and `content_hash` for on-chain attribution.

## Embodiment-X Annotation Schema

The Robotics frontier annotation schema, extending the existing labeling tool's temporal-only format:

| Layer | What | LS XML Tags | Status |
|---|---|---|---|
| Temporal | Action segments with ns-precision boundaries | `<Video>`, `<TimelineLabels>` | Reference: labeling-website Cull+Slice+Annotate |
| Action Labels | Per-segment classification | `<Label>` within `<TimelineLabels>` | Reference: labeling-website AnnotateTab |
| Spatial | Bounding boxes, body keypoints | `<Rectangle>`, `<KeyPointLabels>` | New (data exists in Vision Engine, needs UI) |
| Language | Natural language instruction per segment | `<TextArea name="language_instruction">` | New |
| Task Plan | Ordered high-level steps | `<TextArea name="task_plan">` | New |
| Quality | Blur, brightness, person confidence, hand activity | Metadata (not LS tags — stored in instance payload) | Reference: Vision Engine output |

## Tech Stack

- **Frontend:** Next.js 16 (App Router) + React 19 + Tailwind CSS v4 + shadcn/ui + Konva (frame rendering)
- **Backend API:** Python 3.13+ + FastAPI + uv + httpx
- **ML Backend Adapter:** Python FastAPI service implementing LS ML Backend protocol, wrapping Vision Engine
- **Database:** Shared Supabase (`uxafdddzhgdhsabkwmgw`) — same instance as developer-portal
- **Storage:** Supabase Storage (video/image uploads + processed frames)
- **Vision Engine:** External GPU service (`labeling-vision-engine`), consumed via ML Backend adapter
- **Package manager:** bun (frontend), uv (backend)
- **Deployment:** Vercel (webapp) + Cloud Run (API + ML Backend adapter)

## Repository Layout

```
contributor-portal/
├── CLAUDE.md
├── prd.md                   # Source of truth: capability scope, architecture, build queue
├── design/                  # All UX documentation, assets, and design source
│   ├── overview.md          #   Phase roadmap, user journeys, use cases, screen inventory
│   ├── system.md            #   Design system — tokens, components, shell layout, device rules
│   ├── screens/             #   Per-screen specs (purpose, states, behavior, interactions, devices)
│   ├── exports/             #   PNG exports for quick viewing
│   ├── source/              #   Pencil .pen files (editable design source)
├── reference/               # Upstream docs from huge_leap/docs/contributor-kitchen/ (serves design + implementation)
├── packages/
│   ├── webapp/                  # Next.js 16 App Router
│   │   ├── src/
│   │   │   ├── app/             # Pages: campaigns, upload, processing, annotate, export
│   │   │   ├── components/
│   │   │   │   ├── annotation/  # Cull review, slice, action label, spatial, language, task plan
│   │   │   │   ├── campaign/    # Discovery, detail, task DAG
│   │   │   │   ├── upload/      # Video/ZIP upload, detection presets
│   │   │   │   └── ui/          # shadcn/ui
│   │   │   ├── lib/             # API client, LS XML parser, state
│   │   │   └── hooks/
│   │   └── package.json
│   ├── api/                     # Python FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes/          # campaigns, jobs, instances, attempts, lineage
│   │   │   ├── models/          # Pydantic: Campaign, Task, Instance, Job, Clip, Annotation
│   │   │   ├── services/
│   │   │   │   ├── ml_backend_adapter.py  # LS ML Backend adapter → Vision Engine
│   │   │   │   ├── xml_config.py          # LS XML config parser + validator
│   │   │   │   ├── lineage.py             # Instance lineage walker
│   │   │   │   └── mock/                  # AttemptIndex, attribution hooks
│   │   │   └── db/              # Supabase client (shared instance)
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── shared/                  # Shared TypeScript types
│       └── types/
├── sql-query/
│   └── migrations/              # Supabase migrations (additive to existing schema)
├── templates/                   # Campaign XML configs + task DAG definitions
│   └── robotics_video_collection/
│       ├── campaign.yaml        # Task DAG: T1→T2→T3→T4, defaults, quality gates
│       ├── t1_data_supply.xml   # LS XML config for T1 (upload UI)
│       ├── t2_vision_processing.xml  # LS XML config for T2 (ML backend trigger)
│       ├── t3_human_annotation.xml   # LS XML config for T3 (Embodiment-X)
│       └── t4_validation.xml    # LS XML config for T4 (quality gates)
└── .env.example
```

## Mocked Systems

### AttemptIndex (mock)

```
GET  /v1/attempts/search?campaign_id=&contributor_id=&quality_grade=&status=
GET  /v1/attempts/{instance_id}
GET  /v1/attempts/{instance_id}/lineage
```
Implementation: Postgres queries. Interface stable for future search backend swap.

### On-Chain Data Lineage (mock)

`MockAttributionHooks` writes to `lineage_staging` table matching `InstanceRecord` from data-lineage spec §3.1. Status always `mock_committed`. Same interface as annotation-pipeline spec §4.5.

## Extraction Strategy

Code destined for `annotation-pipeline` repo when it materializes:

| Code | Future home |
|---|---|
| LS XML config parser + validator | `annotation-pipeline/packages/python/parser/` |
| ML Backend adapter (Vision Engine wrapper) | `annotation-pipeline/packages/python/ml_backend_server/` |
| Attribution hooks mock | `annotation-pipeline/packages/python/attribution_hooks/` |
| Embodiment-X annotation schema | `annotation-pipeline/spec/tags/` |
| LS annotation renderer components | `annotation-pipeline/packages/typescript/renderer-web/` |

**Rule:** Extraction-bound code has clean interfaces. No contributor-portal-specific imports. Extraction = copy + delete, not rewrite.

## UI/UX Design Process

Every screen or significant UI change follows this sequence **before any code is written**.

### Step 1 — Write a screen spec

Create `design/screens/<screen-name>.md`. Every screen spec must define:

```markdown
# Screen: <Name>

## Purpose
What this screen accomplishes. One paragraph.

## Phase
V1 / V2 / V3 — when this screen ships.

## Users
Which persona(s) use this screen and in what context.

## Entry Points
How users arrive (nav item, button, redirect, deep link).

## Exit Points
Where users go from here and via what action.

## Devices
Target devices. Responsive behavior or hard min-width constraints.

## States
| State | Trigger | What renders |
|---|---|---|
| Empty | No data | Empty state + CTA |
| Loading | Data fetching | Skeleton pattern |
| Error | Fetch failure | Error message + retry |
| Populated | Data ready | Primary UI |

## User Journey
Step-by-step: what the user does on this screen from entry to exit.

## Behavior
For each action: what the user does, what the system does, any side effects
(DB writes, Supabase Realtime events, optimistic updates, navigation).

## Interactions
| Element | Trigger | Response |
|---|---|---|
| | click / key / drag | |

Keyboard shortcuts if applicable.

## Screen Relationships
Other screens this connects to and the data/state passed between them.

## Excalidraw Design
Pencil file: `design/source/contributor-portal.pen` — node ID + screen name (or "not yet designed")
```

### Step 2 — Draw with Pencil (Excalidraw MCP)

Use `mcp__claude_ai_Excalidraw__create_view` to create the visual design:

1. Call `mcp__claude_ai_Excalidraw__read_me` once per conversation if not already loaded
2. Follow all guidelines in `design/system.md` — tokens, component patterns, shell layout, spacing
3. Use the sidebar shell for standard screens; full-bleed dark for annotation workspace
4. Draw progressively with `cameraUpdate` pans: shell → content → details → interaction states
5. Save the returned checkpoint ID into `design/screens/<screen>.md`
6. Use `restoreCheckpoint` to iterate — never redraw from scratch

### Step 3 — Confirm before coding

Share the design and confirm the screen spec before writing any component or page code.

---

## Request Handling Workflow

Every user request follows this workflow strictly:

### Step 1 — Classify the request

Determine whether the request is:

- **Exploration** — information gathering, questions, research, reading code, explaining behavior. No files are changed. Proceed directly — no branch needed.
- **File changes** — any request that will result in code, config, docs, or migration changes. Always requires a feature branch.

### Step 2 — Branch (for file-change requests only)

Before touching any file, create and checkout a feature branch:

```
git checkout -b feat/<short-description>   # new feature
git checkout -b fix/<short-description>    # bug fix
git checkout -b chore/<short-description>  # config, deps, docs
```

All work for the request happens on this branch. Never commit file changes directly to `main`.

### Step 3 — Implement one feature at a time

If the request involves multiple features or changes:

1. Work on **one feature** fully before starting the next
2. After implementing each feature, run the full quality gate (lint + test + build)
3. Verify correctness — test the happy path, edge cases, and check for regressions
4. Only after the current feature passes all checks, move to the next one
5. Commit each completed feature separately with a conventional commit message

### Step 4 — Create a PR for review

After all features on the branch are complete and passing:

1. Push the branch to the remote
2. Create a pull request using `gh pr create` targeting `main`
3. Include a summary of changes, test plan, and any concerns
4. Wait for user review before merging — never merge without approval

### Feature design flow (unchanged)

Within each feature, the design process still applies: **Request → Criticize → Review & Design → Update prd.md → UI/UX Design (if frontend) → Implement**

## Commands

- **Install (frontend):** `cd packages/webapp && bun install`
- **Install (backend):** `cd packages/api && uv sync`
- **Dev (frontend):** `cd packages/webapp && bun dev`
- **Dev (backend):** `cd packages/api && uv run uvicorn app.main:app --reload`
- **Test (backend):** `cd packages/api && uv run pytest`
- **Test (frontend):** `cd packages/webapp && bun test`
- **Lint:** `cd packages/api && uv run ruff check .` / `cd packages/webapp && bun lint`
- **Build:** `cd packages/webapp && bun run build`

## Conventions

- Follow the one-feature-at-a-time workflow from `~/CLAUDE.md`
- All work items live in `prd.md` under `## Build Queue`
- Never commit with failing tests, lint, or build
- Conventional commits: `feat:`, `fix:`, `test:`, `chore:`, `refactor:`, `docs:`
- Campaign config is Label Studio XML — no custom annotation schema formats
- Agent integration is ML Backend protocol — no custom agent APIs
- Database is shared Supabase — migrations must be additive and non-breaking to developer-portal
- Reference labeling-* repos for logic and UX patterns, but write fresh code
- Python: type hints, Pydantic models at all API boundaries
- TypeScript: strict mode, no `any`
- Mock services share interface with production counterparts; return `X-Mock: true` header
- **Logo:** The Codatta logomark (square symbol from `codatta/brand-kit`) is the shared logo for both the "Codatta" and "Humanbased" brands. Always use the logomark only — never include wordmark text alongside it. Assets: `public/assets/logos/colored/codatta.png` (black, for light backgrounds), `public/assets/logos/white/codatta.png` (white, for dark backgrounds). The product name displayed in the UI is "Humanbased".
- **UI/UX:** Always consult `design/system.md` before writing any component or styling. Use its color tokens, component patterns, shell layout, and device guidelines. Never introduce new colors, fonts, or spacing values outside of what is defined there. When in doubt, refer back to `developer-portal/packages/webapp/design_system.md` for the canonical shared tokens.
- **prd.md is the law:** No feature is real until it is in `prd.md`. No code starts until the build queue item is moved to In Progress with a recorded solution approach. No feature is done until it is marked Done with a commit hash.
- **design/ is the UX contract:** `design/overview.md` is the phase-level roadmap. `design/screens/<screen>.md` is the per-screen contract that governs implementation. Both must exist before a screen is coded.
