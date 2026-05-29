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

checks = [
    ("template counts", """
        SELECT template_id, COUNT(*) cnt
        FROM cfp_task_submission
        WHERE frontier_id='ROBSTIC001' AND status='PENDING'
        GROUP BY template_id
        ORDER BY cnt DESC
        LIMIT 10
    """),
    ("has paragraphs key", """
        SELECT COUNT(*)
        FROM cfp_task_submission
        WHERE frontier_id='ROBSTIC001' AND status='PENDING'
          AND JSON_CONTAINS_PATH(data_submission, 'one', '$.data.paragraphs')
    """),
    ("has segments key", """
        SELECT COUNT(*)
        FROM cfp_task_submission
        WHERE frontier_id='ROBSTIC001' AND status='PENDING'
          AND JSON_CONTAINS_PATH(data_submission, 'one', '$.data.segments')
    """),
    ("has video key", """
        SELECT COUNT(*)
        FROM cfp_task_submission
        WHERE frontier_id='ROBSTIC001' AND status='PENDING'
          AND JSON_CONTAINS_PATH(data_submission, 'one', '$.data.video')
    """),
]

with conn.cursor() as cur:
    for title, sql in checks:
        print("===", title, "===")
        cur.execute(sql)
        for row in cur.fetchall():
            print(row)
        print()

    cur.execute(
        """
        SELECT submission_id, template_id, data_submission
        FROM cfp_task_submission
        WHERE frontier_id='ROBSTIC001' AND status='PENDING'
          AND (
            JSON_CONTAINS_PATH(data_submission, 'one', '$.data.paragraphs')
            OR JSON_CONTAINS_PATH(data_submission, 'one', '$.data.segments')
          )
        LIMIT 1
        """
    )
    row = cur.fetchone()
    print("=== sample with paragraphs/segments ===")
    if row:
        sid, tpl, raw = row
        obj = json.loads(raw) if isinstance(raw, str) else raw
        print("submission_id:", sid, "template_id:", tpl)
        print(json.dumps(obj, ensure_ascii=False, indent=2)[:4000])
    else:
        print("(not found)")

conn.close()
