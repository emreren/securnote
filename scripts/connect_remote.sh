#!/bin/bash

# SecurNote Remote Client Connection Script
# Bu script uzak SecurNote sunucusuna bağlanmak için kullanılır

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonksiyonlar
print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════╗"
    echo "║           SecurNote Remote            ║"
    echo "║     Secure Note-Taking via SSH       ║"
    echo "╚═══════════════════════════════════════╝"
    echo -e "${NC}"
}

print_usage() {
    echo "Usage: $0 [OPTIONS] <server>"
    echo ""
    echo "Options:"
    echo "  -u, --user USER     SSH username (default: securnote)"
    echo "  -p, --port PORT     SSH port (default: 22)"
    echo "  -k, --key KEY_FILE  SSH private key file"
    echo "  -i, --interactive   Start interactive mode"
    echo "  -h, --help          Show this help"
    echo ""
    echo "Commands (non-interactive):"
    echo "  list USER PASS              List all notes"
    echo "  view USER PASS NOTE_ID      View specific note"
    echo "  add USER PASS TITLE CONTENT Add new note"
    echo "  register USER PASS          Register new user"
    echo ""
    echo "Examples:"
    echo "  # Interactive mode"
    echo "  $0 myserver.com"
    echo "  $0 -u myuser -p 2222 myserver.com"
    echo ""
    echo "  # Direct commands"
    echo "  $0 myserver.com list alice password123"
    echo "  $0 myserver.com view alice password123 abc123"
    echo "  $0 myserver.com add alice password123 \"My Note\" \"Note content\""
    echo ""
    echo "  # With custom SSH settings"
    echo "  $0 -u admin -p 2222 -k ~/.ssh/my_key myserver.com"
}

# Default değerler
SSH_USER="securnote"
SSH_PORT="22"
SSH_KEY=""
INTERACTIVE_MODE=""

# Argüman parsing
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--user)
            SSH_USER="$2"
            shift 2
            ;;
        -p|--port)
            SSH_PORT="$2"
            shift 2
            ;;
        -k|--key)
            SSH_KEY="$2"
            shift 2
            ;;
        -i|--interactive)
            INTERACTIVE_MODE="yes"
            shift
            ;;
        -h|--help)
            print_header
            print_usage
            exit 0
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}"
            print_usage
            exit 1
            ;;
        *)
            if [ -z "$SERVER" ]; then
                SERVER="$1"
            else
                COMMANDS+=("$1")
            fi
            shift
            ;;
    esac
done

# Server kontrolü
if [ -z "$SERVER" ]; then
    echo -e "${RED}Error: Server address required${NC}"
    print_usage
    exit 1
fi

# SSH komut oluşturma
SSH_OPTS="-p $SSH_PORT"
if [ -n "$SSH_KEY" ]; then
    SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
fi

# Test bağlantısı
test_connection() {
    echo -e "${YELLOW}Testing connection to $SSH_USER@$SERVER:$SSH_PORT...${NC}"

    if timeout 10 ssh $SSH_OPTS -o ConnectTimeout=5 -o BatchMode=yes "$SSH_USER@$SERVER" "echo 'Connection OK'" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ SSH connection successful${NC}"
        return 0
    else
        echo -e "${RED}✗ SSH connection failed${NC}"
        echo "Please check:"
        echo "  - Server address: $SERVER"
        echo "  - SSH user: $SSH_USER"
        echo "  - SSH port: $SSH_PORT"
        echo "  - SSH key authentication"
        echo "  - Server accessibility"
        return 1
    fi
}

# Ana fonksiyon
main() {
    print_header

    # Bağlantı testi
    if ! test_connection; then
        exit 1
    fi

    # Komut var mı kontrol et
    if [ ${#COMMANDS[@]} -eq 0 ] || [ "$INTERACTIVE_MODE" = "yes" ]; then
        # Interactive mode
        echo -e "${GREEN}Starting interactive SecurNote session...${NC}"
        echo -e "${BLUE}Use Ctrl+D or 'exit' to disconnect${NC}"
        echo ""

        ssh $SSH_OPTS -t "$SSH_USER@$SERVER" "securnote"
    else
        # Command mode
        REMOTE_COMMAND="securnote"
        for cmd in "${COMMANDS[@]}"; do
            REMOTE_COMMAND="$REMOTE_COMMAND \"$cmd\""
        done

        echo -e "${GREEN}Executing: $REMOTE_COMMAND${NC}"
        echo ""

        ssh $SSH_OPTS "$SSH_USER@$SERVER" "$REMOTE_COMMAND"
    fi
}

# Script başlat
main "$@"