#!/bin/bash

# export PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp/}rotostampa-pycache"

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

uv run                                            \
    --directory "$SCRIPT_DIR"                     \
    --exact --no-env-file                         \
    --no-config                                   \
    --python 3.11                                 \
    --python-preference only-managed              \
    --with-requirements rdvhome/requirements.txt \
    python3 run.py "$@"
