#!/bin/sh
set -eu

# AI-GENERATED-BEGIN (by Codex)
TOOL_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET_REPO=${1:-$(pwd)}
TARGET_REPO=$(CDPATH= cd -- "$TARGET_REPO" && pwd)

python "$TOOL_ROOT/setup.py" develop
python -m ai_code_marker.cli install-hook --repo-root "$TARGET_REPO"
# AI-GENERATED-END
