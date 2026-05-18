import pytest

from app.matchers.hash_matcher import HashMatcher, _field_selector
from app.models.request import AdapterConfig, MatcherConfig


def make_matcher(canonical_fields=None):
    config = MatcherConfig(
        methodology="hash",
        adapter_config=AdapterConfig(canonical_fields=canonical_fields),
    )
    return HashMatcher(config)


class TestFieldSelector:
    def test_extracts_fields_in_order(self):
        payload = {"address": "0xABC", "network": "Ethereum", "label": "CEX"}
        result = _field_selector(payload, ["address", "network"])
        assert result == "0xabc|ethereum"

    def test_field_order_is_stable(self):
        payload = {"network": "ethereum", "address": "0xabc"}
        r1 = _field_selector(payload, ["address", "network"])
        r2 = _field_selector(payload, ["address", "network"])
        assert r1 == r2

    def test_missing_field_raises(self):
        with pytest.raises(ValueError, match="missing from payload"):
            _field_selector({"address": "0xabc"}, ["address", "network"])

    def test_extra_fields_ignored(self):
        payload = {"address": "0xabc", "network": "ethereum", "confidence": 0.9, "label": "CEX"}
        result = _field_selector(payload, ["address", "network"])
        assert "|" in result
        assert "confidence" not in result
        assert "label" not in result


class TestHashMatcher:
    def test_same_canonical_fields_same_key(self):
        matcher = make_matcher(["address", "network"])
        p1 = {"address": "0xabc", "network": "ethereum", "label": "CEX", "confidence": 0.9}
        p2 = {"address": "0xabc", "network": "ethereum", "label": "DEX", "confidence": 0.6}
        assert matcher.compute_match_key(p1) == matcher.compute_match_key(p2)

    def test_different_address_different_key(self):
        matcher = make_matcher(["address", "network"])
        p1 = {"address": "0xabc", "network": "ethereum"}
        p2 = {"address": "0xdef", "network": "ethereum"}
        assert matcher.compute_match_key(p1) != matcher.compute_match_key(p2)

    def test_match_key_starts_with_mk(self):
        matcher = make_matcher(["address", "network"])
        key = matcher.compute_match_key({"address": "0xabc", "network": "ethereum"})
        assert key.startswith("mk:")

    def test_text_payload_deterministic(self):
        matcher = make_matcher()
        k1 = matcher.compute_match_key("  Hello  World  ")
        k2 = matcher.compute_match_key("hello world")
        assert k1 == k2

    def test_is_match_same_key(self):
        matcher = make_matcher(["address", "network"])
        key = matcher.compute_match_key({"address": "0xabc", "network": "ethereum"})
        result = matcher.is_match(key, key)
        assert result is not None
        assert result.similarity == 1.0

    def test_is_match_different_key_returns_none(self):
        matcher = make_matcher(["address", "network"])
        k1 = matcher.compute_match_key({"address": "0xabc", "network": "ethereum"})
        k2 = matcher.compute_match_key({"address": "0xdef", "network": "ethereum"})
        assert matcher.is_match(k1, k2) is None

    def test_no_canonical_fields_hashes_all_keys_sorted(self):
        matcher = make_matcher(None)
        p1 = {"b": "2", "a": "1"}
        p2 = {"a": "1", "b": "2"}
        assert matcher.compute_match_key(p1) == matcher.compute_match_key(p2)
