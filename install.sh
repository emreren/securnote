#!/bin/bash

# SecurNote Installation Script
set -e

echo "SecurNote Installation"
echo "====================="

# Check if Docker is available and prefer it
if command -v docker &> /dev/null; then
    echo "Using Docker deployment..."

    # Create SSH keys if not exist
    if [ ! -d "ssh_keys" ]; then
        mkdir -p ssh_keys
        ssh-keygen -t rsa -b 4096 -f ssh_keys/id_rsa -N "" -C "securnote@localhost"
        echo "✓ SSH key generated"
    fi

    # Build and run container
    echo "🏗️  Building container..."
    docker build -t securnote .

    echo "🚀 Starting container..."
    docker run -d \
        --name securnote-server \
        -p 2222:22 \
        -v $(pwd)/ssh_keys:/host_ssh_keys:ro \
        -v securnote_data:/home/securnote/.securnote \
        --restart unless-stopped \
        securnote

    echo ""
    echo "SecurNote is running!"
    echo ""
    echo "Connect with:"
    echo "  ssh -i ssh_keys/id_rsa securnote@localhost -p 2222"
    echo ""

else
    echo "Using local Python deployment..."

    # Create virtual environment
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate

    # Install uv in venv
    echo "Installing uv..."
    pip install uv

    # Install dependencies with uv
    echo "Installing dependencies..."
    uv pip install -e .

    # Create data directory
    mkdir -p data

    echo ""
    echo "SecurNote installation completed!"
    echo ""
    echo "Quick commands (activate venv first):"
    echo "  source .venv/bin/activate"
    echo "  securnote register username password"
    echo "  securnote"
    echo ""

fi