import json
import os
import pymysql
from dotenv import load_dotenv

load_dotenv(".env")
task_id = "6459383134000101991"
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
        SELECT task_id, template_id, name, data_display, data_requirements, asset_info, ext_info
        FROM cfp_frontier_task
        WHERE task_id = %s
        LIMIT 1
        """,
        (task_id,),
    )
    row = cur.fetchone()
conn.close()

if not row:
    print("task not found")
else:
    task_id, template_id, name, data_display, data_requirements, asset_info, ext_info = row
    print("task_id:", task_id)
    print("template_id:", template_id)
    print("name:", name)
    print("\n=== data_display ===")
    print(data_display)
    print("\n=== data_requirements (first 2000 chars) ===")
    text = data_requirements if isinstance(data_requirements, str) else json.dumps(data_requirements)
    print(text[:2000])
    print("\n=== asset_info ===")
    print(asset_info)
    print("\n=== ext_info ===")
    print(ext_info)

    # search for url-like strings
    blob = json.dumps(
        {
            "data_display": data_display,
            "data_requirements": data_requirements,
            "asset_info": asset_info,
            "ext_info": ext_info,
        },
        ensure_ascii=False,
    )
    for kw in ("http", "mp4", "gif", "video", "url", "oss", "s3", "ipfs"):
        print(f"contains '{kw}':", kw in blob.lower())
