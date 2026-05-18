from unittest.mock import MagicMock

AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


def setup_auth(mock_supabase):
    """Set up valid auth mock + user lookup."""
    mock_supabase.auth.get_user.side_effect = None
    mock_user = MagicMock()
    mock_user.id = "auth-123"
    mock_user.email = "owner@example.com"
    mock_user.user_metadata = {"full_name": "Owner"}
    mock_result = MagicMock()
    mock_result.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_result


def setup_user_lookup(mock_supabase, user_id="user-123"):
    """Mock the users table lookup for _get_user_id."""
    # This handles the chained .table("users").select("id").eq("auth_id", ...).single().execute()
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data={"id": user_id}
    )


# --- Step 1: Create Org ---

async def test_create_org_success(client, mock_supabase):
    setup_auth(mock_supabase)

    call_count = [0]

    def table_side_effect(name):
        result = MagicMock()
        if name == "users":
            result.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": "user-123"})
            )
        elif name == "organizations":
            if call_count[0] == 0:
                # Slug check
                result.select.return_value.eq.return_value.execute.return_value = (
                    MagicMock(data=[])
                )
                call_count[0] += 1
            else:
                # Insert
                result.insert.return_value.execute.return_value = MagicMock(
                    data=[{"id": "org-1", "name": "Acme Labs", "slug": "acme-labs"}]
                )
        else:
            # org_memberships, accounts
            result.insert.return_value.execute.return_value = MagicMock(data=[{}])
        return result

    mock_supabase.table.side_effect = table_side_effect

    res = await client.post(
        "/v1/onboarding/org",
        json={"name": "Acme Labs", "slug": "acme-labs"},
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Acme Labs"

    mock_supabase.table.side_effect = None


async def test_create_org_missing_name(client, mock_supabase):
    setup_auth(mock_supabase)
    res = await client.post(
        "/v1/onboarding/org",
        json={"name": "", "slug": "acme"},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 400
    assert "name" in res.json()["detail"].lower()


async def test_create_org_missing_slug(client, mock_supabase):
    setup_auth(mock_supabase)
    res = await client.post(
        "/v1/onboarding/org",
        json={"name": "Acme", "slug": "  "},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 400
    assert "slug" in res.json()["detail"].lower()


async def test_create_org_duplicate_slug(client, mock_supabase):
    setup_auth(mock_supabase)

    def table_side_effect(name):
        result = MagicMock()
        if name == "users":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": "user-123"})
            )
        elif name == "organizations":
            result.select.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{"id": "org-existing"}])
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    res = await client.post(
        "/v1/onboarding/org",
        json={"name": "Acme Labs", "slug": "taken-slug"},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 409

    mock_supabase.table.side_effect = None


async def test_create_org_unauthenticated(client, mock_supabase):
    mock_supabase.auth.get_user.side_effect = Exception("Invalid token")

    res = await client.post(
        "/v1/onboarding/org",
        json={"name": "Acme", "slug": "acme"},
    )
    assert res.status_code == 401


# --- Step 2: Invite Members ---

async def test_invite_members_success(client, mock_supabase):
    setup_auth(mock_supabase)

    def table_side_effect(name):
        result = MagicMock()
        if name == "users":
            # For _get_user_id and email lookups
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": "user-123"})
            )
            chain.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "invitee-1"}]
            )
        elif name == "org_memberships":
            result.insert.return_value.execute.return_value = MagicMock(
                data=[{"id": "mem-1", "role": "admin"}]
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    res = await client.post(
        "/v1/onboarding/invite",
        json={
            "org_id": "org-1",
            "invites": [
                {"email": "alice@acme.com", "role": "admin"},
                {"email": "bob@acme.com", "role": "member"},
            ],
        },
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2

    mock_supabase.table.side_effect = None


async def test_invite_members_invalid_role_skipped(client, mock_supabase):
    setup_auth(mock_supabase)

    def table_side_effect(name):
        result = MagicMock()
        if name == "users":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": "user-123"})
            )
            chain.eq.return_value.execute.return_value = MagicMock(
                data=[{"id": "invitee-1"}]
            )
        elif name == "org_memberships":
            result.insert.return_value.execute.return_value = MagicMock(
                data=[{"id": "mem-1", "role": "member"}]
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    res = await client.post(
        "/v1/onboarding/invite",
        json={
            "org_id": "org-1",
            "invites": [
                {"email": "alice@acme.com", "role": "member"},
                {"email": "hacker@evil.com", "role": "owner"},
            ],
        },
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1

    mock_supabase.table.side_effect = None


async def test_invite_empty_list(client, mock_supabase):
    setup_auth(mock_supabase)

    def table_side_effect(name):
        result = MagicMock()
        if name == "users":
            chain = result.select.return_value
            chain.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": "user-123"})
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    res = await client.post(
        "/v1/onboarding/invite",
        json={"org_id": "org-1", "invites": []},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["data"] == []

    mock_supabase.table.side_effect = None


# --- Step 3: Complete Onboarding (no key creation) ---

async def test_complete_onboarding(client, mock_supabase):
    setup_auth(mock_supabase)

    def table_side_effect(name):
        result = MagicMock()
        if name == "organizations":
            result.update.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    res = await client.post(
        "/v1/onboarding/complete?org_id=org-1",
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["data"]["completed"] is True

    # Verify organizations.update was called with onboarding_completed=True
    org_call = mock_supabase.table.call_args_list
    org_table_calls = [c for c in org_call if c.args == ("organizations",)]
    assert len(org_table_calls) > 0

    mock_supabase.table.side_effect = None


async def test_complete_onboarding_unauthenticated(client, mock_supabase):
    mock_supabase.auth.get_user.side_effect = Exception("Invalid token")

    res = await client.post("/v1/onboarding/complete?org_id=org-1")
    assert res.status_code == 401


async def test_complete_onboarding_no_api_key_created(client, mock_supabase):
    """Ensure /complete does NOT insert into api_keys table."""
    setup_auth(mock_supabase)

    table_calls = []

    def table_side_effect(name):
        table_calls.append(name)
        result = MagicMock()
        if name == "organizations":
            result.update.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    res = await client.post(
        "/v1/onboarding/complete?org_id=org-1",
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert "api_keys" not in table_calls

    mock_supabase.table.side_effect = None


# --- Legacy: Generate API Key ---

async def test_create_first_key(client, mock_supabase):
    setup_auth(mock_supabase)

    def table_side_effect(name):
        result = MagicMock()
        if name == "api_keys":
            result.insert.return_value.execute.return_value = MagicMock(
                data=[{
                    "id": "key-1", "org_id": "org-1", "name": "Default",
                    "key_prefix": "hb_live_sk_xxxxxxxx", "status": "active",
                }]
            )
        elif name == "organizations":
            result.update.return_value.eq.return_value.execute.return_value = (
                MagicMock(data=[{}])
            )
        return result

    mock_supabase.table.side_effect = table_side_effect

    res = await client.post(
        "/v1/onboarding/api-key?org_id=org-1",
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["data"]["raw_key"].startswith("hb_live_sk_")

    mock_supabase.table.side_effect = None


async def test_create_first_key_unauthenticated(client, mock_supabase):
    mock_supabase.auth.get_user.side_effect = Exception("Invalid token")

    res = await client.post("/v1/onboarding/api-key?org_id=org-1")
    assert res.status_code == 401
