"""v1 API router aggregation — the single integration point for all teams.

Each module contributes an ``APIRouter`` from its own file in this package
and registers it below. ``app.main`` mounts this one router under
``/api/v1``, so no team needs to touch ``main.py`` to add endpoints, and
merge conflicts stay confined to the short list below.

**Adding endpoints to your module:** open your module's file (they already
exist, with a registered router) and add routes to the ``router`` in it.
Nothing here needs to change.

**Adding a new file to your module:** define
``router = APIRouter(prefix="/your-thing", tags=["..."])`` in it, then add
one import and one ``include_router`` line in your team's section below.

Keep your routes under your module's prefix (``/case-prep``,
``/peer2peer``) so the URL says which team owns an endpoint. Module 2's
routes predate the three-module split and stay unprefixed — moving them
now would break Team 1 and Team 3's in-flight integration work for no
functional gain.
"""
from fastapi import APIRouter

from app.api.v1 import auth, case_prep, cases, health, peer2peer, users

api_router = APIRouter()

# --- Shared ---
api_router.include_router(health.router)

# --- Module 1 — CasePrep with AI (Team 1) ---
api_router.include_router(case_prep.router)
# chat.py and interview.py are scaffolded and empty. Give each a `router`
# and register it here when you build them out:
#     from app.api.v1 import chat, interview
#     api_router.include_router(chat.router)
#     api_router.include_router(interview.router)

# --- Module 2 — Account Management & Case Repository (Team 2) ---
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(cases.router)

# --- Module 3 — Peer2Peer Group (Team 3) ---
api_router.include_router(peer2peer.router)

__all__ = ["api_router"]
