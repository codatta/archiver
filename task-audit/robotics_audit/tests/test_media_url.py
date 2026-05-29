from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from robotics_audit.task_reference.loader import build_media_url, build_vision_download_url


class TestBuildMediaUrl(unittest.TestCase):
    def test_with_frontier_id(self) -> None:
        os.environ["TASK_MEDIA_BASE_URL"] = "https://codatta-frontier-resource.oss-ap-southeast-1.aliyuncs.com"
        url = build_media_url(
            "task-pick_water_50_4_7th_gifs_episode-44.gif",
            frontier_id="ROBSTIC001",
        )
        self.assertEqual(
            url,
            "https://codatta-frontier-resource.oss-ap-southeast-1.aliyuncs.com/ROBSTIC001/task-pick_water_50_4_7th_gifs_episode-44.gif",
        )

    def test_absolute_url_passthrough(self) -> None:
        raw = "https://example.com/a.gif"
        self.assertEqual(build_media_url(raw, frontier_id="ROBSTIC001"), raw)

    def test_default_frontier_from_env(self) -> None:
        os.environ["TASK_MEDIA_BASE_URL"] = "https://oss.example.com"
        os.environ["DEFAULT_FRONTIER_ID"] = "ROBSTIC001"
        url = build_media_url("clip.gif")
        self.assertEqual(url, "https://oss.example.com/ROBSTIC001/clip.gif")


    def test_vision_download_compresses_gif(self) -> None:
        raw = "https://oss.example.com/ROBSTIC001/clip.gif"
        url, mime = build_vision_download_url(raw)
        self.assertIn("x-oss-process=image/resize,w_512/format,jpg", url)
        self.assertEqual(mime, "image/jpeg")

    def test_vision_download_keeps_existing_process(self) -> None:
        raw = "https://oss.example.com/clip.gif?x-oss-process=image/resize,w_256"
        url, mime = build_vision_download_url(raw)
        self.assertEqual(url, raw)
        self.assertEqual(mime, "image/gif")


if __name__ == "__main__":
    unittest.main()
