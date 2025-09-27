# SecurNote SSH Server
FROM python:3.11-slim

# Install system dependencies including SSH server
RUN apt-get update && apt-get install -y \
    openssh-server \
    build-essential \
    sudo \
    nano \
    vim \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Create securnote user
RUN useradd -m -s /bin/bash securnote && \
    echo "securnote:securnote" | chpasswd && \
    mkdir -p /home/securnote/.ssh && \
    chown -R securnote:securnote /home/securnote && \
    chmod 700 /home/securnote/.ssh

# Setup SSH
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#AuthorizedKeysFile/AuthorizedKeysFile/' /etc/ssh/sshd_config

# Create application directory
WORKDIR /opt/securnote
RUN chown securnote:securnote /opt/securnote

# Copy application files
COPY pyproject.toml poetry.lock ./
COPY securnote/ ./securnote/
COPY scripts/ ./scripts/

# Configure poetry and install dependencies as securnote user
USER securnote
RUN poetry config virtualenvs.create false && \
    poetry install --only=main

# Create startup script
RUN echo '#!/bin/bash\ncd /opt/securnote\nexec poetry run python -m securnote "$@"' > /home/securnote/securnote && \
    chmod +x /home/securnote/securnote

# Setup shell aliases
RUN echo 'alias securnote="/home/securnote/securnote"' >> /home/securnote/.bashrc && \
    echo 'export PATH="/home/securnote/.local/bin:$PATH"' >> /home/securnote/.bashrc && \
    mkdir -p /home/securnote/.securnote

# Switch back to root for SSH setup
USER root

# Copy SSH keys (if provided)
COPY ssh_keys/authorized_keys /home/securnote/.ssh/authorized_keys 2>/dev/null || \
    echo "# Add your public keys here" > /home/securnote/.ssh/authorized_keys

RUN chown securnote:securnote /home/securnote/.ssh/authorized_keys && \
    chmod 600 /home/securnote/.ssh/authorized_keys

# Create startup script
COPY scripts/ssh_server_start.sh /usr/local/bin/start_ssh_server.sh
RUN chmod +x /usr/local/bin/start_ssh_server.sh

# Expose SSH port
EXPOSE 22

# Start SSH server
CMD ["/usr/local/bin/start_ssh_server.sh"]