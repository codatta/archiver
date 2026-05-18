# Campaign Configuration

AttemptIndex is configuration-driven. Every call to `POST /v1/evaluate` carries its own uniqueness rules — there is no global config file. This means each campaign can define exactly how uniqueness is determined.

The configuration lives in four fields of the evaluate request: `matcher_config`, `uniqueness_scope`, `campaign_id`, and `max_attempts`.

---

## Configuration fields

| Field | Where it lives | What it controls |
|-------|---------------|-----------------|
| `matcher_config.methodology` | request body | Which matching algorithm to use |
| `matcher_config.adapter_config.canonical_fields` | request body | Which payload fields jointly form the unique identifier |
| `uniqueness_scope` | request body | How wide to search for prior matches (default: `"campaign"`) |
| `campaign_id` | request body | Isolates `campaign`-scoped attempt counts to one campaign; required when scope is `campaign` |
| `max_attempts` | request body | Collection ceiling per sample |
| `uniqueness_version` | request body | Version string for the uniqueness config — increment when rules change |

---

## Defining which fields form the unique identifier

`canonical_fields` is the primary configuration knob for structured data tasks. It tells AttemptIndex which fields from the submitted JSON payload, when combined, identify a unique *subject*.

```json
"matcher_config": {
  "methodology": "hash",
  "adapter_config": {
    "canonical_fields": ["address", "network"]
  }
}
```

### One field — single-attribute uniqueness

```json
"canonical_fields": ["image_id"]
```

Two contributors annotating `image_id: "img-042"` with different labels → counted as the same subject.

### Two fields — composite uniqueness

```json
"canonical_fields": ["address", "network"]
```

`0xabc` on `ethereum` and `0xabc` on `arbitrum` → different match keys → tracked independently.

### Three or more fields

```json
"canonical_fields": ["country_code", "company_name", "registration_year"]
```

All three must match for submissions to be counted as the same subject.

### Rules

- **Define at task creation.** Never change `canonical_fields` mid-campaign. Changing the list invalidates all prior match keys — treat it as a schema migration and increment `uniqueness_version`.
- **Subject fields only.** Do not include output fields (labels, scores, confidence) — those differ between contributors by design.
- **Order matters.** `["address", "network"]` and `["network", "address"]` produce different match keys. Pick an order and keep it.

---

## Scope configuration

`uniqueness_scope` determines the search boundary for prior matches:

| Scope | Isolation key | Prior records searched | Typical use |
|-------|--------------|----------------------|-------------|
| `campaign` | `campaign_id` | All records with the same `campaign_id` + `sample_key` | **Default** — per-campaign dedup with no cross-campaign bleed |
| `task` | `task_id` | Records with the same `task_id` + `sample_key` | Independent attempt budget per task |
| `frontier` | *(none — domain-wide pool)* | All frontier-scoped records with the same `sample_key` | Cross-campaign dedup within a domain |
| `global` | *(none)* | All records with the same `sample_key` | Platform-wide dedup; use sparingly |

### campaign scope — isolation by campaign_id

Campaign scope is the default and the recommended choice for most annotation campaigns. It uses `campaign_id` as the isolation key so that two campaigns annotating the same data never inflate each other's attempt counts.

```json
{
  "uniqueness_scope": "campaign",
  "campaign_id": "cipherowl-iran-cex-q2",
  "max_attempts": 3
}
```

`campaign_id` must be a stable, consistent string for all submissions in the same campaign. A good default is the campaign's database ID. `campaign_id` is required for campaign scope — the request is rejected if it is absent.

### task scope — per-task isolation

```json
{
  "uniqueness_scope": "task",
  "max_attempts": 3
}
```

Records are isolated by `task_id`. Use this when tasks within the same campaign have independent attempt budgets, or when a `campaign_id` is not available.

### frontier scope — domain-wide dedup

```json
{
  "uniqueness_scope": "frontier",
  "max_attempts": 1
}
```

If the same video appears anywhere across all robotics campaigns, it is flagged on the second submission regardless of which campaign it came from. Use with [bootstrapping](./bootstrap.md) to pre-register known public datasets.

---

## Storing per-campaign configuration

AttemptIndex does not store campaign configuration itself — that is the Contribution Pipeline's responsibility. The recommended pattern is to store campaign config in your task/campaign table and inject it into each evaluate call:

```python
# Pseudocode in the Contribution Pipeline
campaign = db.get_campaign(campaign_id)

response = requests.post("http://attempt-index/v1/evaluate", json={
    "task_id":          campaign.task_id,
    "sample_key":       submission.sample_key,
    "submission_id":    submission.id,
    "payload_type":     campaign.payload_type,
    "submitted_at":     submission.created_at.isoformat(),
    "uniqueness_scope": campaign.uniqueness_scope,
    "campaign_id":      campaign.id,          # always pass the campaign's own ID
    "max_attempts":     campaign.max_attempts,
    "matcher_config": {
        "methodology":    campaign.matcher_methodology,
        "adapter_config": {
            "canonical_fields": campaign.canonical_fields
        }
    },
    "payload":          submission.payload,
    "contributor_uid":  submission.contributor_id,
})
```

### Example campaign config table

```sql
CREATE TABLE campaigns (
    id                  text PRIMARY KEY,
    task_id             text NOT NULL,
    payload_type        text NOT NULL,
    uniqueness_scope    text NOT NULL DEFAULT 'campaign',
    max_attempts        int  NOT NULL DEFAULT 3,
    matcher_methodology text NOT NULL DEFAULT 'hash',
    canonical_fields    text[],         -- e.g. ARRAY['address', 'network']
    uniqueness_version  text NOT NULL DEFAULT 'v1'
    -- campaign.id is passed as campaign_id in every evaluate call
);
```

---

## Versioning configuration changes

If you must change `canonical_fields` after a campaign has received submissions, increment `uniqueness_version` to signal that the old match keys are no longer comparable:

```json
// Original config
{"canonical_fields": ["address"], "uniqueness_version": "v1"}

// After adding "network" to canonical_fields
{"canonical_fields": ["address", "network"], "uniqueness_version": "v2"}
```

Old `v1` records and new `v2` records will never match each other — they use different hash inputs. The version is stored on every `attempt_record` row, so you can query and audit by version.

---

## Quick reference: common campaign patterns

### Annotation campaign — 3 independent labels (default)
```json
{
  "uniqueness_scope": "campaign",
  "campaign_id": "my-annotation-campaign-001",
  "max_attempts": 3,
  "matcher_config": {
    "methodology": "hash",
    "adapter_config": {"canonical_fields": ["subject_id"]}
  }
}
```

### Per-task independent budget
```json
{
  "uniqueness_scope": "task",
  "max_attempts": 3,
  "matcher_config": {
    "methodology": "hash",
    "adapter_config": {"canonical_fields": ["subject_id"]}
  }
}
```

### Data supply campaign — 1 original recording per session
```json
{
  "uniqueness_scope": "campaign",
  "campaign_id": "data-supply-q2-2026",
  "max_attempts": 1,
  "matcher_config": {
    "methodology": "hash"
  }
}
```
`sample_key` is the pre-assigned session ID (never derived from the recording content).

### Frontier dedup — detect public dataset copies
```json
{
  "uniqueness_scope": "frontier",
  "max_attempts": 5,
  "matcher_config": {
    "methodology": "hash"
  }
}
```
Bootstrap the known public dataset first — see [Bootstrapping Known Datasets](./bootstrap.md).
