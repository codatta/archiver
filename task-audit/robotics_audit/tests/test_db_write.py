from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db_client import SubmissionDBClient


class TestDbWrite(unittest.TestCase):
    @patch.dict(os.environ, {"DB_USER": "u", "DB_NAME": "d"}, clear=False)
    @patch.object(SubmissionDBClient, "update_submission_grade", return_value=True)
    def test_write_attempts_all_rows(self, mock_update) -> None:
        client = SubmissionDBClient()
        stats = client.write_audit_results(
            [
                {"submission_id": "1", "audit_grade": "S", "status": "ADOPT", "result": 5, "violations": []},
                {"submission_id": "", "audit_grade": "D", "violations": []},
                {"submission_id": "2", "audit_grade": "D", "status": "REFUSED", "result": 1, "violations": []},
            ]
        )
        self.assertEqual(stats["attempted"], 2)
        self.assertEqual(stats["success"], 2)
        self.assertEqual(stats["skipped"], 1)
        self.assertEqual(mock_update.call_count, 2)


if __name__ == "__main__":
    unittest.main()
