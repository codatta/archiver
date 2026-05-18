"""
Integration tests for POST /v1/evaluate.
All submission_ids use 'test:' prefix for automatic cleanup.
"""

import uuid

BASE_PAYLOAD = {
    "task_id": "test-task-cipherowl",
    "sample_key": "eth:0xtest",
    "payload_type": "structured",
    "submitted_at": "2026-04-27T10:00:00Z",
    "uniqueness_scope": "task",
    "max_attempts": 3,
    "matcher_config": {
        "methodology": "hash",
        "adapter_config": {"canonical_fields": ["address", "network"]},
    },
    "payload": {"address": "0xtest", "network": "ethereum", "label": "CEX", "confidence": 0.9},
}


def uid():
    return f"test:{uuid.uuid4()}"


class TestUC1FirstSubmission:
    def test_first_submission_returns_index_1(self, client, cleanup_db):
        body = {**BASE_PAYLOAD, "submission_id": uid()}
        r = client.post("/v1/evaluate", json=body)
        assert r.status_code == 200
        data = r.json()
        assert data["attempt_index"] == 1
        assert data["cut_off_reached"] is False
        assert data["nearest_prior"] == []
        assert data["processing_stage"] == "complete"
        assert data["match_key"].startswith("mk:")


class TestUC2RepeatSubmission:
    def test_second_submission_returns_index_2(self, client, cleanup_db):
        address = f"0x{uuid.uuid4().hex[:8]}"
        sample_key = f"eth:{address}"
        # Both submissions target the same address — same canonical_fields → same match_key
        shared_payload = {"address": address, "network": "ethereum"}
        base = {
            **BASE_PAYLOAD,
            "sample_key": sample_key,
            "payload": {**shared_payload, "label": "CEX", "confidence": 0.9},
        }

        r1 = client.post("/v1/evaluate", json={**base, "submission_id": uid()})
        assert r1.json()["attempt_index"] == 1

        r2 = client.post("/v1/evaluate", json={
            **base,
            "submission_id": uid(),
            "payload": {**shared_payload, "label": "DEX", "confidence": 0.6},
        })
        # Different label but same canonical_fields → same match_key → attempt_index=2
        assert r2.json()["attempt_index"] == 2
        assert r2.json()["nearest_prior"] != []


class TestUC6CutOff:
    def test_cut_off_reached_at_max_attempts(self, client, cleanup_db):
        sample_key = f"eth:0x{uuid.uuid4().hex[:8]}"
        base = {
            **BASE_PAYLOAD,
            "sample_key": sample_key,
            "max_attempts": 3,
            "payload": {"address": sample_key, "network": "ethereum", "label": "CEX"},
        }

        for i in range(1, 4):
            r = client.post("/v1/evaluate", json={**base, "submission_id": uid()})
            assert r.status_code == 200
            data = r.json()
            assert data["attempt_index"] == i
            if i < 3:
                assert data["cut_off_reached"] is False
            else:
                assert data["cut_off_reached"] is True


class TestUC5GenuinelyNewPayload:
    def test_different_address_gets_index_1(self, client, cleanup_db):
        # Two different addresses → different match_keys → each gets attempt_index=1
        def submit(address):
            return client.post("/v1/evaluate", json={
                **BASE_PAYLOAD,
                "submission_id": uid(),
                "sample_key": f"eth:{address}",
                "payload": {"address": address, "network": "ethereum", "label": "CEX"},
            })

        r1 = submit("0xaaaa")
        r2 = submit("0xbbbb")
        assert r1.json()["attempt_index"] == 1
        assert r2.json()["attempt_index"] == 1


class TestIdempotency:
    def test_same_submission_id_returns_same_index(self, client, cleanup_db):
        sub_id = uid()
        body = {**BASE_PAYLOAD, "submission_id": sub_id}

        r1 = client.post("/v1/evaluate", json=body)
        r2 = client.post("/v1/evaluate", json=body)

        assert r1.json()["attempt_index"] == r2.json()["attempt_index"] == 1

    def test_idempotent_call_does_not_increment_count(self, client, cleanup_db):
        sample_key = f"eth:0x{uuid.uuid4().hex[:8]}"
        sub_id = uid()
        body = {
            **BASE_PAYLOAD,
            "submission_id": sub_id,
            "sample_key": sample_key,
            "payload": {"address": sample_key, "network": "ethereum", "label": "CEX"},
        }

        client.post("/v1/evaluate", json=body)
        client.post("/v1/evaluate", json=body)  # idempotent repeat

        # Third call with a new submission_id should be attempt_index=2, not 3
        r3 = client.post("/v1/evaluate", json={
            **body,
            "submission_id": uid(),
        })
        assert r3.json()["attempt_index"] == 2


class TestPrecomputedMatchKey:
    def test_accepts_precomputed_match_key(self, client, cleanup_db):
        body = {
            **BASE_PAYLOAD,
            "submission_id": uid(),
            "payload": None,
            "match_key": "mk:precomputed123abc",
        }
        r = client.post("/v1/evaluate", json=body)
        assert r.status_code == 200
        assert r.json()["match_key"] == "mk:precomputed123abc"

    def test_requires_payload_or_match_key(self, client):
        body = {**BASE_PAYLOAD, "submission_id": uid(), "payload": None, "match_key": None}
        r = client.post("/v1/evaluate", json=body)
        assert r.status_code == 422


# Campaign-scope tests live in tests/test_campaign_scope.py
