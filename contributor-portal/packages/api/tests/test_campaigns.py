from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_templates():
    res = client.get("/v1/campaigns/templates")
    assert res.status_code == 200
    templates = res.json()
    assert "robotics_video_collection" in templates


def test_seed_creates_campaign_with_4_tasks():
    res = client.post("/v1/campaigns/seed", json={"template_id": "robotics_video_collection"})
    assert res.status_code == 200
    data = res.json()

    assert data["frontier_id"] == "robotics"
    assert data["template_id"] == "robotics_video_collection"
    assert data["name"] == "Robotics Video Collection"
    assert data["status"] == "live"
    assert len(data["tasks"]) == 4


def test_seed_tasks_have_correct_dag():
    res = client.post("/v1/campaigns/seed", json={})
    data = res.json()
    tasks = data["tasks"]

    # Tasks are ordered by position
    assert tasks[0]["task_key"] == "data_supply"
    assert tasks[1]["task_key"] == "vision_processing"
    assert tasks[2]["task_key"] == "human_annotation"
    assert tasks[3]["task_key"] == "validation"

    # T1 has no dependencies
    assert tasks[0]["depends_on"] == []

    # T2 depends on T1
    assert tasks[1]["depends_on"] == [tasks[0]["id"]]

    # T3 depends on T2
    assert tasks[2]["depends_on"] == [tasks[1]["id"]]

    # T4 depends on T3
    assert tasks[3]["depends_on"] == [tasks[2]["id"]]


def test_seed_tasks_have_correct_execution_modes():
    res = client.post("/v1/campaigns/seed", json={})
    tasks = res.json()["tasks"]

    assert tasks[0]["execution"] == "human"
    assert tasks[1]["execution"] == "agent"
    assert tasks[2]["execution"] == "human"
    assert tasks[3]["execution"] == "agent"


def test_seed_tasks_have_annotation_configs():
    res = client.post("/v1/campaigns/seed", json={})
    tasks = res.json()["tasks"]

    for task in tasks:
        assert task["has_annotation_config"] is True


def test_seed_includes_detection_presets_and_vocabulary():
    res = client.post("/v1/campaigns/seed", json={})
    params = res.json()["params"]

    assert "detection_presets" in params
    assert "universal" in params["detection_presets"]
    assert "workstation_pose" in params["detection_presets"]

    assert "action_vocabulary" in params
    labels = [v["value"] for v in params["action_vocabulary"]]
    assert "fold_box" in labels
    assert "fold_textile" in labels
    assert "packing" in labels
    assert "pick_place" in labels
    assert "other_valid" in labels


def test_list_campaigns_returns_seeded():
    # Seed one
    seed_res = client.post("/v1/campaigns/seed", json={"name": "Test List"})
    campaign_id = seed_res.json()["id"]

    res = client.get("/v1/campaigns")
    assert res.status_code == 200
    ids = [c["id"] for c in res.json()]
    assert campaign_id in ids


def test_get_campaign_detail():
    seed_res = client.post("/v1/campaigns/seed", json={})
    campaign_id = seed_res.json()["id"]

    res = client.get(f"/v1/campaigns/{campaign_id}")
    assert res.status_code == 200
    assert res.json()["id"] == campaign_id
    assert len(res.json()["tasks"]) == 4


def test_get_campaign_not_found():
    res = client.get("/v1/campaigns/nonexistent")
    assert res.status_code == 404


def test_get_task_config_returns_xml():
    seed_res = client.post("/v1/campaigns/seed", json={})
    data = seed_res.json()
    campaign_id = data["id"]
    t3_id = data["tasks"][2]["id"]  # human_annotation

    res = client.get(f"/v1/campaigns/{campaign_id}/tasks/{t3_id}/config")
    assert res.status_code == 200
    body = res.json()
    assert body["task_key"] == "human_annotation"
    assert "<View>" in body["annotation_config"]
    assert "Embodiment-X" in body["annotation_config"]
    assert "fold_box" in body["annotation_config"]


def test_seed_nonexistent_template():
    res = client.post("/v1/campaigns/seed", json={"template_id": "nonexistent"})
    assert res.status_code == 404
