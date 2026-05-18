"""Tests for consumer-facing data API endpoints."""
from unittest.mock import MagicMock

VALID_KEY = "hb_live_sk_abc123xyz456789012345678901234567890"
AUTH = {"Authorization": f"Bearer {VALID_KEY}"}


def setup_key_auth(mock_supabase, org_id="org-1"):
    """Mock a valid API key lookup."""
    mock_supabase.table.side_effect = None

    def table_side_effect(name):
        result = MagicMock()
        if name == "api_keys":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={
                    "id": "key-1", "org_id": org_id, "name": "Test",
                    "status": "active", "expires_at": None,
                })
            )
            result.update.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        return result

    mock_supabase.table.side_effect = table_side_effect
    return table_side_effect


async def test_pull_data_success(client, mock_supabase):
    setup_key_auth(mock_supabase)

    def table_effect(name):
        result = MagicMock()
        if name == "api_keys":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={
                    "id": "key-1", "org_id": "org-1", "name": "Test",
                    "status": "active", "expires_at": None,
                })
            )
            result.update.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        elif name == "subscriptions":
            chain = result.select.return_value
            chain.eq.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={
                    "id": "sub-1", "org_id": "org-1",
                    "vertical_id": "vert-1", "status": "active",
                })
            )
        elif name == "delivery_items":
            chain = result.select.return_value
            (
                chain.eq.return_value.eq.return_value
                .order.return_value.limit.return_value.execute.return_value
            ) = (
                MagicMock(data=[
                    {"id": "item-1", "vertical_id": "vert-1", "quality_score": 0.9},
                    {"id": "item-2", "vertical_id": "vert-1", "quality_score": 0.8},
                ])
            )
        return result

    mock_supabase.table.side_effect = table_effect

    res = await client.get(
        "/v1/data/pull?subscription_id=sub-1&limit=10",
        headers=AUTH,
    )
    assert res.status_code == 200
    assert res.json()["count"] == 2

    mock_supabase.table.side_effect = None


async def test_pull_data_no_key(client, mock_supabase):
    res = await client.get("/v1/data/pull?subscription_id=sub-1")
    assert res.status_code == 401


async def test_adopt_item_success(client, mock_supabase):
    def table_effect(name):
        result = MagicMock()
        if name == "api_keys":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={
                    "id": "key-1", "org_id": "org-1", "name": "Test",
                    "status": "active", "expires_at": None,
                })
            )
            result.update.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        elif name == "delivery_items":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={
                    "id": "item-1",
                    "delivery_id": None,
                    "status": "pending",
                    "org_id": "org-1",
                    "unit_price_usd": 0,
                    "environment": "production",
                })
            )
        return result

    mock_supabase.table.side_effect = table_effect

    res = await client.post("/v1/data/items/item-1/adopt", headers=AUTH)
    assert res.status_code == 200
    assert res.json()["status"] == "adopted"

    mock_supabase.table.side_effect = None


async def test_dispute_item_success(client, mock_supabase):
    def table_effect(name):
        result = MagicMock()
        if name == "api_keys":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={
                    "id": "key-1", "org_id": "org-1", "name": "Test",
                    "status": "active", "expires_at": None,
                })
            )
            result.update.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        elif name == "delivery_items":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={
                    "id": "item-2",
                    "delivery_id": None,
                    "status": "pending",
                    "org_id": "org-1",
                })
            )
        return result

    mock_supabase.table.side_effect = table_effect

    res = await client.post("/v1/data/items/item-2/dispute", headers=AUTH)
    assert res.status_code == 200
    assert res.json()["status"] == "disputed"

    mock_supabase.table.side_effect = None


async def test_adopt_item_not_found(client, mock_supabase):
    def table_effect(name):
        result = MagicMock()
        if name == "api_keys":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={
                    "id": "key-1", "org_id": "org-1", "name": "Test",
                    "status": "active", "expires_at": None,
                })
            )
            result.update.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        elif name == "delivery_items":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data=None)
            )
        return result

    mock_supabase.table.side_effect = table_effect

    res = await client.post("/v1/data/items/fake/adopt", headers=AUTH)
    assert res.status_code == 404

    mock_supabase.table.side_effect = None


async def test_list_deliveries(client, mock_supabase):
    def table_effect(name):
        result = MagicMock()
        if name == "api_keys":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={
                    "id": "key-1", "org_id": "org-1", "name": "Test",
                    "status": "active", "expires_at": None,
                })
            )
            result.update.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        elif name == "subscriptions":
            chain = result.select.return_value
            chain.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "sub-1"}]
            )
        elif name == "deliveries":
            chain = result.select.return_value
            chain.in_.return_value.order.return_value.limit.return_value.execute.return_value = (
                MagicMock(data=[
                    {"id": "del-1", "status": "pending", "total_items": 5},
                ])
            )
        return result

    mock_supabase.table.side_effect = table_effect

    res = await client.get("/v1/data/deliveries", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1

    mock_supabase.table.side_effect = None
