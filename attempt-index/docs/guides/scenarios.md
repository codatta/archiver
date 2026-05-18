# Scenarios Walkthrough

This guide walks through three concrete scenarios that demonstrate how AttemptIndex behaves in practice. Each scenario uses the CipherOwl wallet annotation use-case as a running example: multiple contributors independently labeling blockchain wallet addresses.

Run all three scenarios live against the service:

```bash
python scripts/demo_scenarios.py
```

---

## Background: how uniqueness works

Before reading the scenarios, understand two key concepts:

### match_key — what makes two submissions "the same"

AttemptIndex does not compare raw payloads. It extracts the fields named in `canonical_fields`, joins their values with `|`, lowercases and trims each value, and computes a SHA-256 hash:

```
canonical_fields = ["wallet_address", "network"]
payload          = {"wallet_address": "0xABC", "network": "Ethereum", "label": "CEX"}

→ raw   = "0xabc|ethereum"          (values only, lowercased)
→ hash  = sha256("0xabc|ethereum")
→ match_key = "mk:{64-char hex}"
```

Two submissions produce the **same** `match_key` when their canonical field values are identical — regardless of any other fields (labels, confidence scores, contributor IDs). Two submissions produce **different** `match_key` values when any canonical field differs, even for the same wallet address on a different network.

### attempt_index — what it means

`attempt_index = N` means there are exactly `N-1` prior records with the same `match_key` in the configured scope. The first submission for a given subject always gets `attempt_index = 1`.

---

## Scenario 1 — Single field, no cut-off, sequence tracking

**Use case:** Five contributors independently label the same wallet. Verify that AttemptIndex tracks the sequence correctly and never blocks any submission.

**Configuration:**

```json
{
  "canonical_fields": ["wallet_address"],
  "uniqueness_scope": "task",
  "max_attempts": 9999
}
```

`max_attempts = 9999` is a practical stand-in for "no cut-off." Every unique `submission_id` is accepted.

**What happens:**

| Step | Contributor | wallet_address | label | attempt_index | cut_off_reached |
|------|-------------|----------------|-------|---------------|-----------------|
| 1 | Contributor 1 | 0x12dfa3334 | label-variant-1 | **1** | false |
| 2 | Contributor 2 | 0x12dfa3334 | label-variant-2 | **2** | false |
| 3 | Contributor 3 | 0x12dfa3334 | label-variant-3 | **3** | false |
| 4 | Contributor 4 | 0x12dfa3334 | label-variant-4 | **4** | false |
| 5 | Contributor 5 | 0x12dfa3334 | label-variant-5 | **5** | false |

**Key observations:**

1. The `match_key` is identical for all five submissions — only `wallet_address` was hashed, and all five payloads share the same value `"0x12dfa3334"`. The `label` field is not in `canonical_fields` and has no effect.

2. `cut_off_reached` stays `false` throughout because `max_attempts = 9999`.

3. AttemptIndex never rejects a submission. It counts and reports — policy decisions belong to the caller.

**What to look for in the response:**

```json
{
  "attempt_index": 3,
  "cut_off_reached": false,
  "cut_off_limit": 9999,
  "nearest_prior": [{ "submission_id": "test:demo:...", "similarity": 1.0 }],
  "match_key": "mk:b57b3c8e..."
}
```

`nearest_prior` is empty on the first submission (no prior record exists). From submission 2 onward, it contains the most recent prior record with a `similarity` of `1.0` (exact hash match).

---

## Scenario 2 — Composite fields, cross-network independence

**Use case:** The same wallet address `0x12dfa3334` appears on both `eth-mainnet` and `polygon`. Verify that AttemptIndex tracks them as independent subjects when `network` is included in `canonical_fields`.

**Configuration:**

```json
{
  "canonical_fields": ["wallet_address", "network"],
  "uniqueness_scope": "task",
  "max_attempts": 9999
}
```

**What happens:**

```
Submission A1: wallet=0x12dfa3334, network=eth-mainnet
→ raw = "0x12dfa3334|eth-mainnet"
→ match_key = "mk:59166ab9..."    attempt_index = 1

Submission A2: wallet=0x12dfa3334, network=polygon
→ raw = "0x12dfa3334|polygon"
→ match_key = "mk:2631a24d..."    attempt_index = 1   ← DIFFERENT match_key

Submission A3: wallet=0x12dfa3334, network=eth-mainnet  (second contributor)
→ raw = "0x12dfa3334|eth-mainnet"
→ match_key = "mk:59166ab9..."    attempt_index = 2   ← increments eth-mainnet count
```

**Key observations:**

1. `eth-mainnet` and `polygon` produce **different** `match_key` values because `network` is part of `canonical_fields`. They are counted as distinct subjects.

2. Submission A2 (`polygon`) receives `attempt_index = 1` — it is independent, not affected by the prior `eth-mainnet` record.

3. Submission A3 (`eth-mainnet`) finds A1 as its `nearest_prior` and receives `attempt_index = 2`.

**Choosing canonical fields:**

- Use `["wallet_address"]` when the same wallet on any network counts as the same subject.
- Use `["wallet_address", "network"]` when the same wallet on different networks must be tracked independently.
- The choice must be made at campaign launch and must never change mid-campaign (see [Campaign Configuration → versioning](./campaign-configuration.md#versioning-configuration-changes)).

**Full response for submission A3:**

```json
{
  "attempt_index": 2,
  "cut_off_reached": false,
  "cut_off_limit": 9999,
  "nearest_prior": [
    {
      "submission_id": "test:demo:e6c6597c-...",
      "match_key": "mk:59166ab9...",
      "similarity": 1.0,
      "submitted_at": "2026-04-27T08:49:21Z",
      "state": null
    }
  ],
  "match_key": "mk:59166ab9...",
  "error": null
}
```

---

## Scenario 3 — Cut-off threshold, flood behaviour, and pipeline responsibilities

**Use case:** A campaign allows a maximum of 3 labels per wallet. Understand what happens when the ceiling is reached, and what happens if submissions continue to arrive after cut-off.

**Configuration:**

```json
{
  "canonical_fields": ["wallet_address", "network"],
  "uniqueness_scope": "task",
  "max_attempts": 3
}
```

### Part A — Normal flow up to the ceiling

| Submission | attempt_index | cut_off_reached |
|------------|---------------|-----------------|
| 1 | 1 | false |
| 2 | 2 | false |
| 3 | **3** | **true** ← ceiling reached |

When `attempt_index` equals `max_attempts`, `cut_off_reached` flips to `true`. The full response at cut-off:

```json
{
  "attempt_index": 3,
  "cut_off_reached": true,
  "cut_off_limit": 3,
  "nearest_prior": [{ "submission_id": "test:demo:...", "similarity": 1.0 }],
  "match_key": "mk:a2436775...",
  "error": null
}
```

**What the Contribution Pipeline must do here:** cache `cut_off_reached = true` for this `(campaign_id, sample_key)` pair and gate all further submissions before calling AttemptIndex again. AttemptIndex itself does not block.

### Part B — Flood behaviour (advisory-only cut-off)

If the pipeline does *not* gate and continues to call AttemptIndex after cut-off:

| Flood submission | attempt_index | cut_off_reached |
|------------------|---------------|-----------------|
| 4 | 4 | true |
| 5 | 5 | true |
| 6 | 6 | true |
| 7 | 7 | true |
| 8 | 8 | true |

**`cut_off_reached = true` is advisory.** AttemptIndex writes every unique `submission_id` to `attempt_records` regardless of the ceiling. This is by design — AttemptIndex counts, it never decides.

### Known limitations under flooding

| # | Limitation | Mitigation |
|---|-----------|-----------|
| 1 | AttemptIndex does not block flood submissions | The **Contribution Pipeline** must cache `cut_off_reached = true` on first detection and gate all subsequent submissions before calling evaluate |
| 2 | `query_prior_matches` does a full `SELECT *` scan. After N flood submissions, each call transfers N rows of data — O(N) per call | Fast-mode `SELECT COUNT(*)` would reduce overhead, but cannot prevent the flood (documented in `prd.md` backlog) |
| 3 | Each flood submission creates a permanent row in `attempt_records` | Prevent at the pipeline layer; rows cannot be cheaply undone |

### The correct pipeline gate

```
Contribution Pipeline intake:
  ├── Gate 1: Has consensus already been reached?  → reject before AttemptIndex
  ├── Gate 2: Is cut_off cached for this sample?   → reject before AttemptIndex
  └── Gate 3: Call AttemptIndex.evaluate()
                      ↓
              cut_off_reached = true → cache it, reject caller
              cut_off_reached = false → proceed to create instance record
```

The pipeline caches the `cut_off_reached` flag per `(campaign_id, sample_key)`. Once set, no further evaluate calls are made for that sample in that campaign. AttemptIndex never needs to see flood traffic.

---

## Summary: choosing the right configuration

| Goal | canonical_fields | uniqueness_scope | campaign_id | max_attempts |
|------|-----------------|-----------------|-------------|--------------|
| Track same wallet, any network | `["wallet_address"]` | `campaign` | your campaign ID | desired ceiling |
| Track wallet per network | `["wallet_address", "network"]` | `campaign` | your campaign ID | desired ceiling |
| Unlimited collection | any | `campaign` | your campaign ID | very large (e.g. 9999) |
| Cross-campaign dedup | any | `frontier` | not required | desired ceiling |
| Platform-wide dedup | any | `global` | not required | desired ceiling |

---

## Running the scenarios yourself

```bash
# From the project root with the venv active
python scripts/demo_scenarios.py
```

The script uses FastAPI's `TestClient` — no running server is needed. It connects to the live Supabase staging DB and cleans up all `test:demo:*` records automatically on completion.

See [Evaluate API reference →](./evaluate.md) and [Campaign Configuration →](./campaign-configuration.md) for the full request/response contract.
