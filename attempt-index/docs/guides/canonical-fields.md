# Canonical Fields — Structured Data Uniqueness

When contributors submit structured JSON payloads (annotations, labels, classifications), not every field should count towards uniqueness. The label a contributor assigns is the *output* of the task — it differs between contributors by design. Only the *subject* being labeled should define uniqueness.

`canonical_fields` lets you specify exactly which fields determine whether two submissions are targeting the same subject.

---

## The problem it solves

Consider a wallet labeling task. Contributor A and Contributor B both annotate wallet `0xabc`:

```json
// Contributor A
{"address": "0xabc", "network": "ethereum", "label": "CEX", "confidence": 0.9}

// Contributor B
{"address": "0xabc", "network": "ethereum", "label": "DEX", "confidence": 0.6}
```

These are two independent attempts at the *same subject*. They should be counted as attempt 1 and attempt 2 — and the ceiling (e.g. `max_attempts = 3`) should apply across both.

If you hashed the full payload, Contributor A and B would produce *different* match keys (because `label` and `confidence` differ), and each would appear as a fresh first submission. The dedup would fail entirely.

`canonical_fields` solves this: only `["address", "network"]` are extracted and hashed. The `label` and `confidence` fields are ignored for uniqueness purposes.

---

## Configuration

Set `canonical_fields` in `matcher_config.adapter_config`:

```json
"matcher_config": {
  "methodology": "hash",
  "adapter_config": {
    "canonical_fields": ["address", "network"]
  }
}
```

### How the match key is computed

1. Extract `canonical_fields` values from the payload **in the defined order**
2. Normalize each value: trim whitespace, lowercase
3. Join with `|`
4. SHA-256 hash → `mk:{hex_digest}`

For `{"address": "0xABC", "network": "Ethereum"}` with `canonical_fields = ["address", "network"]`:

```
"0xabc" + "|" + "ethereum"  →  SHA-256  →  mk:94866cf6...
```

Any two payloads with the same `address` and `network` — regardless of `label`, `confidence`, or any other field — produce the same match key.

---

## Worked example: CipherOwl wallet annotation

**Task setup:**

```json
{
  "task_id":          "cipherowl-iran-cex-q2",
  "uniqueness_scope": "task",
  "max_attempts":     3,
  "matcher_config": {
    "methodology": "hash",
    "adapter_config": {
      "canonical_fields": ["address", "network"]
    }
  }
}
```

**Three contributors label the same wallet:**

```bash
# Contributor A — first observation
POST /v1/evaluate
payload: {"address": "0xabc", "network": "ethereum", "label": "CEX", "confidence": 0.9}
→ attempt_index: 1, cut_off_reached: false

# Contributor B — same subject, different opinion
POST /v1/evaluate
payload: {"address": "0xabc", "network": "ethereum", "label": "DEX", "confidence": 0.6}
→ attempt_index: 2, cut_off_reached: false, nearest_prior: [sub-A]

# Contributor C — ceiling hit
POST /v1/evaluate
payload: {"address": "0xabc", "network": "ethereum", "label": "CEX", "confidence": 0.8}
→ attempt_index: 3, cut_off_reached: true
```

Your pipeline receives `cut_off_reached: true` and caches it. All further submissions for `(task, eth:0xabc)` are gated before AttemptIndex is called.

---

## Choosing the right canonical_fields

| Task type | Example payload fields | canonical_fields |
|-----------|----------------------|-----------------|
| Wallet annotation | address, network, label, confidence | `["address", "network"]` |
| Image classification | image_id, category, bounding_box | `["image_id"]` |
| Text sentiment | text_id, text_content, sentiment, score | `["text_id"]` |
| Product tagging | product_sku, tag, source | `["product_sku"]` |

**Rules:**
- Include only the fields that identify the *subject*, not the contributor's opinion
- The list must be defined at task creation and **never changed mid-campaign** — changing it invalidates all prior match keys (treat it as a schema migration requiring a new `uniqueness_version`)
- Field order matters for the hash — `["address", "network"]` and `["network", "address"]` produce different match keys

---

## What if canonical_fields is omitted?

If `adapter_config.canonical_fields` is not provided, AttemptIndex hashes all fields sorted alphabetically. This is a safe default for simple cases, but not recommended for annotation tasks where output fields (labels, scores) vary by design.

```json
// No canonical_fields — full payload hashed (sorted keys)
"matcher_config": {"methodology": "hash"}
```

---

## Text payloads

For `payload_type: "text"`, `canonical_fields` is ignored. The full text string is normalized (NFKC, lowercase, whitespace collapse) and hashed:

```json
{
  "payload_type": "text",
  "payload": "  Hello  World  ",
  "matcher_config": {"methodology": "hash"}
}
// match_key computed from normalized "hello world"
```

Two text submissions with the same normalized content → same match key → counted as the same attempt.
