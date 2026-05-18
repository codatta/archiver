# Campaign Launch — Implementation Roadmap

> Phased plan for adding the **demand-push campaign flow** to the Humanbased Developer Portal.
> Peer document to [prd.md](./prd.md) and [prod_overview.md](./prod_overview.md).
>
> **Source of truth for the vision:** `codatta/huge_leap` — domain model in `docs/model/prd.md`, campaign builder spec in `docs/specs/developer-portal.md §9.2`, data lineage schema in `docs/specs/data-lineage.md`, walk-through examples in `docs/model/walk-through-examples.md`.

---

## Context

The current developer-portal implements only the **consumer side** of the marketplace — orgs subscribe to a pre-existing data vertical, pull validated items, adopt or dispute. The supply is pre-curated.

The **campaign flow** reverses the direction: orgs push tasks into the pipeline, recruit contributors (human or agent), and receive validated instances back as first-party output. This unlocks custom data requests (robotics footage, video supply + annotation, etc.) with full provenance tracking suitable for future on-chain anchoring.

---

## Target domain model (from huge_leap)

```
Frontier
  └── Campaign          # org-launched scoped work request
        └── Task        # specification, possibly DAG-shaped
              └── Task Instance   # atomic contribution, one record
```

Every `Task Instance` is the unit of lineage — it carries `parent_instances[]`, `content_hash`, `annotation_config_ver`, `contributor_did`, and (in later phases) `upstream_shares` for royalty splits.

This is identical to the on-chain `InstanceRecord` schema defined in huge_leap's `docs/specs/data-lineage.md §3`, so Phase 1's off-chain storage is the exact shape that later gets anchored on-chain in Phase 5 — **no rework.**

---

## Phase 0 — Foundation

**Goal:** schema + minimal campaign CRUD. Prerequisite for any campaign work.

### Scope

- Supabase migration adding three tables:
  - `campaigns` — `id`, `org_id`, `frontier_id`, `template_id`, `name`, `status`, `params jsonb`, `created_at`
  - `tasks` — `id`, `campaign_id`, `template_task_key`, `name`, `execution` (`human` / `agent`), `config jsonb`, `depends_on uuid[]`
  - `task_instances` — `id`, `task_id`, `campaign_id`, `parent_instances uuid[]`, `content_hash text`, `annotation_config_ver text`, `contributor_did text nullable`, `quality_grade text`, `status text`, `payload jsonb`, `submitted_at`, `validated_at`
- FKs and indexes: `task_instances(campaign_id)`, `task_instances(task_id)`, GIN on `parent_instances`
- RLS policies mirroring existing org-scoped patterns (org_member can read their org's campaigns)
- Minimal API surface: `POST /v1/orgs/{org_id}/campaigns`, `GET /v1/orgs/{org_id}/campaigns`, `GET /v1/orgs/{org_id}/campaigns/{id}`

### Out of scope

- Template engine (Phase 1)
- UI (Phase 1)
- Compensation logic (Phase 4)

### Deliverables

- 1 migration file
- 3 Pydantic models in `packages/api/app/models/`
- 3 API endpoints in `packages/api/app/routes/campaigns.py`
- Unit tests for the CRUD path

---

## Phase 1 — **NEXT MILESTONE** — Pre-set template, fixed UI, off-chain lineage ⭐

**Goal:** end-to-end campaign launch with hard-coded templates. User brief: _"launch a campaign with pre-set (not so flexible) template (robotics, video supply and annotation) with fixed UI; and can retrieve the data with full lineage (can be later to integrate on-chain)."_

### Scope

**Templates** (hard-coded JSON/YAML in `packages/api/app/templates/`):

1. **`robotics_video_collection.yaml`** — modeled on huge_leap's Nvidia housekeeping example:
   - Task 1: Video Recording (human, 2-camera setup)
   - Task 2: Agent Pre-Labeling (agent placeholder — manual for V1)
   - Task 3: Human Labeling (forces, task planning, NL descriptions)
   - Task 4: Validation (sample 10%, IAA threshold 0.85)

2. **`video_supply_annotation.yaml`** — modeled on the Unitree robot footage example:
   - Task 1: Supply (human, raw footage upload)
   - Task 2: Annotation (human, bounding boxes + action labels)
   - Task 3: Validation (sample check, quality grade)

Each template declares: task DAG shape, default parameters, quality gates, placeholder annotation config version string.

**Fixed UI** at `/dashboard/campaigns/new`:

- Template picker — 2 cards with preview of task DAG
- Parameter form — 3–4 fields only:
  - Campaign name
  - Frontier (dropdown, currently fixed list)
  - Target quantity (items)
  - Quality threshold (preset choices: Standard / High / Premium)
- "Launch campaign" button → calls `POST /v1/orgs/{org_id}/campaigns` with `template_id` + params
- Campaign detail page `/dashboard/campaigns/{id}`:
  - Task DAG visualization (static, no drag-drop)
  - Progress: items received, by task status
  - Items table with lineage column

**Data pull enriched with lineage:**

Extend `GET /v1/live/pull` response to include a `lineage` object per item:

```json
{
  "submission_id": "inst_7f3...",
  "data": { "..." },
  "quality_grade": "A",
  "lineage": {
    "campaign_id": "cmp_abc...",
    "task_id": "tsk_def...",
    "parent_instances": ["inst_upstream_1", "inst_upstream_2"],
    "annotation_config_ver": "robotics_v1.0.0",
    "content_hash": "sha256:4a7b9c...",
    "contributor_did": null
  }
}
```

For campaigns launched via Phase 1, `lineage` is always populated. For legacy subscription pulls (no campaign), `lineage` is `null` or a minimal stub (`campaign_id: null`).

**Lineage retrieval endpoint:**

`GET /v1/orgs/{org_id}/campaigns/{campaign_id}/lineage/{instance_id}` — returns the full parent chain as a tree, off-chain. Output format designed so that Phase 5 can serve the same payload from on-chain reads.

### Out of scope (deferred)

- Dynamic campaign builder (Phase 3)
- Compensation model selection beyond fixed-per-item (Phase 4)
- KYB / trust tier gating (Phase 4)
- Agent registration / ML backend protocol (Phase 6)
- On-chain writes (Phase 5)
- Qualification gates beyond built-ins in the template

### Acceptance criteria

- [ ] User can launch a `robotics_video_collection` campaign in < 30 seconds from the dashboard
- [ ] User can launch a `video_supply_annotation` campaign in < 30 seconds
- [ ] Launching a campaign creates campaign + task + task_instance rows matching the template DAG
- [ ] `GET /v1/live/pull` response includes a `lineage` object when the item originated from a Phase 1 campaign
- [ ] `GET .../lineage/{instance_id}` returns the full parent chain with `content_hash`, `annotation_config_ver`, `contributor_did` (null in Phase 1)
- [ ] `content_hash` is deterministic (SHA-256 of canonicalized payload) so Phase 5's on-chain anchoring is rewrite-free
- [ ] Docs page added to `packages/docs/content/docs/` covering the campaign flow
- [ ] Unit tests for template instantiation
- [ ] Integration test for end-to-end: launch campaign → simulate validator submission → pull with lineage

### Deliverables

- Phase 0 migration (if not already shipped)
- 2 template YAML files
- `packages/api/app/routes/campaigns.py` (extended from Phase 0)
- `packages/api/app/services/template_engine.py` — parses template + instantiates rows
- `packages/api/app/services/lineage.py` — walks parent chain
- `packages/webapp/src/pages/CampaignLaunch.tsx`
- `packages/webapp/src/pages/CampaignDetail.tsx`
- `packages/webapp/src/components/campaign/TemplatePicker.tsx`
- `packages/webapp/src/components/campaign/TaskDAGView.tsx` (static SVG, no interaction)
- `packages/docs/content/docs/campaigns.mdx`

### Estimated effort

Approximately **3–4 focused weeks** of work. Bulk is in the campaign CRUD + UI; the lineage enrichment and template engine are each ~2 days.

---

## Phase 2 — Template library expansion

**Goal:** add 3–4 more templates without touching the template engine.

- Templates become a small DSL (JSON/YAML). Adding one is a file, not code.
- Template gallery UI showing all available templates grouped by category.
- Templates to add:
  - Fashion item annotation
  - Food product intelligence
  - Crypto wallet annotation
  - Geospatial verification

### Acceptance criteria

- [ ] Adding a new template requires only adding a file to `packages/api/app/templates/` and a thumbnail to `packages/webapp/public/templates/`
- [ ] Template gallery renders all 6+ templates with category tabs
- [ ] Each template has a preview modal showing its DAG and sample output

---

## Phase 3 — Dynamic campaign builder (full 7-step flow)

**Goal:** implement the full campaign builder specced in huge_leap `docs/specs/developer-portal.md §9.2`.

### Scope

- 7-step wizard per the spec:
  1. Campaign metadata (name, frontier, description)
  2. Task DAG designer (drag-drop)
  3. Per-task config (UI, quality gates, payload schema)
  4. Compensation model selection (Phase 4 dependency for non-fixed)
  5. Qualification gates (who can contribute)
  6. Privacy controls (4-tier visibility)
  7. Review & launch
- Task DAG designer — visual node editor with task types, depends_on edges, validation
- Cascading policy resolver scaffold (protocol → frontier → campaign → task)

### Out of scope

- Compensation models beyond fixed (Phase 4)
- Agent attachment (Phase 6)

---

## Phase 4 — Compensation models + trust tiers

**Goal:** unlock bounty, hybrid, and royalty-sharing compensation per huge_leap's cascading policy.

### Scope

- KYB integration → compute trust tier (`new` / `verified` / `established` / `trusted`)
- Trust tier gates which compensation models the org can use
- Implement `upstream_shares` distribution logic. **Input is `parent_instances` from Phase 1** — lineage is the key input, which is why Phase 1 must land first.
- Royalty payout stream in billing (ledger entries per adopt that cascade to upstream contributors)
- Frontier-level and campaign-level policy overrides within parent bounds

### Acceptance criteria

- [ ] Org with `trusted` tier can launch a royalty-share campaign; org with `new` tier cannot
- [ ] On adopt, `upstream_shares` distributes the compensation to contributors in `parent_instances` weighted by depth/config
- [ ] Policy cascade (protocol → frontier → campaign → task) is enforced server-side; client can only override within bounds

---

## Phase 5 — On-chain lineage ("later to integrate on-chain")

**Goal:** anchor every validated instance on-chain with its full parent chain.

### Scope

- Integrate with `codatta/codatta-onchain-protocol` or `codatta/contracts`
- On validation, write `InstanceRecord` on-chain. Payload matches Phase 1's schema exactly — `content_hash`, `parent_instances`, `annotation_config_ver`, `contributor_did`, `upstream_shares`
- `contributor_did` is required at this phase — backfill blanks from earlier phases via attestation flow
- Public lineage verification UI (read-only) — any item's lineage can be independently verified against the chain
- Gas strategy: batch writes per validator epoch, use gas-payment-bundler repo for ERC-4337-style payment in any ERC-20

### Dependencies

- `codatta-onchain-protocol` must expose an `InstanceRecord` contract
- `gas-payment-bundler` must be deployed for production writes

### Out of scope

- Dispute resolution on-chain (off-chain in V1)
- Reputation scoring on-chain (future)

---

## Phase 6 — Agent integration

**Goal:** pre-label / validation agents attached to task nodes.

### Scope

- Agent registration via ML backend protocol (per huge_leap `docs/specs/annotation-pipeline.md`)
- Task node with `execution: "agent"` routes to registered agent instead of human queue
- Agent output captured as `task_instance` with `contributor_did = agent_did`
- Integration with annotation-pipeline repo (if/when it materializes)

### Dependencies

- `humanbased/annotation-pipeline` must exist and implement the ML backend protocol

---

## Phase sequencing

```
Phase 0 ── Phase 1 ⭐ ── Phase 2 ── Phase 3 ── Phase 4 ── Phase 5 ── Phase 6
(schema)  (MVP)       (more       (full       (comp      (on-chain) (agents)
                      templates)  builder)    models)
```

**Phase 0 + Phase 1 is the next milestone.** Every later phase can be built on the Phase 1 schema without rework — the `task_instance` row shape is the on-chain row shape.

**Phases 2 and 3 are independent** once Phase 1 is live; they can ship in either order based on user feedback (more templates vs. dynamic builder).

**Phases 4, 5, 6 have dependencies** on external projects (KYB, onchain-protocol, annotation-pipeline) and should be planned in sync with those teams.

---

## Open questions for planning

1. **Frontier writable storage.** Frontiers currently live in AliCloud MySQL (`mysql_db`, read-only). Campaigns need to reference frontier IDs. Do we keep frontiers read-only and campaigns reference them by opaque ID, or do we mirror frontiers into Supabase?
2. **Content hash computation.** Who computes `content_hash` — the worker client, the API on receive, or the validator on submit? Determinism matters for future on-chain anchoring.
3. **Template versioning.** Templates shipped in Phase 1 will evolve. Does the `annotation_config_ver` field track template version separately, or is it a single version covering both template + annotation schema?
4. **Off-chain lineage TTL.** Before Phase 5, lineage lives only in Supabase. Do we need to snapshot it to object storage (S3 / Supabase Storage) for durability, or is Postgres enough until we go on-chain?
5. **Campaign status lifecycle.** `draft` → `launched` → `collecting` → `completed` / `cancelled`? Who transitions between states — manual or automated based on `target_quantity`?

These should be answered during Phase 0 design review.

---

## Related documents

- [prd.md](./prd.md) — existing feature spec and build queue
- [prod_overview.md](./prod_overview.md) — business model and platform architecture
- `codatta/huge_leap` — full domain model, data lineage spec, walk-through examples
- [release-workflow.md](./release-workflow.md) — branching and release process
