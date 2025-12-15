"""Conftest for standalone tests that don't require database access.

This overrides the session-scoped db fixture from the root conftest.py.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def db():
    """Override db fixture to do nothing for standalone tests."""
    yield None
