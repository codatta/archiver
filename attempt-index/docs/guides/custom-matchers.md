# Custom Matchers — Extending the Matching Engine

AttemptIndex ships with a hash matcher for structured and text payloads. When you need a different matching strategy — perceptual similarity for images, embedding-based semantic matching for text, audio fingerprinting — you implement a custom matcher.

Matchers are pluggable via an abstract base class. Adding a new modality or detection strategy requires two things:

1. A class that extends `AbstractMatcher`
2. A one-line registration in `get_matcher()`

---

## The matcher interface

```python
# app/matchers/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from app.models.request import MatcherConfig


@dataclass
class MatchResult:
    match_key: str
    similarity: float = 1.0   # 1.0 = exact match, <1.0 = fuzzy


class AbstractMatcher(ABC):
    def __init__(self, config: MatcherConfig):
        self.config = config

    @abstractmethod
    def compute_match_key(self, payload: dict[str, Any] | str) -> str:
        """Derive a match key from a raw payload. Must be deterministic."""
        ...

    @abstractmethod
    def is_match(self, a: str, b: str) -> MatchResult | None:
        """
        Compare two match keys.
        Return MatchResult if they are considered a match, None otherwise.
        """
        ...
```

### Contract

| Method | Requirement |
|--------|------------|
| `compute_match_key` | Must be **deterministic** — same input always produces the same key |
| `compute_match_key` | Return value must start with `mk:` |
| `is_match` | Return `MatchResult` if the two keys represent the same (or sufficiently similar) content |
| `is_match` | Return `None` if the keys do not match |
| Both | Must not raise exceptions on valid input — catch and handle internally |

---

## Registration

Matchers are selected by `matcher_config.methodology`. The factory function maps methodology names to classes:

```python
# app/matchers/hash_matcher.py

def get_matcher(config: MatcherConfig) -> AbstractMatcher:
    if config.methodology == "perceptual":
        from app.matchers.perceptual_matcher import PerceptualMatcher
        return PerceptualMatcher(config)
    if config.methodology == "embedding":
        from app.matchers.embedding_matcher import EmbeddingMatcher
        return EmbeddingMatcher(config)
    # default
    return HashMatcher(config)
```

Add your matcher's methodology name here and it becomes available to all callers.

---

## Example: perceptual hash matcher for images (V2)

Perceptual hashing (pHash / dHash) detects visually similar images even after minor edits — cropping, recolouring, JPEG recompression — where SHA-256 would produce a completely different hash.

```python
# app/matchers/perceptual_matcher.py

from typing import Any
from app.matchers.base import AbstractMatcher, MatchResult
from app.models.request import MatcherConfig


class PerceptualMatcher(AbstractMatcher):
    """
    Hamming-distance matcher over perceptual hashes.
    Requires 'imagehash' package: pip install imagehash Pillow
    match_key format: mk:phash:{64-char hex}
    """

    DEFAULT_THRESHOLD = 10  # Hamming distance ≤ 10 → match

    def __init__(self, config: MatcherConfig):
        super().__init__(config)
        self.threshold = config.adapter_config.threshold or self.DEFAULT_THRESHOLD

    def compute_match_key(self, payload: dict[str, Any] | str) -> str:
        import imagehash
        from PIL import Image
        import io, base64

        # payload is expected to be a base64-encoded image or a file path
        if isinstance(payload, dict):
            image_bytes = base64.b64decode(payload["image_b64"])
        else:
            image_bytes = base64.b64decode(payload)

        img = Image.open(io.BytesIO(image_bytes))
        phash = imagehash.phash(img)
        return f"mk:phash:{str(phash)}"

    def is_match(self, a: str, b: str) -> MatchResult | None:
        if not (a.startswith("mk:phash:") and b.startswith("mk:phash:")):
            return None

        import imagehash
        hash_a = imagehash.hex_to_hash(a.removeprefix("mk:phash:"))
        hash_b = imagehash.hex_to_hash(b.removeprefix("mk:phash:"))

        distance = hash_a - hash_b  # Hamming distance
        if distance <= self.threshold:
            # Normalise similarity: distance 0 → 1.0, distance = threshold → 0.0
            similarity = 1.0 - (distance / self.threshold)
            return MatchResult(match_key=a, similarity=round(similarity, 4))

        return None
```

Request using this matcher:

```json
{
  "payload_type": "image",
  "matcher_config": {
    "methodology": "perceptual",
    "adapter_config": {"threshold": 10}
  },
  "payload": {"image_b64": "...base64..."}
}
```

---

## Example: embedding similarity matcher for text (Stage 2)

Embedding matchers detect semantically equivalent content — paraphrased sentences, translated text — that hash matchers would miss. They are expensive and intended for Stage 2 (run only when Stage 1 is inconclusive).

```python
# app/matchers/embedding_matcher.py

from typing import Any
import json
from app.matchers.base import AbstractMatcher, MatchResult
from app.models.request import MatcherConfig


class EmbeddingMatcher(AbstractMatcher):
    """
    Cosine-similarity matcher over text embeddings.
    match_key format: mk:emb:{vector_store_id}
    
    The vector is stored externally (e.g. pgvector, Pinecone).
    compute_match_key generates and stores the vector, returns its ID.
    is_match retrieves both vectors and computes cosine similarity.
    """

    DEFAULT_THRESHOLD = 0.92

    def __init__(self, config: MatcherConfig):
        super().__init__(config)
        self.threshold = config.adapter_config.threshold or self.DEFAULT_THRESHOLD
        self._model = None  # lazy-loaded

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def compute_match_key(self, payload: dict[str, Any] | str) -> str:
        text = payload if isinstance(payload, str) else payload.get("text", "")
        vector = self._get_model().encode(text).tolist()

        # Store vector in your vector DB; return a reference ID
        vector_id = _store_vector(vector)
        return f"mk:emb:{vector_id}"

    def is_match(self, a: str, b: str) -> MatchResult | None:
        if not (a.startswith("mk:emb:") and b.startswith("mk:emb:")):
            return None

        vec_a = _load_vector(a.removeprefix("mk:emb:"))
        vec_b = _load_vector(b.removeprefix("mk:emb:"))
        similarity = _cosine_similarity(vec_a, vec_b)

        if similarity >= self.threshold:
            return MatchResult(match_key=a, similarity=round(similarity, 4))

        return None


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _store_vector(vector: list[float]) -> str:
    # Implement: store in pgvector, Pinecone, etc.
    # Return a stable ID that can later be used to retrieve the vector.
    raise NotImplementedError

def _load_vector(vector_id: str) -> list[float]:
    # Implement: retrieve from your vector store by ID.
    raise NotImplementedError
```

---

## Example: agentic AI matcher

For complex content — video scenes, audio segments, structured documents — you can wrap an AI agent call as a matcher. The agent receives the payload, performs its own analysis, and returns a match key or similarity score.

```python
# app/matchers/agent_matcher.py

from typing import Any
from app.matchers.base import AbstractMatcher, MatchResult
from app.models.request import MatcherConfig


class AgentMatcher(AbstractMatcher):
    """
    Delegates match key computation to an external AI agent.
    The agent endpoint must conform to the Label Studio ML Backend
    protocol: POST /predict with the payload, returns a match_key.
    """

    def __init__(self, config: MatcherConfig):
        super().__init__(config)
        self.agent_url = config.adapter_config.agent_url
        self.threshold = config.adapter_config.threshold or 0.9

    def compute_match_key(self, payload: dict[str, Any] | str) -> str:
        import httpx
        response = httpx.post(
            f"{self.agent_url}/predict",
            json={"payload": payload},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["match_key"]

    def is_match(self, a: str, b: str) -> MatchResult | None:
        import httpx
        response = httpx.post(
            f"{self.agent_url}/compare",
            json={"match_key_a": a, "match_key_b": b},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        similarity = data.get("similarity", 0.0)
        if similarity >= self.threshold:
            return MatchResult(match_key=a, similarity=similarity)
        return None
```

Register it:

```python
# in get_matcher()
if config.methodology == "agent":
    from app.matchers.agent_matcher import AgentMatcher
    return AgentMatcher(config)
```

Call it:

```json
{
  "matcher_config": {
    "methodology": "agent",
    "adapter_config": {
      "agent_url": "http://my-agent-service:8080",
      "threshold": 0.88
    }
  }
}
```

---

## Extending AdapterConfig

`AdapterConfig` in `app/models/request.py` currently holds `canonical_fields`. Add fields as your matchers need them:

```python
# app/models/request.py

class AdapterConfig(BaseModel):
    canonical_fields: list[str] | None = None
    threshold: float | None = None          # for fuzzy matchers
    agent_url: str | None = None            # for agent-based matchers
    model_name: str | None = None           # for embedding matchers
    frame_sample_rate: int | None = None    # for video matchers (V3)
```

All new fields should be optional with sensible defaults inside the matcher class itself — callers that don't need them are unaffected.

---

## Testing a new matcher

Unit test your matcher independently of the service:

```python
# tests/test_perceptual_matcher.py

from app.matchers.perceptual_matcher import PerceptualMatcher
from app.models.request import AdapterConfig, MatcherConfig


def make_matcher(threshold=10):
    return PerceptualMatcher(MatcherConfig(
        methodology="perceptual",
        adapter_config=AdapterConfig(threshold=threshold),
    ))


def test_similar_images_match():
    matcher = make_matcher()
    key_a = matcher.compute_match_key({"image_b64": ORIGINAL_IMAGE_B64})
    key_b = matcher.compute_match_key({"image_b64": SLIGHTLY_EDITED_B64})
    result = matcher.is_match(key_a, key_b)
    assert result is not None
    assert result.similarity > 0.5


def test_different_images_do_not_match():
    matcher = make_matcher()
    key_a = matcher.compute_match_key({"image_b64": IMAGE_A_B64})
    key_b = matcher.compute_match_key({"image_b64": COMPLETELY_DIFFERENT_B64})
    assert matcher.is_match(key_a, key_b) is None
```

Once unit tests pass, the matcher integrates automatically into the full `evaluate` flow with no other changes.
