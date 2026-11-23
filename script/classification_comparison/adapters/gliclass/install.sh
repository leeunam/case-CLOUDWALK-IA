#!/bin/sh
set -eu
cd "$(dirname "$0")"
umask 077
python3 -B -c 'from model import verify_platform; verify_platform()'
mkdir -p .cache/tmp
export PIP_CONFIG_FILE=/dev/null
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_CACHE_DIR=1
export TMPDIR="$PWD/.cache/tmp"
unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL PIP_TRUSTED_HOST PIP_FIND_LINKS
python3 -m venv .venv
.venv/bin/python -m pip install --index-url https://pypi.org/simple --only-binary=:all: --retries 0 --timeout 12 -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -B model.py --check-runtime
.venv/bin/python -m pip freeze > .cache/runtime-freeze.txt
.venv/bin/python -B provision.py
