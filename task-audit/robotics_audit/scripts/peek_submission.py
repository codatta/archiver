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
    cur.execute(
        """
        SELECT submission_id, data_submission
        FROM cfp_task_submission
        WHERE frontier_id='ROBSTIC001' AND status='PENDING'
        LIMIT 1
        """
    )
    sid, raw = cur.fetchone()
conn.close()

obj = json.loads(raw) if isinstance(raw, str) else raw
print("submission_id:", sid)
print(json.dumps(obj, ensure_ascii=False, indent=2)[:4000])
