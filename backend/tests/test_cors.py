"""CORS origin matching.

The regex here is security-relevant: it decides which websites may call
this API with the user's credentials. A pattern that is too loose is not a
cosmetic bug, so the rejection cases below matter more than the acceptance
ones.
"""
import re

import pytest

from app.core.config import Settings, vercel_origin_regex


@pytest.fixture()
def matches():
    pattern = re.compile(vercel_origin_regex("ai-case-prep"))
    return lambda origin: pattern.match(origin) is not None


class TestVercelOriginRegex:
    def test_matches_the_production_origin(self, matches):
        assert matches("https://ai-case-prep.vercel.app")

    def test_matches_a_branch_preview(self, matches):
        assert matches("https://ai-case-prep-git-team1-chat.vercel.app")

    def test_matches_a_deployment_preview(self, matches):
        assert matches("https://ai-case-prep-k3j4h5g6.vercel.app")

    def test_rejects_a_lookalike_domain(self, matches):
        # The attack an unanchored pattern lets through: register
        # evil-ai-case-prep.vercel.app, or a domain merely containing the
        # string, and inherit CORS access.
        assert not matches("https://evil-ai-case-prep.vercel.app")

    def test_rejects_a_suffixed_domain(self, matches):
        assert not matches("https://ai-case-prep.vercel.app.attacker.com")

    def test_rejects_another_projects_vercel_app(self, matches):
        # Scoping to the project slug keeps every *other* app hosted on
        # Vercel out.
        assert not matches("https://someone-elses-app.vercel.app")

    def test_rejects_plain_http(self, matches):
        assert not matches("http://ai-case-prep.vercel.app")

    def test_rejects_a_subdomain_prefix(self, matches):
        assert not matches("https://attacker.ai-case-prep.vercel.app")

    def test_escapes_regex_characters_in_the_slug(self):
        # A slug is attacker-controlled only by whoever sets the env var,
        # but an unescaped "." would silently widen the match.
        pattern = re.compile(vercel_origin_regex("a.b"))
        assert pattern.match("https://a.b.vercel.app")
        assert not pattern.match("https://axb.vercel.app")


class TestSettingsWiring:
    def test_regex_is_none_when_no_project_is_configured(self):
        assert Settings(vercel_project_slug="").cors_allow_origin_regex is None

    def test_regex_is_built_from_the_project_slug(self):
        regex = Settings(vercel_project_slug="ai-case-prep").cors_allow_origin_regex
        assert regex is not None
        assert re.compile(regex).match("https://ai-case-prep.vercel.app")

    def test_localhost_stays_allowed_by_default(self):
        # Breaking this would break every developer's `npm run dev`.
        # Read the declared default rather than instantiating: a developer
        # with a local .env would otherwise see a spurious failure.
        assert "http://localhost:5173" in Settings.model_fields["cors_allow_origins"].default
