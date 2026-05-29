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
        SELECT template_id,
               JSON_UNQUOTE(JSON_EXTRACT(data_submission, '$.templateId')) AS json_template_id,
               COUNT(*) AS cnt
        FROM cfp_task_submission
        WHERE frontier_id='ROBSTIC001' AND status='PENDING'
        GROUP BY template_id, json_template_id
        """
    )
    print("=== template_id column vs JSON templateId ===")
    for row in cur.fetchall():
        print(row)

conn.close()
