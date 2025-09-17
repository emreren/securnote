"""
Pytest configuration and fixtures for SecurNote tests.
"""

import tempfile
from pathlib import Path

import pytest

from securnote.application import SecurNoteApplication


@pytest.fixture
def temp_dir():
    """Provide temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def app(temp_dir):
    """Provide SecurNote application instance."""
    return SecurNoteApplication(data_dir=temp_dir)


@pytest.fixture
def test_user_data():
    """Provide standard test user data."""
    return {
        "username": "testuser",
        "password": "SecurePass123!",
    }


@pytest.fixture
def test_note_data():
    """Provide standard test note data."""
    return {
        "title": "Test Note",
        "content": "This is a test note content.",
    }
