# SecurNote

A simple encrypted note-taking application for educational cryptography purposes.

## Features

- **Secure Authentication**: SHA-256 + salt password hashing (Linux-style)
- **Note Encryption**: AES-256-GCM authenticated encryption
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
docker-compose up --build

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

1. **Password Hashing**: User passwords are hashed with SHA-256 + unique salt
2. **Key Derivation**: Note encryption keys derived from password using PBKDF2 (100k iterations)
3. **Encryption**: Notes encrypted with AES-256-GCM (authenticated encryption)
4. **Storage**: Only hashed passwords and encrypted notes stored on disk

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
- Password hashing and salt usage
- Symmetric encryption (AES-GCM)
- Key derivation (PBKDF2)
- Secure software architecture
- API development with FastAPI
- Containerization with Docker