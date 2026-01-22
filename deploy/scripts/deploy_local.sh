#!/usr/bin/env bash
set -euo pipefail

HOST="${1:-}"
REF="${2:-main}"

if [[ -z "$HOST" ]]; then
  echo "Usage: deploy_local.sh user@host [ref]" >&2
  exit 1
fi

ssh "$HOST" "sudo /opt/tg-digest/deploy/scripts/install_app.sh --repo \"$(git config --get remote.origin.url)\" --ref $REF"
ssh "$HOST" "sudo /opt/tg-digest/deploy/scripts/smoke_test.sh"
ssh "$HOST" "systemctl status tg-digest.timer --no-pager"
