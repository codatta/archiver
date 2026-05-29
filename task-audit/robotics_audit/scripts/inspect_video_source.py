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
            SELECT submission_id, task_id, template_id, data_submission
            FROM cfp_task_submission
            WHERE frontier_id='ROBSTIC001' AND status='PENDING' AND template_id=%s
            LIMIT 1
            """,
            (tpl,),
        )
        sid, task_id, template_id, raw = cur.fetchone()
        obj = json.loads(raw) if isinstance(raw, str) else raw
        print("=" * 60)
        print("template:", template_id, "task_id:", task_id, "submission:", sid)
        print("top keys:", list(obj.keys()))
        data = obj.get("data")
        print("data type:", type(data).__name__)
        # search video url paths
        text = json.dumps(obj, ensure_ascii=False)
        for kw in ("video", "url", "mp4", "http"):
            if kw in text.lower():
                print("contains:", kw)
        print(json.dumps(obj, ensure_ascii=False, indent=2)[:3500])

    cur.execute(
        """
        SELECT task_id, COUNT(*) cnt
        FROM cfp_task_submission
        WHERE frontier_id='ROBSTIC001' AND status='PENDING'
        GROUP BY task_id
        ORDER BY cnt DESC
        LIMIT 5
        """
    )
    print("\n=== top task_id by submission count ===")
    for row in cur.fetchall():
        print(row)

conn.close()
