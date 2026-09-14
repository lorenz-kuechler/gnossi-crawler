#!/bin/sh
# Cron entry point. Runs the crawler with its dedicated pyenv virtualenv.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Only pull PYTHON_BIN out of .env (not a full source) since other values in
# there, like SMTP_PASSWORD, may contain shell-special characters.
PYTHON="$(grep -E '^PYTHON_BIN=' "$SCRIPT_DIR/.env" | head -n1 | cut -d '=' -f2-)"

exec "$PYTHON" "$SCRIPT_DIR/crawler.py"
