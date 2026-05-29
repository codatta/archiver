"""Phase 1：极速元数据校验（C 级）。"""

from .metadata_auditor import MetadataCheckOutcome, run_metadata_check

__all__ = ["MetadataCheckOutcome", "run_metadata_check"]
