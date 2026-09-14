#!/bin/sh
# Cron entry point. Runs the crawler with its dedicated pyenv virtualenv.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$HOME/.pyenv/versions/env-gnossi-crawler/bin/python"

exec "$PYTHON" "$SCRIPT_DIR/crawler.py"
