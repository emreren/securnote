"""
Admin panel tests.
"""

import pytest
from fastapi.testclient import TestClient

from securnote.web.admin import admin_app


@pytest.mark.unit
class TestAdminPanel:
    """Test admin panel functionality."""

    @pytest.fixture
    def client(self):
        """Provide test client for admin app."""
        return TestClient(admin_app)

    def test_admin_authentication_required(self, client):
        """Test that admin endpoints require authentication."""
        response = client.get("/")
        assert response.status_code == 401

    def test_admin_invalid_credentials(self, client):
        """Test admin access with invalid credentials."""
        response = client.get("/", auth=("wrong", "credentials"))
        assert response.status_code == 401

    def test_admin_valid_credentials(self, client):
        """Test admin access with valid credentials."""
        response = client.get("/", auth=("admin", "securnote_admin_2024"))
        assert response.status_code == 200
        data = response.json()
        assert "admin_panel" in data

    def test_admin_cleanup_system(self, client):
        """Test admin system cleanup endpoint."""
        response = client.post(
            "/system/cleanup", auth=("admin", "securnote_admin_2024")
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_admin_user_list(self, client):
        """Test admin user list endpoint."""
        response = client.get("/users/list", auth=("admin", "securnote_admin_2024"))
        assert response.status_code == 200
