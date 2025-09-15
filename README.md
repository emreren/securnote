# SecurNote

Encrypted note-taking application for educational cryptography purposes.

## Features

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

## Security Architecture

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

