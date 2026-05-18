# Bootstrapping Known Datasets

When a campaign launches against data that already exists — a prior Humanbased collection, a public open-source dataset, or a customer's own historical records — the AttemptIndex store is empty. A contributor submitting an exact copy of pre-existing data would receive `attempt_index = 1`, because there are no prior records to match against.

Bootstrapping solves this by pre-registering known records *before* the campaign opens for submissions.

---

## When to bootstrap

Bootstrap is needed when:

- The campaign is launching against a known public or prior-collected dataset
- `uniqueness_scope` is `frontier` or `global` and cross-campaign dedup is required
- `uniqueness_scope` is `campaign` and you want to pre-populate the campaign's prior-record pool before contributors start submitting
- You want to prevent reward farming via copies of existing data

Bootstrap is **not** needed for:

- Fresh data with no prior history — contributors are collecting it for the first time
- Campaigns where duplicate detection only needs to apply within contributions made during the campaign itself

---

## The bootstrap endpoint

```
POST /v1/bootstrap
```

Accepts a batch of records to pre-register. Each record follows the same schema as a real submission, with one required distinction: `submission_id` must start with `bootstrap:`.

### Bootstrap for campaign scope (most common)

For campaigns using the default `campaign` scope, pass `campaign_id` in each bootstrap record so the pre-loaded records are visible only to the correct campaign:

```json
POST /v1/bootstrap
Content-Type: application/json

{
  "records": [
    {
      "task_id":          "task-cipherowl-q2",
      "sample_key":       "eth:0xabc123",
      "submission_id":    "bootstrap:cipherowl-known-0xabc123",
      "payload_type":     "structured",
      "match_key":        "mk:94866cf64eebbd9864c2b5de6a2ca1ad9a2366bf93c29205db600ac0ec4e4b76",
      "submitted_at":     "2025-11-01T00:00:00Z",
      "uniqueness_scope": "campaign",
      "campaign_id":      "cipherowl-iran-cex-q2"
    }
  ]
}
```

`campaign_id` is **required** when `uniqueness_scope = "campaign"` — the request is rejected (HTTP 422) if it is absent. The bootstrapped record is then visible only to evaluate calls that use the same `campaign_id`.

### Bootstrap for frontier scope

For domain-wide dedup, use `frontier` scope without a `campaign_id`. Optionally tag the record to one or more named frontier categories via `frontier_ids` — the frontier must already exist before being referenced.

**Step 1 — create the frontier category (once per domain):**

```bash
POST /v1/frontiers
{
  "frontier_id":  "robotics-motion-capture",
  "name":         "Robotics Motion Capture",
  "description":  "Video recordings of robotic arm motion across all campaigns"
}
```

**Step 2 — bootstrap records with frontier tags:**

```json
{
  "records": [
    {
      "task_id":          "task-frontier-robotics",
      "sample_key":       "roboarm1k:vid-042",
      "submission_id":    "bootstrap:roboarm1k-vid-042",
      "payload_type":     "structured",
      "match_key":        "mk:phash-roboarm1k-042",
      "submitted_at":     "2025-11-01T00:00:00Z",
      "uniqueness_scope": "frontier",
      "frontier_ids":     ["robotics-motion-capture"]
    }
  ]
}
```

Response:

```json
{"inserted": 1, "skipped": 0}
```

A record can belong to multiple frontiers — pass all IDs in `frontier_ids`. Omit the field entirely if the record does not belong to any named category. Tags are idempotent: re-bootstrapping the same `submission_id` with the same `frontier_ids` writes nothing new.

---

## Idempotency

Bootstrap writes are idempotent by `submission_id`. Re-running the same bootstrap job (e.g. after a failure) produces no duplicates:

```json
// First run
POST /v1/bootstrap  →  {"inserted": 1000, "skipped": 0}

// Re-run (all already exist)
POST /v1/bootstrap  →  {"inserted": 0, "skipped": 1000}
```

This makes it safe to run bootstrap jobs in CI or as a pre-flight step without worrying about state.

---

## How it affects evaluate

Once a bootstrapped record exists, any submission whose match key matches it receives `attempt_index = 2` — not 1 — because the bootstrapped record counts as the first prior observation.

**Campaign-scoped example:**

```
Pre-flight: bootstrap "cipherowl-iran-cex-q2" / 0xabc123  →  attempt_records written (campaign_id="cipherowl-iran-cex-q2")

Campaign open:
  Fraudulent submission (same wallet) → match found → attempt_index: 2
                                         nearest_prior: [{submission_id: "bootstrap:cipherowl-known-0xabc123", similarity: 1.0}]
```

Your downstream systems can inspect `nearest_prior[0].submission_id` — if it starts with `bootstrap:`, the submission is a copy of a known pre-existing record.

**Cross-campaign isolation:** a bootstrap record with `campaign_id = "campaign-A"` is *not* visible to evaluate calls using `campaign_id = "campaign-B"`. Each campaign sees only its own bootstrapped data.

---

## Bulk bootstrap from a file

Use the CLI to bootstrap from a JSON file:

```bash
attempt-index bootstrap records.json
```

The file can be either an array of records or a `{"records": [...]}` wrapper:

```json
[
  {
    "task_id": "task-cipherowl-q2",
    "sample_key": "eth:0xabc001",
    "submission_id": "bootstrap:cipherowl-known-0xabc001",
    "payload_type": "structured",
    "match_key": "mk:abc123...",
    "submitted_at": "2025-11-01T00:00:00Z",
    "uniqueness_scope": "campaign",
    "campaign_id": "cipherowl-iran-cex-q2"
  },
  {
    "task_id": "task-cipherowl-q2",
    "sample_key": "eth:0xabc002",
    "submission_id": "bootstrap:cipherowl-known-0xabc002",
    "payload_type": "structured",
    "match_key": "mk:def456...",
    "submitted_at": "2025-11-01T00:00:00Z",
    "uniqueness_scope": "campaign",
    "campaign_id": "cipherowl-iran-cex-q2"
  }
]
```

```bash
attempt-index bootstrap --file ./known-wallets.json --url http://localhost:8000
# {"inserted": 2, "skipped": 0}
```

For large datasets (thousands of records), split into batches of 500–1000 and call bootstrap multiple times. Idempotency makes this safe.

---

## Computing match_key for bootstrap records

Bootstrap records require a pre-computed `match_key` (format: `mk:{sha256hex}`). The key must be computed using exactly the same `canonical_fields` and value order that the campaign's evaluate calls will use.

The hash is computed over **field values only** (not field names), joined with `|`, lowercased, and trimmed:

```python
import hashlib

def compute_match_key(canonical_values: list[str]) -> str:
    raw = "|".join(v.strip().lower() for v in canonical_values)
    hex_digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"mk:{hex_digest}"

# canonical_fields = ["address", "network"]
key = compute_match_key(["0xabc123", "ethereum"])
# → "mk:94866cf64eebbd..."
```

If you use `canonical_fields = ["address", "network"]` in evaluate, use the same order in the bootstrap pre-computation. Value format must also match — `"ethereum"` and `"eth-mainnet"` produce different hashes.

---

## submission_id naming convention

The `bootstrap:` prefix is required and enforced. Beyond that, use a naming scheme that makes the origin traceable in audits:

| Source | Recommended pattern |
|--------|-------------------|
| Public dataset | `bootstrap:{dataset-name}-{item-id}` |
| Prior Humanbased campaign | `bootstrap:campaign-{campaign-id}-{submission-id}` |
| Customer-provided historical data | `bootstrap:customer-{customer-id}-{record-id}` |
| Migration from legacy system | `bootstrap:migration-{legacy-id}` |

Consistent naming makes it easy to identify bootstrapped records in `nearest_prior` responses and anti-fraud signals.

---

## Security note

Bootstrap records carry no reward, quality, or acceptance state. They exist solely to anchor the attempt index for future submissions. A downstream system that sees `nearest_prior[0].submission_id` starting with `bootstrap:` knows the new submission matched a known pre-existing record and can apply whatever policy is appropriate (e.g. zero reward, fraud flag, rejection).

AttemptIndex makes no policy decision — it only provides the signal.
