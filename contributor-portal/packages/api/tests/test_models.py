from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.domain import (
    ActionSegment,
    Annotation,
    BoundingBox,
    Campaign,
    Clip,
    ClipFrame,
    Contributor,
    Keypoint,
    LineageStagingRecord,
    ProcessingJob,
    Segment,
    Task,
    TaskInstance,
)
from app.models.enums import (
    CampaignStatus,
    InstanceStatus,
    JobStatus,
    QualityGrade,
    SegmentState,
    TaskExecution,
    TaskOrigin,
)

NOW = datetime.now(timezone.utc)


class TestCampaign:
    def test_valid_campaign(self):
        c = Campaign(
            id=uuid4(),
            frontier_id="robotics",
            template_id="robotics_video_collection",
            name="Test Campaign",
            created_at=NOW,
        )
        assert c.status == CampaignStatus.DRAFT
        assert c.params == {}
        assert c.org_id is None

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            Campaign(
                id=uuid4(),
                frontier_id="robotics",
                template_id="test",
                name="Bad",
                status="nonexistent",
                created_at=NOW,
            )


class TestTask:
    def test_valid_task(self):
        t = Task(
            id=uuid4(),
            campaign_id=uuid4(),
            task_key="data_supply",
            name="Data Supply",
            origin=TaskOrigin.MANUAL,
            execution=TaskExecution.HUMAN,
            depends_on=[],
            position=0,
        )
        assert t.ml_backend_url is None
        assert t.annotation_config is None

    def test_agent_task_with_ml_backend(self):
        t = Task(
            id=uuid4(),
            campaign_id=uuid4(),
            task_key="vision_processing",
            name="Vision Processing",
            origin=TaskOrigin.MANUAL,
            execution=TaskExecution.AGENT,
            ml_backend_url="http://localhost:8001/predict",
            position=1,
        )
        assert t.execution == TaskExecution.AGENT
        assert t.ml_backend_url is not None


class TestTaskInstance:
    def test_valid_instance_with_lineage(self):
        parent_id = uuid4()
        inst = TaskInstance(
            id=uuid4(),
            task_id=uuid4(),
            campaign_id=uuid4(),
            parent_instances=[parent_id],
            content_hash="sha256:abc123",
            annotation_config_ver="embodiment_x_v1.0.0",
            status=InstanceStatus.SUBMITTED,
            created_at=NOW,
        )
        assert inst.parent_instances == [parent_id]
        assert inst.quality_grade is None

    def test_defaults(self):
        inst = TaskInstance(
            id=uuid4(),
            task_id=uuid4(),
            campaign_id=uuid4(),
            created_at=NOW,
        )
        assert inst.status == InstanceStatus.PENDING
        assert inst.parent_instances == []
        assert inst.content_hash is None


class TestProcessingJob:
    def test_valid_job(self):
        j = ProcessingJob(
            id=uuid4(),
            t1_instance_id=uuid4(),
            campaign_id=uuid4(),
            filename="video.mp4",
            created_at=NOW,
        )
        assert j.status == JobStatus.PROCESSING
        assert j.step == "upload"
        assert j.step_pct == 0


class TestClip:
    def test_valid_clip(self):
        c = Clip(
            id=uuid4(),
            job_id=uuid4(),
            start_idx=0,
            end_idx=100,
            start_ms=0,
            end_ms=3333,
            fps=30.0,
            frame_count=100,
        )
        assert c.t2_instance_id is None
        assert c.actions is None


class TestClipFrame:
    def test_frame_with_detection(self):
        f = ClipFrame(
            id=uuid4(),
            clip_id=uuid4(),
            frame_idx=42,
            file_url="/clips/frames/abc/000042.jpg",
            person_detected=True,
            person_bbox={"label": "person", "x": 0.2, "y": 0.3, "w": 0.4, "h": 0.5},
            arm_keypoints=[{"label": "left_wrist", "x": 0.5, "y": 0.6, "confidence": 0.87}],
        )
        assert f.person_detected is True


class TestSegment:
    def test_culled_segment(self):
        s = Segment(
            id=uuid4(),
            job_id=uuid4(),
            state=SegmentState.CULLED_MOTION,
            start_idx=0,
            end_idx=50,
            frame_count=50,
            duration_ms=1666,
            cull_reason="below motion threshold",
        )
        assert s.is_reviewed is False
        assert s.review_decision is None


class TestAnnotation:
    def test_embodiment_x_annotation(self):
        a = Annotation(
            id=uuid4(),
            t3_instance_id=uuid4(),
            job_id=uuid4(),
            temporal={
                "segments": [
                    {
                        "id": "seg_001",
                        "start_ns": 1000000,
                        "end_ns": 2000000,
                        "action_label": "fold_textile",
                        "language_instruction": "Fold the towel in half",
                        "task_plan": ["pick up towel", "fold", "place"],
                    }
                ]
            },
            spatial={
                "frames": [
                    {
                        "frame_idx": 42,
                        "bounding_boxes": [
                            {"label": "towel", "x": 0.2, "y": 0.3, "w": 0.4, "h": 0.3}
                        ],
                        "keypoints": [],
                    }
                ]
            },
            created_at=NOW,
        )
        assert len(a.temporal["segments"]) == 1


class TestEmbodimentXSubModels:
    def test_bounding_box(self):
        bb = BoundingBox(label="towel", x=0.2, y=0.3, w=0.4, h=0.3, confidence=0.92)
        assert bb.label == "towel"

    def test_keypoint(self):
        kp = Keypoint(label="left_wrist", x=0.5, y=0.6, confidence=0.87)
        assert kp.confidence == 0.87

    def test_action_segment(self):
        seg = ActionSegment(
            id="seg_001",
            start_ns=1000000,
            end_ns=2000000,
            action_label="fold_textile",
            language_instruction="Fold the towel",
            task_plan=["pick up", "fold", "place"],
        )
        assert len(seg.task_plan) == 3


class TestContributor:
    def test_defaults(self):
        c = Contributor(id=uuid4(), created_at=NOW)
        assert c.reputation_score == 0.0
        assert c.email is None


class TestLineageStaging:
    def test_valid_staging_record(self):
        r = LineageStagingRecord(
            instance_id=uuid4(),
            campaign_id=uuid4(),
            task_id=uuid4(),
            frontier_id="robotics",
            parent_instances=[uuid4()],
            content_hash="sha256:abc",
            annotation_config_ver="embodiment_x_v1.0.0",
            upstream_shares={"self_bps": 6000, "platform_bps": 500, "parents": []},
            quality_grade=QualityGrade.A,
            staged_at=NOW,
        )
        assert r.staging_status == "mock_committed"
        assert r.compensation_model == "fixed"
