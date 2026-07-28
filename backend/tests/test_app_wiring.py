"""Application wiring: routing, mounting, and the cross-module contract.

These are the tests that protect three teams from each other. The
per-feature suites check behavior; these check that the *shape* of the API
hasn't shifted underneath somebody — a router that stopped being
registered, a prefix that moved, two modules claiming the same path. Those
failures are invisible in a module's own tests and obvious here.

If a change here fails, treat it as a contract change: fix the code, or
update this file *and* docs/API/api-spec.md and tell the affected team.
"""
from fastapi.routing import APIRoute

from app.core.config import get_settings
from app.main import app

API = get_settings().api_v1_prefix


def _routes():
    """(path, method) pairs for every registered API route."""
    pairs = set()
    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in route.methods:
                if method not in {"HEAD", "OPTIONS"}:
                    pairs.add((route.path, method))
    return pairs


def _paths():
    return {path for path, _ in _routes()}


class TestModuleMounting:
    """All three modules must be reachable. A module that silently stops
    being registered is the single most likely integration failure here."""

    def test_module_1_case_prep_is_mounted(self, client):
        response = client.get("/case-prep/status")
        assert response.status_code == 200, response.text
        assert response.json()["module"] == 1

    def test_module_2_case_repository_is_mounted(self, client, signup_and_login):
        headers, _ = signup_and_login()
        assert client.get("/cases", headers=headers).status_code == 200

    def test_module_3_peer2peer_is_mounted(self, client):
        response = client.get("/peer2peer/status")
        assert response.status_code == 200, response.text
        assert response.json()["module"] == 3

    def test_every_module_prefix_has_at_least_one_route(self):
        for prefix in (f"{API}/case-prep", f"{API}/auth", f"{API}/cases", f"{API}/peer2peer"):
            assert any(p.startswith(prefix) for p in _paths()), f"no routes under {prefix}"


class TestVersionPrefix:
    """Every feature route lives under /api/v1. Health and root do not —
    hosting platforms probe a fixed path and shouldn't break on a version
    bump."""

    def test_feature_routes_are_versioned(self):
        unversioned = {
            path
            for path in _paths()
            if not path.startswith(API) and path not in {"/", "/health"}
            # FastAPI's own docs endpoints are mounted at the root.
            and path not in {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}
        }
        assert unversioned == set(), f"routes outside {API}: {sorted(unversioned)}"

    def test_root_and_health_are_unversioned(self, raw_client):
        assert raw_client.get("/").status_code == 200
        assert raw_client.get("/health").json() == {"status": "ok"}

    def test_versioned_health_also_exists(self, client):
        assert client.get("/health").json() == {"status": "ok"}

    def test_root_advertises_where_to_go_next(self, raw_client):
        body = raw_client.get("/").json()
        assert body["docs"] == "/docs"
        assert body["api"] == API


class TestNoRouteCollisions:
    """Two teams registering the same path is a merge accident that FastAPI
    resolves silently by first-match — the earlier route wins and the later
    one is dead. Catch it here instead of in someone's demo."""

    def test_no_duplicate_path_and_method(self):
        seen = set()
        duplicates = set()
        for route in app.routes:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    key = (route.path, method)
                    if key in seen:
                        duplicates.add(key)
                    seen.add(key)
        assert duplicates == set(), f"duplicate routes: {sorted(duplicates)}"


class TestOpenApiSchema:
    """The generated schema is the contract other teams' clients read. It
    also fails loudly on response-model mistakes that would otherwise only
    surface at request time."""

    def test_schema_generates(self):
        schema = app.openapi()
        assert schema["openapi"].startswith("3.")
        assert schema["paths"]

    def test_schema_covers_all_three_modules(self):
        paths = app.openapi()["paths"]
        assert f"{API}/case-prep/status" in paths
        assert f"{API}/cases" in paths
        assert f"{API}/peer2peer/status" in paths


class TestModule2PublicContract:
    """The endpoints documented in docs/API/api-spec.md, which Team 1 and
    Team 3 build against. Renaming one is a breaking change, so it should
    require deliberately editing this list."""

    EXPECTED = {
        ("/auth/signup", "POST"),
        ("/auth/verify", "POST"),
        ("/auth/login", "POST"),
        ("/auth/refresh", "POST"),
        ("/auth/me", "GET"),
        ("/profile/onboarding", "POST"),
        ("/profile/me", "GET"),
        ("/profile/me", "PATCH"),
        ("/dashboard", "GET"),
        ("/account/me", "DELETE"),
        ("/cases", "GET"),
        ("/cases", "POST"),
        ("/cases/{case_id}", "GET"),
        ("/cases/{case_id}", "PATCH"),
        ("/cases/{case_id}", "DELETE"),
        ("/cases/{case_id}/file", "GET"),
        ("/cases/{case_id}/share", "POST"),
        ("/cases/{case_id}/withdraw", "POST"),
        ("/cases/{case_id}/practice", "POST"),
        ("/cases/{case_id}/moderate", "PATCH"),
    }

    def test_all_documented_endpoints_exist(self):
        registered = _routes()
        missing = {
            (path, method)
            for path, method in self.EXPECTED
            if (f"{API}{path}", method) not in registered
        }
        assert missing == set(), f"documented endpoints missing: {sorted(missing)}"


class TestAuthenticationIsEnforced:
    """Protected endpoints must reject anonymous callers. A dependency
    dropped during a refactor turns a private repository public, and no
    other test in this suite would notice."""

    PROTECTED = [
        ("get", "/auth/me"),
        ("get", "/profile/me"),
        ("get", "/dashboard"),
        ("get", "/cases"),
        ("post", "/cases"),
        ("delete", "/account/me"),
    ]

    def test_requires_a_token(self, client):
        for method, path in self.PROTECTED:
            response = getattr(client, method)(path)
            assert response.status_code == 401, f"{method.upper()} {path} allowed anonymous access"

    def test_rejects_a_garbage_token(self, client):
        headers = {"Authorization": "Bearer not-a-real-token"}
        assert client.get("/auth/me", headers=headers).status_code == 401
