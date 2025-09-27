# SecurNote

Encrypted notes via SSH

## Quick Start

```bash
git clone https://github.com/emreren/securnote.git
cd securnote
./quick-start.sh
```

## Features

- AES-256 encryption
- SSH-only access
- Editor support (nano/vim)
- Multi-user
- Lightweight

## Usage

```bash
# Connect and register
ssh -i ssh_keys/id_rsa securnote@localhost -p 2222
securnote register username password
securnote

# Commands
securnote list username password
securnote add username password "Title" "Content"
```

## License

MIT