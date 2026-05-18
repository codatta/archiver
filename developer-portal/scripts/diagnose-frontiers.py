"""Diagnostic: check frontier/task counts directly from MySQL."""
import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "api"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.mysql_db import create_pool, close_pool, fetch_all


async def main():
    await create_pool()

    # 1. Total frontier count (all, not filtered)
    all_frontiers = await fetch_all(
        "SELECT frontier_id, title, status, gmt_create "
        "FROM cfp_frontier WHERE deleted = 0 ORDER BY gmt_create DESC"
    )
    print(f"\n=== ALL FRONTIERS (deleted=0): {len(all_frontiers)} ===")
    for f in all_frontiers:
        print(f"  {f['frontier_id']}  {f['status']:12s}  {f['title']}")

    # 2. Frontiers with tasks
    with_tasks = await fetch_all("""
        SELECT f.frontier_id, f.title, f.status,
               COUNT(DISTINCT t.task_id) AS task_count
        FROM cfp_frontier f
        LEFT JOIN cfp_frontier_task t
            ON t.frontier_id = f.frontier_id AND t.deleted = 0
        WHERE f.deleted = 0
        GROUP BY f.frontier_id, f.title, f.status
        ORDER BY task_count DESC
    """)
    print(f"\n=== FRONTIERS WITH TASK COUNTS: {len(with_tasks)} ===")
    with_any = [f for f in with_tasks if f["task_count"] > 0]
    without = [f for f in with_tasks if f["task_count"] == 0]
    print(f"  With >=1 task: {len(with_any)}")
    print(f"  With 0 tasks:  {len(without)}")
    for f in with_tasks:
        print(f"  {f['frontier_id']}  tasks={f['task_count']:3d}  {f['status']:12s}  {f['title']}")

    # 3. Submission status distribution
    print("\n=== SUBMISSION STATUS DISTRIBUTION ===")
    status_dist = await fetch_all("""
        SELECT status, COUNT(*) AS cnt
        FROM cfp_task_submission
        WHERE deleted = 0
        GROUP BY status
        ORDER BY cnt DESC
    """)
    for s in status_dist:
        print(f"  {s['status']:15s}  {s['cnt']:>10,}")

    # 4. CEX Hot Wallet specifically
    print("\n=== CEX HOT WALLET — ALL TASKS ===")
    cex = await fetch_all(
        "SELECT frontier_id FROM cfp_frontier "
        "WHERE title = 'CEX Hot Wallet' AND deleted = 0"
    )
    if cex:
        fid = cex[0]["frontier_id"]
        tasks = await fetch_all("""
            SELECT t.task_id, t.name, t.task_type, t.status, t.deleted,
                   COUNT(s.id) AS total_subs,
                   SUM(CASE WHEN s.status = 'ADOPT' THEN 1 ELSE 0 END) AS adopt_subs
            FROM cfp_frontier_task t
            LEFT JOIN cfp_task_submission s
                ON s.task_id = t.task_id AND s.deleted = 0
            WHERE t.frontier_id = %s
            GROUP BY t.task_id, t.name, t.task_type, t.status, t.deleted
            ORDER BY total_subs DESC
        """, (fid,))
        print(f"  Frontier ID: {fid}")
        print(f"  Total tasks (including deleted): {len(tasks)}")
        active = [t for t in tasks if t["deleted"] == 0]
        print(f"  Active tasks (deleted=0): {len(active)}")
        for t in tasks:
            d = "DEL" if t["deleted"] else "   "
            print(
                f"  {d} {t['task_id']}  "
                f"total={t['total_subs']:>6,}  "
                f"adopt={t['adopt_subs']:>6,}  "
                f"{t['status']:10s}  {t['name']}"
            )

    # 5. Frontiers filtered by the API logic
    print("\n=== FRONTIERS AS RETURNED BY API (status=all) ===")
    api_rows = await fetch_all("""
        SELECT
            f.frontier_id, f.title, f.status, f.gmt_create,
            COUNT(DISTINCT t.task_id) AS task_count,
            COALESCE(SUM(sub_counts.cnt), 0) AS total_submissions
        FROM cfp_frontier f
        LEFT JOIN cfp_frontier_task t
            ON t.frontier_id = f.frontier_id AND t.deleted = 0
        LEFT JOIN (
            SELECT task_id, COUNT(*) AS cnt
            FROM cfp_task_submission
            WHERE deleted = 0 AND status = 'ADOPT'
            GROUP BY task_id
        ) sub_counts ON sub_counts.task_id = t.task_id
        WHERE f.deleted = 0
        GROUP BY f.frontier_id, f.title, f.status, f.gmt_create
        HAVING COUNT(DISTINCT t.task_id) >= 1
        ORDER BY total_submissions DESC
    """)
    print(f"  After HAVING task_count >= 1: {len(api_rows)}")

    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    filtered = []
    removed = []
    for r in api_rows:
        created = r.get("gmt_create")
        subs = int(r["total_submissions"])
        if subs == 0 and created and created.replace(tzinfo=timezone.utc) < cutoff:
            removed.append(r)
        else:
            filtered.append(r)

    print(f"  After 3-day zero-submission filter: {len(filtered)}")
    print(f"  Removed by filter: {len(removed)}")
    if removed:
        print("  Removed frontiers:")
        for r in removed:
            print(f"    {r['title']} (tasks={r['task_count']}, subs={r['total_submissions']})")

    print(f"\n  FINAL LIST ({len(filtered)} frontiers):")
    for r in filtered:
        print(
            f"    {r['title']:30s}  tasks={r['task_count']:2d}  "
            f"subs={int(r['total_submissions']):>8,}  {r['status']}"
        )

    await close_pool()


asyncio.run(main())
