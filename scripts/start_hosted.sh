#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
: "${ASTERISK_ALLOWED_HOSTS:?Set the exact public hostname}"
: "${ASTERISK_PREVIEW_PASSWORD:?Set the reviewer password in the host secret manager}"
: "${ASTERISK_DB:?Set an absolute database path on persistent storage}"
# The legacy single-binding checker uses a baked image; ladder replay ships
# its installed checker source to a disposable base-image Sandbox instead.
case "${ASTERISK_HOSTED_WORKFLOW:-legacy}" in
  legacy)
    : "${ASTERISK_PROBE_IMAGE:?Set the matching v4 Sandbox image}"
    : "${ASTERISK_PROBE_DRIVER_SHA256:?Set the matching v4 driver hash}"
    ;;
  ladder) ;;
  *) echo "ASTERISK_HOSTED_WORKFLOW must be legacy or ladder" >&2; exit 1 ;;
esac
: "${NEBIUS_API_KEY:?Set the Nebius secret}"
: "${NEBIUS_PROJECT_ID:?Set the Nebius project}"
export ASTERISK_PUBLIC=1
export ASTERISK_ENTITY_ONLY=1
exec .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8765}" --workers 1
