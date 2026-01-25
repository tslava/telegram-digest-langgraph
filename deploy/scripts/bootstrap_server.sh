#!/usr/bin/env bash
set -euo pipefail

# Deployment mode: "docker" or "native" (default: docker)
DEPLOY_MODE="${DEPLOY_MODE:-docker}"

# Create user if it doesn't exist
if ! id -u tgdigest >/dev/null 2>&1; then
  useradd -m -s /bin/bash tgdigest
fi

# Create required directories
mkdir -p /opt/tg-digest /var/lib/tg-digest /var/log/tg-digest /etc/tg-digest
chown -R tgdigest:tgdigest /opt/tg-digest /var/lib/tg-digest /var/log/tg-digest /etc/tg-digest

apt-get update

if [[ "$DEPLOY_MODE" == "docker" ]]; then
  # Docker deployment
  apt-get install -y curl

  if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
  fi

  # Add tgdigest user to docker group
  usermod -aG docker tgdigest

  # Create Docker volume for persistent data
  docker volume create tg-digest-data || true
else
  # Native deployment (legacy)
  apt-get install -y git curl sqlite3 build-essential python3.12 python3.12-venv python3.12-dev

  if ! sudo -u tgdigest bash -lc 'command -v uv' >/dev/null 2>&1; then
    sudo -u tgdigest bash -lc 'curl -LsSf https://astral.sh/uv/install.sh | sh'
  fi
fi
