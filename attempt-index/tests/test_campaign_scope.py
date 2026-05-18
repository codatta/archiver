"""
Tests for campaign_id and campaign-scope behaviour.

Covers:
  - Isolation: different campaign_ids never share attempt counts
  - Validator: campaign_id required iff scope is 'campaign'
  - Default scope: omitting uniqueness_scope defaults to 'campaign'
  - Bootstrap + campaign scope: bootstrapped records found / not found per campaign_id
  - Cut-off per campaign: ceiling in campaign A does not affect campaign B
  - Idempotency under campaign scope
  - Cross-scope boundary: task-scoped records are invisible to campaign-scope queries
"""

import uuid

import pytest

# ── helpers ───────────────────────────────────────────────────────────────────

def uid():
    return f"test:{uuid.uuid4()}"


def buid():
    return f"bootstrap:test:{uuid.uuid4()}"


def _address():
    return f"0x{uuid.uuid4().hex[:8]}"


CAMPAIGN_BASE = {
    "task_id": "test-task-campaign",
    "payload_type": "structured",
    "submitted_at": "2026-04-27T10:00:00Z",
    "uniqueness_scope": "campaign",
    "campaign_id": "test-campaign-default",
    "max_attempts": 5,
    "matcher_config": {
        "methodology": "hash",
        "adapter_config": {"canonical_fields": ["address", "network"]},
    },
}

TASK_BASE = {
    "task_id": "test-task-scope",
    "payload_type": "structured",
    "submitted_at": "2026-04-27T10:00:00Z",
    "uniqueness_scope": "task",
    "max_attempts": 5,
    "matcher_config": {
        "methodology": "hash",
        "adapter_config": {"canonical_fields": ["address", "network"]},
    },
}


# ── Campaign isolation ────────────────────────────────────────────────────────

class TestCampaignScopeIsolation:
    def test_two_campaigns_same_subject_independent_counts(self, client, cleanup_db):
        """campaign-alpha and campaign-beta tracking the same wallet never share counts."""
        address = _address()
        sample_key = f"eth:{address}"
        payload = {"address": address, "network": "ethereum", "label": "CEX"}

        def submit(campaign_id: str) -> dict:
            return client.post("/v1/evaluate", json={
                **CAMPAIGN_BASE,
                "submission_id": uid(),
                "sample_key": sample_key,
                "campaign_id": campaign_id,
                "payload": payload,
            }).json()

        assert submit("campaign-alpha")["attempt_index"] == 1
        assert submit("campaign-beta")["attempt_index"] == 1   # isolated, not 2
        assert submit("campaign-alpha")["attempt_index"] == 2  # increments within alpha
        assert submit("campaign-beta")["attempt_index"] == 2   # increments within beta
        assert submit("campaign-alpha")["attempt_index"] == 3  # alpha unaffected by beta

    def test_three_campaigns_all_start_at_one(self, client, cleanup_db):
        """Three campaigns each see attempt_index=1 for the same subject."""
        address = _address()
        sample_key = f"eth:{address}"
        payload = {"address": address, "network": "ethereum"}

        for campaign_id in ("camp-x", "camp-y", "camp-z"):
            r = client.post("/v1/evaluate", json={
                **CAMPAIGN_BASE,
                "submission_id": uid(),
                "sample_key": sample_key,
                "campaign_id": campaign_id,
                "payload": payload,
            })
            assert r.json()["attempt_index"] == 1, f"{campaign_id} should start at 1"

    def test_nearest_prior_only_returns_records_from_same_campaign(self, client, cleanup_db):
        """nearest_prior must not surface records from a different campaign."""
        address = _address()
        sample_key = f"eth:{address}"
        payload = {"address": address, "network": "ethereum"}

        # Seed campaign-A with one record
        client.post("/v1/evaluate", json={
            **CAMPAIGN_BASE,
            "submission_id": uid(),
            "sample_key": sample_key,
            "campaign_id": "camp-a",
            "payload": payload,
        })

        # First submission in campaign-B for same subject should have empty nearest_prior
        r = client.post("/v1/evaluate", json={
            **CAMPAIGN_BASE,
            "submission_id": uid(),
            "sample_key": sample_key,
            "campaign_id": "camp-b",
            "payload": payload,
        }).json()

        assert r["attempt_index"] == 1
        assert r["nearest_prior"] == []


# ── Validator ─────────────────────────────────────────────────────────────────

class TestCampaignScopeValidator:
    def test_campaign_scope_without_campaign_id_is_rejected(self, client):
        r = client.post("/v1/evaluate", json={
            **CAMPAIGN_BASE,
            "submission_id": uid(),
            "sample_key": "eth:0xtest",
            "payload": {"address": "0xtest", "network": "ethereum"},
            "campaign_id": None,
        })
        assert r.status_code == 422

    def test_campaign_scope_with_empty_string_campaign_id_is_rejected(self, client):
        r = client.post("/v1/evaluate", json={
            **CAMPAIGN_BASE,
            "submission_id": uid(),
            "sample_key": "eth:0xtest",
            "payload": {"address": "0xtest", "network": "ethereum"},
            "campaign_id": "",
        })
        assert r.status_code == 422

    @pytest.mark.parametrize("scope", ["task", "frontier", "global"])
    def test_non_campaign_scopes_do_not_require_campaign_id(self, client, cleanup_db, scope):
        """task / frontier / global scopes never require campaign_id."""
        address = _address()
        r = client.post("/v1/evaluate", json={
            **TASK_BASE,
            "submission_id": uid(),
            "sample_key": f"eth:{address}",
            "uniqueness_scope": scope,
            "payload": {"address": address, "network": "ethereum"},
            # campaign_id intentionally absent
        })
        assert r.status_code == 200
        assert r.json()["error"] is None


# ── Default scope ─────────────────────────────────────────────────────────────

class TestDefaultScope:
    def test_omitting_scope_defaults_to_campaign(self, client):
        """No uniqueness_scope in request → defaults to 'campaign' → requires campaign_id."""
        body = {
            "task_id": "test-task-default",
            "sample_key": "eth:0xtest",
            "submission_id": uid(),
            "payload_type": "structured",
            "submitted_at": "2026-04-27T10:00:00Z",
            "max_attempts": 3,
            "payload": {"address": "0xtest", "network": "ethereum"},
            # uniqueness_scope deliberately omitted
            # campaign_id deliberately omitted
        }
        r = client.post("/v1/evaluate", json=body)
        # Default scope is 'campaign', which requires campaign_id → 422
        assert r.status_code == 422

    def test_omitting_scope_with_campaign_id_works(self, client, cleanup_db):
        """No uniqueness_scope but campaign_id provided → campaign scope, HTTP 200."""
        address = _address()
        body = {
            "task_id": "test-task-default",
            "sample_key": f"eth:{address}",
            "submission_id": uid(),
            "payload_type": "structured",
            "submitted_at": "2026-04-27T10:00:00Z",
            "max_attempts": 3,
            "campaign_id": "default-scope-test",
            "payload": {"address": address, "network": "ethereum"},
            # uniqueness_scope deliberately omitted
        }
        r = client.post("/v1/evaluate", json=body)
        assert r.status_code == 200
        assert r.json()["uniqueness_scope"] == "campaign"
        assert r.json()["attempt_index"] == 1


# ── Bootstrap + campaign scope ────────────────────────────────────────────────

class TestBootstrapCampaignScope:
    def test_bootstrap_with_campaign_id_detected_by_matching_campaign(self, client, cleanup_db):
        """Bootstrap record with campaign_id counts for evaluate in the same campaign."""
        address = _address()
        sample_key = f"eth:{address}"
        match_key = f"mk:bootstrap-camp-{uuid.uuid4().hex[:8]}"
        campaign_id = "camp-bootstrap-test"

        bootstrap_body = {
            "records": [{
                "task_id": "test-task-campaign",
                "sample_key": sample_key,
                "submission_id": buid(),
                "payload_type": "structured",
                "match_key": match_key,
                "submitted_at": "2025-11-01T00:00:00Z",
                "uniqueness_scope": "campaign",
                "campaign_id": campaign_id,
            }]
        }
        br = client.post("/v1/bootstrap", json=bootstrap_body)
        assert br.json()["inserted"] == 1

        r = client.post("/v1/evaluate", json={
            **CAMPAIGN_BASE,
            "submission_id": uid(),
            "sample_key": sample_key,
            "campaign_id": campaign_id,
            "match_key": match_key,
            "payload": None,
        })
        data = r.json()
        assert data["attempt_index"] == 2
        assert data["nearest_prior"][0]["submission_id"].startswith("bootstrap:")

    def test_bootstrap_with_campaign_id_invisible_to_different_campaign(self, client, cleanup_db):
        """Bootstrap record in campaign A does not affect attempt count in campaign B."""
        address = _address()
        sample_key = f"eth:{address}"
        match_key = f"mk:bootstrap-camp-iso-{uuid.uuid4().hex[:8]}"

        bootstrap_body = {
            "records": [{
                "task_id": "test-task-campaign",
                "sample_key": sample_key,
                "submission_id": buid(),
                "payload_type": "structured",
                "match_key": match_key,
                "submitted_at": "2025-11-01T00:00:00Z",
                "uniqueness_scope": "campaign",
                "campaign_id": "camp-source",
            }]
        }
        client.post("/v1/bootstrap", json=bootstrap_body)

        r = client.post("/v1/evaluate", json={
            **CAMPAIGN_BASE,
            "submission_id": uid(),
            "sample_key": sample_key,
            "campaign_id": "camp-other",  # different campaign
            "match_key": match_key,
            "payload": None,
        })
        assert r.json()["attempt_index"] == 1
        assert r.json()["nearest_prior"] == []

    def test_bootstrap_requires_campaign_id_for_campaign_scope(self, client):
        """Bootstrap record with scope=campaign but no campaign_id is rejected."""
        body = {
            "records": [{
                "task_id": "test-task",
                "sample_key": "eth:0xtest",
                "submission_id": buid(),
                "payload_type": "structured",
                "match_key": "mk:testkey",
                "submitted_at": "2025-11-01T00:00:00Z",
                "uniqueness_scope": "campaign",
                # campaign_id intentionally absent
            }]
        }
        r = client.post("/v1/bootstrap", json=body)
        assert r.status_code == 422


# ── Cut-off per campaign ──────────────────────────────────────────────────────

class TestCampaignScopeCutOff:
    def test_cut_off_triggers_within_campaign(self, client, cleanup_db):
        """cut_off_reached flips to true at max_attempts within a campaign."""
        address = _address()
        sample_key = f"eth:{address}"
        payload = {"address": address, "network": "ethereum"}
        base = {**CAMPAIGN_BASE, "sample_key": sample_key, "max_attempts": 2, "payload": payload}

        r1 = client.post("/v1/evaluate", json={**base, "submission_id": uid()}).json()
        r2 = client.post("/v1/evaluate", json={**base, "submission_id": uid()}).json()

        assert r1["attempt_index"] == 1
        assert r1["cut_off_reached"] is False
        assert r2["attempt_index"] == 2
        assert r2["cut_off_reached"] is True

    def test_cut_off_in_campaign_a_does_not_affect_campaign_b(self, client, cleanup_db):
        """Hitting the ceiling in campaign A leaves campaign B unaffected."""
        address = _address()
        sample_key = f"eth:{address}"
        payload = {"address": address, "network": "ethereum"}

        # Fill campaign-A to its ceiling (max_attempts=2)
        for _ in range(2):
            client.post("/v1/evaluate", json={
                **CAMPAIGN_BASE,
                "submission_id": uid(),
                "sample_key": sample_key,
                "campaign_id": "camp-full",
                "max_attempts": 2,
                "payload": payload,
            })

        # campaign-B for the same subject should start fresh
        r = client.post("/v1/evaluate", json={
            **CAMPAIGN_BASE,
            "submission_id": uid(),
            "sample_key": sample_key,
            "campaign_id": "camp-fresh",
            "max_attempts": 2,
            "payload": payload,
        }).json()

        assert r["attempt_index"] == 1
        assert r["cut_off_reached"] is False


# ── Idempotency under campaign scope ─────────────────────────────────────────

class TestCampaignScopeIdempotency:
    def test_repeat_submission_id_returns_same_index(self, client, cleanup_db):
        address = _address()
        sub_id = uid()
        body = {
            **CAMPAIGN_BASE,
            "submission_id": sub_id,
            "sample_key": f"eth:{address}",
            "payload": {"address": address, "network": "ethereum"},
        }

        r1 = client.post("/v1/evaluate", json=body).json()
        r2 = client.post("/v1/evaluate", json=body).json()

        assert r1["attempt_index"] == r2["attempt_index"] == 1

    def test_idempotent_repeat_does_not_inflate_count(self, client, cleanup_db):
        """Calling evaluate twice with the same submission_id counts as one submission."""
        address = _address()
        sub_id = uid()
        body = {
            **CAMPAIGN_BASE,
            "submission_id": sub_id,
            "sample_key": f"eth:{address}",
            "payload": {"address": address, "network": "ethereum"},
        }

        client.post("/v1/evaluate", json=body)
        client.post("/v1/evaluate", json=body)  # idempotent repeat

        # New submission_id → attempt_index=2, not 3
        r3 = client.post("/v1/evaluate", json={**body, "submission_id": uid()}).json()
        assert r3["attempt_index"] == 2


# ── Cross-scope boundary ──────────────────────────────────────────────────────

class TestCrossScopeBoundary:
    def test_task_scoped_record_invisible_to_campaign_scope(self, client, cleanup_db):
        """
        A record written under task scope has campaign_id=NULL.
        A campaign-scope query for the same match_key finds nothing.
        """
        address = _address()
        sample_key = f"eth:{address}"
        payload = {"address": address, "network": "ethereum"}

        # Write a task-scoped record first
        client.post("/v1/evaluate", json={
            **TASK_BASE,
            "submission_id": uid(),
            "sample_key": sample_key,
            "payload": payload,
        })

        # Campaign-scope evaluate for the same subject should not find it
        r = client.post("/v1/evaluate", json={
            **CAMPAIGN_BASE,
            "submission_id": uid(),
            "sample_key": sample_key,
            "campaign_id": "camp-isolated",
            "payload": payload,
        }).json()

        assert r["attempt_index"] == 1
        assert r["nearest_prior"] == []

    def test_campaign_record_invisible_to_task_scope(self, client, cleanup_db):
        """
        A record written under campaign scope is not found by a task-scope query.
        Task scope queries by task_id, not campaign_id.
        """
        address = _address()
        sample_key = f"eth:{address}"
        payload = {"address": address, "network": "ethereum"}

        # Write a campaign-scoped record
        client.post("/v1/evaluate", json={
            **CAMPAIGN_BASE,
            "submission_id": uid(),
            "sample_key": sample_key,
            "campaign_id": "camp-write",
            "payload": payload,
        })

        # Task-scope evaluate with a different task_id should not find it
        r = client.post("/v1/evaluate", json={
            **TASK_BASE,
            "task_id": "a-completely-different-task",
            "submission_id": uid(),
            "sample_key": sample_key,
            "payload": payload,
        }).json()

        assert r["attempt_index"] == 1
        assert r["nearest_prior"] == []
