"""定价逻辑单元测试 — 测 resolve_price() 函数

背景：每条数据记录在被消费者拉取时会查一个价格表（pricing_schedule），
按 frontier → task → quality_tier 三级匹配，越精确的规则优先级越高，
找不到任何规则时返回默认价 $0.00。

注意：所有测试都通过 monkeypatch 把 _refresh_cache 替换成空操作，
确保完全不走数据库，只测纯匹配逻辑。
"""
import pytest
from decimal import Decimal

import app.pricing as pricing


# ---------- 辅助：构造一条价格规则 ----------

def _rule(frontier_id, unit_price_usd, task_id=None, quality_tier=None):
    return {
        "frontier_id": frontier_id,
        "task_id": task_id,
        "quality_tier": quality_tier,
        "unit_price_usd": unit_price_usd,
        "effective_from": None,
        "effective_until": None,
    }


@pytest.fixture(autouse=True)
def no_db(monkeypatch):
    """每个测试自动 patch _refresh_cache 为空操作，完全隔离数据库。"""
    monkeypatch.setattr(pricing, "_refresh_cache", lambda: None)


def _set(monkeypatch, schedules: list[dict]) -> None:
    monkeypatch.setattr(pricing, "_cache", schedules)


# ---------- 测试用例 ----------

def test_价格表为空时返回默认价格零(monkeypatch):
    # 没有配置任何价格规则 → 应该返回 $0.00
    _set(monkeypatch, [])
    result = pricing.resolve_price("frontier-1")
    assert result == Decimal("0.00"), f"期望 0.00，实际得到 {result}"


def test_精确匹配到规则时返回对应价格(monkeypatch):
    # frontier=10, task=99, 质量等级=A → 价格 $0.05
    _set(monkeypatch, [_rule("10", "0.05", task_id="99", quality_tier="A")])
    result = pricing.resolve_price("10", "99", "A")
    assert result == Decimal("0.05"), f"期望 0.05，实际得到 {result}"


def test_精确规则优先于宽泛规则(monkeypatch):
    # 同时存在两条规则：
    #   - frontier=10（宽泛，$0.01）
    #   - frontier=10 + task=99 + tier=S（精确，$0.10）
    # 查询 frontier=10, task=99, tier=S → 应该匹配精确规则，返回 $0.10
    _set(monkeypatch, [
        _rule("10", "0.01"),                                   # 宽泛规则
        _rule("10", "0.10", task_id="99", quality_tier="S"),   # 精确规则
    ])
    result = pricing.resolve_price("10", "99", "S")
    assert result == Decimal("0.10"), f"期望精确规则 0.10，实际得到 {result}"


def test_没有精确规则时回退到宽泛规则(monkeypatch):
    # 只有 frontier=10 的宽泛规则，没有针对具体 task 的规则
    # 查任意 task → 应该用宽泛规则，返回 $0.02
    _set(monkeypatch, [_rule("10", "0.02")])
    result = pricing.resolve_price("10", task_id="999", quality_tier="B")
    assert result == Decimal("0.02"), f"期望回退到宽泛规则 0.02，实际得到 {result}"


def test_frontier不匹配时返回默认价格零(monkeypatch):
    # 价格表里只有 frontier=10 的规则，查 frontier=99 → 找不到 → $0.00
    _set(monkeypatch, [_rule("10", "0.02")])
    result = pricing.resolve_price("99")
    assert result == Decimal("0.00"), f"期望 0.00，实际得到 {result}"
