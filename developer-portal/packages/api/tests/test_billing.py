from unittest.mock import MagicMock, patch

AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


def setup_auth(mock_supabase):
    mock_supabase.auth.get_user.side_effect = None
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "dev@example.com"
    mock_user.email_confirmed_at = "2026-01-01T00:00:00Z"
    mock_user.user_metadata = {}
    mock_result = MagicMock()
    mock_result.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_result


async def test_get_balance(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    # _get_or_create_account uses .select("*").eq("org_id").eq("environment").execute()
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{
            "id": "acc-1",
            "org_id": "org-1",
            "environment": "test",
            "balance_available_usd": 8420,
            "balance_frozen_usd": 1580,
            "balance_earnings_usd": 0,
        }]
    )

    res = await client.get("/v1/orgs/org-1/billing/balance", headers=AUTH_HEADERS)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["balance_available_usd"] == 8420


async def test_get_balance_auto_creates_account(client, mock_supabase, as_org_owner):
    """When no account exists, _get_or_create_account inserts a zeroed-out row."""
    setup_auth(mock_supabase)
    # select returns empty → insert is called
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    mock_supabase.table.return_value.insert.return_value.execute.return_value = (
        MagicMock(data=[{
            "id": "acc-new",
            "org_id": "org-1",
            "environment": "test",
            "balance_available_usd": 0,
            "balance_frozen_usd": 0,
            "balance_spent_usd": 0,
            "balance_earnings_usd": 0,
        }])
    )

    res = await client.get("/v1/orgs/org-1/billing/balance", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert res.json()["data"]["balance_available_usd"] == 0


async def test_create_checkout(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)

    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/test_session"

    with patch("app.routes.billing.stripe") as mock_stripe:
        mock_stripe.checkout.Session.create.return_value = mock_session

        res = await client.post(
            "/v1/orgs/org-1/billing/checkout",
            json={"amount_cents": 10000},
            headers=AUTH_HEADERS,
        )

    assert res.status_code == 200
    assert "checkout.stripe.com" in res.json()["data"]["checkout_url"]


async def test_list_transactions(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)

    def table_side_effect(name):
        result = MagicMock()
        if name == "accounts":
            # _get_or_create_account uses .select("*").eq().eq().execute()
            chain = result.select.return_value
            chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "acc-1", "org_id": "org-1", "environment": "test"}]
            )
        elif name == "transactions":
            # list_transactions chain: .select().eq(account_id).eq(env).order().limit().execute()
            chain = result.select.return_value
            (
                chain.eq.return_value.eq.return_value
                .order.return_value.limit.return_value.execute.return_value
            ) = (
                MagicMock(data=[
                    {"id": "t1", "type": "topup", "amount_usd": 10000},
                    {"id": "t2", "type": "freeze", "amount_usd": -17.35},
                ])
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    res = await client.get("/v1/orgs/org-1/billing/transactions", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2

    mock_supabase.table.side_effect = None


async def test_stripe_webhook_invalid_sig(client, mock_supabase):
    """The Stripe webhook is mounted under /v1/billing (no org_id prefix)."""
    with patch("app.routes.billing.stripe") as mock_stripe:
        mock_stripe.Webhook.construct_event.side_effect = Exception("bad sig")

        res = await client.post(
            "/v1/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "bad"},
        )

    assert res.status_code == 400
