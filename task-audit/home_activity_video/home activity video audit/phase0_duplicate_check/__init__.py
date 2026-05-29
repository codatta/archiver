"""Phase 0：轻量化查重（D 级）。"""

from .duplicate_auditor import DuplicateCheckOutcome, run_duplicate_check

__all__ = ["DuplicateCheckOutcome", "run_duplicate_check"]
