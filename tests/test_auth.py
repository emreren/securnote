"""
Authentication system tests.
"""

import pytest

from securnote.exceptions import UserAlreadyExistsError


@pytest.mark.unit
class TestAuthentication:
    """Test authentication functionality."""

    def test_user_creation(self, app, test_user_data):
        """Test successful user creation."""
        result = app.create_user(test_user_data["username"], test_user_data["password"])
        assert result is True

    def test_duplicate_user_creation(self, app, test_user_data):
        """Test that duplicate users cannot be created."""
        # Create user first time
        app.create_user(test_user_data["username"], test_user_data["password"])

        # Attempt to create same user again
        result = app.create_user(test_user_data["username"], test_user_data["password"])
        assert result is False

    def test_user_login(self, app, test_user_data):
        """Test successful user login."""
        # Create user
        app.create_user(test_user_data["username"], test_user_data["password"])

        # Login
        note_key = app.login(test_user_data["username"], test_user_data["password"])
        assert note_key is not None
        assert len(note_key) == 32  # 256-bit key

    def test_invalid_login(self, app, test_user_data):
        """Test login with invalid credentials."""
        # Create user
        app.create_user(test_user_data["username"], test_user_data["password"])

        # Test wrong password
        note_key = app.login(test_user_data["username"], "wrongpassword")
        assert note_key is None

        # Test non-existent user
        note_key = app.login("nonexistent", test_user_data["password"])
        assert note_key is None

    def test_user_exists(self, app, test_user_data):
        """Test user existence check."""
        # User doesn't exist initially
        assert not app.user_exists(test_user_data["username"])

        # Create user
        app.create_user(test_user_data["username"], test_user_data["password"])

        # User now exists
        assert app.user_exists(test_user_data["username"])
