#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
: "${ASTERISK_ALLOWED_HOSTS:?Set the exact public hostname}"
: "${ASTERISK_PREVIEW_PASSWORD:?Set the reviewer password in the host secret manager}"
: "${ASTERISK_DB:?Set an absolute database path on persistent storage}"
: "${ASTERISK_PROBE_IMAGE:?Set the matching v4 Sandbox image}"
: "${NEBIUS_API_KEY:?Set the Nebius secret}"
: "${NEBIUS_PROJECT_ID:?Set the Nebius project}"
export ASTERISK_PUBLIC=1
export ASTERISK_ENTITY_ONLY=1
exec .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8765}" --workers 1
