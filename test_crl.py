#!/usr/bin/env python3
"""
Certificate Revocation List (CRL) Test
"""
import tempfile
import sys
import os

# Add securnote to path
sys.path.append('/workspace/securnote')

from securnote.crypto import CertificateAuthority, SecureUser


def test_certificate_revocation():
    """Test certificate revocation functionality."""
    print("=== Certificate Revocation Test ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create CA and users
        ca = CertificateAuthority(data_dir=temp_dir)
        alice = SecureUser("alice")
        bob = SecureUser("bob")

        # Issue certificates
        alice_cert = alice.request_certificate(ca)
        bob_cert = bob.request_certificate(ca)

        print(f"Alice cert ID: {alice_cert['cert_id']}")
        print(f"Bob cert ID: {bob_cert['cert_id']}")

        # Test 1: Initially certificates should be valid
        alice_valid = ca.verify_certificate(alice_cert)
        bob_valid = ca.verify_certificate(bob_cert)
        print(f"Alice cert initially valid: {'✅' if alice_valid else '❌'}")
        print(f"Bob cert initially valid: {'✅' if bob_valid else '❌'}")

        # Test 2: Check revocation status (should be False)
        alice_revoked = ca.is_certificate_revoked(alice_cert['cert_id'])
        print(f"Alice cert initially revoked: {'❌' if not alice_revoked else '⚠️ FAIL'}")

        # Test 3: Revoke Alice's certificate
        revoke_success = ca.revoke_certificate(alice_cert['cert_id'], "key_compromise")
        print(f"Alice cert revoked successfully: {'✅' if revoke_success else '❌'}")

        # Test 4: Check if Alice's cert is now invalid
        alice_valid_after = ca.verify_certificate(alice_cert)
        print(f"Alice cert valid after revocation: {'❌' if not alice_valid_after else '⚠️ FAIL'}")

        # Test 5: Bob's cert should still be valid
        bob_valid_after = ca.verify_certificate(bob_cert)
        print(f"Bob cert still valid: {'✅' if bob_valid_after else '❌'}")

        # Test 6: Try to revoke same certificate again (should fail)
        revoke_duplicate = ca.revoke_certificate(alice_cert['cert_id'], "test")
        print(f"Duplicate revocation blocked: {'✅' if not revoke_duplicate else '⚠️ FAIL'}")

        print()


def test_crl_management():
    """Test CRL management functions."""
    print("=== CRL Management Test ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        ca = CertificateAuthority(data_dir=temp_dir)

        # Create some users and revoke their certificates
        users = []
        for name in ["alice", "bob", "charlie"]:
            user = SecureUser(name)
            cert = user.request_certificate(ca)
            users.append((user, cert))

        # Revoke first two certificates
        ca.revoke_certificate(users[0][1]['cert_id'], "key_compromise")
        ca.revoke_certificate(users[1][1]['cert_id'], "cessation_of_operation")

        # Get revoked certificates list
        revoked_list = ca.get_revoked_certificates()
        print(f"Number of revoked certificates: {len(revoked_list)}")

        for revoked in revoked_list:
            print(f"  - Cert ID: {revoked['cert_id'][:8]}... Reason: {revoked['reason']}")

        # Test that third certificate is still valid
        charlie_valid = ca.verify_certificate(users[2][1])
        print(f"Charlie's cert still valid: {'✅' if charlie_valid else '❌'}")

        print()


def test_messaging_with_revoked_cert():
    """Test secure messaging with revoked certificates."""
    print("=== Messaging with Revoked Certificate Test ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        ca = CertificateAuthority(data_dir=temp_dir)

        # Create users
        alice = SecureUser("alice")
        bob = SecureUser("bob")

        # Get certificates
        alice_cert = alice.request_certificate(ca)
        bob_cert = bob.request_certificate(ca)

        # Alice sends message to Bob (should work)
        try:
            message = "Hello Bob!"
            encrypted_msg = alice.encrypt_message(message, bob_cert, ca)
            decrypted, sig_valid = bob.decrypt_message(encrypted_msg, ca)
            print(f"Normal messaging works: {'✅' if decrypted == message and sig_valid else '❌'}")
        except Exception as e:
            print(f"Normal messaging failed: ❌ {e}")

        # Revoke Alice's certificate
        ca.revoke_certificate(alice_cert['cert_id'], "key_compromise")

        # Try to send message with revoked certificate (should fail)
        try:
            message = "This should fail!"
            encrypted_msg = alice.encrypt_message(message, bob_cert, ca)
            print("Message with revoked cert: ⚠️ FAIL - Should have been blocked")
        except Exception as e:
            print(f"Message with revoked cert blocked: ✅ {str(e)[:50]}...")

        print()


def main():
    """Run all CRL tests."""
    print("🔒 Certificate Revocation List (CRL) Tests\n")

    test_certificate_revocation()
    test_crl_management()
    test_messaging_with_revoked_cert()

    print("All CRL tests completed!")


if __name__ == "__main__":
    main()