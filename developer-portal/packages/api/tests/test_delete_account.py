from unittest.mock import MagicMock

import pytest

AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


def setup_auth(mock_supabase, email="dev@example.com"):
    mock_supabase.auth.get_user.side_effect = None
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = email
    mock_user.email_confirmed_at = "2026-01-01T00:00:00Z"
    mock_user.user_metadata = {}
    mock_result = MagicMock()
    mock_result.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_result


def _mock_table_chain():
    """Build a mock chain for supabase.table(...).select/delete/eq/is_/single/execute."""
    chain = MagicMock()
    chain.select.return_value = chain
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.is_.return_value = chain
    chain.single.return_value = chain
    return chain


# ── Email mismatch → 400 ─────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_delete_account_email_mismatch(client, mock_supabase):
    setup_auth(mock_supabase, email="real@example.com")

    res = await client.request("DELETE",
        "/v1/auth/account",
        params={"confirm_email": "wrong@example.com"},
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 400
    assert "does not match" in res.json()["detail"].lower()


# ── Missing profile → 404 ────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_delete_account_missing_profile(client, mock_supabase):
    setup_auth(mock_supabase, email="dev@example.com")

    chain = _mock_table_chain()
    chain.execute.return_value = MagicMock(data=None)
    mock_supabase.table.return_value = chain

    res = await client.request("DELETE",
        "/v1/auth/account",
        params={"confirm_email": "dev@example.com"},
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 404
    assert "profile" in res.json()["detail"].lower()


# ── Sole member → org cleaned up ─────────────────────────────────────────────


@pytest.mark.anyio
async def test_delete_account_sole_member_cleans_org(client, mock_supabase):
    setup_auth(mock_supabase, email="dev@example.com")

    call_log = []

    def table_router(name):
        call_log.append(name)
        chain = _mock_table_chain()

        if name == "users" and "users" not in [c for c in call_log[:-1]]:
            # First users call: select user profile
            chain.execute.return_value = MagicMock(
                data={"id": "db-user-1"}
            )
        elif name == "org_memberships":
            if len([c for c in call_log if c == "org_memberships"]) == 1:
                # First call: select memberships
                chain.execute.return_value = MagicMock(
                    data=[{"org_id": "org-1", "role": "owner"}]
                )
            elif len([c for c in call_log if c == "org_memberships"]) == 2:
                # Second call: delete memberships
                chain.execute.return_value = MagicMock(data=[])
            else:
                # Third call: check remaining members → empty
                chain.execute.return_value = MagicMock(data=[])
        elif name == "org_invitations":
            chain.execute.return_value = MagicMock(data=[])
        elif name == "api_keys":
            chain.execute.return_value = MagicMock(data=[])
        elif name == "organizations":
            chain.execute.return_value = MagicMock(data=[])
        else:
            # Org data tables (delivery_items, subscriptions, etc.)
            chain.execute.return_value = MagicMock(data=[])
        return chain

    mock_supabase.table.side_effect = table_router
    mock_supabase.auth.admin.delete_user.return_value = None

    res = await client.request("DELETE",
        "/v1/auth/account",
        params={"confirm_email": "dev@example.com"},
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 200
    data = res.json()
    assert data["deleted"] is True
    step_names = [s["step"] for s in data["steps"]]
    assert "org_cleanup" in step_names
    assert "auth" in step_names
    assert "profile" in step_names


# ── Multi-member → org preserved ─────────────────────────────────────────────


@pytest.mark.anyio
async def test_delete_account_multi_member_preserves_org(client, mock_supabase):
    setup_auth(mock_supabase, email="dev@example.com")

    call_log = []

    def table_router(name):
        call_log.append(name)
        chain = _mock_table_chain()

        if name == "users":
            chain.execute.return_value = MagicMock(
                data={"id": "db-user-1"}
            )
        elif name == "org_memberships":
            count = len([c for c in call_log if c == "org_memberships"])
            if count == 1:
                chain.execute.return_value = MagicMock(
                    data=[{"org_id": "org-1", "role": "member"}]
                )
            elif count == 2:
                chain.execute.return_value = MagicMock(data=[])
            else:
                # Remaining members check → org has other members
                chain.execute.return_value = MagicMock(
                    data=[{"id": "other-member"}]
                )
        elif name == "org_invitations":
            chain.execute.return_value = MagicMock(data=[])
        elif name == "api_keys":
            chain.execute.return_value = MagicMock(data=[])
        else:
            chain.execute.return_value = MagicMock(data=[])
        return chain

    mock_supabase.table.side_effect = table_router
    mock_supabase.auth.admin.delete_user.return_value = None

    res = await client.request("DELETE",
        "/v1/auth/account",
        params={"confirm_email": "dev@example.com"},
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 200
    data = res.json()
    assert data["deleted"] is True
    step_names = [s["step"] for s in data["steps"]]
    assert "org_cleanup" not in step_names


# ── Auth deletion failure → 502 ──────────────────────────────────────────────


@pytest.mark.anyio
async def test_delete_account_auth_failure_returns_502(client, mock_supabase):
    setup_auth(mock_supabase, email="dev@example.com")

    def table_router(name):
        chain = _mock_table_chain()
        if name == "users":
            chain.execute.return_value = MagicMock(
                data={"id": "db-user-1"}
            )
        elif name == "org_memberships":
            chain.execute.return_value = MagicMock(data=[])
        elif name == "org_invitations":
            chain.execute.return_value = MagicMock(data=[])
        elif name == "api_keys":
            chain.execute.return_value = MagicMock(data=[])
        else:
            chain.execute.return_value = MagicMock(data=[])
        return chain

    mock_supabase.table.side_effect = table_router
    mock_supabase.auth.admin.delete_user.side_effect = Exception(
        "Supabase auth error"
    )

    res = await client.request("DELETE",
        "/v1/auth/account",
        params={"confirm_email": "dev@example.com"},
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 502
    assert "auth" in res.json()["detail"].lower()


# ── Trimmed email matches ────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_delete_account_trimmed_email_matches(client, mock_supabase):
    setup_auth(mock_supabase, email="dev@example.com")

    def table_router(name):
        chain = _mock_table_chain()
        if name == "users":
            chain.execute.return_value = MagicMock(
                data={"id": "db-user-1"}
            )
        elif name == "org_memberships":
            chain.execute.return_value = MagicMock(data=[])
        elif name == "org_invitations":
            chain.execute.return_value = MagicMock(data=[])
        elif name == "api_keys":
            chain.execute.return_value = MagicMock(data=[])
        else:
            chain.execute.return_value = MagicMock(data=[])
        return chain

    mock_supabase.table.side_effect = table_router
    mock_supabase.auth.admin.delete_user.side_effect = None
    mock_supabase.auth.admin.delete_user.return_value = None

    # Email with trailing space should still match
    res = await client.request("DELETE",
        "/v1/auth/account",
        params={"confirm_email": "  dev@example.com  "},
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 200
    assert res.json()["deleted"] is True
