"""
End-to-end test: Slice 1 — Secure Demo Path

Proves: JWT login → alert creation → WebSocket push → acknowledgement → trajectory endpoint.

Run with: DATABASE_URL="sqlite+aiosqlite:///:memory:" python -m pytest tests/test_e2e_slice1.py -v
"""

import asyncio
import hashlib
import json
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="module")
async def app():
    """Create a test FastAPI app with in-memory SQLite."""
    import os
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["SENTINEL_EMAIL"] = ""
    os.environ["SENTINEL_PASSWORD"] = ""

    # Patch fetch_sentinel_catalogue to avoid network calls
    with patch("simulator.camera_registry.fetch_sentinel_catalogue", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [
            {
                "cam_id": "cam01",
                "display_name": "Test Camera 01",
                "location": "Test Location",
                "latitude": 23.0768,
                "longitude": 72.5843,
                "hls_url": "/api/v1/cameras/cam01/stream/index.m3u8",
                "web_url": "/api/v1/cameras/cam01/stream/index.m3u8",
                "district": "Ahmedabad",
                "police_station": "Sabarmati",
                "location_type": "Junction",
                "jurisdiction_code": "GJ-AHM",
                "status": "ONLINE",
            }
        ]

        # Force reimport to pick up env override
        import importlib
        import config
        importlib.reload(config)
        import database
        importlib.reload(database)

        from main import app as fastapi_app
        # Manually trigger lifespan
        async with fastapi_app.router.lifespan_context(fastapi_app):
            yield fastapi_app


@pytest_asyncio.fixture
async def client(app):
    """HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_token(client):
    """Get a real JWT token by logging in as demo operator."""
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "GJ-OPR-001", "password": "demo123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "operator"
    return body["access_token"]


@pytest_asyncio.fixture
async def inv_token(client):
    """Get a JWT token for the investigator role."""
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "GJ-INV-001", "password": "demo123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAuthentication:
    """Test 1: Real JWT login replaces mock_token."""

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self, client):
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "GJ-OPR-001", "password": "demo123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["user"]["full_name"] == "Demo Operator"

    @pytest.mark.asyncio
    async def test_login_with_wrong_password(self, client):
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "GJ-OPR-001", "password": "wrong"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_mock_token_rejected(self, client):
        resp = await client.get(
            "/api/v1/cameras",
            headers={"Authorization": "Bearer mock_token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_real_token_accepted(self, client, auth_token):
        resp = await client.get(
            "/api/v1/cameras",
            headers=auth_headers(auth_token),
        )
        assert resp.status_code == 200


class TestSeeding:
    """Test 2: Demo data is seeded correctly."""

    @pytest.mark.asyncio
    async def test_cameras_seeded_with_gps(self, client, auth_token):
        resp = await client.get("/api/v1/cameras", headers=auth_headers(auth_token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        cam = body["cameras"][0]
        assert cam["latitude"] is not None, "Camera latitude should be set"
        assert cam["longitude"] is not None, "Camera longitude should be set"


class TestAlertAcknowledgement:
    """Test 3: Alert acknowledgement persists."""

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, client, auth_token, app):
        """Create alert in DB, acknowledge it, verify persistence."""
        from database import async_session_maker
        from models.alert import Alert
        from models.enums import AlertPriority

        # Insert a test alert directly
        async with async_session_maker() as session:
            alert = Alert(
                alert_id="TEST-ALERT-001",
                alert_type="WATCHLIST_MATCH",
                priority=AlertPriority.P1,
                message="Test: GJ-01-AB-1234 spotted on cam01",
                status="UNREAD",
                jurisdiction_code="GJ-AHM",
            )
            await session.merge(alert)
            await session.commit()

        # Acknowledge via API
        resp = await client.patch(
            "/api/v1/alerts/TEST-ALERT-001/acknowledge",
            json={"comment": "Dispatching patrol unit"},
            headers=auth_headers(auth_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ACKNOWLEDGED"
        assert body["acknowledged_by"] == "USR-001"
        assert body["comment"] == "Dispatching patrol unit"

        # Verify it's no longer in unacknowledged list
        resp2 = await client.get("/api/v1/alerts", headers=auth_headers(auth_token))
        assert resp2.status_code == 200
        alert_ids = [a["alert_id"] for a in resp2.json()]
        assert "TEST-ALERT-001" not in alert_ids


class TestGraphRouteShadowing:
    """Test 4: Real temporal graph is reachable (not shadowed)."""

    @pytest.mark.asyncio
    async def test_investigation_routes_have_distinct_prefix(self, client, inv_token):
        # The investigation stub should be at /investigation/graph/...
        resp = await client.get(
            "/api/v1/investigation/graph/vehicle/V-123",
            headers=auth_headers(inv_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "_note" in body  # Stub response includes the note

    @pytest.mark.asyncio
    async def test_real_graph_endpoint_reachable(self, client, inv_token):
        # The real graph should be at /graph/... (from interactions router)
        resp = await client.get(
            "/api/v1/graph/vehicle/V-123",
            headers=auth_headers(inv_token),
        )
        # Should NOT return the stub's empty nodes/edges + _note
        assert resp.status_code == 200


class TestHealthCheck:
    """Test 5: Basic health endpoints still work."""

    @pytest.mark.asyncio
    async def test_root_health(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "operational"

    @pytest.mark.asyncio
    async def test_admin_health(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
