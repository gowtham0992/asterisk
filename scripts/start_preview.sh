#!/bin/sh
# Acceptance failed. Keep the existing entity-only fallback enabled.
set -eu
cd "$(dirname "$0")/.."
export ASTERISK_ENTITY_ONLY=1
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8765
