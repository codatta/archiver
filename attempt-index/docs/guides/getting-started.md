# Getting Started

AttemptIndex is a backend microservice that answers one question per submission:

> "Is this the 1st, 2nd, or Nth attempt at the same sample under this task's uniqueness rules?"

It assigns a monotonically increasing `attempt_index` and reports whether the configured collection ceiling has been reached. It never rejects submissions — that is always the caller's decision.

---

## Prerequisites

- Python 3.12+
- A Supabase project (staging: `uxafdddzhgdhsabkwmgw`)

---

## Install

```bash
# Clone and enter the project
cd attempt-index

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

---

## Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
SUPABASE_URL=https://uxafdddzhgdhsabkwmgw.supabase.co
SUPABASE_SECRET_KEY=sb_publishable_Dc6CRJPwXTO_KGvAb8tjyw_Wwpybbuo
ENV=development
PORT=8000
```

> **Note:** Use the `sb_publishable_` key for the supabase-py client, not the `sb_secret_` management key.

---

## Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

Or via the CLI:

```bash
attempt-index serve --reload
```

Check it's running:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Run the test suite

All tests run against the live Supabase staging database. Test records use the `test:` prefix and are cleaned up automatically after each test.

```bash
pytest -v
```

Expected output: **43 passed**.

---

## Project layout

```
app/
  main.py           # FastAPI app entry point
  config.py         # Settings loaded from .env
  routes/
    health.py       # GET /health
    evaluate.py     # POST /v1/evaluate
    bootstrap.py    # POST /v1/bootstrap
  services/
    attempt.py      # Core evaluate() and bootstrap() logic
  matchers/
    base.py         # Abstract matcher interface
    hash_matcher.py # SHA-256 + canonical_fields field selector
  db/
    client.py       # Supabase client singleton
    queries.py      # All database read/write functions
  models/
    request.py      # Pydantic request models
    response.py     # Pydantic response models
cli/
  main.py           # Typer CLI (attempt-index command)
tests/
  test_evaluate.py  # Integration tests for /v1/evaluate
  test_bootstrap.py # Integration tests for /v1/bootstrap
  test_matchers.py  # Unit tests for hash matching logic
migrations/
  001_attempt_records.sql
```

---

## What's next

- [Scenarios walkthrough →](./scenarios.md) — three concrete examples with expected output
- [Evaluating submissions →](./evaluate.md)
- [Structured data with canonical fields →](./canonical-fields.md)
- [Bootstrapping known datasets →](./bootstrap.md)
