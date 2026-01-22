#!/usr/bin/env bash
set -euo pipefail

if ! id -u tgdigest >/dev/null 2>&1; then
  useradd -m -s /bin/bash tgdigest
fi

mkdir -p /opt/tg-digest /var/lib/tg-digest /var/log/tg-digest
chown -R tgdigest:tgdigest /opt/tg-digest /var/lib/tg-digest /var/log/tg-digest

apt-get update
apt-get install -y git curl sqlite3 build-essential python3.12 python3.12-venv python3.12-dev

if ! sudo -u tgdigest bash -lc 'command -v uv' >/dev/null 2>&1; then
  sudo -u tgdigest bash -lc 'curl -LsSf https://astral.sh/uv/install.sh | sh'
fi
