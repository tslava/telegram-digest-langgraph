#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/opt/tg-digest"

sudo -u tgdigest bash -lc "cd $REPO_DIR && export DRY_RUN=1 && export POST_TO_TELEGRAM=0 && ./.venv/bin/tg-digest run-all"
