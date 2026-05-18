"""
Integration tests for POST /v1/bootstrap.
All submission_ids use 'bootstrap:test:' prefix for automatic cleanup.
"""

import uuid


def buid():
    return f"bootstrap:test:{uuid.uuid4()}"


RECORD = {
    "task_id": "task-frontier-test",
    "sample_key": "bootstrap-sample-001",
    "payload_type": "structured",
    "match_key": "mk:bootstraptest123",
    "submitted_at": "2025-11-01T00:00:00Z",
    "uniqueness_scope": "frontier",
    "uniqueness_version": "v1",
}


class TestBootstrapInsert:
    def test_inserts_fresh_record(self, client, cleanup_db):
        body = {"records": [{**RECORD, "submission_id": buid()}]}
        r = client.post("/v1/bootstrap", json=body)
        assert r.status_code == 200
        assert r.json()["inserted"] == 1
        assert r.json()["skipped"] == 0

    def test_idempotent_duplicate_is_skipped(self, client, cleanup_db):
        sub_id = buid()
        body = {"records": [{**RECORD, "submission_id": sub_id}]}

        r1 = client.post("/v1/bootstrap", json=body)
        r2 = client.post("/v1/bootstrap", json=body)

        assert r1.json()["inserted"] == 1
        assert r2.json()["inserted"] == 0
        assert r2.json()["skipped"] == 1

    def test_batch_mixed_new_and_duplicate(self, client, cleanup_db):
        sub_id = buid()
        body_first = {"records": [{**RECORD, "submission_id": sub_id}]}
        client.post("/v1/bootstrap", json=body_first)

        body_batch = {
            "records": [
                {**RECORD, "submission_id": sub_id},       # duplicate
                {**RECORD, "submission_id": buid()},       # new
                {**RECORD, "submission_id": buid()},       # new
            ]
        }
        r = client.post("/v1/bootstrap", json=body_batch)
        assert r.json()["inserted"] == 2
        assert r.json()["skipped"] == 1

    def test_requires_bootstrap_prefix(self, client):
        body = {"records": [{**RECORD, "submission_id": "not-bootstrap-prefix"}]}
        r = client.post("/v1/bootstrap", json=body)
        assert r.status_code == 422


class TestBootstrapDeduplication:
    def test_bootstrapped_record_detected_by_evaluate(self, client, cleanup_db):
        """A bootstrapped record is found by evaluate → attempt_index = 2, not 1."""
        sample_key = f"eth:0x{uuid.uuid4().hex[:8]}"
        match_key = f"mk:bootstrap-test-{uuid.uuid4().hex[:8]}"

        # Bootstrap a known record
        bootstrap_body = {
            "records": [{
                **RECORD,
                "submission_id": buid(),
                "sample_key": sample_key,
                "match_key": match_key,
                "uniqueness_scope": "task",
            }]
        }
        client.post("/v1/bootstrap", json=bootstrap_body)

        # Now evaluate a submission with the same match_key
        eval_body = {
            "task_id": "task-frontier-test",
            "sample_key": sample_key,
            "submission_id": f"test:{uuid.uuid4()}",
            "payload_type": "structured",
            "submitted_at": "2026-04-27T10:00:00Z",
            "uniqueness_scope": "task",
            "max_attempts": 5,
            "match_key": match_key,
            "matcher_config": {"methodology": "hash"},
        }
        r = client.post("/v1/evaluate", json=eval_body)
        assert r.status_code == 200
        data = r.json()
        # Should be attempt_index=2 because bootstrapped record exists
        assert data["attempt_index"] == 2
        assert data["nearest_prior"][0]["submission_id"].startswith("bootstrap:")
