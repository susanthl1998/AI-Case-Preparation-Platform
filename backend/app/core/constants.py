"""Shared enumerations and constants.

The stable import surface for values other modules need. Team 1 and Team 3
should import the case taxonomy from **here** rather than from
``app.models.case``: this module is a deliberate contract, whereas the
models file is Module 2's internal storage detail and may be reorganized.

    from app.core.constants import CaseType, Difficulty

The enums are currently *defined* alongside their SQLAlchemy models (so the
Postgres native ENUM type and the Python enum can never drift — see the
``name=`` note in ``app/models/case.py``) and re-exported here. If they
ever move, this import path stays valid.

The case taxonomy is frozen per PRD §9 — Team 1 depends on it. Adding a
value requires a migration (the Postgres ENUM type must be altered too) and
cross-team sign-off, not just an edit here.
"""
from app.models.case import CaseType, Difficulty
from app.models.profile import TargetFirmType

# Only PDFs are accepted for case uploads in v1.0 (FR-09). The size limit
# is deployment-configurable (MAX_UPLOAD_SIZE_BYTES) rather than constant.
ALLOWED_UPLOAD_CONTENT_TYPES = ("application/pdf",)

# Minimum characters before a repository search executes (US-04 AC).
MIN_SEARCH_QUERY_LENGTH = 3

__all__ = [
    "CaseType",
    "Difficulty",
    "TargetFirmType",
    "ALLOWED_UPLOAD_CONTENT_TYPES",
    "MIN_SEARCH_QUERY_LENGTH",
]
