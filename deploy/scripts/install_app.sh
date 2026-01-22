#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/opt/tg-digest"
REPO_URL="${REPO_URL:-}"
REF="${REF:-main}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO_URL="$2"
      shift 2
      ;;
    --ref)
      REF="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -z "$REPO_URL" ]]; then
  echo "REPO_URL is required (--repo or env)" >&2
  exit 1
fi

if [[ ! -d "$REPO_DIR/.git" ]]; then
  git clone "$REPO_URL" "$REPO_DIR"
fi

git -C "$REPO_DIR" fetch --all
if git -C "$REPO_DIR" show-ref --verify --quiet "refs/heads/$REF"; then
  git -C "$REPO_DIR" checkout "$REF"
  git -C "$REPO_DIR" pull --ff-only
else
  git -C "$REPO_DIR" checkout "$REF"
fi

chown -R tgdigest:tgdigest "$REPO_DIR"

sudo -u tgdigest bash -lc "cd $REPO_DIR && ~/.local/bin/uv sync"

sudo -u tgdigest bash -lc "cd $REPO_DIR && ./.venv/bin/python -m app.cli init-db"

cp $REPO_DIR/deploy/systemd/tg-digest.service /etc/systemd/system/tg-digest.service
cp $REPO_DIR/deploy/systemd/tg-digest.timer /etc/systemd/system/tg-digest.timer
systemctl daemon-reload
systemctl enable --now tg-digest.timer
