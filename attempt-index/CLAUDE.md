# AttemptIndex — CLAUDE.md

## Project

AttemptIndex is a standalone Python/FastAPI microservice within the Humanbased platform.
It assigns a monotonically increasing attempt number to each submission based on configurable uniqueness rules.
It must fail-open, never block submissions, and have zero coupling to rewards, consensus, or on-chain state.

**Spec source:** `huge_leap/docs/specs/attempt-index.md`

## Tech Stack

- **Language:** Python 3.12+
- **Framework:** FastAPI
- **Validation:** Pydantic v2
- **Database:** Supabase PostgreSQL — project `uxafdddzhgdhsabkwmgw` (Inductive Network, staging)
- **DB Client:** supabase-py (sync, via service_role key)
- **Config:** pydantic-settings, `.env` file
- **Lint:** ruff
- **Tests:** pytest + httpx TestClient
- **CLI:** Typer (`attempt-index` command)

## Running Locally

```bash
# Install
pip install -e ".[dev]"

# Copy env
cp .env.example .env
# Fill in SUPABASE_SECRET_KEY from Supabase dashboard → Settings → API

# Start server
uvicorn app.main:app --reload --port 8000

# Or via CLI
attempt-index serve

# Run tests
pytest

# Lint
ruff check .
```

## Project Structure

```
app/
  main.py          # FastAPI app + router registration
  config.py        # pydantic-settings Settings
  models/
    request.py     # EvaluateRequest, BootstrapRequest
    response.py    # EvaluateResponse, BootstrapResponse
  db/
    client.py      # Supabase client singleton
    queries.py     # All DB read/write functions
  matchers/
    base.py        # AbstractMatcher interface
    hash_matcher.py  # SHA-256 + canonical_fields field selector
  services/
    attempt.py     # Core evaluate() and write_record() logic
  routes/
    health.py      # GET /health
    evaluate.py    # POST /v1/evaluate
    bootstrap.py   # POST /v1/bootstrap
cli/
  main.py          # Typer CLI
tests/
  conftest.py
  test_evaluate.py
  test_bootstrap.py
  test_matchers.py
migrations/
  001_attempt_records.sql
```

## Design Rules

- AttemptIndex **fails open**: any internal error returns `attempt_index=1` + `error` field, HTTP 200
- AttemptIndex **never rejects** submissions — it only counts and reports
- `submission_id` idempotency: same ID always returns same `attempt_index`
- No raw payloads stored — only `match_ref` (computed hash)
- `bootstrap:` prefix on `submission_id` = pre-registered known dataset record
- V0 supports only `methodology: "hash"` with `canonical_fields` for structured data

## Supabase

- Project ID: `uxafdddzhgdhsabkwmgw`
- Table: `attempt_records`
- Use `SUPABASE_SECRET_KEY` (service_role) for all DB access
- RLS: disabled on `attempt_records` (service-to-service only, no user-facing access)

## Test Strategy

- Unit tests: matchers in isolation (no DB)
- Integration tests: routes against real Supabase staging DB
- Test records use `submission_id` prefix `test:` — cleaned up in teardown
- All tests must pass before commit
