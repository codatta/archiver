# AttemptIndex

A standalone backend microservice that answers one question per incoming submission:

> **"Is this the 1st, 2nd, or Nth attempt at the same sample under this task's uniqueness rules?"**

AttemptIndex assigns a monotonically increasing `attempt_index` and reports whether the configured collection ceiling has been reached. It never rejects submissions — downstream systems decide what to do with the index.

---

## System design

This service is specified in the Humanbased platform architecture. Full design documentation lives in the `huge_leap` repository:

- **Product spec:** [`huge_leap/docs/specs/attempt-index.md`](../huge_leap/docs/specs/attempt-index.md)
- **Visual guide:** [`huge_leap/docs/specs/attempt-index-illustrated.md`](../huge_leap/docs/specs/attempt-index-illustrated.md)
- **System context:** [`huge_leap/docs/architecture/system.md`](../huge_leap/docs/architecture/system.md) §3.2

AttemptIndex is a module within the **Contribution Pipeline** (§3.2 in the system map). It is called synchronously during submission intake, after the pipeline's own gating checks, and before the instance record is created.

```
Contribution Pipeline
  Gate 1: consensus already reached?  → close before AttemptIndex
  Gate 2: cut_off cached?             → close before AttemptIndex
  Gate 3: call AttemptIndex.evaluate()
              ↓
  attempt_index + cut_off_reached → create instance record → QC → reward → anti-fraud
```

---

## Version plan

| Version | Modality | Matching strategy | Status |
|---------|----------|------------------|--------|
| **V0** | Structured JSON, plain text | SHA-256 hash with `canonical_fields` config | ✅ Built |
| **V1** | Structured JSON, plain text | Semantic embedding similarity (Stage 2 of V0 pipeline) | 🔜 Next |
| **V2** | Images (evidence attachments) | Perceptual hash (pHash/dHash), Hamming distance | ⬜ |
| **V3** | Video | Keyframe extraction + pHash aggregate; full video embedding | ⬜ |
| **V4** | Audio | Waveform hash; audio embedding | ⬜ |
| **V5** | All modalities | Staged pipeline: cheap matcher first, embedding only if inconclusive | ⬜ |

Each version adds a new pluggable matcher — the core evaluate logic, database schema, and API contract do not change.

---

## Quick start

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env  # fill in SUPABASE_SECRET_KEY

# Start
uvicorn app.main:app --reload --port 8000

# Health check
curl http://localhost:8000/health
```

See [Getting Started](docs/guides/getting-started.md) for full setup instructions.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/v1/evaluate` | Assign attempt_index to a submission |
| `POST` | `/v1/bootstrap` | Pre-register known records before a campaign opens |
| `POST` | `/v1/frontiers` | Create a named frontier category |
| `GET` | `/v1/frontiers` | List all frontier categories |

Interactive docs: `http://localhost:8000/docs`

### Example — evaluate a submission

```bash
curl -X POST http://localhost:8000/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "task_id":          "cipherowl-iran-cex-q2",
    "sample_key":       "eth:0xabc123",
    "submission_id":    "sub-001",
    "payload_type":     "structured",
    "submitted_at":     "2026-04-27T10:00:00Z",
    "uniqueness_scope": "campaign",
    "campaign_id":      "cipherowl-iran-cex-q2",
    "max_attempts":     3,
    "matcher_config": {
      "methodology": "hash",
      "adapter_config": {"canonical_fields": ["address", "network"]}
    },
    "payload": {"address": "0xabc123", "network": "ethereum", "label": "CEX"}
  }'
```

```json
{
  "attempt_index": 1,
  "cut_off_reached": false,
  "cut_off_limit": 3,
  "nearest_prior": [],
  "match_key": "mk:94866cf64eebbd...",
  "processing_stage": "complete"
}
```

### Example — create a frontier category

```bash
curl -X POST http://localhost:8000/v1/frontiers \
  -H "Content-Type: application/json" \
  -d '{
    "frontier_id":  "crypto-wallets",
    "name":         "Crypto Wallets",
    "description":  "Blockchain wallet addresses across all networks"
  }'
```

```json
{
  "frontier_id":  "crypto-wallets",
  "name":         "Crypto Wallets",
  "description":  "Blockchain wallet addresses across all networks",
  "created_at":   "2026-04-27T10:00:00Z"
}
```

### Example — bootstrap records with frontier tags

Pre-register a known record and tag it to a frontier so it participates in frontier-scoped dedup:

```bash
curl -X POST http://localhost:8000/v1/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "records": [{
      "submission_id":    "bootstrap:roboarm1k-vid-042",
      "task_id":          "task-frontier-robotics",
      "sample_key":       "roboarm1k:vid-042",
      "match_key":        "mk:phash-roboarm1k-042",
      "payload_type":     "structured",
      "submitted_at":     "2025-11-01T00:00:00Z",
      "uniqueness_scope": "frontier",
      "frontier_ids":     ["robotics-motion-capture"]
    }]
  }'
```

```json
{"inserted": 1, "skipped": 0}
```

`frontier_ids` is optional — omit it for records not associated with a named frontier. The frontier must already exist (`POST /v1/frontiers`) before being referenced here.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ |
| Framework | FastAPI + Pydantic v2 |
| Database | Supabase PostgreSQL |
| Linting | ruff |
| Tests | pytest (24 tests, integration against live DB) |
| CLI | Typer (`attempt-index` command) |

---

## Project structure

```
attempt-index/
├── app/
│   ├── main.py                  # FastAPI app
│   ├── config.py                # Settings (pydantic-settings, .env)
│   ├── routes/
│   │   ├── health.py            # GET /health
│   │   ├── evaluate.py          # POST /v1/evaluate
│   │   └── bootstrap.py         # POST /v1/bootstrap
│   ├── services/
│   │   └── attempt.py           # Core evaluate() and bootstrap() logic
│   ├── matchers/
│   │   ├── base.py              # AbstractMatcher interface + MatchResult
│   │   └── hash_matcher.py      # SHA-256 + canonical_fields (V0)
│   ├── db/
│   │   ├── client.py            # Supabase client singleton
│   │   └── queries.py           # All DB read/write functions
│   └── models/
│       ├── request.py           # EvaluateRequest, BootstrapRequest
│       └── response.py          # EvaluateResponse, BootstrapResponse
├── cli/
│   └── main.py                  # Typer CLI (serve / health / evaluate / bootstrap)
├── tests/
│   ├── conftest.py              # Fixtures, DB cleanup
│   ├── test_evaluate.py         # Integration tests — /v1/evaluate
│   ├── test_bootstrap.py        # Integration tests — /v1/bootstrap
│   └── test_matchers.py         # Unit tests — hash matching logic
├── migrations/
│   └── 001_attempt_records.sql  # attempt_records table + indexes
├── docs/
│   └── guides/
│       ├── getting-started.md       # Setup and running
│       ├── evaluate.md              # POST /v1/evaluate reference
│       ├── canonical-fields.md      # Structured data uniqueness config
│       ├── bootstrap.md             # Pre-loading known datasets
│       ├── campaign-configuration.md # Per-campaign config patterns
│       ├── custom-matchers.md       # Extending the matching engine
│       └── database-setup.md        # DB schema, migration, bulk loading
├── prd.md                       # Build queue and progress tracking
├── CLAUDE.md                    # Project context for Claude Code
├── pyproject.toml
└── .env.example
```

---

## Guides

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/guides/getting-started.md) | Install, configure, run, test |
| [Scenarios Walkthrough](docs/guides/scenarios.md) | Three concrete examples with expected output and pipeline responsibilities |
| [Evaluate API](docs/guides/evaluate.md) | Request/response reference, idempotency, fail-open |
| [Canonical Fields](docs/guides/canonical-fields.md) | How to configure per-campaign field-based uniqueness |
| [Campaign Configuration](docs/guides/campaign-configuration.md) | Scope, ceilings, versioning, per-campaign config patterns |
| [Custom Matchers](docs/guides/custom-matchers.md) | Extend the engine: perceptual hash, embeddings, AI agents |
| [Bootstrap](docs/guides/bootstrap.md) | Pre-register known datasets before a campaign opens |
| [Database Setup](docs/guides/database-setup.md) | Schema, migration, bulk pre-load, useful queries |
| [Glossary](docs/guides/glossary.md) | Terminology reference: attempt_index, campaign_id, scope, match_key, and more |

---

## Deployment

### Current setup — fast iteration (default)

Deploy to Cloud Run with public ingress and no authentication. Easy to call from a laptop or CI during active development.

```bash
gcloud run deploy attempt-index \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SUPABASE_URL=...,SUPABASE_SECRET_KEY=...
```

The service URL can then be hit directly:

```bash
curl https://<service-url>/health
curl -X POST https://<service-url>/v1/evaluate -H "Content-Type: application/json" -d '{...}'
```

> **Note:** `SUPABASE_SECRET_KEY` and other secrets should be stored in Google Secret Manager and injected via `--set-secrets` rather than `--set-env-vars` even in dev. `--set-env-vars` is shown above for clarity only.

### Target setup — production (Contribution Pipeline)

AttemptIndex is an internal service — only the Contribution Pipeline's main component should ever call it. When hardening for production:

| Concern | Approach |
|---------|----------|
| Network exposure | `--ingress internal` — VPC-only, no public internet access |
| Caller identity | Cloud Run service-to-service OIDC auth; Contribution Pipeline attaches its Google service account token as `Authorization: Bearer <id-token>` |
| Secret management | All env vars injected from Secret Manager via `--set-secrets` |
| No static API keys | Service account tokens are short-lived and automatically rotated by GCP — no key storage or rotation overhead |

```bash
# Production deploy
gcloud run deploy attempt-index \
  --source . \
  --region us-central1 \
  --ingress internal \
  --no-allow-unauthenticated \
  --set-secrets SUPABASE_URL=supabase-url:latest,SUPABASE_SECRET_KEY=supabase-secret-key:latest

# Grant Contribution Pipeline's service account permission to call AttemptIndex
gcloud run services add-iam-policy-binding attempt-index \
  --region us-central1 \
  --member serviceAccount:contribution-pipeline@<project>.iam.gserviceaccount.com \
  --role roles/run.invoker
```

The Contribution Pipeline fetches an identity token for `https://<attempt-index-url>` and attaches it to each request. Cloud Run validates it; no application-layer auth code required.

> See `prd.md` → Backlog for the full production deployment ticket.

---

## Design principles

- **Single responsibility.** AttemptIndex counts. It never rejects, rewards, or makes policy decisions.
- **Fail-open.** Any internal error returns `attempt_index = 1` + an `error` field at HTTP 200. The submission flow is never blocked.
- **Idempotent.** The same `submission_id` always returns the same `attempt_index`, regardless of how many times it is called.
- **No raw payloads stored.** Only the computed `match_key` is persisted.
- **Zero coupling.** No knowledge of rewards, consensus, fraud detection, or on-chain state.
