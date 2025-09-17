# SecurNote

A secure note-taking application that demonstrates modern cryptographic techniques for protecting user data and authentication.

## Description

SecurNote provides encrypted note storage with zero-knowledge authentication, ensuring that passwords are never transmitted or stored in plain text. The application implements multiple layers of security including symmetric encryption for notes and public key infrastructure for digital signatures.

## Features

- Zero-knowledge password authentication
- Encrypted note storage with AES-256
- Digital signatures for data integrity
- Command-line and web interfaces
- Docker deployment support
- REST API with interactive documentation

## Installation

### Using Docker

```bash
git clone <repo-url>
cd securnote
docker compose up --build
```

The web interface will be available at http://localhost:8000/docs

### Using Poetry

```bash
poetry install
```

## Usage

### Command Line Interface
```bash
poetry run python -m securnote
```

### Web API
```bash
poetry run python run_web.py
```

### Demo
```bash
poetry run python demo.py
```

## How It Works

### Authentication
The system uses zero-knowledge proofs for authentication:
- Passwords are hashed locally and never sent over the network
- Server challenges are used to verify identity without password transmission
- Each login session uses a unique challenge

### Encryption
Notes are protected using industry-standard encryption:
- AES-256-GCM for symmetric encryption
- PBKDF2 for key derivation
- Digital signatures ensure data hasn't been tampered with

## Development

### Setup Development Environment
```bash
# Install with development dependencies
poetry install --extras dev

# Setup pre-commit hooks
make pre-commit
```

### Code Quality
```bash
# Format code
make format

# Run linting
make lint

# Run tests with coverage
make test

# Run all checks
make check
```

### Running Tests
```bash
poetry run pytest
```

### Project Structure
```
securnote/
├── securnote/
│   ├── auth.py          # Authentication system
│   ├── zkauth.py        # Zero-knowledge authentication
│   ├── crypto.py        # Encryption and digital signatures
│   ├── storage.py       # Encrypted data storage
│   └── web/             # Web API components
├── tests/               # Test files
└── scripts/             # Demo and utility scripts
```

## Requirements

- Python 3.8+
- Poetry for dependency management
- Docker (optional, for containerized deployment)

## License

This project is for demonstration purposes.
