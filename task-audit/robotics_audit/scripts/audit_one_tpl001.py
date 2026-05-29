import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pymysql
from dotenv import load_dotenv

from robotics_audit.auditor import SegmentAuditor

load_dotenv(ROOT / ".env")
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
        SELECT submission_id, data_submission ->> '$.data' AS data_submission, user_id, template_id
        FROM cfp_task_submission
        WHERE frontier_id='ROBSTIC001' AND status='PENDING' AND template_id='ROBOTICS_TPL_000001'
        LIMIT 1
        """
    )
    row = cur.fetchone()
conn.close()

auditor = SegmentAuditor()
result = auditor.audit(row[0], row[1], user_id=str(row[2]))
print("submission_id:", row[0], "template:", row[3])
print("grade:", result.audit_grade, "segments:", result.segment_count)
print("violations:", [v.message for v in result.violations[:5]])
