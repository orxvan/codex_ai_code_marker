$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath $PSScriptRoot
python (Join-Path $repoRoot "src/ai_code_marker/cli.py") install-hook --repo-root $repoRoot
