"""Shared fixtures — session-scoped TestClient (MCP session manager is one-shot)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def api_client():
    """One TestClient per pytest session; MCP session manager starts once.

    ``mount_mcp`` also rebuilds the manager if a prior lifespan already exited.
    """
    with TestClient(app) as c:
        yield c
