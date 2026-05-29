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

queries = [
    ("basic pending", "SELECT COUNT(*) FROM cfp_task_submission WHERE frontier_id='ROBSTIC001' AND status='PENDING'"),
    ("env frontier literal", "SELECT COUNT(*) FROM cfp_task_submission WHERE frontier_id IN ('ROBSTIC001') AND status='PENDING'"),
    ("with json extract", "SELECT COUNT(*) FROM cfp_task_submission WHERE frontier_id='ROBSTIC001' AND status='PENDING' AND data_submission IS NOT NULL"),
    ("exact env sql count", f"SELECT COUNT(*) FROM ({os.getenv('DB_SUBMISSIONS_SQL')}) t"),
    ("simple select 3 cols", "SELECT submission_id, user_id, status FROM cfp_task_submission WHERE frontier_id='ROBSTIC001' AND status='PENDING' LIMIT 3"),
]

with conn.cursor() as cur:
    for title, sql in queries:
        print("===", title, "===")
        try:
            cur.execute(sql)
            print(cur.fetchall())
        except Exception as e:
            print("ERROR:", e)
        print()

    # inspect frontier_id bytes from one pending row
    cur.execute("SELECT frontier_id, LENGTH(frontier_id), HEX(frontier_id) FROM cfp_task_submission WHERE status='PENDING' LIMIT 1")
    print("=== sample frontier_id bytes ===")
    print(cur.fetchone())

    # show env sql frontier substring
    env_sql = os.getenv("DB_SUBMISSIONS_SQL", "")
    start = env_sql.find("('")
    print("=== env sql frontier snippet ===")
    print(repr(env_sql[start : start + 20]))

conn.close()
