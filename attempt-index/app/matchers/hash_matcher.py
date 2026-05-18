import hashlib
import unicodedata
from typing import Any

from app.matchers.base import AbstractMatcher, MatchResult
from app.models.request import MatcherConfig


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = " ".join(text.split())
    return text


def _field_selector(payload: dict[str, Any], canonical_fields: list[str]) -> str:
    """Extract canonical_fields from a structured payload and join with '|'."""
    parts = []
    for field in canonical_fields:
        if field not in payload:
            raise ValueError(f"canonical_field '{field}' missing from payload")
        parts.append(str(payload[field]).strip().lower())
    return "|".join(parts)


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class HashMatcher(AbstractMatcher):
    def __init__(self, config: MatcherConfig):
        super().__init__(config)

    def compute_match_key(self, payload: dict[str, Any] | str) -> str:
        canonical_fields = self.config.adapter_config.canonical_fields

        if isinstance(payload, dict):
            if canonical_fields:
                raw = _field_selector(payload, canonical_fields)
            else:
                # No canonical_fields: hash all keys sorted for determinism
                raw = "|".join(f"{k}={payload[k]}" for k in sorted(payload.keys()))
        else:
            raw = _normalize_text(payload)

        return f"mk:{_sha256_hex(raw)}"

    def is_match(self, a: str, b: str) -> MatchResult | None:
        if a == b:
            return MatchResult(match_key=a, similarity=1.0)
        return None


def get_matcher(config: MatcherConfig) -> AbstractMatcher:
    # V0: only hash methodology supported
    return HashMatcher(config)
