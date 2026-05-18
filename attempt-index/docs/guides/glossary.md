# Terminology Glossary

Quick reference for terms used across AttemptIndex documentation, API contracts, and the wider Humanbased platform.

---

## Concept map

The diagram below shows how a submission flows through AttemptIndex and which terms apply at each step.

```
Submission payload
┌──────────────────────────────────────────┐
│  wallet_address: "0xABC"                 │
│  network:        "ethereum"              │◄── only these fields matter for identity
│  label:          "CEX"                   │    ("label" is ignored — not in canonical_fields)
│  contributor_uid: "alice"                │
└──────────────────────────────────────────┘
          │
          │  canonical_fields = ["wallet_address", "network"]
          │  (config; defines which fields form the subject identity)
          ▼
  extract + lowercase + join
  ──────────────────────────
  raw = "0xabc|ethereum"
          │
          │  SHA-256
          ▼
  match_key = "mk:94866cf6..."   ◄── subject identity; same payload → same match_key
          │
          │  + sample_key = "eth:0xABC"     (caller-assigned label for the item)
          │  + uniqueness_scope = "campaign" (search boundary)
          │  + campaign_id = "q2-2026"       (isolation key within campaign scope)
          ▼
  query attempt_records WHERE
    campaign_id = "q2-2026"
    AND sample_key = "eth:0xABC"
    AND match_key  = "mk:94866cf6..."
          │
          │  found N prior records
          ▼
  attempt_index = N + 1
  cut_off_reached = (attempt_index >= max_attempts)
```

**Key insight — `sample_key` vs `match_key`:**
- `sample_key` is what the *caller* calls the item. It scopes the DB index but is not part of subject identity.
- `match_key` is what AttemptIndex *computes* from the payload. Two submissions with the same `match_key` are about the same subject regardless of any other fields.

**Key insight — `subject` vs `submission`:**
- A *subject* is the real-world entity (e.g. the wallet `0xABC` on Ethereum). It maps 1-to-1 with a `match_key`.
- A *submission* is one contributor's attempt to label that subject. Many submissions can share the same subject — that's what `attempt_index` counts.

---

## Core concepts

### attempt_index
A monotonically increasing integer assigned to each submission for the same *subject* (identified by `match_key`) within the configured scope. The first submission gets `attempt_index = 1`, the second gets `2`, and so on. AttemptIndex never resets or skips — it only counts.

### subject
The real-world entity being labeled or annotated. A subject is identified by the combination of canonical field values extracted from the payload. Two submissions refer to the same subject if and only if their `match_key` values are equal. Example: in a wallet annotation task, the subject is the wallet address (and optionally the network).

### sample_key
A caller-assigned string that names the item being submitted. It is used alongside `match_key` to scope queries. It does not need to be globally unique — it just needs to be consistent for the same item across all submissions in a campaign. Example: `"eth:0xabc123"`.

### match_key
The computed identifier that AttemptIndex uses to determine whether two submissions refer to the same subject. In V0 this is a SHA-256 hash of the canonical field values (`mk:{64-char hex}`). Only values are hashed — field names are not part of the hash. Stored in the `match_key` column of `attempt_records` and returned in both the top-level response and each `nearest_prior` entry.

### canonical_fields
The ordered list of payload field names whose values jointly form the subject identity. Example: `["wallet_address", "network"]` means two submissions are about the same subject only if both the wallet address and the network match exactly. Field names do not affect the hash — only the extracted values do, in the specified order. Defined in `matcher_config.adapter_config.canonical_fields`.

---

## Scope and isolation

### uniqueness_scope
Determines how widely AttemptIndex searches for prior matching submissions when assigning `attempt_index`. Four levels:

| Scope | Isolated by | Typical use |
|-------|------------|-------------|
| `task` | `task_id` | A single labeling task with its own attempt budget |
| `campaign` | `campaign_id` | All tasks within one campaign share attempt counts |
| `frontier` | Platform-wide frontier pool | Cross-campaign dedup within a domain |
| `global` | Platform-wide all records | Broadest dedup; use sparingly |

Default: `campaign`.

### campaign_id
An opaque string that identifies a campaign for the purpose of `campaign`-scoped dedup. Required whenever `uniqueness_scope = "campaign"`. Records written under the same `campaign_id` are counted together; records under different `campaign_id` values are counted independently. It is the caller's responsibility to pass a stable, consistent `campaign_id` for all submissions belonging to the same campaign.

### task_id
An opaque string that identifies a specific labeling task. Used as the isolation key for `task`-scoped queries. A campaign typically contains one or more tasks.

---

## Limits and control flow

### max_attempts
The collection ceiling — the maximum number of accepted attempts for a given subject within the configured scope. When `attempt_index` reaches `max_attempts`, `cut_off_reached` is set to `true`. AttemptIndex does not block further submissions; the caller (Contribution Pipeline) is responsible for gating on this flag.

### cut_off_reached
Boolean flag in the evaluate response. `true` when `attempt_index >= max_attempts`. This is advisory: AttemptIndex always writes the record regardless. The Contribution Pipeline should cache this flag and gate further submissions before calling AttemptIndex again.

### cut_off_limit
The value of `max_attempts` echoed back in the response, so callers do not need to re-fetch campaign config to interpret `cut_off_reached`.

---

## Submission lifecycle

### submission_id
A caller-assigned unique identifier for a single submission. AttemptIndex uses it to guarantee idempotency: calling evaluate twice with the same `submission_id` always returns the same `attempt_index`, with no new record written on the second call. Must be globally unique within the platform.

### contributor_uid
Optional identifier for the contributor (human labeler or automated agent) that made the submission. Stored for audit purposes; not used in matching or counting logic.

### submitted_at
The timestamp of the original submission as recorded by the caller. Stored as-is. Used only for ordering `nearest_prior` results (oldest first).

### payload_type
The modality of the submitted content. V0 supports `structured` and `text`. Future versions will add `image`, `video`, and `audio`.

### nearest_prior
The single most-recent prior record (by `submitted_at`) that matched the same subject in the same scope. Returned in the evaluate response. Useful for the Contribution Pipeline to identify which earlier submission is the closest duplicate.

---

## Pre-loading

### bootstrap
The process of pre-registering known records in AttemptIndex before a campaign opens. Bootstrap records are inserted via `POST /v1/bootstrap` and are indistinguishable from live records at query time — they count toward `attempt_index` like any other record. Their `submission_id` must start with `bootstrap:`.

### bootstrap record
A record written via the bootstrap API. It represents a previously known item (e.g. a public dataset, a prior campaign's output, or a customer-provided dataset) that should count against the attempt ceiling for any future submission about the same subject.

---

## Reliability

### fail-open
AttemptIndex's error handling policy: any internal failure (database timeout, matcher exception) returns `attempt_index = 1` with an `error` field at HTTP 200. The submission flow is never blocked by an AttemptIndex failure.

### idempotency
The guarantee that submitting the same `submission_id` more than once produces the same response and leaves the database unchanged after the first call. Implemented by storing `attempt_index` on write and reconstructing the response from the stored record on repeat calls.

---

## Versioning

### uniqueness_version
A string (e.g. `"v1"`) that tags the uniqueness configuration in use at the time of submission. Increment when `canonical_fields` or the matching methodology changes mid-campaign. Old records and new records with different `uniqueness_version` values will not match each other.

### methodology
The matching algorithm. V0 only: `"hash"` (SHA-256). Future: `"perceptual"` (images), `"embedding"` (semantic text), `"agent"` (AI-delegated). Specified in `matcher_config.methodology`.
