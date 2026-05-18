from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.models.request import MatcherConfig


@dataclass
class MatchResult:
    match_key: str
    # similarity is 1.0 for exact hash match, <1.0 for fuzzy (future)
    similarity: float = 1.0


class AbstractMatcher(ABC):
    def __init__(self, config: MatcherConfig):
        self.config = config

    @abstractmethod
    def compute_match_key(self, payload: dict[str, Any] | str) -> str:
        """Compute a match_key from a raw payload."""
        ...

    @abstractmethod
    def is_match(self, a: str, b: str) -> MatchResult | None:
        """
        Compare two match_keys. Returns MatchResult if they match,
        None if they do not.
        """
        ...
