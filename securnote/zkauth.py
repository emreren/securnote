"""
Simple Zero-Knowledge Proof Authentication
Challenge-response system without password transmission
"""

import hashlib
import json
import os
import secrets


class ZKAuth:
    """Zero-knowledge authentication using challenge-response."""

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def register_user(self, username, password):
        """Register user with password hash storage."""
        user_file = os.path.join(self.data_dir, f"{username}_zk.json")

        if os.path.exists(user_file):
            return False

        # Generate salt and hash password
        salt = secrets.token_bytes(16)
        password_hash = hashlib.sha256(salt + password.encode()).hexdigest()

        user_data = {
            "username": username,
            "salt": salt.hex(),
            "password_hash": password_hash,
        }

        with open(user_file, "w") as f:
            json.dump(user_data, f)

        return True

    def create_challenge(self, username):
        """Generate random challenge for user."""
        user_file = os.path.join(self.data_dir, f"{username}_zk.json")

        if not os.path.exists(user_file):
            return None

        # Create random challenge
        challenge = secrets.token_hex(16)

        # Store challenge temporarily
        challenge_file = os.path.join(self.data_dir, f"challenge_{challenge}.json")
        challenge_data = {"username": username, "challenge": challenge, "used": False}

        with open(challenge_file, "w") as f:
            json.dump(challenge_data, f)

        return challenge

    def create_proof(self, username, password, challenge):
        """Generate ZK proof without sending password."""
        user_file = os.path.join(self.data_dir, f"{username}_zk.json")

        if not os.path.exists(user_file):
            return None

        # Load user data
        with open(user_file, "r") as f:
            user_data = json.load(f)

        # Recreate password hash
        salt = bytes.fromhex(user_data["salt"])
        password_hash = hashlib.sha256(salt + password.encode()).hexdigest()

        # Verify password is correct
        if password_hash != user_data["password_hash"]:
            return None

        # Generate proof: hash(password_hash + challenge)
        proof = hashlib.sha256((password_hash + challenge).encode()).hexdigest()

        return proof

    def verify_proof(self, username, challenge, proof):
        """Verify ZK proof against stored hash."""
        user_file = os.path.join(self.data_dir, f"{username}_zk.json")
        challenge_file = os.path.join(self.data_dir, f"challenge_{challenge}.json")

        if not os.path.exists(user_file) or not os.path.exists(challenge_file):
            return False

        # Check challenge validity
        with open(challenge_file, "r") as f:
            challenge_data = json.load(f)

        if challenge_data["used"] or challenge_data["username"] != username:
            return False

        # Mark challenge as used
        challenge_data["used"] = True
        with open(challenge_file, "w") as f:
            json.dump(challenge_data, f)

        # Load user data
        with open(user_file, "r") as f:
            user_data = json.load(f)

        # Calculate expected proof
        expected_proof = hashlib.sha256(
            (user_data["password_hash"] + challenge).encode()
        ).hexdigest()

        return proof == expected_proof

    def authenticate(self, username, password):
        """Complete ZK authentication flow."""
        # Step 1: Create challenge
        challenge = self.create_challenge(username)
        if not challenge:
            return False

        # Step 2: Generate proof
        proof = self.create_proof(username, password, challenge)
        if not proof:
            return False

        # Step 3: Verify proof
        return self.verify_proof(username, challenge, proof)
