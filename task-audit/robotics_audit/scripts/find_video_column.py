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
queries = [
    ("columns cfp_task_submission", "SHOW COLUMNS FROM cfp_task_submission LIKE '%video%'"),
    ("sample row extra cols", f"""
        SELECT submission_id, task_id, frontier_id, template_id,
               JSON_KEYS(data_submission) AS keys1
        FROM cfp_task_submission
        WHERE task_id='{task_id}' LIMIT 1
    """),
    ("task table exists", "SHOW TABLES LIKE '%task%'"),
]

with conn.cursor() as cur:
    for title, sql in queries:
        print("===", title, "===")
        try:
            cur.execute(sql)
            for row in cur.fetchall():
                print(row)
        except Exception as e:
            print("ERROR", e)
        print()

conn.close()
