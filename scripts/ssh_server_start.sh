#!/bin/bash

# SecurNote SSH Server Startup Script

set -e

echo "🔐 Starting SecurNote SSH Server..."

# Generate SSH host keys if they don't exist
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    echo "🔑 Generating SSH host keys..."
    ssh-keygen -A
fi

# Check SSH configuration
echo "🔧 Checking SSH configuration..."
sshd -t

# Ensure securnote user has proper permissions
chown -R securnote:securnote /home/securnote
chmod 700 /home/securnote/.ssh
chmod 600 /home/securnote/.ssh/authorized_keys 2>/dev/null || true

# Create data directory if it doesn't exist
mkdir -p /home/securnote/.securnote
chown -R securnote:securnote /home/securnote/.securnote
chmod 700 /home/securnote/.securnote

# Display server information
echo "📋 SecurNote SSH Server Information:"
echo "   SSH Port: 22"
echo "   User: securnote"
echo "   Data Directory: /home/securnote/.securnote"
echo ""

# Check if authorized_keys exists and has content
if [ -s /home/securnote/.ssh/authorized_keys ]; then
    key_count=$(wc -l < /home/securnote/.ssh/authorized_keys)
    echo "🔑 SSH Keys: $key_count authorized key(s) found"
else
    echo "⚠️  Warning: No SSH keys found in /home/securnote/.ssh/authorized_keys"
    echo "   Add your public key to enable SSH access:"
    echo "   docker exec -it <container> bash"
    echo "   echo 'your-public-key' >> /home/securnote/.ssh/authorized_keys"
fi

echo ""
echo "📡 Connection Examples:"
echo "   ssh securnote@your-server-ip securnote"
echo "   ssh securnote@your-server-ip 'securnote list user pass'"
echo ""

# Test SecurNote CLI
echo "🧪 Testing SecurNote CLI..."
sudo -u securnote bash -c "cd /opt/securnote && python -c 'from securnote.cli import SecurNoteCLI; print(\"✓ SecurNote CLI ready\")'"

echo "✅ Starting SSH daemon..."

# Start SSH daemon in foreground
exec /usr/sbin/sshd -D