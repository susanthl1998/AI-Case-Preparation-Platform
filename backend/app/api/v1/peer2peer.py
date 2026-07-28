"""Module 3 — Peer2Peer Group (Team 3).

TEAM 3: this is your entry point. The router is already registered in
``app/api/v1/__init__.py``, so anything you add here is served under
``/api/v1/peer2peer`` immediately.

Put group/session logic in a ``app/services/group_service.py`` and keep
this file thin — routers parse requests and return responses, nothing more
(see CONTRIBUTING.md).

Useful pieces that already exist:

- ``Depends(get_current_user)`` for the authenticated user
- ``Depends(get_db)`` for a PostgreSQL session
- New tables go in ``app/models/`` with an Alembic migration; read the
  migrations section of CONTRIBUTING.md first — all three teams share one
  migration history, and branching it from a stale head breaks every
  environment at once.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/peer2peer", tags=["module-3: peer2peer"])


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
        "module": 3,
        "name": "Peer2Peer Group",
        "team": "Team 3",
        "status": "not_implemented",
    }
