# Evaluating Submissions

`POST /v1/evaluate` is the core endpoint. Call it once per incoming submission, after your own gating checks, before creating an instance record.

---

## Request

```json
POST /v1/evaluate
Content-Type: application/json

{
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
    "adapter_config": {
      "canonical_fields": ["address", "network"]
    }
  },
  "payload": {
    "address": "0xabc123",
    "network": "ethereum",
    "label":   "CEX",
    "confidence": 0.9
  }
}
```

### Required fields

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Identifies the labeling task |
| `sample_key` | string | Canonical identifier of the item being submitted on |
| `submission_id` | string | Globally unique ID for this submission |
| `payload_type` | `structured` \| `text` | Payload modality (V0 supports these two) |
| `submitted_at` | ISO 8601 | Timestamp used for ordering prior records |
| `max_attempts` | int ≥ 1 | Collection ceiling — when reached, `cut_off_reached = true` |

### Optional fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `uniqueness_scope` | `task` \| `campaign` \| `frontier` \| `global` | `"campaign"` | How wide to search for prior matches |
| `campaign_id` | string | — | **Required when `uniqueness_scope = "campaign"`**. Isolates attempt counts to a single campaign. |
| `contributor_uid` | string | — | Identifier of the contributor; stored for audit, not used in matching |
| `uniqueness_version` | string | `"v1"` | Version tag for the uniqueness config; increment when `canonical_fields` change |

### Providing the payload

You have two options:

**Option A — raw payload + `matcher_config`** (AttemptIndex computes the match key)

```json
{
  "payload": {"address": "0xabc", "network": "ethereum", "label": "CEX"},
  "matcher_config": {
    "methodology": "hash",
    "adapter_config": {"canonical_fields": ["address", "network"]}
  }
}
```

**Option B — pre-computed `match_key`** (your ingestion layer already computed it)

```json
{
  "match_key": "mk:94866cf64eebbd9864c2b5de6a2ca1ad9a2366bf93c29205db600ac0ec4e4b76"
}
```

At least one of `payload` or `match_key` must be present. If both are provided, `match_key` takes precedence.

---

## Response

```json
{
  "attempt_index":    2,
  "cut_off_reached":  false,
  "cut_off_limit":    3,
  "nearest_prior": [
    {
      "submission_id": "sub-001",
      "match_key":     "mk:94866cf64eebbd...",
      "similarity":    1.0,
      "submitted_at":  "2026-04-27T10:00:00Z",
      "state":         null
    }
  ],
  "uniqueness_scope":   "campaign",
  "uniqueness_version": "v1",
  "processing_stage":   "complete",
  "match_key":          "mk:94866cf64eebbd...",
  "error":              null
}
```

| Field | Meaning |
|-------|---------|
| `attempt_index` | 1 = no prior match found. N = N−1 prior matching submissions exist |
| `cut_off_reached` | `true` when `attempt_index >= max_attempts` |
| `cut_off_limit` | The `max_attempts` value echoed back |
| `nearest_prior` | The most recent prior matching record within the scope. Empty list if this is attempt 1 |
| `match_key` | The match key used for this evaluation (computed or passed through) |
| `error` | Non-null if the service hit an internal error (see [Fail-open](#fail-open)) |

`nearest_prior` is informational only. Your pipeline decides what to do with it.

---

## Uniqueness scope

`uniqueness_scope` controls how wide the search for prior submissions is:

| Scope | Isolation key | Searches | Use when |
|-------|--------------|----------|----------|
| `campaign` | `campaign_id` | All records with the same `campaign_id` and `sample_key` | Default — per-campaign dedup; prevents cross-campaign bleed |
| `task` | `task_id` | Within the same `task_id` and `sample_key` | When each task needs its own independent attempt budget |
| `frontier` | Platform frontier pool | All frontier-scoped records with the same `sample_key` | Domain-wide dedup (e.g. all robotics campaigns) |
| `global` | None | Platform-wide, same `sample_key` | Maximum dedup; use sparingly |

### campaign scope (default)

```json
{
  "uniqueness_scope": "campaign",
  "campaign_id": "cipherowl-iran-cex-q2",
  "max_attempts": 3
}
```

Records from `campaign_id = "cipherowl-iran-cex-q2"` are counted together. Records from any other campaign are invisible — no bleed. `campaign_id` is **required** for this scope; the request is rejected (HTTP 422) if it is absent.

### task scope

```json
{
  "uniqueness_scope": "task",
  "max_attempts": 3
}
```

Attempt counts are isolated to `task_id`. Useful when tasks within the same campaign have independent budgets, or when `campaign_id` is unavailable.

---

## Idempotency

Calling `evaluate` twice with the same `submission_id` is safe. The second call returns the same `attempt_index` without writing a new record.

```bash
# First call
curl -X POST /v1/evaluate -d '{"submission_id": "sub-001", ...}'
# → attempt_index: 1

# Identical second call
curl -X POST /v1/evaluate -d '{"submission_id": "sub-001", ...}'
# → attempt_index: 1  (no duplicate written)
```

---

## Fail-open

AttemptIndex never blocks the submission flow. If any internal error occurs (database timeout, unexpected exception), the response is still HTTP 200:

```json
{
  "attempt_index":  1,
  "cut_off_reached": false,
  "cut_off_limit":  3,
  "nearest_prior":  [],
  "processing_stage": "partial",
  "error": "connection timeout"
}
```

Your pipeline should always proceed after receiving this response. The `error` field being non-null is your signal to log and alert, but not to block.

---

## CLI shortcut

```bash
attempt-index evaluate --json '{
  "task_id": "cipherowl-demo",
  "sample_key": "eth:0xabc123",
  "submission_id": "sub-test-1",
  "payload_type": "structured",
  "submitted_at": "2026-04-27T10:00:00Z",
  "uniqueness_scope": "campaign",
  "campaign_id": "cipherowl-demo",
  "max_attempts": 3,
  "matcher_config": {"methodology": "hash", "adapter_config": {"canonical_fields": ["address","network"]}},
  "payload": {"address": "0xabc123", "network": "ethereum", "label": "CEX"}
}'
```

---

## See also

- [Canonical fields for structured data →](./canonical-fields.md)
- [Campaign configuration →](./campaign-configuration.md)
- [Bootstrapping known datasets →](./bootstrap.md)
- [Glossary →](./glossary.md)
