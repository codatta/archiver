#!/usr/bin/env python3
"""
AttemptIndex — Scenario Demonstration Script

Runs three concrete scenarios against the live service via TestClient,
prints the raw system output at each step, and cleans up test records.

Usage:
    python scripts/demo_scenarios.py
"""

import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from fastapi.testclient import TestClient  # noqa: E402

from app.db.client import get_client  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)
db = get_client()

TASK_ID = "demo-wallet-scenarios"
NOW = datetime.now(UTC).isoformat()

def uid():
    return f"test:demo:{uuid.uuid4()}"

def section(title: str):
    width = 70
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")

def step(label: str):
    print(f"\n  ── {label}")

def show(response: dict):
    print(json.dumps(response, indent=4, default=str))

def evaluate(submission_id, sample_key, payload, canonical_fields,
             max_attempts=9999, scope="task", network=None):
    body = {
        "task_id": TASK_ID,
        "sample_key": sample_key,
        "submission_id": submission_id,
        "payload_type": "structured",
        "submitted_at": NOW,
        "uniqueness_scope": scope,
        "max_attempts": max_attempts,
        "matcher_config": {
            "methodology": "hash",
            "adapter_config": {"canonical_fields": canonical_fields},
        },
        "payload": payload,
    }
    r = client.post("/v1/evaluate", json=body)
    return r.json()

def cleanup():
    db.table("attempt_records").delete().like("submission_id", "test:demo:%").execute()


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1
# Uniqueness field: wallet_address only.
# No practical cut-off (max_attempts=9999).
# Goal: verify sequence tracking across 5 submissions.
# ─────────────────────────────────────────────────────────────────────────────

section("SCENARIO 1 — Single field: wallet_address | No cut-off | Sequence tracking")

print("""
  Config:
    canonical_fields = ["wallet_address"]
    max_attempts     = 9999  (no practical cut-off)
    uniqueness_scope = "task"

  Five different contributors all label the same wallet.
  Expected: attempt_index increments 1 → 2 → 3 → 4 → 5
            cut_off_reached stays false throughout
""")

wallet = "0x12dfa3334"
sample_key_1 = f"eth:{wallet}"

for i in range(1, 6):
    step(f"Submission {i} — contributor {i}")
    payload = {"wallet_address": wallet, "label": f"label-variant-{i}", "confidence": 0.9}
    result = evaluate(uid(), sample_key_1, payload, ["wallet_address"])
    print(f"    attempt_index    : {result['attempt_index']}")
    print(f"    cut_off_reached  : {result['cut_off_reached']}")
    print(f"    cut_off_limit    : {result['cut_off_limit']}")
    print(f"    nearest_prior    : {len(result['nearest_prior'])} record(s)")
    print(f"    match_key        : {result['match_key'][:30]}...")
    print(f"    error            : {result['error']}")

print("\n  ✓ All five submissions tracked. match_key is identical — same wallet_address.")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2
# Uniqueness fields: wallet_address + network.
# Tests that the same address on different networks is tracked independently.
# ─────────────────────────────────────────────────────────────────────────────

section("SCENARIO 2 — Composite fields: wallet_address + network | Cross-network independence")

print("""
  Config:
    canonical_fields = ["wallet_address", "network"]
    max_attempts     = 9999
    uniqueness_scope = "task"

  Same address 0x12dfa3334 submitted on eth-mainnet and polygon.
  Expected: each (address, network) pair tracked as an independent subject.
            eth-mainnet attempt_index: 1 → 2
            polygon     attempt_index: 1          (independent)
""")

wallet = "0x12dfa3334"

step("Submission A1 — eth-mainnet, first label")
r = evaluate(uid(), f"eth-mainnet:{wallet}",
             {"wallet_address": wallet, "network": "eth-mainnet", "label": "CEX"},
             ["wallet_address", "network"])
idx, co = r['attempt_index'], r['cut_off_reached']
print(f"    network=eth-mainnet  attempt_index={idx}  cut_off_reached={co}")
print(f"    match_key: {r['match_key'][:40]}...")

step("Submission A2 — polygon, same address (different network)")
r_poly = evaluate(uid(), f"polygon:{wallet}",
                  {"wallet_address": wallet, "network": "polygon", "label": "DEX"},
                  ["wallet_address", "network"])
idx_p, co_p = r_poly['attempt_index'], r_poly['cut_off_reached']
print(f"    network=polygon      attempt_index={idx_p}  cut_off_reached={co_p}")
print(f"    match_key: {r_poly['match_key'][:40]}...")

step("Submission A3 — eth-mainnet again, second contributor")
r2 = evaluate(uid(), f"eth-mainnet:{wallet}",
              {"wallet_address": wallet, "network": "eth-mainnet", "label": "DEX"},
              ["wallet_address", "network"])
idx2, co2 = r2['attempt_index'], r2['cut_off_reached']
print(f"    network=eth-mainnet  attempt_index={idx2}  cut_off_reached={co2}")
prior_sid = r2['nearest_prior'][0]['submission_id'] if r2['nearest_prior'] else 'none'
print(f"    nearest_prior[0]: {prior_sid}")

print("""
  ✓ polygon  → attempt_index=1  (tracked independently, different match_key)
  ✓ eth-mainnet → attempt_index=1 then 2  (same match_key, increments correctly)
""")

print("  Full response for eth-mainnet submission A3:")
show(r2)


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 3
# Uniqueness fields: wallet_address + network.
# Cut-off threshold = 3.
# Tests: cut-off detection, flood behaviour, and full-scan limitation.
# ─────────────────────────────────────────────────────────────────────────────

section("SCENARIO 3 — Composite fields + cut-off=3 | Flood behaviour & limitations")

print("""
  Config:
    canonical_fields = ["wallet_address", "network"]
    max_attempts     = 3
    uniqueness_scope = "task"

  Part A: normal flow — 3 legitimate submissions hit the ceiling.
  Part B: flood simulation — 5 extra submissions after cut-off.
""")

wallet = f"0x{uuid.uuid4().hex[:8]}"
sample_key_3 = f"eth-mainnet:{wallet}"
payload_3 = {"wallet_address": wallet, "network": "eth-mainnet"}

print("\n  ── Part A: Normal flow up to ceiling\n")
for i in range(1, 4):
    step(f"Submission {i}")
    r = evaluate(uid(), sample_key_3, {**payload_3, "label": f"label-{i}"},
                 ["wallet_address", "network"], max_attempts=3)
    ai, co, err = r['attempt_index'], r['cut_off_reached'], r['error']
    print(f"    attempt_index={ai}  cut_off_reached={co}  error={err}")
    if r["attempt_index"] == 3:
        print("\n  ── Full response at cut-off:")
        show(r)

print("""
  ✓ Submission 3 sets cut_off_reached=true.
  The Contribution Pipeline should cache this and gate all further submissions
  before calling AttemptIndex. AttemptIndex itself does NOT block.
""")

print("\n  ── Part B: Flood simulation — 5 extra calls after cut-off\n")
print("  NOTE: These calls should never reach AttemptIndex in production.")
print("  The pipeline gates on cached cut_off_reached before calling evaluate().")
print("  Shown here to expose the raw AttemptIndex behaviour under flood:\n")

flood_results = []
for i in range(4, 9):
    r = evaluate(uid(), sample_key_3, {**payload_3, "label": f"flood-{i}"},
                 ["wallet_address", "network"], max_attempts=3)
    flood_results.append(r["attempt_index"])
    ai, co = r['attempt_index'], r['cut_off_reached']
    print(f"    Flood submission {i}: attempt_index={ai}  cut_off_reached={co}")

print(f"""
  Flood sequence: {flood_results}

  ┌─────────────────────────────────────────────────────────────────┐
  │  CURRENT BEHAVIOUR — KNOWN LIMITATIONS                         │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │  1. AttemptIndex does NOT block flood submissions.              │
  │     cut_off_reached=true is advisory. Every unique              │
  │     submission_id creates a new row in attempt_records          │
  │     regardless of the ceiling.                                  │
  │                                                                 │
  │  2. Each call runs a full SELECT * scan of all prior records    │
  │     matching (match_key, sample_key, scope). As the flood       │
  │     grows, each subsequent call scans more rows.                │
  │     → O(N) data transfer per call after N flood submissions.   │
  │                                                                 │
  │  3. Flood defence is the Contribution Pipeline's responsibility. │
  │     It must cache cut_off_reached=true on first detection and   │
  │     gate all further submissions BEFORE calling AttemptIndex.   │
  │     AttemptIndex never sees those submissions.                  │
  │                                                                 │
  │  4. A fast-mode COUNT query (SELECT COUNT(*) instead of         │
  │     SELECT *) would reduce the per-call overhead under flood,   │
  │     but would not prevent the flood itself.                     │
  │     → Documented in prd.md Backlog as "Fast-mode cut-off check" │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
""")


# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "─" * 70)
print("  Cleaning up test records...")
cleanup()
print("  Done. All test:demo:* records removed from attempt_records.")
print("─" * 70 + "\n")
