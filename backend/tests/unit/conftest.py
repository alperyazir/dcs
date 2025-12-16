"""
Conftest for unit tests - overrides autouse db fixture.

These tests run without database connection for fast, isolated testing.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def db():
    """Override parent db fixture - no database needed for unit tests."""
    yield None
