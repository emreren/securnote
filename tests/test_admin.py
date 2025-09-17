#!/usr/bin/env python3
"""
Admin Panel Test - Test admin authentication and endpoints
"""
import sys
import tempfile

# Add securnote to path
sys.path.append("/workspace/securnote")

import base64

from fastapi.security import HTTPBasicCredentials
from fastapi.testclient import TestClient

from securnote.web.admin import admin_app, verify_admin


def test_admin_authentication():
    """Test admin authentication functionality."""
    print("=== Admin Authentication Test ===")

    client = TestClient(admin_app)

    # Test 1: Access without credentials (should fail)
    response = client.get("/")
    print(f"Access without auth: {'✅' if response.status_code == 401 else '❌'}")

    # Test 2: Access with wrong credentials (should fail)
    response = client.get("/", auth=("wrong", "credentials"))
    print(f"Wrong credentials rejected: {'✅' if response.status_code == 401 else '❌'}")

    # Test 3: Access with correct credentials (should work)
    response = client.get("/", auth=("admin", "securnote_admin_2024"))
    success = response.status_code == 200 and "admin_panel" in response.json()
    print(f"Correct credentials accepted: {'✅' if success else '❌'}")

    if success:
        data = response.json()
        print(f"  - Admin panel: {data['admin_panel']}")
        print(f"  - Available endpoints: {len(data['available_endpoints'])} endpoints")

    print()


def test_admin_endpoints():
    """Test admin PKI management endpoints."""
    print("=== Admin PKI Endpoints Test ===")

    client = TestClient(admin_app)
    auth = ("admin", "securnote_admin_2024")

    # Test 1: System cleanup endpoint
    response = client.post("/system/cleanup", auth=auth)
    cleanup_works = response.status_code == 200
    print(f"System cleanup endpoint: {'✅' if cleanup_works else '❌'}")

    if cleanup_works:
        data = response.json()
        print(f"  - Cleaned challenges: {data['expired_challenges_removed']}")

    # Test 2: Revoked certificates list
    response = client.get("/certificates/revoked", auth=auth)
    revoked_works = response.status_code == 200
    print(f"Revoked certificates list: {'✅' if revoked_works else '❌'}")

    if revoked_works:
        data = response.json()
        print(f"  - Total revoked: {data['total_revoked']}")

    # Test 3: User certificate (non-existent user)
    response = client.get("/certificates/nonexistent", auth=auth)
    not_found_works = response.status_code == 404
    print(f"Non-existent user handling: {'✅' if not_found_works else '❌'}")

    print()


def test_integration_with_main_system():
    """Test admin panel integration with main SecurNote system."""
    print("=== Integration Test ===")

    # Create a test user first using the main application
    with tempfile.TemporaryDirectory() as temp_dir:
        from securnote.application import get_application

        app_instance = get_application()

        # Create user
        success = app_instance.create_user("testadmin", "testpass")
        print(f"Test user created: {'✅' if success else '❌'}")

        if success:
            client = TestClient(admin_app)
            auth = ("admin", "securnote_admin_2024")

            # Test viewing user's certificate
            response = client.get("/certificates/testadmin", auth=auth)
            cert_works = response.status_code == 200
            print(f"View user certificate: {'✅' if cert_works else '❌'}")

            if cert_works:
                data = response.json()
                print(f"  - Certificate found for: {data['username']}")
                print(f"  - Security level: {data['security_level']}")

            # Test revoking user's certificate
            response = client.post(
                "/certificates/testadmin/revoke",
                params={"reason": "test_revocation"},
                auth=auth,
            )
            revoke_works = response.status_code == 200
            print(f"Revoke certificate: {'✅' if revoke_works else '❌'}")

            if revoke_works:
                data = response.json()
                print(f"  - Revoked by: {data['revoked_by']}")
                print(f"  - Reason: {data['reason']}")

    print()


def main():
    """Run all admin panel tests."""
    print("🔧 SecurNote Admin Panel Tests\n")

    test_admin_authentication()
    test_admin_endpoints()
    test_integration_with_main_system()

    print("Admin panel tests completed!")
    print("\n📝 Setup Instructions:")
    print("1. Install uvicorn: pip install uvicorn")
    print("2. Start admin panel: python3 run_admin.py")
    print("3. Access: http://localhost:8001")
    print("4. Login: admin / securnote_admin_2024")


if __name__ == "__main__":
    main()
