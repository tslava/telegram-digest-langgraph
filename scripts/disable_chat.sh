#!/usr/bin/env bash
set -euo pipefail
uv run tg-digest disable-chat "$@"
