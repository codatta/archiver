from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


GARBAGE_PATTERNS = (
    r"^(test|asdf|xxx+|111+|aaa+|null|none|na|n/a)$",
    r"^(.)\1{2,}$",
)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", normalize_text(text))


def tokenize(text: str) -> Set[str]:
    norm = normalize_text(text)
    if not norm:
        return set()
    parts = re.findall(r"[a-z0-9\u4e00-\u9fff]+", norm)
    return {p for p in parts if len(p) >= 2}


def is_garbage_text(text: str, *, min_len: int = 2) -> bool:
    raw = (text or "").strip()
    compact = compact_text(raw)
    if not compact:
        return True
    if len(compact) < min_len:
        return True
    if compact.isdigit():
        return True
    for pattern in GARBAGE_PATTERNS:
        if re.fullmatch(pattern, compact, flags=re.IGNORECASE):
            return True
    if len(set(compact)) == 1:
        return True
    if re.fullmatch(r"[a-z]{4,}", compact) and not re.search(r"[aeiou]", compact):
        return True
    return False


def overlap_score(text: str, vocabulary: Iterable[str]) -> float:
    text_tokens = tokenize(text)
    if not text_tokens:
        return 0.0
    vocab_tokens: Set[str] = set()
    for item in vocabulary:
        vocab_tokens.update(tokenize(str(item)))
    if not vocab_tokens:
        return 0.0
    hit = text_tokens & vocab_tokens
    if not hit:
        norm = normalize_text(text)
        for item in vocabulary:
            item_norm = normalize_text(str(item))
            if item_norm and (item_norm in norm or norm in item_norm):
                hit.add(item_norm)
    return len(hit) / max(len(text_tokens), 1)


def best_overlap(text: str, candidates: Iterable[str]) -> float:
    scores = [overlap_score(text, [candidate]) for candidate in candidates if str(candidate).strip()]
    return max(scores) if scores else 0.0


def load_json_config(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
