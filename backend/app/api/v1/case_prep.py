"""Module 1 — CasePrep with AI (Team 1).

TEAM 1: this is your entry point. The router is already registered in
``app/api/v1/__init__.py``, so anything you add here is served under
``/api/v1/case-prep`` immediately.

Put the AI logic in ``app/services/ai_service.py`` /
``rag_service.py`` / ``evaluation_service.py`` and keep this file thin —
the routers in this package parse requests and return responses, nothing
more (see CONTRIBUTING.md). Chat and interview endpoints can live in the
scaffolded ``chat.py`` / ``interview.py``; register them the same way.

Useful pieces that already exist:

- ``Depends(get_current_user)`` for the authenticated user
- ``Depends(get_db)`` for a PostgreSQL session
- ``Depends(get_mongo_db)`` for Mongo, once ``MONGODB_URI`` is set
- Module 2's cases: query the ``Case`` model directly, and call
  ``POST /cases/{id}/practice`` semantics via ``case_service`` when a
  practice session completes
"""
from fastapi import APIRouter

router = APIRouter(prefix="/case-prep", tags=["module-1: case prep"])


@router.get("/status")
def status() -> dict:
    """Report that the module is scaffolded but not yet implemented.

    Exists so the route tree is complete from day one: the frontend can
    reach every module, and the integration test that asserts all three
    modules are mounted has something concrete to check. Replace it with
    real endpoints — nothing depends on this specific response beyond
    that test.
    """
    return {
        "module": 1,
        "name": "CasePrep with AI",
        "team": "Team 1",
        "status": "not_implemented",
    }
