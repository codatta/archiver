from __future__ import annotations

import re
from typing import Any, Dict, List

from robotics_audit.common.text_utils import compact_text, is_garbage_text, normalize_text

ENGLISH_VERBS = {
    "pick", "picks", "picked", "picking",
    "place", "places", "placed", "placing",
    "move", "moves", "moved", "moving",
    "grab", "grabs", "grabbed", "grabbing",
    "grasp", "grasps", "grasped", "grasping",
    "lift", "lifts", "lifted", "lifting",
    "lower", "lowers", "lowered", "lowering",
    "reach", "reaches", "reached", "reaching",
    "push", "pushes", "pushed", "pushing",
    "pull", "pulls", "pulled", "pulling",
    "open", "opens", "opened", "opening",
    "close", "closes", "closed", "closing",
    "pour", "pours", "poured", "pouring",
    "fill", "fills", "filled", "filling",
    "hold", "holds", "held", "holding",
    "release", "releases", "released", "releasing",
    "rotate", "rotates", "rotated", "rotating",
    "insert", "inserts", "inserted", "inserting",
    "remove", "removes", "removed", "removing",
    "press", "presses", "pressed", "pressing",
    "touch", "touches", "touched", "touching",
    "take", "takes", "took", "taken", "taking",
    "put", "puts", "putting",
    "drop", "drops", "dropped", "dropping",
    "slide", "slides", "slid", "sliding",
    "align", "aligns", "aligned", "aligning",
    "adjust", "adjusts", "adjusted", "adjusting",
}


def contains_word(text: str, word: str) -> bool:
    token = (word or "").strip()
    if not token:
        return False
    if re.search(r"[\u4e00-\u9fff]", token):
        return token in text
    return bool(re.search(rf"\b{re.escape(token)}\b", text, flags=re.IGNORECASE))


def contains_any_word(text: str, words: List[str]) -> bool:
    return any(contains_word(text, word) for word in words)


def is_plausible_description(description: str, word_lists: Dict[str, List[str]]) -> bool:
    raw = (description or "").strip()
    if not raw or is_garbage_text(raw, min_len=4):
        return False

    if re.search(r"[\u4e00-\u9fff]", raw):
        return len(compact_text(raw)) >= 4

    norm = normalize_text(raw)
    words = re.findall(r"[a-zA-Z']+", norm)
    if len(words) < 2:
        return False

    if not any(re.search(r"[aeiou]", word, flags=re.IGNORECASE) for word in words):
        return False

    has_verb = any(word.lower() in ENGLISH_VERBS for word in words)
    if has_verb:
        return True

    action_hits = contains_any_word(raw, word_lists.get("action", []))
    object_hits = contains_any_word(raw, word_lists.get("object", []))
    subject_hits = contains_any_word(raw, word_lists.get("subject", []))
    if action_hits and (object_hits or subject_hits):
        return True

    if len(words) >= 3 and any(word.lower() in ENGLISH_VERBS for word in words[:3]):
        return True

    return len(words) >= 4
