# SecurNote

Encrypted note-taking application for educational cryptography purposes.

## Features

- **Zero-Knowledge Authentication**: Password verification without password transmission
- **Secure Authentication**: SHA-256 + salt password hashing
- **Note Encryption**: AES-256-GCM authenticated encryption
- **PKI System**: RSA-based Public Key Infrastructure with Certificate Authority
- **Digital Signatures**: Message authentication and non-repudiation
- **CLI Interface**: Command-line tool for note management
- **Web API**: FastAPI REST API with Swagger UI
- **JSON Storage**: Simple file-based storage
- **Docker Support**: Easy containerization and deployment

## Quick Start

### Docker (Recommended)

```bash
git clone <repo-url>
cd securnote
docker compose up --build
```

Access Swagger UI at: http://localhost:8000/docs

### Poetry

```bash
poetry install
poetry run python -m securnote          # CLI interface
poetry run python run_web.py            # Web API (http://localhost:8000/docs)
poetry run python demo.py               # Demo
```

## Zero-Knowledge Authentication

Password verification without sending passwords over network.

**Registration:**
- You provide: username + password
- System stores: username + hash(password)
- Your actual password is never stored

**Login Process:**
1. Server sends random challenge number
2. Client calculates: proof = hash(password_hash + challenge)
3. Server verifies proof matches expected value
4. Challenge is destroyed after use

### Symmetric Encryption
- Password hashing with SHA-256 + salt
- Key derivation using PBKDF2 (100k iterations)
- AES-256-GCM authenticated encryption
- Secure file-based storage

### Public Key Infrastructure (PKI)
- RSA-2048 Certificate Authority system
- Digital signatures with RSA-PSS + SHA-256
- Certificate-based identity verification
- End-to-end encrypted messaging

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
│   ├── auth.py          # Traditional + ZK authentication
│   ├── zkauth.py        # Zero-knowledge proof system
│   ├── crypto.py        # Encryption + PKI system
│   ├── storage.py       # Encrypted note storage
│   └── web/app.py       # Web API interface
├── tests/               # Basic functionality tests
├── test_zkauth.py       # Zero-knowledge auth tests
└── test_pki.py          # PKI system tests
```

