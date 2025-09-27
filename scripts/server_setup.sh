#!/bin/bash

# SecurNote Server Setup Script
# Bu script sunucuda SecurNote'u kurar ve SSH erişimi için hazırlar

set -e

echo "🔐 SecurNote Server Setup Starting..."

# 1. System packages
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git curl

# 2. Create securnote user
echo "👤 Creating securnote user..."
if ! id "securnote" &>/dev/null; then
    sudo useradd -m -s /bin/bash securnote
    echo "✓ User 'securnote' created"
else
    echo "✓ User 'securnote' already exists"
fi

# 3. Setup application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/securnote
sudo chown securnote:securnote /opt/securnote

# 4. Install Poetry for securnote user
echo "📚 Installing Poetry..."
sudo -u securnote bash -c "
    cd /opt/securnote
    curl -sSL https://install.python-poetry.org | python3 -
    echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc
"

# 5. Clone and setup SecurNote
echo "🚀 Cloning SecurNote..."
sudo -u securnote bash -c "
    cd /opt/securnote
    if [ ! -d 'securnote' ]; then
        git clone https://github.com/emreren/securnote.git .
    fi

    # Install dependencies
    export PATH=\"\$HOME/.local/bin:\$PATH\"
    poetry install
"

# 6. Create startup script
echo "⚙️ Creating startup script..."
sudo tee /opt/securnote/run_securnote.sh > /dev/null << 'EOF'
#!/bin/bash
cd /opt/securnote
export PATH="$HOME/.local/bin:$PATH"
exec poetry run python -m securnote "$@"
EOF

sudo chown securnote:securnote /opt/securnote/run_securnote.sh
sudo chmod +x /opt/securnote/run_securnote.sh

# 7. Setup SSH command shortcuts
echo "🔑 Setting up SSH shortcuts..."
sudo -u securnote bash -c "
    echo 'alias securnote=\"/opt/securnote/run_securnote.sh\"' >> ~/.bashrc
    echo 'export SECURNOTE_DATA_DIR=\"/home/securnote/.securnote\"' >> ~/.bashrc
    mkdir -p /home/securnote/.securnote
"

# 8. Create systemd service (optional)
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/securnote-web.service > /dev/null << 'EOF'
[Unit]
Description=SecurNote Web API
After=network.target

[Service]
Type=simple
User=securnote
WorkingDirectory=/opt/securnote
Environment=PATH=/home/securnote/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/home/securnote/.local/bin/poetry run uvicorn securnote.web.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 9. Setup data directories with proper permissions
echo "📂 Setting up data directories..."
sudo -u securnote bash -c "
    mkdir -p /home/securnote/.securnote/{users,notes,challenges,certificates}
    chmod 700 /home/securnote/.securnote
"

echo ""
echo "✅ SecurNote Server Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Add SSH public keys for users:"
echo "   sudo mkdir -p /home/securnote/.ssh"
echo "   sudo nano /home/securnote/.ssh/authorized_keys"
echo "   sudo chown -R securnote:securnote /home/securnote/.ssh"
echo "   sudo chmod 700 /home/securnote/.ssh"
echo "   sudo chmod 600 /home/securnote/.ssh/authorized_keys"
echo ""
echo "2. Test local CLI:"
echo "   sudo -u securnote /opt/securnote/run_securnote.sh"
echo ""
echo "3. Start web service (optional):"
echo "   sudo systemctl enable securnote-web"
echo "   sudo systemctl start securnote-web"
echo ""
echo "4. Connect from client:"
echo "   ssh securnote@your-server-ip securnote"
echo ""
echo "🔐 SSH Connection Examples:"
echo "   ssh securnote@server.com securnote"
echo "   ssh securnote@server.com 'securnote list'"