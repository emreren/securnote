# Lightweight SecurNote SSH Server
FROM python:3.11-alpine

# Install minimal dependencies
RUN apk add --no-cache openssh-server nano vim

# Create securnote user
RUN adduser -D -s /bin/sh securnote && \
    mkdir -p /home/securnote/.ssh && \
    chown -R securnote:securnote /home/securnote && \
    chmod 700 /home/securnote/.ssh

# Configure SSH
RUN ssh-keygen -A && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Setup application
WORKDIR /app
COPY pyproject.toml ./
COPY securnote/ ./securnote/

# Install uv (super fast pip replacement)
RUN pip install --no-cache-dir uv

# Install app with uv
RUN uv pip install --system --no-cache .

# Setup user environment
USER securnote
RUN mkdir -p /home/securnote/.securnote && \
    echo 'alias securnote="python -m securnote"' >> /home/securnote/.profile

# Switch to root for startup
USER root

# Setup SSH keys
RUN echo "# Add your public keys here" > /home/securnote/.ssh/authorized_keys && \
    chown securnote:securnote /home/securnote/.ssh/authorized_keys && \
    chmod 600 /home/securnote/.ssh/authorized_keys

EXPOSE 22

# Simple startup
CMD ["/usr/sbin/sshd", "-D"]