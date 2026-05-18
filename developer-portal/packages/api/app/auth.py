from fastapi import Depends, HTTPException, Request

from app.db import supabase


def get_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )
    return auth[7:]


async def get_current_user(token: str = Depends(get_token)) -> dict:
    """Verify JWT with Supabase and return user dict (with retry for flaky TLS)."""
    import time

    last_err = None
    for attempt in range(3):
        try:
            res = supabase.auth.get_user(token)
            if res.user is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            if res.user.email_confirmed_at is None:
                raise HTTPException(status_code=403, detail="Email not verified")
            return {
                "id": res.user.id,
                "email": res.user.email,
                "user_metadata": res.user.user_metadata,
            }
        except HTTPException:
            raise
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(0.5)
    raise HTTPException(status_code=401, detail=str(last_err))


async def require_org_member(
    org_id: str, user: dict = Depends(get_current_user)
) -> dict:
    """Verify user is a member of the given org via org_memberships."""
    # First get the public.users.id from auth_id
    user_res = (
        supabase.table("users")
        .select("id")
        .eq("auth_id", user["id"])
        .single()
        .execute()
    )
    if not user_res.data:
        raise HTTPException(status_code=403, detail="User profile not found")

    res = (
        supabase.table("org_memberships")
        .select("*")
        .eq("org_id", org_id)
        .eq("user_id", user_res.data["id"])
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(
            status_code=403, detail="Not a member of this organization"
        )
    return {**user, "membership": res.data, "user_db_id": user_res.data["id"]}


async def require_org_admin(
    org_id: str, user: dict = Depends(get_current_user)
) -> dict:
    """Verify user is admin or owner of the given org."""
    member = await require_org_member(org_id, user)
    if member["membership"]["role"] not in ("owner", "admin"):
        raise HTTPException(
            status_code=403, detail="Admin or owner role required"
        )
    return member


async def require_superadmin(user: dict = Depends(get_current_user)) -> dict:
    """Verify user has is_admin=true in the users table."""
    user_res = (
        supabase.table("users")
        .select("id, is_admin")
        .eq("auth_id", user["id"])
        .single()
        .execute()
    )
    if not user_res.data or not user_res.data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Superadmin required")
    return {**user, "user_db_id": user_res.data["id"]}
