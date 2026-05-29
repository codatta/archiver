import json
import os
import pymysql
from dotenv import load_dotenv

load_dotenv(".env")
conn = pymysql.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    charset="utf8mb4",
)
task_id = "6459372306700101811"

tables = ["cfp_frontier_task", "cfp_task_templates", "cfp_frontier_activity_task"]
with conn.cursor() as cur:
    for table in tables:
        print("===", table, "columns ===")
        cur.execute(f"SHOW COLUMNS FROM {table}")
        cols = [r[0] for r in cur.fetchall()]
        print(cols[:30])
        video_cols = [c for c in cols if any(k in c.lower() for k in ("video", "url", "media", "asset", "content", "data"))]
        print("interesting:", video_cols)
        id_cols = [c for c in cols if "task" in c.lower() or "id" in c.lower()]
        print("id cols:", id_cols[:15])
        print()

    for table in tables:
        print("=== probe", table, "===")
        with conn.cursor() as cur2:
            cur2.execute(f"SELECT * FROM {table} LIMIT 1")
            row = cur2.fetchone()
            if row:
                desc = [d[0] for d in cur2.description]
                sample = dict(zip(desc, row))
                print({k: sample[k] for k in list(sample.keys())[:12]})
        print()

    # try find by task_id in frontier task
    probes = [
        f"SELECT * FROM cfp_frontier_task WHERE task_id='{task_id}' LIMIT 1",
        f"SELECT * FROM cfp_frontier_task WHERE id='{task_id}' LIMIT 1",
        f"SELECT * FROM cfp_frontier_activity_task WHERE task_id='{task_id}' LIMIT 1",
    ]
    for sql in probes:
        print("===", sql[:80], "===")
        try:
            with conn.cursor() as cur3:
                cur3.execute(sql)
                row = cur3.fetchone()
                if row:
                    desc = [d[0] for d in cur3.description]
                    data = dict(zip(desc, row))
                    for k, v in data.items():
                        sv = str(v)
                        if len(sv) > 300:
                            sv = sv[:300] + "..."
                        print(k, ":", sv)
                else:
                    print("(empty)")
        except Exception as e:
            print("ERROR", e)
        print()

conn.close()
