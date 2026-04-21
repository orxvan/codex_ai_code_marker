#!/bin/sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python "$REPO_ROOT/src/ai_code_marker/cli.py" install-hook --repo-root "$REPO_ROOT"
