#!/usr/bin/env python3
"""
Zero-Knowledge Authentication Test
"""
import tempfile
import sys
import os

# Add securnote to path
sys.path.append('/workspace/securnote')

from securnote.zkauth import ZKAuth
from securnote.auth import UserAuth


def test_zk_basic():
    """Test basic ZK authentication flow."""
    print("=== Basic ZK Test ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        zk = ZKAuth(temp_dir)

        # Register user
        result = zk.register_user("alice", "password123")
        print(f"Register: {'✅' if result else '❌'}")

        # Test authentication
        auth_result = zk.authenticate("alice", "password123")
        print(f"Auth correct password: {'✅' if auth_result else '❌'}")

        # Test wrong password
        auth_result = zk.authenticate("alice", "wrongpass")
        print(f"Auth wrong password: {'❌' if not auth_result else '⚠️ FAIL'}")

        print()


def test_zk_integration():
    """Test ZK integration with existing auth system."""
    print("=== ZK Integration Test ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        auth = UserAuth(temp_dir)

        # Register user (now includes ZK registration)
        result = auth.create_user("bob", "secret456")
        print(f"Register with ZK: {'✅' if result else '❌'}")

        # Traditional login
        note_key = auth.login("bob", "secret456")
        print(f"Traditional login: {'✅' if note_key else '❌'}")

        # ZK login
        zk_note_key = auth.zk_login("bob", "secret456")
        print(f"ZK login: {'✅' if zk_note_key else '❌'}")

        # Wrong password ZK login
        zk_fail = auth.zk_login("bob", "wrongpass")
        print(f"ZK login wrong pass: {'❌' if not zk_fail else '⚠️ FAIL'}")

        print()


def test_challenge_security():
    """Test challenge security features."""
    print("=== Challenge Security Test ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        zk = ZKAuth(temp_dir)

        # Register user
        zk.register_user("charlie", "test789")

        # Get challenge
        challenge = zk.create_challenge("charlie")
        print(f"Challenge created: {'✅' if challenge else '❌'}")

        # Create proof
        proof = zk.create_proof("charlie", "test789", challenge)
        print(f"Proof created: {'✅' if proof else '❌'}")

        # Verify proof
        valid = zk.verify_proof("charlie", challenge, proof)
        print(f"Proof valid: {'✅' if valid else '❌'}")

        # Try to reuse challenge (should fail)
        reuse_attempt = zk.verify_proof("charlie", challenge, proof)
        print(f"Challenge reuse blocked: {'✅' if not reuse_attempt else '⚠️ FAIL'}")

        print()


def main():
    """Run all ZK authentication tests."""
    print("🔐 Zero-Knowledge Authentication Tests\n")

    test_zk_basic()
    test_zk_integration()
    test_challenge_security()

    print("All tests completed!")


if __name__ == "__main__":
    main()