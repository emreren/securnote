# SecurNote - SSH-Only Secure Note Taking

🔐 **Minimal, secure note-taking application accessed via SSH only**

## Description

SecurNote provides encrypted note storage with SSH-only access. No web interface, no complex monitoring - just secure, terminal-based note management with end-to-end encryption.

## Features

- 🔒 **End-to-end encryption** with AES-256
- 🔑 **SSH-only access** - no web interface
- 📝 **External editor support** (nano, vim)
- 👤 **Multi-user isolation**
- 🛡️ **Zero-knowledge authentication**
- 🐳 **Docker deployment ready**
- ⚡ **Minimal resource usage** (~50MB RAM)

## Quick Start

### 1. Docker Deployment
```bash
# Clone and deploy
git clone https://github.com/emreren/securnote.git
cd securnote
docker-compose up -d

# Check status
docker-compose ps
```

### 2. SSH Connection
```bash
# Connect to SecurNote
ssh securnote@your-server-ip

# Or with custom port
ssh securnote@your-server-ip -p 2222
```

### 3. First Time Setup
```bash
# Register new user
securnote register myusername mypassword

# Start interactive mode
securnote
```

## Usage

### Command Line
```bash
# Register user
securnote register username password

# List notes
securnote list username password

# Add note
securnote add username password "Title" "Content"

# View note
securnote view username password note-id

# Delete note
securnote delete username password note-id
```

### Interactive Mode
```bash
# Start interactive CLI
securnote

# Follow prompts for:
# - User login
# - Note management
# - Editor preferences
```

## Configuration

### SSH Key Setup
```bash
# Generate SSH key (on client)
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Copy public key to server
ssh-copy-id securnote@your-server-ip
```

### External Editors
- Automatically detects: nano, vim, vi
- Set preference in interactive mode
- Supports inline typing as fallback

## Deployment

### Docker Compose (Recommended)
```yaml
version: '3.8'
services:
  securnote:
    build: .
    ports:
      - "2222:22"
    volumes:
      - ./data:/app/data
      - ./ssh_keys:/app/ssh_keys
    restart: unless-stopped
```

### Manual Installation
```bash
# Install dependencies
poetry install

# Setup SSH access
./scripts/setup_ssh_user.sh

# Start application
poetry run securnote
```

## Security Features

- ✅ **No web interface** - attack surface minimized
- ✅ **SSH-only access** - secure transport
- ✅ **End-to-end encryption** - notes encrypted at rest
- ✅ **User isolation** - each user's data is separate
- ✅ **No network listeners** - only SSH daemon

## Project Structure

```
securnote/
├── securnote/          # Core application
│   ├── auth.py         # User authentication
│   ├── crypto.py       # Encryption/decryption
│   ├── storage.py      # Data persistence
│   ├── cli.py          # Interactive CLI
│   └── remote_cli.py   # Command-line interface
├── scripts/            # Deployment scripts
├── data/              # User data storage
└── Dockerfile         # Container configuration
```

## Development

```bash
# Install dev dependencies
poetry install --extras dev

# Format code
make format

# Run lints
make lint

# Run tests
make test

# All checks
make check
```

## Examples

### Basic Usage
```bash
# Connect via SSH
ssh securnote@server

# Register and use
securnote register alice password123
securnote add alice password123 "Shopping List" "Milk, Bread, Eggs"
securnote list alice password123
```

### Advanced Usage
```bash
# Use external editor
securnote
> Login: alice / password123
> Choice: 1 (Add Note)
> Use external editor for content editing
```

## System Requirements

- **RAM**: 50MB base usage
- **Storage**: 100MB (application + user data)
- **Network**: SSH port only (22 or custom)
- **OS**: Linux (Docker) or any Unix-like system

## License

MIT License - see LICENSE file for details.

---

**SecurNote**: Keeping your notes secure, one SSH connection at a time 🔐