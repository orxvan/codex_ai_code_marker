$ErrorActionPreference = "Stop"

# AI-GENERATED-BEGIN (by Codex)
param(
    [string]$RepoRoot = (Get-Location).Path
)

$toolRoot = Resolve-Path -LiteralPath $PSScriptRoot
$targetRepo = Resolve-Path -LiteralPath $RepoRoot

python (Join-Path $toolRoot "setup.py") develop
python -m ai_code_marker.cli install-hook --repo-root $targetRepo
# AI-GENERATED-END
