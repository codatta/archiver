from unittest.mock import MagicMock, patch

AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


def setup_auth(mock_supabase):
    mock_supabase.auth.get_user.side_effect = None
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "owner@example.com"
    mock_user.email_confirmed_at = "2026-01-01T00:00:00Z"
    mock_user.user_metadata = {}
    mock_result = MagicMock()
    mock_result.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_result


async def test_list_members(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[
            {"id": "m1", "role": "owner", "users": {"name": "Yi", "email": "yi@acme.ai"}},
            {"id": "m2", "role": "admin", "users": {"name": "Anna", "email": "anna@acme.ai"}},
        ]
    )

    res = await client.get("/v1/orgs/org-1/members", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2


async def test_invite_member(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)

    def table_side_effect(name):
        result = MagicMock()
        if name == "users":
            # select by email: existing user; select by auth_id: inviter lookup
            result.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "invitee-1"}]
            )
            result.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": "inviter-1", "email": "owner@example.com"})
            )
        elif name == "organizations":
            result.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"name": "Test Org"})
            )
        elif name == "org_memberships":
            # existing membership check returns empty (not yet a member)
            result.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[])
            )
            result.insert.return_value.execute.return_value = MagicMock(
                data=[{"id": "m3", "role": "member", "user_id": "invitee-1"}]
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    with patch("app.routes.members.send_invite_email", return_value=True), \
         patch("app.routes.members.queue_invite_notification"):
        res = await client.post(
            "/v1/orgs/org-1/members/invite",
            json={"email": "new@acme.com", "role": "member"},
            headers=AUTH_HEADERS,
        )
    assert res.status_code == 200

    mock_supabase.table.side_effect = None


async def test_invite_invalid_role(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    res = await client.post(
        "/v1/orgs/org-1/members/invite",
        json={"email": "x@acme.com", "role": "superadmin"},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 400


async def test_invite_unknown_sends_email(client, mock_supabase, as_org_owner):
    """When user doesn't exist, invite still succeeds with pending_signup."""
    setup_auth(mock_supabase)

    def table_side_effect(name):
        result = MagicMock()
        if name == "users":
            # email lookup: no matching user (unknown invitee)
            result.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[]
            )
            # auth_id lookup for inviter
            result.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": "inviter-1", "email": "owner@example.com"})
            )
        elif name == "organizations":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data={"name": "Test Org"}
            )
        elif name == "org_invitations":
            # existing pending invitation check returns empty
            (
                result.select.return_value.eq.return_value.eq.return_value
                .is_.return_value.execute.return_value
            ) = MagicMock(data=[])
            # insert the new invitation
            result.insert.return_value.execute.return_value = MagicMock(
                data=[{"id": "inv-1", "email": "nobody@acme.com", "role": "member"}]
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    with patch("app.routes.members.send_invite_email", return_value=True), \
         patch("app.routes.members.queue_invite_notification"):
        res = await client.post(
            "/v1/orgs/org-1/members/invite",
            json={"email": "nobody@acme.com", "role": "member"},
            headers=AUTH_HEADERS,
        )
    assert res.status_code == 200
    assert res.json()["status"] == "pending_signup"
    assert res.json()["email_sent"] is True

    mock_supabase.table.side_effect = None


async def test_update_role(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)

    mock_supabase.table.side_effect = None
    chain = mock_supabase.table.return_value.update.return_value
    chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "m2", "role": "admin"}]
    )

    res = await client.patch(
        "/v1/orgs/org-1/members/m2/role",
        json={"role": "admin"},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["data"]["role"] == "admin"


async def test_remove_member(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.delete.return_value
    chain.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    res = await client.delete(
        "/v1/orgs/org-1/members/m2",
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True
