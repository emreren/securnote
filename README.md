# SecurNote

A simple encrypted note-taking application for educational cryptography purposes.

## Features

- **Secure Authentication**: SHA-256 + salt password hashing (Linux-style)
- **Note Encryption**: AES-256-GCM authenticated encryption
- **PKI System**: RSA-based Public Key Infrastructure with Certificate Authority
- **Digital Signatures**: Message authentication and non-repudiation
- **Single Password**: Same password for auth and note encryption (with different salts)
- **CLI Interface**: Command-line tool for note management
- **Web API**: FastAPI REST API with Swagger UI
- **JSON Storage**: Simple file-based storage (no database required)
- **Docker Support**: Easy containerization and deployment

## Quick Start

### Using Docker (Recommended)

```bash
# Clone and run
git clone <repo-url>
cd securnote
docker compose up --build

# Access Swagger UI at http://localhost:8000/docs
```

### Using Poetry

```bash
# Install dependencies
poetry install

# CLI interface
poetry run python -m securnote

# Web API
poetry run python run_web.py
# Visit http://localhost:8000/docs
```

## API Usage

### Register User
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'
```

### Create Note
```bash
curl -X POST "http://localhost:8000/notes" \
  -H "Content-Type: application/json" \
  -d '{"title":"Secret Note","content":"This is encrypted!"}' \
  -u testuser:test123
```

### List Notes
```bash
curl -X GET "http://localhost:8000/notes" -u testuser:test123
```

## Security Architecture

### Symmetric Encryption (Classic Mode)
1. **Password Hashing**: User passwords are hashed with SHA-256 + unique salt
2. **Key Derivation**: Note encryption keys derived from password using PBKDF2 (100k iterations)
3. **Encryption**: Notes encrypted with AES-256-GCM (authenticated encryption)
4. **Storage**: Only hashed passwords and encrypted notes stored on disk

### Public Key Infrastructure (PKI Mode)

#### Certificate Authority (CA) System
The PKI implementation follows industry-standard certificate authority architecture:

**1. Trust Root Establishment**
- CA generates RSA-2048 key pair during initialization
- CA public key serves as the trust anchor for all certificate verification
- CA private key used exclusively for certificate issuance

**2. Certificate Lifecycle**
```
User Registration → Key Generation → Certificate Request → CA Signing → Certificate Issuance
```

**3. Certificate Structure**
Each certificate contains:
- Username (certificate subject)
- User's RSA public key (2048-bit)
- CA digital signature (RSA-PSS with SHA-256)
- Issuing authority identifier

**4. Cryptographic Operations**

*Message Encryption Flow:*
1. Verify recipient certificate against CA public key
2. Extract recipient's public key from valid certificate
3. Encrypt message using RSA-OAEP with SHA-256
4. Sign message with sender's private key (RSA-PSS)
5. Package ciphertext with sender's certificate

*Message Decryption Flow:*
1. Verify sender certificate against CA public key
2. Decrypt message using recipient's private key
3. Verify message signature using sender's public key
4. Return plaintext with signature validation status

**5. Security Properties**
- **Confidentiality**: RSA-OAEP encryption with 2048-bit keys
- **Authenticity**: RSA-PSS digital signatures with SHA-256
- **Integrity**: Cryptographic signature verification prevents tampering
- **Non-repudiation**: Digital signatures provide proof of origin
- **Certificate Validation**: CA-based trust model prevents identity spoofing

**6. Attack Resistance**
- **Man-in-the-Middle**: Certificate validation prevents key substitution attacks
- **Impersonation**: CA signatures cannot be forged without access to CA private key
- **Message Tampering**: PSS signatures detect any content modification
- **Replay Attacks**: Each message includes fresh cryptographic material

#### PKI Usage Example
```python
from securnote.crypto import CertificateAuthority, SecureUser

# Initialize Certificate Authority
ca = CertificateAuthority()

# Create users and obtain certificates
alice = SecureUser("alice")
bob = SecureUser("bob")

alice_cert = alice.request_certificate(ca)
bob_cert = bob.request_certificate(ca)

# Secure messaging
encrypted_msg = alice.encrypt_message("confidential data", bob_cert, ca)
decrypted_msg, signature_valid = bob.decrypt_message(encrypted_msg, ca)
```

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run python tests/test_basic.py

# Run demo
poetry run python demo.py
```

## Project Structure

```
securnote/
├── securnote/
│   ├── auth.py          # User authentication
│   ├── crypto.py        # Note encryption
│   ├── storage.py       # JSON file storage
│   ├── cli.py           # CLI interface
│   └── web/
│       └── app.py       # FastAPI web interface
├── tests/               # Basic tests
├── Dockerfile           # Docker container
├── docker-compose.yml   # Docker Compose setup
└── run_web.py          # Web server runner
```

## Educational Purpose

This project demonstrates:

### Cryptographic Concepts
- **Password hashing and salt usage**: SHA-256 with unique salts
- **Symmetric encryption**: AES-256-GCM authenticated encryption
- **Asymmetric encryption**: RSA-2048 with OAEP padding
- **Key derivation**: PBKDF2 with 100k iterations
- **Digital signatures**: RSA-PSS with SHA-256
- **Certificate management**: X.509-style certificate validation

### Security Architecture
- **Public Key Infrastructure (PKI)**: Complete CA-based trust model
- **Certificate lifecycle management**: Issuance and verification
- **Multi-layer security**: Authentication, encryption, and integrity
- **Attack mitigation**: Protection against common cryptographic attacks

### Software Engineering
- **Secure software architecture**: Defense in depth principles
- **API development**: FastAPI with cryptographic endpoints
- **Containerization**: Docker for secure deployment
- **Testing**: Comprehensive cryptographic testing suite

### Real-world Applications
- **Digital certificates**: Similar to SSL/TLS certificate systems
- **Secure messaging**: End-to-end encrypted communication patterns
- **Identity verification**: PKI-based authentication systems
- **Trust networks**: Certificate authority trust models