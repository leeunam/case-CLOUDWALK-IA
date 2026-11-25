#!/bin/sh
set -eu
cd "$(dirname "$0")"
umask 077
mkdir -p .cache/tmp
unset HF_TOKEN HUGGING_FACE_HUB_TOKEN FEITA_API_KEY TYPESAFE_API_KEY
unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL PIP_TRUSTED_HOST PIP_FIND_LINKS
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_TELEMETRY=1
export PIP_CONFIG_FILE=/dev/null PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
export TMPDIR="$PWD/.cache/tmp"
exec timeout --kill-after=5s 30m sh -eu -c '
    python3 -m venv .venv
    .venv/bin/python -m pip install --index-url https://pypi.org/simple --only-binary=:all: --timeout 30 --retries 1 -r requirements.txt
    .venv/bin/python -m pip check
    python3 -B provision.py
'
