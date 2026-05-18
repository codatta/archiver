"""
Integration tests for frontier taxonomy (P0-11).
- POST /v1/frontiers  — create a named frontier
- GET  /v1/frontiers  — list frontiers
- frontier_ids on bootstrap records
All frontier IDs use 'test-' prefix; all submission IDs use 'bootstrap:test:' prefix
for automatic cleanup via the cleanup_db fixture.
"""

import uuid


def fid(label: str = "") -> str:
    """Generate a unique test frontier ID."""
    suffix = f"-{label}" if label else ""
    return f"test-frontier{suffix}-{uuid.uuid4().hex[:8]}"


def buid() -> str:
    return f"bootstrap:test:{uuid.uuid4()}"


BOOTSTRAP_RECORD = {
    "task_id": "task-frontier-test",
    "sample_key": "frontier-sample-001",
    "payload_type": "structured",
    "match_key": "mk:frontiertest001",
    "submitted_at": "2025-11-01T00:00:00Z",
    "uniqueness_scope": "frontier",
    "uniqueness_version": "v1",
}


# ---------------------------------------------------------------------------
# Frontier CRUD
# ---------------------------------------------------------------------------


class TestFrontierCreate:
    def test_creates_frontier(self, client, cleanup_db):
        frontier_id = fid("create")
        r = client.post(
            "/v1/frontiers",
            json={"frontier_id": frontier_id, "name": "Test Frontier", "description": "desc"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["frontier_id"] == frontier_id
        assert data["name"] == "Test Frontier"
        assert data["description"] == "desc"
        assert "created_at" in data

    def test_create_without_description(self, client, cleanup_db):
        r = client.post(
            "/v1/frontiers",
            json={"frontier_id": fid("nodesc"), "name": "No Desc"},
        )
        assert r.status_code == 200
        assert r.json()["description"] is None

    def test_duplicate_frontier_id_returns_error(self, client, cleanup_db):
        frontier_id = fid("dup")
        body = {"frontier_id": frontier_id, "name": "First"}
        client.post("/v1/frontiers", json=body)
        r = client.post("/v1/frontiers", json=body)
        assert r.status_code == 409

    def test_missing_name_returns_422(self, client):
        r = client.post("/v1/frontiers", json={"frontier_id": fid("noname")})
        assert r.status_code == 422


class TestFrontierList:
    def test_lists_created_frontiers(self, client, cleanup_db):
        frontier_id = fid("list")
        client.post("/v1/frontiers", json={"frontier_id": frontier_id, "name": "Listed"})
        r = client.get("/v1/frontiers")
        assert r.status_code == 200
        ids = [f["frontier_id"] for f in r.json()]
        assert frontier_id in ids


# ---------------------------------------------------------------------------
# Bootstrap with frontier_ids
# ---------------------------------------------------------------------------


class TestBootstrapFrontierTags:
    def test_bootstrap_without_frontier_ids_succeeds(self, client, cleanup_db):
        body = {"records": [{**BOOTSTRAP_RECORD, "submission_id": buid()}]}
        r = client.post("/v1/bootstrap", json=body)
        assert r.status_code == 200
        assert r.json()["inserted"] == 1

    def test_bootstrap_with_frontier_ids_creates_tags(self, client, db, cleanup_db):
        frontier_id = fid("tag")
        client.post("/v1/frontiers", json={"frontier_id": frontier_id, "name": "Tag Test"})

        sub_id = buid()
        body = {
            "records": [
                {**BOOTSTRAP_RECORD, "submission_id": sub_id, "frontier_ids": [frontier_id]}
            ]
        }
        r = client.post("/v1/bootstrap", json=body)
        assert r.status_code == 200
        assert r.json()["inserted"] == 1

        tags = (
            db.table("record_frontiers")
            .select("*")
            .eq("submission_id", sub_id)
            .execute()
        )
        assert len(tags.data) == 1
        assert tags.data[0]["frontier_id"] == frontier_id

    def test_bootstrap_with_two_frontiers_creates_both_tags(self, client, db, cleanup_db):
        fid_a, fid_b = fid("two-a"), fid("two-b")
        for f, n in [(fid_a, "A"), (fid_b, "B")]:
            client.post("/v1/frontiers", json={"frontier_id": f, "name": n})

        sub_id = buid()
        body = {
            "records": [
                {**BOOTSTRAP_RECORD, "submission_id": sub_id, "frontier_ids": [fid_a, fid_b]}
            ]
        }
        r = client.post("/v1/bootstrap", json=body)
        assert r.status_code == 200

        tags = (
            db.table("record_frontiers")
            .select("frontier_id")
            .eq("submission_id", sub_id)
            .execute()
        )
        tagged = {row["frontier_id"] for row in tags.data}
        assert tagged == {fid_a, fid_b}

    def test_rebootstrap_same_frontier_ids_is_idempotent(self, client, db, cleanup_db):
        frontier_id = fid("idem")
        client.post("/v1/frontiers", json={"frontier_id": frontier_id, "name": "Idem"})

        sub_id = buid()
        body = {
            "records": [
                {**BOOTSTRAP_RECORD, "submission_id": sub_id, "frontier_ids": [frontier_id]}
            ]
        }
        client.post("/v1/bootstrap", json=body)
        # Second call — same submission_id + same frontier_ids
        r2 = client.post("/v1/bootstrap", json=body)
        assert r2.status_code == 200
        assert r2.json()["skipped"] == 1  # record itself skipped (duplicate submission_id)

        tags = (
            db.table("record_frontiers")
            .select("*")
            .eq("submission_id", sub_id)
            .execute()
        )
        assert len(tags.data) == 1  # no duplicate tag rows

    def test_nonexistent_frontier_id_returns_error(self, client, cleanup_db):
        body = {
            "records": [
                {
                    **BOOTSTRAP_RECORD,
                    "submission_id": buid(),
                    "frontier_ids": ["test-does-not-exist-999"],
                }
            ]
        }
        r = client.post("/v1/bootstrap", json=body)
        assert r.status_code == 422

    def test_record_appears_in_both_frontier_tag_lookups(self, client, db, cleanup_db):
        fid_x, fid_y = fid("lookup-x"), fid("lookup-y")
        for f, n in [(fid_x, "X"), (fid_y, "Y")]:
            client.post("/v1/frontiers", json={"frontier_id": f, "name": n})

        sub_id = buid()
        body = {
            "records": [
                {**BOOTSTRAP_RECORD, "submission_id": sub_id, "frontier_ids": [fid_x, fid_y]}
            ]
        }
        client.post("/v1/bootstrap", json=body)

        for f in (fid_x, fid_y):
            rows = (
                db.table("record_frontiers")
                .select("submission_id")
                .eq("frontier_id", f)
                .execute()
            )
            assert any(row["submission_id"] == sub_id for row in rows.data)


# ---------------------------------------------------------------------------
# Evaluate unaffected
# ---------------------------------------------------------------------------


class TestEvaluateUnaffected:
    def test_evaluate_response_unchanged_by_frontier_tags(self, client, cleanup_db):
        """Frontier tags on a bootstrap record must not affect evaluate response shape."""
        frontier_id = fid("eval")
        client.post("/v1/frontiers", json={"frontier_id": frontier_id, "name": "Eval Test"})

        sample_key = f"eth:0x{uuid.uuid4().hex[:8]}"
        match_key = f"mk:frontier-eval-{uuid.uuid4().hex[:8]}"

        client.post(
            "/v1/bootstrap",
            json={
                "records": [
                    {
                        **BOOTSTRAP_RECORD,
                        "submission_id": buid(),
                        "sample_key": sample_key,
                        "match_key": match_key,
                        "uniqueness_scope": "task",
                        "frontier_ids": [frontier_id],
                    }
                ]
            },
        )

        r = client.post(
            "/v1/evaluate",
            json={
                "task_id": "task-frontier-test",
                "sample_key": sample_key,
                "submission_id": f"test:{uuid.uuid4()}",
                "payload_type": "structured",
                "submitted_at": "2026-04-27T10:00:00Z",
                "uniqueness_scope": "task",
                "max_attempts": 5,
                "match_key": match_key,
                "matcher_config": {"methodology": "hash"},
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["attempt_index"] == 2
        assert "frontier_ids" not in data  # evaluate response shape is unchanged
        assert data["nearest_prior"][0]["submission_id"].startswith("bootstrap:")
