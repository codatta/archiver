# Product Requirements Document: AttemptIndex

> Version: 0.1 | Date: 2026-04-27 | Status: In Progress
> Spec: `docs/specs/attempt-index.md` in huge_leap repo

---

## Product Vision

AttemptIndex is a standalone Python/FastAPI microservice that answers one question per submission:
**"Is this the 1st, 2nd, or Nth attempt at the same sample under this task's uniqueness rules?"**

It is a dependency of the Humanbased Contribution Pipeline. It must never block submission flow (fail-open), must be deterministic, and must have zero coupling to reward, consensus, or on-chain logic.

---

## Target Users

| User | Description |
|------|-------------|
| **Contribution Pipeline** | Primary caller — invokes evaluate() during submission intake |
| **CipherOwl Campaign** | V0 target customer — structured wallet annotation dedup |
| **Platform Ingestion Pipeline** | Calls bootstrap API to pre-register known datasets |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Framework | FastAPI + Pydantic v2 |
| Database | Supabase PostgreSQL (`uxafdddzhgdhsabkwmgw`, Inductive Network) |
| DB Client | supabase-py (sync) |
| Config | pydantic-settings |
| Testing | pytest + httpx (TestClient) |
| Linting | ruff |
| CLI | Typer |
| Deploy | Railway |

---

## Versioning

| Version | Modalities | Status |
|---------|-----------|--------|
| **V0** | Structured JSON + plain text (hash matching, canonical_fields) | 🔜 Building |
| **V2** | Images as evidence attachments (perceptual hash, different scope) | ⬜ |
| **V3** | Video | ⬜ |
| **V4** | Audio | ⬜ |

---

## Build Queue

### ✅ Completed

- [x] **[P0-1: Project Scaffolding]** — FastAPI skeleton, pyproject.toml, ruff, health endpoint
- [x] **[P0-2: Database Schema]** — `attempt_records` + 3 indexes applied via Supabase MCP; RLS disabled
- [x] **[P0-3: Hash Matcher + Field Selector]** — SHA-256 + canonical_fields for structured/text
- [x] **[P0-4: POST /v1/evaluate]** — Full attempt assignment with scope queries and nearest_prior
- [x] **[P0-5: Uniqueness Scope]** — task / campaign / frontier / global
- [x] **[P0-6: Bootstrap Write API]** — POST /v1/bootstrap, idempotent by submission_id
- [x] **[P0-7: Idempotency + Fail-Open]** — Duplicate submission_id safe; all errors return HTTP 200
- [x] **[P0-8: CLI]** — serve / health / evaluate / bootstrap via Typer
- [x] **[P0-9: campaign_id + Campaign Default Scope]** — Added `campaign_id` column (migration 002), isolated campaign-scope query, default `uniqueness_scope="campaign"`, validator requires `campaign_id` when scope is `campaign`; 2 new tests
- [x] **[P0-11: Frontier Taxonomy — metadata tags]** — `frontiers` + `record_frontiers` tables (migration 004); `POST/GET /v1/frontiers`; optional `frontier_ids` on bootstrap records with FK validation and idempotent tagging; `query_prior_matches` unchanged; 12 new tests

### 🔜 Next Up

- [ ] **[P0-1: Project Scaffolding]** — FastAPI app skeleton, config, linting, health endpoint
  - **User:** Engineering
  - **Acceptance Criteria:**
    - `GET /health` returns `{"status": "ok"}`
    - `ruff check .` passes with zero errors
    - `pytest` runs and collects tests (even if zero pass yet)
    - Project starts with `uvicorn app.main:app --reload`
  - **Technical Notes:** `pyproject.toml` with all deps; `app/`, `tests/`, `cli/`, `migrations/` dirs
  - **Tests Required:** health endpoint returns 200 + correct body

- [ ] **[P0-2: Database Schema]** — `attempt_records` table + 3 indexes
  - **User:** Engineering
  - **Acceptance Criteria:**
    - Table exists in Supabase with all columns from spec §12 + `attempt_index` + `created_at`
    - 3 indexes created: sample_lookup, match_lookup, scope_lookup
    - Migration is idempotent (IF NOT EXISTS)
  - **Technical Notes:** Apply via Supabase MCP `apply_migration`; schema in `migrations/001_attempt_records.sql`
  - **Tests Required:** table exists query returns success

- [ ] **[P0-3: Hash Matcher + Field Selector]** — SHA-256 matching for text and structured payloads
  - **User:** Contribution Pipeline, CipherOwl
  - **Acceptance Criteria:**
    - Text: normalise (NFKC, lowercase, collapse whitespace) → SHA-256 → `mk:{hex}`
    - Structured: extract `canonical_fields` in order → join with `|` → SHA-256 → `mk:{hex}`
    - Two payloads with same canonical field values produce identical `match_key` regardless of other fields
    - Matcher is pluggable via abstract base class
  - **Technical Notes:** `app/matchers/hash_matcher.py`; `canonical_fields` comes from `matcher_config.adapter_config`
  - **Tests Required:** same fields → same key; different fields → different key; field order is stable; missing fields raise error; extra fields ignored

- [ ] **[P0-4: POST /v1/evaluate — Core Endpoint]** — Assign attempt_index to a submission
  - **User:** Contribution Pipeline
  - **Acceptance Criteria:**
    - Accepts raw `payload` + `matcher_config.adapter_config.canonical_fields` OR pre-computed `match_key`
    - Returns `attempt_index`, `cut_off_reached`, `cut_off_limit`, `nearest_prior`, `processing_stage`
    - First submission for a (scope, sample_key, match_key) → `attempt_index = 1`, `nearest_prior = []`
    - Nth submission → `attempt_index = N`, `nearest_prior = [most recent match]`
    - `cut_off_reached = true` when `attempt_index >= max_attempts`
    - Similarity = 1.0 for exact hash match
  - **Technical Notes:** `app/routes/evaluate.py` + `app/services/attempt.py`; scoped queries per §scope table below
  - **Tests Required:** UC-1 first submission; UC-2 repeat while in_queue; UC-6 cut-off reached; UC-5 genuinely new payload under same sample_key

- [ ] **[P0-5: Uniqueness Scope]** — Support task / campaign / frontier / global scope queries
  - **User:** Contribution Pipeline
  - **Acceptance Criteria:**
    - `task`: queries by `(task_id, sample_key, match_key)`
    - `campaign` / `frontier` / `global`: queries by `(uniqueness_scope, sample_key, match_key)`
    - Records written with correct `uniqueness_scope` for cross-scope dedup to work
  - **Technical Notes:** `app/db/queries.py`; uses existing indexes
  - **Tests Required:** task-scoped record not found in frontier-scoped query; frontier-scoped record found in frontier query

- [ ] **[P0-6: Bootstrap Write API]** — Pre-register known datasets before campaign opens
  - **User:** Platform Ingestion Pipeline
  - **Acceptance Criteria:**
    - `POST /v1/bootstrap` accepts an array of records
    - `submission_id` must start with `bootstrap:`
    - Idempotent: re-running with same `submission_id` inserts nothing new
    - Returns `{"inserted": N, "skipped": M}`
  - **Technical Notes:** `app/routes/bootstrap.py`; upsert with ON CONFLICT DO NOTHING on `submission_id`
  - **Tests Required:** fresh insert; duplicate is skipped; bad submission_id prefix rejected; batch of 1000 completes

- [ ] **[P0-7: Idempotency + Fail-Open]** — Same submission_id → same result; errors never block
  - **User:** Contribution Pipeline
  - **Acceptance Criteria:**
    - Calling evaluate twice with same `submission_id` returns identical `attempt_index`
    - Any internal error (DB timeout, matcher crash) returns `attempt_index = 1` + `error` field, HTTP 200
    - Never returns HTTP 5xx to the caller
  - **Technical Notes:** Check `submission_id` existence before write; wrap service in try/except; return fail-open response on exception
  - **Tests Required:** duplicate submission_id; DB unavailable simulation; matcher exception

- [ ] **[P0-8: CLI]** — Management and testing CLI via Typer
  - **User:** Engineering / Ops
  - **Acceptance Criteria:**
    - `attempt-index serve` — starts uvicorn server
    - `attempt-index evaluate --json '{...}'` — call evaluate and pretty-print result
    - `attempt-index bootstrap --file records.json` — bulk bootstrap from JSON file
    - `attempt-index health [--url URL]` — check service health
  - **Technical Notes:** `cli/main.py` using Typer; reads `ATTEMPT_INDEX_URL` env var for remote calls
  - **Tests Required:** CLI help text renders; evaluate command round-trips

### 📋 Backlog

- [ ] **[Infra: Production Deployment — Cloud Run + VPC + OIDC]** — Harden the Cloud Run deployment for production: VPC-internal ingress only, service-to-service OIDC auth (no static API keys), secrets via Secret Manager
  - **User:** Platform Engineering / Ops
  - **Acceptance Criteria:**
    - `--ingress internal` — service unreachable from the public internet
    - `--no-allow-unauthenticated` — Cloud Run validates caller's Google service account token
    - Contribution Pipeline's service account granted `roles/run.invoker`; all other callers rejected at the platform layer
    - All env vars (`SUPABASE_URL`, `SUPABASE_SECRET_KEY`) injected from Secret Manager via `--set-secrets`
    - A `Dockerfile` (or `cloudbuild.yaml`) checked into the repo for repeatable builds
    - Dev/staging environment keeps `--allow-unauthenticated` + `--ingress all` for laptop testing
  - **Technical Notes:** No application-layer auth code needed — Cloud Run handles token validation. Contribution Pipeline attaches an identity token scoped to the AttemptIndex service URL. See README.md → Deployment for the `gcloud` commands.
  - **Depends on:** Contribution Pipeline service account provisioned in the shared GCP project

- [ ] **[V2: Image Evidence Support]** — Perceptual hash (pHash/dHash) for image evidence attachments, separate uniqueness scope to prevent abuse
- [ ] **[V3: Video Support]** — Keyframe extraction + pHash aggregate
- [ ] **[V4: Audio Support]** — Waveform hash
- [ ] **Embedding/Semantic Matcher (Stage 2)** — Cosine similarity via embedding vectors for near-duplicate text/image
- [ ] **Staged Processing** — Two-stage pipeline (cheap → expensive) with `staged: true` config
- [ ] **Rate Limiting** — Per-caller limits
- [ ] **Observability** — Structured logging + metrics endpoint
- [ ] **Railway Deploy** — Production deployment with health checks

#### Pending

- [ ] **[P0-11: Frontier Taxonomy — metadata tags (Option A)]** — Add named frontier categories and tag bootstrap (and promoted live) records to them, with no change to dedup query logic
  - **User:** Platform Ingestion Pipeline, Engineering
  - **Acceptance Criteria:**
    - New `frontiers` table: `frontier_id text PK`, `name text NOT NULL`, `description text`, `created_at timestamptz`
    - New `record_frontiers` junction table: `(submission_id text FK → attempt_records, frontier_id text FK → frontiers)` with composite PK; partial index for lookups
    - `POST /v1/bootstrap` accepts optional `frontier_ids: list[str]` per record; inserts rows into `record_frontiers` for each
    - `POST /v1/frontiers` (or equivalent) to create/list named frontier categories
    - `query_prior_matches` is **unchanged** — frontier-scope dedup still uses `uniqueness_scope = 'frontier'`
    - A bootstrap record with `frontier_ids = ["crypto-wallets", "eth-mainnet"]` is tagged to both; querying either frontier returns it
    - Live record promotion path: update `uniqueness_scope` to `'frontier'` + insert tag rows (documented, not yet automated)
    - Re-bootstrapping the same `submission_id` with a new `frontier_ids` list is idempotent per tag (no duplicate junction rows)
  - **Technical Notes:**
    - Migration 004: create `frontiers` and `record_frontiers` tables
    - `app/models/request.py`: add `frontier_ids: list[str] = []` to `BootstrapRecord`
    - `app/db/queries.py`: new `tag_record_frontiers(client, submission_id, frontier_ids)` helper
    - `app/services/attempt.py bootstrap()`: call tagging helper after upsert
    - New route `app/routes/frontiers.py`: `POST /v1/frontiers`, `GET /v1/frontiers`
    - Depends on: P0-6 (Bootstrap API) — already complete
  - **Tests Required:**
    - Bootstrap with valid `frontier_ids` creates rows in `record_frontiers`
    - Bootstrap without `frontier_ids` succeeds (empty list = no tags written)
    - Re-bootstrap with same `frontier_ids` is idempotent (no duplicate rows)
    - Bootstrap record tagged to two frontiers appears in both tag lookups
    - `frontier_ids` referencing a non-existent `frontier_id` returns a clear error
    - `evaluate` response unaffected by presence or absence of frontier tags

- [ ] **[P1-1: Named Frontier Scope — query integration (Option B, follow-up)]** — Upgrade `query_prior_matches` to filter by named `frontier_id`, enabling per-domain dedup isolation
  - **User:** Contribution Pipeline
  - **Acceptance Criteria:**
    - `evaluate` and `query_prior_matches` accept an optional `frontier_id` parameter
    - When `frontier_id` is provided with `uniqueness_scope = "frontier"`, query narrows to records tagged to that frontier via `record_frontiers`
    - When `frontier_id` is absent, falls back to current undifferentiated `uniqueness_scope = 'frontier'` behavior
    - Existing tests pass unchanged (backward compatible)
  - **Technical Notes:** Builds on P0-11 schema; requires JOIN in `query_prior_matches`; add `frontier_id` to `EvaluateRequest` and to the `idx_attempt_campaign_lookup`-equivalent index for frontiers
  - **Depends on:** P0-11

- [ ] **[P0-10: Bootstrap payload + matcher_config support]** — Allow `BootstrapRecord` to accept `payload + matcher_config` as an alternative to a pre-computed `match_key`, so AttemptIndex computes the hash consistently with evaluate. Eliminates the risk of value-order mismatches between bootstrap and live submissions.
  - **Acceptance Criteria:** `match_key` becomes optional in `BootstrapRecord`; validator requires either `match_key` or `payload + matcher_config`; hash computed server-side on bootstrap using the same `HashMatcher` path as evaluate.
  - **Technical Notes:** `app/models/request.py` + `app/services/attempt.py bootstrap()` + new test in `test_bootstrap.py`

#### Known Limitations — Flood Behaviour & Cut-off Enforcement

- [ ] **Fast-mode cut-off check** — `query_prior_matches` in `app/db/queries.py` issues a `SELECT *` (full row fetch) for every evaluate call. Under a flooding attack, each call scans an ever-growing set of rows matching `(match_key, sample_key, scope)`, producing O(N) data transfer per call after N flood submissions. A `SELECT COUNT(*)` with a separate single-row fetch for `nearest_prior` would reduce per-call overhead but would not prevent the flood itself.

- [ ] **Advisory cut-off — flood prevention is the pipeline's responsibility** — `cut_off_reached = true` in the evaluate response is advisory only. AttemptIndex does **not** block subsequent submissions once the ceiling is reached; every unique `submission_id` creates a new row in `attempt_records` regardless of `max_attempts`. The Contribution Pipeline must cache `cut_off_reached = true` on first detection and gate all further submissions **before** calling AttemptIndex. If the pipeline gates correctly, AttemptIndex never sees flood traffic.

---

## Scope Queries (V0 Reference)

| uniqueness_scope | WHERE clause |
|-----------------|-------------|
| `task` | `task_id = :task_id AND sample_key = :sample_key AND match_key = :match_key` |
| `campaign` | `uniqueness_scope = 'campaign' AND sample_key = :sample_key AND match_key = :match_key` |
| `frontier` | `uniqueness_scope = 'frontier' AND sample_key = :sample_key AND match_key = :match_key` |
| `global` | `sample_key = :sample_key AND match_key = :match_key` |

---

## V0 Exit Criteria

- [ ] Deterministic outputs in replay tests (same inputs → same `attempt_index`)
- [ ] p95 Stage 1 latency < 50ms (hash matching)
- [ ] Zero coupling to reward, consensus, or on-chain systems
- [ ] CipherOwl use case: 3 contributors labeling same wallet → attempt_index 1, 2, 3; 4th → gated by caller
- [ ] Fail-open: no HTTP 5xx returned under any internal error condition

---

## Success Metrics

| Metric | Target |
|--------|--------|
| p95 evaluate latency | < 50ms |
| Idempotency | 100% — same submission_id always returns same attempt_index |
| Fail-open rate | 100% — never returns 5xx |
| CipherOwl dedup accuracy | 0 false negatives on exact match |
