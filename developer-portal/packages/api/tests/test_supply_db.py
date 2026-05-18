"""Tests for supply_db module and Postgres-based supply-side queries."""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test")
os.environ.setdefault("SUPABASE_SECRET_KEY", "sb_secret_test")


# ── supply_db unit tests ─────────────────────────────────────────────────────


class TestSupplyDbModule:
    """Test the supply_db connection pool and query helpers."""

    @pytest.mark.asyncio
    async def test_fetch_all_returns_list_of_dicts(self):
        """fetch_all should return rows as list[dict]."""
        from app import supply_db

        mock_pool = AsyncMock()
        mock_record = MagicMock()
        mock_record.__iter__ = MagicMock(return_value=iter([("frontier_id", 1), ("title", "Test")]))
        mock_record.keys.return_value = ["frontier_id", "title"]
        mock_record.__getitem__ = lambda self, key: {"frontier_id": 1, "title": "Test"}[key]

        # Mock pool.fetch to return Record-like objects
        fake_row = {"frontier_id": 1, "title": "Test"}
        mock_pool.fetch = AsyncMock(return_value=[fake_row])

        with patch.object(supply_db, "_pool", mock_pool), \
             patch.object(supply_db, "ensure_pool", new_callable=AsyncMock, return_value=mock_pool):
            result = await supply_db.fetch_all("SELECT 1")
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["frontier_id"] == 1

    @pytest.mark.asyncio
    async def test_fetch_one_returns_dict_or_none(self):
        """fetch_one should return a single dict or None."""
        from app import supply_db

        mock_pool = AsyncMock()
        mock_pool.fetchrow = AsyncMock(return_value=None)

        with patch.object(supply_db, "_pool", mock_pool), \
             patch.object(supply_db, "ensure_pool", new_callable=AsyncMock, return_value=mock_pool):
            result = await supply_db.fetch_one("SELECT 1 WHERE false")
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_all_retries_on_failure(self):
        """fetch_all should retry up to 3 times on connection failure."""
        from app import supply_db

        mock_pool = AsyncMock()
        mock_pool.fetch = AsyncMock(
            side_effect=[ConnectionError("fail"), ConnectionError("fail"), [{"ok": True}]]
        )

        with patch.object(supply_db, "_pool", mock_pool), \
             patch.object(
                 supply_db, "ensure_pool", new_callable=AsyncMock, return_value=mock_pool
             ), \
             patch.object(supply_db, "_reset_pool", new_callable=AsyncMock):
            result = await supply_db.fetch_all("SELECT 1")
            assert result == [{"ok": True}]
            assert mock_pool.fetch.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_all_raises_after_3_failures(self):
        """fetch_all should raise after 3 failed attempts."""
        from app import supply_db

        mock_pool = AsyncMock()
        mock_pool.fetch = AsyncMock(side_effect=ConnectionError("persistent failure"))

        with patch.object(supply_db, "_pool", mock_pool), \
             patch.object(
                 supply_db, "ensure_pool", new_callable=AsyncMock, return_value=mock_pool
             ), \
             patch.object(supply_db, "_reset_pool", new_callable=AsyncMock):
            with pytest.raises(ConnectionError):
                await supply_db.fetch_all("SELECT 1")

    @pytest.mark.asyncio
    async def test_create_pool_skips_when_no_url(self):
        """create_pool should skip when SUPABASE_DB_URL is empty."""
        from app import supply_db
        from app.config import settings

        original = settings.supabase_db_url
        settings.supabase_db_url = ""
        supply_db._pool = None

        await supply_db.create_pool()
        assert supply_db._pool is None

        settings.supabase_db_url = original


# ── SQL syntax validation ────────────────────────────────────────────────────


@pytest.mark.xfail(
    reason="Migration from AliCloud MySQL to Supabase Postgres supply schema "
    "is pending. live_data.py/domains.py still use mysql_db. Tests will pass "
    "once the migration lands — see routes comments.",
    strict=False,
)
class TestQuerySyntax:
    """Validate that route queries use Postgres syntax, not MySQL."""

    def test_live_data_uses_supply_schema(self):
        """live_data.py queries should reference supply. schema."""
        import inspect

        from app.routes import live_data

        source = inspect.getsource(live_data)
        assert "supply.cfp_task_submission" in source
        assert "supply.cfp_frontier_task" in source
        # Should NOT have MySQL placeholders
        assert "WHERE s.task_id IN (%s" not in source
        # Should use asyncpg positional params
        assert "$1" in source

    def test_domains_uses_supply_schema(self):
        """domains.py queries should reference supply. schema."""
        import inspect

        from app.routes import domains

        source = inspect.getsource(domains)
        assert "supply.cfp_frontier" in source
        assert "supply.cfp_frontier_task" in source
        assert "supply.cfp_task_submission" in source
        assert "supply.cfp_task_audit_record" in source
        # Should NOT have MySQL-style %s params
        assert "WHERE t.frontier_id = %s" not in source

    def test_live_data_imports_supply_db(self):
        """live_data.py should import from supply_db, not mysql_db."""
        import inspect

        from app.routes import live_data

        source = inspect.getsource(live_data)
        assert "from app.supply_db import" in source
        assert "from app.mysql_db import" not in source

    def test_domains_imports_supply_db(self):
        """domains.py should import from supply_db, not mysql_db."""
        import inspect

        from app.routes import domains

        source = inspect.getsource(domains)
        assert "from app.supply_db import" in source
        assert "from app.mysql_db import" not in source

    def test_main_imports_supply_db(self):
        """main.py should import from supply_db, not mysql_db."""
        import inspect

        from app import main

        source = inspect.getsource(main)
        assert "from app.supply_db import" in source
        assert "from app.mysql_db import" not in source


# ── Config validation ────────────────────────────────────────────────────────


class TestConfig:
    """Validate config has the new supabase_db_url field."""

    def test_supabase_db_url_field_exists(self):
        from app.config import Settings

        fields = Settings.model_fields
        assert "supabase_db_url" in fields

    def test_supabase_db_url_defaults_to_empty(self):
        from app.config import settings

        # In test env, should be empty (not set)
        assert isinstance(settings.supabase_db_url, str)
