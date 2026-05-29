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

with conn.cursor() as cur:
    for tpl in ("ROBOTICS_TPL_000001", "ROBOTICS_TPL_000003"):
        cur.execute(
            """
            SELECT task_id, name, data_display, data_requirements
            FROM cfp_frontier_task
            WHERE frontier_id='ROBSTIC001' AND template_id=%s
            LIMIT 1
            """,
            (tpl,),
        )
        task_id, name, data_display, data_requirements = cur.fetchone()
        print("=" * 60)
        print("template:", tpl, "task_id:", task_id, "name:", name)
        print("data_display:", data_display)
        req = json.loads(data_requirements) if data_requirements else {}
        print("data_requirements keys:", list(req.keys()) if isinstance(req, dict) else type(req))
        print(json.dumps(req, ensure_ascii=False, indent=2)[:2500])

conn.close()
