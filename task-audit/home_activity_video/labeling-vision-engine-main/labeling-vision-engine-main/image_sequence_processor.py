import cv2
import json
import numpy as np
import shutil
import uuid
import os
import re
import zipfile
import tempfile
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional

from video_processor import (
    compute_blur_score,
    compute_brightness,
    make_person_detector,
    DEFAULT_YOLO_MODEL,
)

logger = logging.getLogger(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


# ─── extraction_info parsers (JSON + Chinese TXT) ────────────────────────────

def _parse_fps_from_str(val: str) -> Optional[float]:
    """Extract a float from strings like '5.00 Hz' or '5.0'."""
    m = re.search(r"[\d]+(?:\.\d+)?", val)
    return float(m.group()) if m else None


def _parse_extraction_json(json_path: str) -> dict:
    """
    Parse extraction_info.json produced by the ROS bag extractor.
    Expected keys: effective_frequency / target_frequency, extracted_images[]
    """
    result: dict = {"fps": 10.0, "total_frames": 0, "frames": []}
    try:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Could not parse %s: %s", json_path, e)
        return result

    fps = (
        data.get("effective_frequency")
        or data.get("target_frequency")
        or data.get("original_frequency")
        or 10.0
    )
    result["fps"] = float(fps)

    images = data.get("extracted_images", [])
    if images:
        t0_ns = images[0].get("timestamp_ns", 0)
        frames = []
        for img in images:
            fname = img.get("filename", "")
            if not fname:
                continue
            ts_ns = img.get("timestamp_ns", 0)
            frames.append({
                "filename": fname,
                "timestamp": (ts_ns - t0_ns) / 1e9,
                "timestamp_ns": ts_ns,
            })
        result["frames"] = frames
        result["total_frames"] = len(frames)

    logger.info(
        "[json] fps=%.2f frames=%d from %s",
        result["fps"], result["total_frames"], json_path,
    )
    return result


def _parse_extraction_txt(txt_path: str) -> dict:
    """
    Parse extraction_info.txt (Chinese or English).

    Supported key names (case-insensitive, Chinese or English):
      fps / frame_rate / framerate
      目标频率 / 实际频率 / 原始频率  (values may include ' Hz')
      total_frames / frame_count / 提取图像数量

    Frame list section starts after a line containing
    '图像列表', 'frame list', 'images:', or 'frames:'.
    Rows are either:
      • CSV: index, timestamp_ns, filename, ...   (column 2 = filename)
      • Space-separated: filename  timestamp_sec
    """
    result: dict = {"fps": 10.0, "total_frames": 0, "frames": []}
    try:
        text = Path(txt_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        logger.warning("extraction_info.txt not found: %s", txt_path)
        return result

    kv_pattern = re.compile(r"^(.+?)\s*[:=]\s*(.+)$")
    # Chinese fps key aliases
    FPS_KEYS = {
        "fps", "frame_rate", "framerate",
        "目标频率", "实际频率", "原始频率",
    }
    COUNT_KEYS = {"total_frames", "frame_count", "提取图像数量"}

    in_frame_list = False
    skip_header = False  # skip the CSV column header row
    frame_entries: list[dict] = []

    SECTION_TRIGGERS = ("图像列表", "frame list", "images:", "frames:")

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or set(stripped) <= {"-"}:
            continue

        lower = stripped.lower()

        # Detect start of the frame list section
        if any(t in stripped for t in SECTION_TRIGGERS):
            in_frame_list = True
            skip_header = True   # next non-empty line is the column header
            continue

        if in_frame_list:
            if skip_header:
                # Skip the column-name row: '序号, 时间戳(ns), 文件名, ...'
                skip_header = False
                continue

            # Try CSV first (comma-separated)
            parts = [p.strip() for p in stripped.split(",")]
            if len(parts) >= 3:
                # Format: index, timestamp_ns, filename, ...
                fname = parts[2]
                ext = Path(fname).suffix.lower()
                if ext in IMAGE_EXTS:
                    try:
                        ts_ns = int(parts[1])
                        frame_entries.append({"filename": fname, "timestamp_ns": ts_ns})
                    except ValueError:
                        pass
                    continue

            # Fall back to space-separated: filename  timestamp_sec
            ws_parts = stripped.split()
            if ws_parts:
                fname = ws_parts[0]
                if Path(fname).suffix.lower() in IMAGE_EXTS:
                    ts = float(ws_parts[1]) if len(ws_parts) >= 2 else -1.0
                    frame_entries.append({"filename": fname, "timestamp": ts})
            continue

        # Key-value header
        m = kv_pattern.match(stripped)
        if not m:
            continue
        raw_key = m.group(1).strip()
        val = m.group(2).strip()
        key = raw_key.lower().replace(" ", "_")

        if key in FPS_KEYS or raw_key in FPS_KEYS:
            fps_val = _parse_fps_from_str(val)
            if fps_val:
                result["fps"] = fps_val
        elif key in COUNT_KEYS or raw_key in COUNT_KEYS:
            try:
                result["total_frames"] = int(re.search(r"\d+", val).group())
            except (AttributeError, ValueError):
                pass

    if frame_entries:
        fps = result["fps"]
        if "timestamp_ns" in frame_entries[0]:
            # Normalise ns timestamps to seconds starting at 0, keep abs timestamp
            t0_ns = frame_entries[0]["timestamp_ns"]
            result["frames"] = [
                {
                    "filename": fe["filename"],
                    "timestamp": (fe["timestamp_ns"] - t0_ns) / 1e9,
                    "timestamp_ns": fe["timestamp_ns"],
                }
                for fe in frame_entries
            ]
        else:
            # Synthesise missing timestamps from fps
            for i, fe in enumerate(frame_entries):
                if fe.get("timestamp", -1) < 0:
                    fe["timestamp"] = i / fps
            t0 = frame_entries[0]["timestamp"]
            result["frames"] = [
                {"filename": fe["filename"], "timestamp": fe["timestamp"] - t0}
                for fe in frame_entries
            ]
        result["total_frames"] = len(result["frames"])

    logger.info(
        "[txt] fps=%.2f frames=%d from %s",
        result["fps"], result["total_frames"], txt_path,
    )
    return result


def parse_extraction_info(info_path: str) -> dict:
    """
    Unified entry point: tries extraction_info.json first (same directory),
    then falls back to extraction_info.txt.
    """
    p = Path(info_path)
    # If caller passed the txt path, look for a sibling json
    if p.suffix == ".txt":
        json_candidate = p.with_name("extraction_info.json")
    elif p.suffix == ".json":
        json_candidate = p
    else:
        json_candidate = Path("__nonexistent__")

    if json_candidate.is_file():
        return _parse_extraction_json(str(json_candidate))

    # Fall back to txt (may be empty string → returns defaults)
    return _parse_extraction_txt(info_path)


# ─── Fast zip extraction (with optional on-the-fly compression) ──────────────

def _extract_zip_maybe_compressed(
    zip_path: str,
    tmpdir: str,
    compress_px: int = 0,
    progress_cb: Optional[Callable[[int], None]] = None,
    n_workers: int = 4,
) -> None:
    """
    Extract zip → tmpdir.

    When compress_px > 0 every image file is decoded from zip bytes,
    resized so the longest side ≤ compress_px, and written as JPEG-85.
    Non-image entries are extracted as-is.

    Why this matters: a 400 MB PNG archive typically shrinks to ~40-60 MB
    JPEG on disk, reducing extract I/O by ~90 % and making all downstream
    cv2.imread() calls 5-10× faster.  Motion analysis already runs at
    320×180 internally, so quality loss is negligible.

    Image decode/resize/write is parallelised with a thread pool (cv2
    releases the GIL, so threads genuinely speed things up on multi-core).
    Progress is reported via progress_cb(0-100) after each image is saved.
    """
    # Phase 1: open zip, create dirs, read non-image files immediately,
    # collect (bytes, dest_path) for image files.
    with zipfile.ZipFile(zip_path, "r") as zf:
        all_members = zf.infolist()
        # Pre-create all directories
        for m in all_members:
            dest = os.path.join(tmpdir, m.filename)
            parent = os.path.dirname(dest)
            if parent:
                os.makedirs(parent, exist_ok=True)

        file_members = [m for m in all_members if not m.is_dir()]

        if not compress_px:
            # No compression: plain extraction with progress reporting
            total = max(1, len(file_members))
            for i, m in enumerate(file_members):
                zf.extract(m, tmpdir)
                if progress_cb:
                    progress_cb(int((i + 1) / total * 100))
            return

        img_tasks: list[tuple[bytes, str, str]] = []  # (png_bytes, orig_dest, jpg_dest)
        n_img_done = [0]
        done_lock = threading.Lock()

        for m in file_members:
            orig_dest = os.path.join(tmpdir, m.filename)
            if Path(m.filename).suffix.lower() in IMAGE_EXTS:
                data = zf.read(m)          # must be serial inside ZipFile
                jpg_dest = str(Path(orig_dest).with_suffix(".jpg"))
                img_tasks.append((data, orig_dest, jpg_dest))
            else:
                zf.extract(m, tmpdir)

    # Phase 2: decode + resize + write in parallel (zip is closed – thread-safe)
    n_img = max(1, len(img_tasks))

    def _process(task: tuple[bytes, str, str]) -> None:
        data, orig_dest, jpg_dest = task
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is not None:
            h, w = img.shape[:2]
            if max(h, w) > compress_px:
                scale = compress_px / max(h, w)
                img = cv2.resize(
                    img, (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA,
                )
            cv2.imwrite(jpg_dest, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        else:
            # Decode failed – write raw bytes under original name
            with open(orig_dest, "wb") as f:
                f.write(data)
        with done_lock:
            n_img_done[0] += 1
            if progress_cb:
                progress_cb(int(n_img_done[0] / n_img * 100))

    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        pool.map(_process, img_tasks)


# ─── Discover images inside extracted dir ────────────────────────────────────

def discover_images(base_dir: str, known_filenames: list[str]) -> list[str]:
    """
    Return sorted absolute paths for images inside base_dir.
    Prefers the ordered `known_filenames` list; falls back to sorted glob.

    When images were compressed during extraction (e.g. .png → .jpg rename),
    the exact filename won't be found.  A stem-based fallback handles this:
    if 'frame_000001.png' is missing but 'frame_000001.jpg' exists, the jpg
    is used transparently.
    """
    base = Path(base_dir)
    if known_filenames:
        paths = []
        for fname in known_filenames:
            # 1st try: exact filename match (normal case)
            found = list(base.rglob(fname))
            if not found:
                # 2nd try: same stem, any image extension
                # (handles .png → .jpg rename from compress-during-extraction)
                stem = Path(fname).stem
                found = sorted(
                    p for p in base.rglob(f"{stem}.*")
                    if p.suffix.lower() in IMAGE_EXTS
                )
            if found:
                paths.append(str(found[0]))
        if paths:
            return paths

    # Fallback: collect all image files, sort by name
    all_imgs = sorted(
        p for p in base.rglob("*") if p.suffix.lower() in IMAGE_EXTS
    )
    return [str(p) for p in all_imgs]


# ─── Resize helper ───────────────────────────────────────────────────────────

def _load_resized(path: str, max_dim: int = 640) -> Optional[np.ndarray]:
    """
    Read an image and downscale it so the longest side <= max_dim.
    Returns None if the file can't be read.
    Upscaling is never done (scale > 1 is clamped to 1).
    """
    img = cv2.imread(path)
    if img is None:
        return None
    h, w = img.shape[:2]
    scale = min(1.0, max_dim / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


# ─── Quality scoring on raw frames ───────────────────────────────────────────

def score_frames(frame_paths: list[str], sample_count: int = 5, max_dim: int = 640) -> dict:
    """Sample up to sample_count frames, resize to max_dim, return avg blur + brightness."""
    if not frame_paths:
        return {"blur_score": 0.0, "brightness": 0.0}
    step = max(1, len(frame_paths) // (sample_count + 1))
    indices = [min(step * (i + 1), len(frame_paths) - 1) for i in range(sample_count)]
    blurs, brights = [], []
    for idx in indices:
        frame = _load_resized(frame_paths[idx], max_dim)
        if frame is not None:
            blurs.append(compute_blur_score(frame))
            brights.append(compute_brightness(frame))
    return {
        "blur_score": round(float(np.mean(blurs)), 1) if blurs else 0.0,
        "brightness": round(float(np.mean(brights)), 1) if brights else 0.0,
    }


# ─── Signal smoothing ─────────────────────────────────────────────────────────

def _smooth_signal(values: list[float], window: int = 5) -> list[float]:
    """Sliding window mean smoothing; edges are padded to avoid shrinkage."""
    n = len(values)
    if window <= 1 or n <= 1:
        return list(values)
    arr = np.array(values, dtype=np.float64)
    half = window // 2
    padded = np.pad(arr, (half, half), mode="edge")
    kernel = np.ones(window) / window
    smoothed = np.convolve(padded, kernel, mode="valid")
    return smoothed[:n].tolist()


# ─── Thumbnail from image frame ───────────────────────────────────────────────

def save_thumbnail(frame_path: str, output_path: str, size: tuple = (320, 180)) -> bool:
    frame = cv2.imread(frame_path)
    if frame is None:
        return False
    resized = cv2.resize(frame, size)
    return cv2.imwrite(output_path, resized, [cv2.IMWRITE_JPEG_QUALITY, 82])


# ─── Person detection on a list of frames ────────────────────────────────────

def detect_person_in_frames(
    frame_paths: list[str],
    detector: str = "hog",
    sample_count: int = 3,
    max_dim: int = 640,
) -> bool:
    if not frame_paths:
        return False
    step = max(1, len(frame_paths) // (sample_count + 1))
    detect_fn = _yolo_has_person if detector == "yolo" else _hog_has_person
    for i in range(sample_count):
        idx = min(step * (i + 1), len(frame_paths) - 1)
        frame = _load_resized(frame_paths[idx], max_dim)
        if frame is not None and detect_fn(frame):
            return True
    return False


# ─── Per-frame analysis ──────────────────────────────────────────────────────

def analyze_frames_per_frame(
    frame_paths: list[str],
    motion_threshold: float = 0.015,
    low_action_threshold: float = 0.04,
    hand_activity_threshold: float = 0.0,
    smooth_window: int = 5,
    filter_humans: bool = False,
    detector: str = "yolo",
    yolo_model: str = DEFAULT_YOLO_MODEL,
    detection_strategy: str = "single",
    require_center: bool = False,
    center_margin: float = 0.20,
    require_arms: bool = False,
    arm_conf_threshold: float = 0.30,
    person_sample_interval: int = 3,
    continuity_gap_frames: int = 5,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> list[dict]:
    """
    Analyse every frame and assign one of five states:
      keep              — active motion + high hand activity (optical flow),
                          person present & all filters passed (if filter_humans)
      review            — 待审核: person at frame edge / arms not visible / OR
                          motion present but no person detected
      culled_motion     — 静止时段: below motion_threshold (no movement)
      culled_low_action — 整理时段: motion present but optical flow below
                          hand_activity_threshold (person idle / organising)
      culled_person     — 无人时段: active motion but no person detected

    Pipeline:
      Phase 1   — MOG2 motion + dense optical flow (Farneback) on all frames
      Phase 1.5 — Sliding-window smoothing on both signals
      Phase 2   — YOLO person detection (single model, no cascade)
      Phase 3   — State assignment using smoothed motion + flow + person
      Phase 4   — Continuity gap fill (bridges short culled runs between keeps)

    hand_activity_threshold:
      <=0 → auto-calibrate from data (P40 of non-zero flows)
      >0  → use as-is

    Returns list of dicts:
      {path, idx, motion_score, flow_score, state, reason}
    """
    n = len(frame_paths)
    if n == 0:
        return []

    fgbg = cv2.createBackgroundSubtractorMOG2(
        history=300, varThreshold=40, detectShadows=False
    )

    # ── Phase 1: motion + optical flow analysis (all frames) ─────────────────
    motion_data: list[dict] = []
    raw_motions: list[float] = []
    raw_flows: list[float] = []
    prev_gray: Optional[np.ndarray] = None
    last_reported = -1

    for i, path in enumerate(frame_paths):
        frame = cv2.imread(path)
        if frame is None:
            motion_data.append({"idx": i, "path": path, "motion": 0.0, "flow": 0.0, "ok": False})
            raw_motions.append(0.0)
            raw_flows.append(0.0)
            prev_gray = None
        else:
            small = cv2.resize(frame, (320, 180))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            # MOG2 foreground ratio
            fg = fgbg.apply(small)
            motion = float(np.count_nonzero(fg > 127)) / (320 * 180)

            # Dense optical flow magnitude (Farneback)
            flow_mag = 0.0
            if prev_gray is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, gray, None,
                    pyr_scale=0.5, levels=3, winsize=15,
                    iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
                )
                mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                flow_mag = float(np.mean(mag))

            motion_data.append({
                "idx": i, "path": path,
                "motion": motion, "flow": flow_mag, "ok": True,
            })
            raw_motions.append(motion)
            raw_flows.append(flow_mag)
            prev_gray = gray

        if progress_cb:
            pct = int((i + 1) / n * (40 if filter_humans else 80))
            if pct != last_reported:
                progress_cb(pct)
                last_reported = pct

    # ── Phase 1.5: smooth signals + auto-calibrate thresholds ────────────────
    if smooth_window > 1:
        sm_motions = _smooth_signal(raw_motions, smooth_window)
        sm_flows = _smooth_signal(raw_flows, smooth_window)
        for i, d in enumerate(motion_data):
            d["motion"] = sm_motions[i]
            d["flow"] = sm_flows[i]

    # Auto-calibrate hand_activity_threshold from data distribution
    effective_hat = hand_activity_threshold
    non_zero_flows = [d["flow"] for d in motion_data if d["ok"] and d["flow"] > 0.1]
    if effective_hat <= 0 and non_zero_flows:
        effective_hat = float(np.percentile(non_zero_flows, 25))
    elif effective_hat <= 0:
        effective_hat = 1.5   # safe fallback

    logger.info(
        "[analyze] flow stats: min=%.2f median=%.2f mean=%.2f max=%.2f  "
        "hand_activity_threshold=%.2f (auto=%s, smooth=%d)",
        min(raw_flows) if raw_flows else 0,
        float(np.median(raw_flows)) if raw_flows else 0,
        float(np.mean(raw_flows)) if raw_flows else 0,
        max(raw_flows) if raw_flows else 0,
        effective_hat,
        "yes" if hand_activity_threshold <= 0 else "no",
        smooth_window,
    )

    # ── Phase 2: YOLO person detection (single model, no cascade) ────────────
    _STATUS_RANK = {"discard": 0, "review": 1, "keep": 2}
    person_status: list[str] = ["discard"] * n
    person_reason: list[str] = [""] * n
    if filter_humans:
        detect_fn = make_person_detector(
            detector=detector,
            yolo_model=yolo_model,
            detection_strategy=detection_strategy,
            require_center=require_center,
            center_margin=center_margin,
            require_arms=require_arms,
            arm_conf_threshold=arm_conf_threshold,
        )
        motion_pass = [
            d["idx"] for d in motion_data
            if d["ok"] and d["motion"] >= motion_threshold
        ]
        sample_idxs = motion_pass[::person_sample_interval]
        total_samples = max(len(sample_idxs), 1)
        last_reported = -1
        for si, orig_idx in enumerate(sample_idxs):
            frame = cv2.imread(frame_paths[orig_idx])
            if frame is not None:
                result, detect_reason = detect_fn(frame)
                if _STATUS_RANK.get(result, 0) > 0:
                    lo = max(0, orig_idx - person_sample_interval)
                    hi = min(n, orig_idx + person_sample_interval + 1)
                    for k in range(lo, hi):
                        if _STATUS_RANK[result] > _STATUS_RANK.get(person_status[k], 0):
                            person_status[k] = result
                            person_reason[k] = detect_reason
            if progress_cb:
                pct = 40 + int((si + 1) / total_samples * 50)
                if pct != last_reported:
                    progress_cb(pct)
                    last_reported = pct

        # For YOLO / Pose: any motion frame not covered by sampling stays
        # "discard" and would silently become culled_person.  Since YOLO
        # returns at least "review" for any frame without a confident person,
        # unsampled motion frames should default to "review", not "discard".
        if detector in ("yolo", "pose"):
            for i, d in enumerate(motion_data):
                if d["ok"] and d["motion"] >= motion_threshold and person_status[i] == "discard":
                    person_status[i] = "review"
                    person_reason[i] = "unsampled"

    # ── Phase 3: assign state (motion + flow + person) ───────────────────────
    # Optical flow (hand activity) is the key discriminator between
    # "active operation" (keep) and "idle/organising" (culled_low_action).
    records: list[dict] = []
    for d in motion_data:
        i = d["idx"]
        ps = person_status[i]
        pr = person_reason[i]
        flow_val = d.get("flow", 0.0)

        # MOG2 can absorb a steadily-working person into its background model,
        # causing motion scores to drop below motion_threshold even when the
        # person is clearly active.  Optical flow is frame-to-frame and has no
        # such adaptation bias.  We rescue frames where flow alone shows
        # significant activity (using the same threshold as the keep/low-action
        # split so the calibration is consistent).
        has_motion = d["ok"] and (
            d["motion"] >= motion_threshold
            or flow_val >= 0.6 * effective_hat
        )
        if not has_motion:
            state = "culled_motion"
            reason = ""
        elif filter_humans:
            if ps == "keep":
                if flow_val >= effective_hat:
                    state = "keep"
                    reason = ""
                else:
                    state = "culled_low_action"
                    reason = "low_hand_activity"
            elif ps == "review":
                state = "review"
                reason = pr
            else:
                state = "culled_person"
                reason = pr or "no_person"
        else:
            # No human filtering — use flow to distinguish keep vs low_action
            if flow_val >= 0.6 * effective_hat:
                state = "keep"
                reason = ""
            elif d["motion"] >= low_action_threshold:
                state = "keep"
                reason = ""
            else:
                state = "culled_low_action"
                reason = ""

        records.append({
            "path": d["path"],
            "idx": i,
            "motion_score": round(d["motion"], 4),
            "flow_score": round(flow_val, 4),
            "state": state,
            "reason": reason,
        })

    # ── Phase 4: continuity gap fill ──────────────────────────────────────────
    # Only fills 'culled_*' runs between keep frames.  'review' frames are
    # intentionally NOT promoted — they must remain in the review queue.
    if continuity_gap_frames > 0:
        i = 0
        while i < len(records):
            if records[i]["state"] not in ("keep", "review"):
                j = i
                while j < len(records) and records[j]["state"] not in ("keep", "review"):
                    j += 1
                gap_len = j - i
                preceded = i > 0 and records[i - 1]["state"] == "keep"
                followed = j < len(records) and records[j]["state"] == "keep"
                if preceded and followed and gap_len <= continuity_gap_frames:
                    for k in range(i, j):
                        records[k]["state"] = "keep"
                i = j
            else:
                i += 1

    # ── Phase 4b: second-round gap fill for culled_low_action ────────────────
    # More aggressively bridge low-action gaps surrounded by keep frames,
    # using 2× the continuity gap.  This reduces false "organising" segments.
    if continuity_gap_frames > 0:
        max_low_action_gap = continuity_gap_frames * 2
        i = 0
        while i < len(records):
            if records[i]["state"] == "culled_low_action":
                j = i
                while j < len(records) and records[j]["state"] == "culled_low_action":
                    j += 1
                gap_len = j - i
                preceded = i > 0 and records[i - 1]["state"] == "keep"
                followed = j < len(records) and records[j]["state"] == "keep"
                if preceded and followed and gap_len <= max_low_action_gap:
                    for k in range(i, j):
                        records[k]["state"] = "keep"
                i = j
            else:
                i += 1

    kept = sum(1 for r in records if r["state"] == "keep")
    review_cnt = sum(1 for r in records if r["state"] == "review")
    logger.info(
        "[analyze] %d/%d kept  待审核=%d  静止=%d  整理=%d  无人=%d  (gap=%d, hat=%.2f)",
        kept, n, review_cnt,
        sum(1 for r in records if r["state"] == "culled_motion"),
        sum(1 for r in records if r["state"] == "culled_low_action"),
        sum(1 for r in records if r["state"] == "culled_person"),
        continuity_gap_frames, effective_hat,
    )
    return records


def _build_segment(frames: list[dict], fps: float, index: int) -> dict:
    """Build one culled-segment dict from a consecutive run of culled frames."""
    center = frames[len(frames) // 2]
    reasons = [f.get("reason", "") for f in frames if f.get("reason")]
    cull_reason = max(set(reasons), key=reasons.count) if reasons else ""
    return {
        "id": f"seg_{index:04d}",
        "state": frames[0]["state"],
        "start_idx": frames[0]["idx"],
        "end_idx": frames[-1]["idx"],
        "frame_count": len(frames),
        "duration_ms": round(len(frames) / max(fps, 1) * 1000),
        "thumb_url": center["url"],
        "frames": frames,
        "cull_reason": cull_reason,
    }


MIN_SEGMENT_FRAMES = 3  # segments shorter than this are absorbed into neighbors


def _merge_tiny_segments(frame_groups: list[list[dict]], min_frames: int = MIN_SEGMENT_FRAMES) -> list[list[dict]]:
    """
    Absorb tiny frame groups (< min_frames) into their nearest neighbor.
    Tiny groups are merged into whichever adjacent group is larger; ties go left.
    """
    if len(frame_groups) <= 1:
        return frame_groups
    merged = True
    while merged:
        merged = False
        new_groups: list[list[dict]] = []
        i = 0
        while i < len(frame_groups):
            grp = frame_groups[i]
            if len(grp) < min_frames and len(frame_groups) > 1:
                # Absorb into left or right neighbor (whichever is bigger)
                if new_groups and (i + 1 >= len(frame_groups) or len(new_groups[-1]) >= len(frame_groups[i + 1])):
                    new_groups[-1] = new_groups[-1] + grp
                elif i + 1 < len(frame_groups):
                    frame_groups[i + 1] = grp + frame_groups[i + 1]
                else:
                    new_groups.append(grp)
                merged = True
            else:
                new_groups.append(grp)
            i += 1
        frame_groups = new_groups
    return frame_groups


def _group_frames_into_runs(sorted_frames: list[dict], max_gap: int = 5) -> list[list[dict]]:
    """Group sorted frames into consecutive runs of same state with idx gap ≤ max_gap."""
    if not sorted_frames:
        return []
    runs: list[list[dict]] = []
    run: list[dict] = [sorted_frames[0]]
    for frame in sorted_frames[1:]:
        prev = run[-1]
        if frame["state"] == run[0]["state"] and frame["idx"] - prev["idx"] <= max_gap:
            run.append(frame)
        else:
            runs.append(run)
            run = [frame]
    runs.append(run)
    return runs


def group_culled_into_segments(culled_frames: list[dict], fps: float) -> list[dict]:
    """
    Merge consecutive culled frames (same state, idx gap ≤ 5) into segments.
    Segments with < MIN_SEGMENT_FRAMES frames are absorbed into neighbors.
    Returns a list of segment dicts suitable for the review UI.
    """
    if not culled_frames:
        return []
    sorted_frames = sorted(culled_frames, key=lambda f: f["idx"])
    runs = _group_frames_into_runs(sorted_frames)
    runs = _merge_tiny_segments(runs)
    segments = [_build_segment(run, fps, i) for i, run in enumerate(runs)]
    logger.info("[group_culled] %d frames → %d segments (min %d frames/seg)",
                len(culled_frames), len(segments), MIN_SEGMENT_FRAMES)
    return segments


def group_all_into_segments(all_frames: list[dict], fps: float) -> list[dict]:
    """
    Group ALL frames (keep + culled) into consecutive segments by state.
    Segments with < MIN_SEGMENT_FRAMES frames are absorbed into neighbors.
    Returns a unified list of segment dicts suitable for the review UI.
    """
    if not all_frames:
        return []
    sorted_frames = sorted(all_frames, key=lambda f: f["idx"])
    runs = _group_frames_into_runs(sorted_frames)
    runs = _merge_tiny_segments(runs)
    segments = [_build_segment(run, fps, i) for i, run in enumerate(runs)]
    logger.info("[group_all] %d frames → %d segments (min %d frames/seg)",
                len(all_frames), len(segments), MIN_SEGMENT_FRAMES)
    return segments


def build_clips_from_states(
    frame_records: list[dict],
    min_frames: int = 10,
    merge_gap_frames: int = 8,
) -> list[tuple[int, int]]:
    """
    Group consecutive 'keep' frames into (start_idx, end_idx) clip ranges.
    Gaps ≤ merge_gap_frames between keep-runs are bridged.
    Clips with fewer than min_frames keep-frames are discarded.
    Returns list of (start_idx, end_idx) using original frame indices.
    """
    keeps = sorted(r["idx"] for r in frame_records if r["state"] == "keep")
    if not keeps:
        return []

    groups: list[tuple[int, int]] = []
    run_start = keeps[0]
    run_end = keeps[0]
    for idx in keeps[1:]:
        if idx - run_end <= merge_gap_frames:
            run_end = idx
        else:
            groups.append((run_start, run_end))
            run_start = idx
            run_end = idx
    groups.append((run_start, run_end))

    idx_to_state = {r["idx"]: r["state"] for r in frame_records}
    result: list[tuple[int, int]] = []
    for gs, ge in groups:
        keep_count = sum(
            1 for i in range(gs, ge + 1)
            if idx_to_state.get(i) == "keep"
        )
        if keep_count >= min_frames:
            result.append((gs, ge))

    logger.info("[build_clips] %d clips from %d candidate groups", len(result), len(groups))
    return result


# ─── Action segmentation within clips ─────────────────────────────────────────

def segment_actions_in_clip(
    frame_records: list[dict],
    start_idx: int,
    end_idx: int,
    fps: float,
    min_action_frames: int = 8,
    pause_frames: int = 3,
) -> list[dict]:
    """
    Split a keep-frame clip into individual action segments using the flow
    signal.  An "action" is a contiguous run of frames whose flow_score is
    above a local threshold, separated by short dips (pauses).

    Returns list of action dicts:
      {action_idx, start_idx, end_idx, start_ms, end_ms, frame_count}
    """
    clip_records = [
        r for r in frame_records
        if start_idx <= r["idx"] <= end_idx and r.get("state") == "keep"
    ]
    if not clip_records:
        return [{
            "action_idx": 0,
            "start_idx": start_idx, "end_idx": end_idx,
            "start_ms": round(start_idx / max(fps, 1) * 1000),
            "end_ms": round(end_idx / max(fps, 1) * 1000),
            "frame_count": end_idx - start_idx + 1,
        }]

    clip_records.sort(key=lambda r: r["idx"])
    flows = [r.get("flow_score", 0.0) for r in clip_records]

    # Local threshold: 30th-percentile of flows within this clip
    local_thresh = float(np.percentile(flows, 30)) if flows else 0.0

    # Label each frame as active or pause
    active = [f > local_thresh for f in flows]

    # Merge short pause gaps (≤ pause_frames) between active runs
    i = 0
    while i < len(active):
        if not active[i]:
            j = i
            while j < len(active) and not active[j]:
                j += 1
            gap = j - i
            preceded = i > 0 and active[i - 1]
            followed = j < len(active) and active[j] if j < len(active) else False
            if preceded and followed and gap <= pause_frames:
                for k in range(i, j):
                    active[k] = True
            i = j
        else:
            i += 1

    # Extract contiguous active runs as action segments
    actions: list[dict] = []
    seg_start = None
    for i, is_active in enumerate(active):
        if is_active and seg_start is None:
            seg_start = i
        elif not is_active and seg_start is not None:
            if i - seg_start >= min_action_frames:
                s = clip_records[seg_start]["idx"]
                e = clip_records[i - 1]["idx"]
                actions.append({
                    "action_idx": len(actions),
                    "start_idx": s, "end_idx": e,
                    "start_ms": round(s / max(fps, 1) * 1000),
                    "end_ms": round(e / max(fps, 1) * 1000),
                    "frame_count": i - seg_start,
                })
            seg_start = None
    # Flush last run
    if seg_start is not None and len(active) - seg_start >= min_action_frames:
        s = clip_records[seg_start]["idx"]
        e = clip_records[-1]["idx"]
        actions.append({
            "action_idx": len(actions),
            "start_idx": s, "end_idx": e,
            "start_ms": round(s / max(fps, 1) * 1000),
            "end_ms": round(e / max(fps, 1) * 1000),
            "frame_count": len(active) - seg_start,
        })

    # Fallback: if no action detected, treat entire clip as one action
    if not actions:
        actions.append({
            "action_idx": 0,
            "start_idx": start_idx, "end_idx": end_idx,
            "start_ms": round(start_idx / max(fps, 1) * 1000),
            "end_ms": round(end_idx / max(fps, 1) * 1000),
            "frame_count": end_idx - start_idx + 1,
        })

    return actions


# ─── Copy frames to a served directory ───────────────────────────────────────

def _save_frame_maybe_compressed(src: str, dest: str, compress_px: Optional[int]) -> None:
    """
    Save src → dest.  When compress_px > 0, resize so the longest side ≤ compress_px
    before writing (skip resize if the image is already small enough).
    Falls back to hard-link / copy when compress_px is falsy or cv2 can't read the file.
    """
    if compress_px:
        img = cv2.imread(src)
        if img is not None:
            h, w = img.shape[:2]
            if max(h, w) > compress_px:
                scale = compress_px / max(h, w)
                img = cv2.resize(
                    img,
                    (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA,
                )
            cv2.imwrite(dest, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return
    # No compression (or imread failed) — hard-link / copy
    try:
        os.link(src, dest)
    except OSError:
        shutil.copy2(src, dest)


def copy_frames_to_clip_dir(
    frame_paths: list[str],
    clip_frames_dir: str,
    orig_indices: Optional[list[int]] = None,
    compress_px: Optional[int] = None,
) -> list[str]:
    """
    Copy (or hard-link) frames into clip_frames_dir.
    If orig_indices is provided each file is named by its original sequence
    index (enabling chronological re-sort after a restore operation).
    When compress_px > 0, frames are resized and saved as JPEG.
    """
    os.makedirs(clip_frames_dir, exist_ok=True)
    dest_paths: list[str] = []
    for i, src in enumerate(frame_paths):
        name_idx = orig_indices[i] if orig_indices else i
        # Use .jpg when compressing (always JPEG output); keep original ext otherwise
        ext = ".jpg" if compress_px else (Path(src).suffix or ".jpg")
        dest = os.path.join(clip_frames_dir, f"{name_idx:06d}{ext}")
        _save_frame_maybe_compressed(src, dest, compress_px)
        dest_paths.append(dest)
    return dest_paths


# ─── Main entry point ─────────────────────────────────────────────────────────

def process_sequence(
    job_id: str,
    zip_path: str,
    clips_dir: str,
    on_done: Callable,
    on_progress: Optional[Callable[[str, str, int], None]] = None,
    filter_humans: bool = False,
    detector: str = "yolo",
    yolo_model: str = DEFAULT_YOLO_MODEL,
    detection_strategy: str = "single",
    require_center: bool = False,
    center_margin: float = 0.20,
    require_arms: bool = False,
    arm_conf_threshold: float = 0.30,
    motion_threshold: float = 0.015,
    low_action_threshold: float = 0.04,
    hand_activity_threshold: float = 0.0,
    smooth_window: int = 5,
    frame_sample_step: int = 2,
    min_frames: int = 10,
    merge_gap_frames: int = 8,
    continuity_gap_frames: int = 5,
    compress_px: int = 0,
) -> None:
    """
    Full pipeline for a ZIP containing an image sequence:
      1. extract  — unzip into a temp dir
      2. parse    — read extraction_info (JSON/TXT)
      3. analyze  — per-frame motion score + optional person detection
      4. cut      — group keep-frames into clips, copy to clips/frames/{id}/
                    save culled frames to clips/culled/{job_id}/
      5. done     — call on_done with clips_data + culled_frames

    frame_sample_step: process every Nth frame (1 = all frames, 2 = every 2nd, …).
    Uploaded sequences are often already subsampled; set to 1 to skip re-sampling.

    on_progress(job_id, step, pct) is called at key milestones.
    """

    def progress(step: str, pct: int) -> None:
        if on_progress:
            on_progress(job_id, step, pct)
        logger.info("[%s] step=%s pct=%d", job_id, step, pct)

    tmpdir = tempfile.mkdtemp(prefix="seq_")
    try:
        # ── Step 1: extract (with optional on-the-fly compression) ──────────
        progress("extract", 0)
        _extract_zip_maybe_compressed(
            zip_path,
            tmpdir,
            compress_px=compress_px,
            progress_cb=lambda pct: progress("extract", min(pct, 99)),
        )
        progress("extract", 100)
        logger.info(
            "[%s] extracted ZIP to %s (compress_px=%s)",
            job_id, tmpdir, compress_px or "off",
        )

        # ── Step 2: parse extraction_info (JSON preferred, TXT fallback) ─────
        progress("parse", 0)
        json_candidates = list(Path(tmpdir).rglob("extraction_info.json"))
        txt_candidates = list(Path(tmpdir).rglob("extraction_info.txt"))
        info_path = (
            str(json_candidates[0]) if json_candidates
            else str(txt_candidates[0]) if txt_candidates
            else ""
        )
        seq_info = parse_extraction_info(info_path)
        fps = seq_info["fps"]
        frames_meta = seq_info["frames"]
        known_files = [fe["filename"] for fe in frames_meta]
        # Build index→absolute timestamp_ns lookup (None if not available)
        # orig_idx_to_ts_ns keeps the full original-index mapping even after sub-sampling
        idx_to_ts_ns: list[Optional[int]] = [
            fe.get("timestamp_ns") for fe in frames_meta
        ]
        orig_idx_to_ts_ns = list(idx_to_ts_ns)
        logger.info(
            "[%s] fps=%.2f total_frames=%d has_ts=%s",
            job_id, fps, seq_info["total_frames"],
            "yes" if any(t is not None for t in idx_to_ts_ns) else "no",
        )
        image_paths = discover_images(tmpdir, known_files)
        if not image_paths:
            raise RuntimeError("No images found in ZIP archive")
        logger.info("[%s] discovered %d images", job_id, len(image_paths))

        # ── Frame sub-sampling ────────────────────────────────────────────────
        step = max(1, int(frame_sample_step))
        if step > 1:
            sampled_indices = list(range(0, len(image_paths), step))
            sampled_paths = [image_paths[i] for i in sampled_indices]
            sampled_ts = [idx_to_ts_ns[i] if i < len(idx_to_ts_ns) else None
                          for i in sampled_indices]
            logger.info(
                "[%s] sub-sampling step=%d: %d → %d frames",
                job_id, step, len(image_paths), len(sampled_paths),
            )
        else:
            sampled_indices = list(range(len(image_paths)))
            sampled_paths = image_paths
            sampled_ts = list(idx_to_ts_ns)

        # Override for the rest of the pipeline
        image_paths = sampled_paths
        idx_to_ts_ns = sampled_ts
        # Build mapping: analysis idx → original frame idx
        orig_idx_map = {ai: oi for ai, oi in enumerate(sampled_indices)}
        progress("parse", 100)

        # ── Step 3: per-frame analysis ────────────────────────────────────────
        progress("analyze", 0)
        frame_records = analyze_frames_per_frame(
            image_paths,
            motion_threshold=motion_threshold,
            low_action_threshold=low_action_threshold,
            hand_activity_threshold=hand_activity_threshold,
            smooth_window=smooth_window,
            filter_humans=filter_humans,
            detector=detector,
            yolo_model=yolo_model,
            detection_strategy=detection_strategy,
            require_center=require_center,
            center_margin=center_margin,
            require_arms=require_arms,
            arm_conf_threshold=arm_conf_threshold,
            continuity_gap_frames=continuity_gap_frames,
            progress_cb=lambda pct: progress("analyze", pct),
        )

        # Remap analysis idx → original frame idx so timestamps stay correct
        if step > 1:
            for r in frame_records:
                r["idx"] = orig_idx_map.get(r["idx"], r["idx"])
            # Restore full original-index timestamp lookup (sampled_ts was
            # indexed by analysis-idx which no longer matches r["idx"])
            idx_to_ts_ns = orig_idx_to_ts_ns

        clip_ranges = build_clips_from_states(
            frame_records,
            min_frames=min_frames,
            merge_gap_frames=merge_gap_frames,
        )
        if not clip_ranges:
            raise RuntimeError("No motion segments found in sequence")
        progress("analyze", 100)

        # ── Step 4: copy frames & build clip data ─────────────────────────────
        os.makedirs(clips_dir, exist_ok=True)
        thumbs_dir = Path(clips_dir) / "thumbs"
        frames_base = Path(clips_dir) / "frames"
        culled_base = Path(clips_dir) / "culled" / job_id
        thumbs_dir.mkdir(exist_ok=True)
        frames_base.mkdir(exist_ok=True)
        culled_base.mkdir(parents=True, exist_ok=True)

        # Track which frame indices belong to a clip
        in_clip: set[int] = set()
        for gs, ge in clip_ranges:
            in_clip.update(range(gs, ge + 1))

        idx_to_record = {r["idx"]: r for r in frame_records}
        clips_data: list[dict] = []
        total = len(clip_ranges)

        for i, (start_idx, end_idx) in enumerate(clip_ranges):
            progress("cut", int(i / total * 100))

            seg_records = [
                idx_to_record[j] for j in range(start_idx, end_idx + 1)
                if j in idx_to_record
            ]
            seg_paths = [r["path"] for r in seg_records]
            seg_orig_idx = [r["idx"] for r in seg_records]

            if not seg_paths:
                continue

            clip_id = str(uuid.uuid4())
            thumb_filename: Optional[str] = None

            mid = len(seg_paths) // 2
            thumb_path = str(thumbs_dir / f"{clip_id}.jpg")
            if save_thumbnail(seg_paths[mid], thumb_path):
                thumb_filename = f"thumbs/{clip_id}.jpg"

            quality = score_frames(seg_paths)

            clip_frames_dir = str(frames_base / clip_id)
            dest_paths = copy_frames_to_clip_dir(
                seg_paths, clip_frames_dir, seg_orig_idx,
                compress_px=compress_px or None,
            )
            frame_filenames = [
                f"frames/{clip_id}/{Path(p).name}" for p in dest_paths
            ]

            start_ms = int(start_idx / fps * 1000)
            end_ms = int(end_idx / fps * 1000)
            start_ns = idx_to_ts_ns[start_idx] if start_idx < len(idx_to_ts_ns) else None
            end_ns = idx_to_ts_ns[end_idx] if end_idx < len(idx_to_ts_ns) else None

            # Action segmentation within this clip
            actions = segment_actions_in_clip(
                frame_records, start_idx, end_idx, fps,
            )

            clips_data.append({
                "id": clip_id,
                "clip_filename": None,
                "frame_filenames": frame_filenames,
                "fps": fps,
                "thumb_filename": thumb_filename,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "start_ns": start_ns,
                "end_ns": end_ns,
                "start_idx": start_idx,
                "end_idx": end_idx,
                "order": i,
                "has_person": None,
                "actions": actions,
                **quality,
            })
            logger.info(
                "[%s] clip %d/%d idx=%d–%d frames=%d blur=%.1f actions=%d",
                job_id, i + 1, total, start_idx, end_idx,
                len(seg_paths), quality["blur_score"], len(actions),
            )

        # ── Culled frames ─────────────────────────────────────────────────────
        culled_records = [r for r in frame_records if r["idx"] not in in_clip]
        culled_data: list[dict] = []
        _cpx = compress_px or None
        for r in culled_records:
            src = r["path"]
            ext = ".jpg" if _cpx else (Path(src).suffix or ".jpg")
            dest_name = f"{r['idx']:06d}{ext}"
            dest = str(culled_base / dest_name)
            _save_frame_maybe_compressed(src, dest, _cpx)
            culled_data.append({
                "idx": r["idx"],
                "url": f"/clips/culled/{job_id}/{dest_name}",
                "state": r["state"],
                "motion_score": r["motion_score"],
                "timestamp_ns": idx_to_ts_ns[r["idx"]] if r["idx"] < len(idx_to_ts_ns) else None,
            })

        culled_segments = group_culled_into_segments(culled_data, fps)
        logger.info(
            "[%s] culled %d frames → %d segments (待审核=%d 静止=%d 整理=%d 无人=%d)",
            job_id, len(culled_data), len(culled_segments),
            sum(1 for c in culled_data if c["state"] == "review"),
            sum(1 for c in culled_data if c["state"] == "culled_motion"),
            sum(1 for c in culled_data if c["state"] == "culled_low_action"),
            sum(1 for c in culled_data if c["state"] == "culled_person"),
        )

        # ── Build unified all_segments (keep + culled) ────────────────────
        keep_records = [r for r in frame_records if r["idx"] in in_clip]
        keep_frame_data: list[dict] = []
        for r in keep_records:
            src = r["path"]
            ext = ".jpg" if _cpx else (Path(src).suffix or ".jpg")
            dest_name = f"{r['idx']:06d}{ext}"
            # Keep frames already copied into clip dirs; use culled dir for URL
            dest = str(culled_base / dest_name)
            if not os.path.exists(dest):
                _save_frame_maybe_compressed(src, dest, _cpx)
            keep_frame_data.append({
                "idx": r["idx"],
                "url": f"/clips/culled/{job_id}/{dest_name}",
                "state": r["state"],
                "motion_score": r["motion_score"],
                "timestamp_ns": idx_to_ts_ns[r["idx"]] if r["idx"] < len(idx_to_ts_ns) else None,
            })
        all_frame_data = list(culled_data) + keep_frame_data
        all_segments = group_all_into_segments(all_frame_data, fps)

        total_duration_ms = int((len(image_paths) - 1) / fps * 1000) if image_paths else 0
        progress("cut", 100)
        progress("done", 100)
        on_done(job_id, total_duration_ms, clips_data, culled_segments, all_segments)
        logger.info("[%s] done — %d clips, %d culled", job_id, len(clips_data), len(culled_data))

    except Exception as e:
        logger.exception("[%s] sequence processing failed: %s", job_id, e)
        raise
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.info("[%s] cleaned up temp dir %s", job_id, tmpdir)
