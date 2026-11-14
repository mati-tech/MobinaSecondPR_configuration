"""Shared helpers for the test suite."""

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MAVEN_REPO_URL = (FIXTURES / "maven_repo").as_uri()


def fixture(name: str) -> str:
    """Return the path of a fixture file as a string."""
    return str(FIXTURES / name)
