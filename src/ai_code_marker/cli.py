import argparse
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


AI_PREFIX_LABEL = "[AI\u534f\u540c]"
AI_NOTES_REF = "refs/notes/ai"
PENDING_ATTRIBUTION_FILE = Path(".git") / "ai-code-marker" / "staged-attribution.json"
TRAILER_KEYS = [
    "AI-Code-Lines",
    "AI-Total-Lines",
    "AI-Code-Ratio",
    "AI-Tools",
    "AI-Files",
]
PREFIX_RE = re.compile(r"^\[[^\]]+\]\(ai:\d+/total:\d+/ratio:\d+(?:\.\d+)?%\)\s+")
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


@dataclass
class Stats:
    ai_lines: int
    total_lines: int
    files: list[str]
    tools: list[str]
    details: list[dict]

    @property
    def ai_ratio(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return round((self.ai_lines / self.total_lines) * 100, 2)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    return result.stdout


def get_git_dir() -> Path:
    return Path(git("rev-parse", "--git-dir").strip())


def get_pending_attr_path() -> Path:
    return get_git_dir() / "ai-code-marker" / "staged-attribution.json"


def parse_staged_diff() -> list[dict]:
    diff = git("diff", "--cached", "--unified=0", "--no-color", "--no-ext-diff")
    changes: list[dict] = []
    current_file: str | None = None
    current_new_line = 0

    for raw_line in diff.splitlines():
        if raw_line.startswith("+++ b/"):
            current_file = raw_line[6:]
            continue
        if raw_line.startswith("diff --git") or raw_line.startswith("index ") or raw_line.startswith("--- "):
            continue
        if raw_line.startswith("@@"):
            match = HUNK_RE.match(raw_line)
            if not match:
                continue
            current_new_line = int(match.group(1))
            continue
        if not current_file or not raw_line:
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            content = raw_line[1:]
            changes.append(
                {
                    "file": current_file,
                    "line_number": current_new_line,
                    "content": content,
                    "is_blank": not content.strip(),
                }
            )
            current_new_line += 1
            continue
        if raw_line.startswith(" ") and not raw_line.startswith("  "):
            current_new_line += 1

    return changes


def load_pending_attribution() -> dict | None:
    path = get_pending_attr_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_pending_attribution(payload: dict) -> Path:
    path = get_pending_attr_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def clear_pending_attribution() -> None:
    path = get_pending_attr_path()
    if path.exists():
        path.unlink()


def attribution_line_set(payload: dict | None) -> dict[str, set[int]]:
    mapping: dict[str, set[int]] = {}
    if not payload:
        return mapping
    for file_entry in payload.get("files", []):
        mapping[file_entry["path"]] = set(file_entry.get("added_lines", []))
    return mapping


def build_stats(changes: list[dict], pending: dict | None) -> Stats:
    ai_lines = 0
    total_lines = 0
    files = OrderedDict()
    tools = OrderedDict()
    details = []
    ai_line_map = attribution_line_set(pending)
    tool = pending.get("tool") if pending else None
    model = pending.get("model") if pending else None

    for change in changes:
        if change["is_blank"]:
            continue
        total_lines += 1
        files[change["file"]] = True
        if change["line_number"] in ai_line_map.get(change["file"], set()):
            ai_lines += 1
            if tool:
                tools[tool] = True
            details.append(
                {
                    "file": change["file"],
                    "tool": tool or "unknown",
                    "model": model,
                    "line_number": change["line_number"],
                    "line": change["content"],
                }
            )

    return Stats(
        ai_lines=ai_lines,
        total_lines=total_lines,
        files=list(files.keys()),
        tools=list(tools.keys()),
        details=details,
    )


def parse_staged_stats() -> Stats:
    return build_stats(parse_staged_diff(), load_pending_attribution())


def remove_existing_metadata(lines: Iterable[str]) -> list[str]:
    cleaned = []
    for index, line in enumerate(lines):
        if index == 0:
            line = PREFIX_RE.sub("", line)
        if any(line.startswith(f"{key}:") for key in TRAILER_KEYS):
            continue
        cleaned.append(line)

    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return cleaned


def build_commit_message(original: str, stats: Stats) -> str:
    lines = original.splitlines()
    if not lines:
        lines = [""]

    cleaned = remove_existing_metadata(lines)
    subject = cleaned[0] if cleaned else ""
    prefix = f"{AI_PREFIX_LABEL}(ai:{stats.ai_lines}/total:{stats.total_lines}/ratio:{stats.ai_ratio:.2f}%) "
    cleaned[0] = prefix + subject

    trailers = [
        "",
        f"AI-Code-Lines: {stats.ai_lines}",
        f"AI-Total-Lines: {stats.total_lines}",
        f"AI-Code-Ratio: {stats.ai_ratio:.2f}%",
        f"AI-Tools: {', '.join(stats.tools) if stats.tools else 'none'}",
        f"AI-Files: {', '.join(stats.files) if stats.files else 'none'}",
    ]

    return "\n".join(cleaned + trailers) + "\n"


def render_hook(repo_root: Path, command: str) -> str:
    repo_root_posix = repo_root.as_posix()
    return (
        "#!/bin/sh\n"
        "set -eu\n\n"
        f'REPO_ROOT="{repo_root_posix}"\n'
        'PYTHON_BIN="${PYTHON_BIN:-python}"\n'
        f'exec "$PYTHON_BIN" "$REPO_ROOT/src/ai_code_marker/cli.py" {command} "$@"\n'
    )


def install_hook(repo_root: Path) -> list[Path]:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        raise FileNotFoundError(f"Current directory is not a Git repository: {repo_root}")

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    prepare_hook = hooks_dir / "prepare-commit-msg"
    prepare_hook.write_text(render_hook(repo_root, "prepare-commit-msg"), encoding="utf-8", newline="\n")

    post_hook = hooks_dir / "post-commit"
    post_hook.write_text(render_hook(repo_root, "post-commit"), encoding="utf-8", newline="\n")

    if os.name != "nt":
        prepare_hook.chmod(0o755)
        post_hook.chmod(0o755)

    return [prepare_hook, post_hook]


def build_pending_payload(tool: str, model: str | None, changes: list[dict]) -> dict:
    files = OrderedDict()
    for change in changes:
        if change["is_blank"]:
            continue
        files.setdefault(change["file"], [])
        files[change["file"]].append(change["line_number"])

    return {
        "version": 1,
        "tool": tool,
        "model": model,
        "files": [{"path": path, "added_lines": lines} for path, lines in files.items()],
    }


def cmd_stats(args: argparse.Namespace) -> int:
    stats = parse_staged_stats()
    payload = {
        "ai_lines": stats.ai_lines,
        "total_lines": stats.total_lines,
        "ai_ratio": stats.ai_ratio,
        "files": stats.files,
        "tools": stats.tools,
        "details": stats.details,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"AI lines: {stats.ai_lines}")
        print(f"Total lines: {stats.total_lines}")
        print(f"AI ratio: {stats.ai_ratio:.2f}%")
        print(f"Tools: {', '.join(stats.tools) if stats.tools else 'none'}")
        print(f"Files: {', '.join(stats.files) if stats.files else 'none'}")
    return 0


def cmd_record_staged(args: argparse.Namespace) -> int:
    changes = parse_staged_diff()
    payload = build_pending_payload(args.tool, args.model, changes)
    save_pending_attribution(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_prepare_commit_msg(args: argparse.Namespace) -> int:
    msg_path = Path(args.message_file)
    original = msg_path.read_text(encoding="utf-8")
    stats = parse_staged_stats()
    updated = build_commit_message(original, stats)
    msg_path.write_text(updated, encoding="utf-8")
    return 0


def cmd_post_commit(args: argparse.Namespace) -> int:
    payload = load_pending_attribution()
    if not payload:
        return 0
    git("notes", "--ref", AI_NOTES_REF, "add", "-f", "-m", json.dumps(payload, ensure_ascii=False, indent=2), "HEAD")
    clear_pending_attribution()
    return 0


def cmd_install_hook(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path.cwd()
    hook_paths = install_hook(repo_root)
    for hook_path in hook_paths:
        print(f"Installed hook at {hook_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-code-marker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    stats_parser = subparsers.add_parser("stats")
    stats_parser.add_argument("--staged", action="store_true")
    stats_parser.add_argument("--json", action="store_true")
    stats_parser.set_defaults(func=cmd_stats)

    record_parser = subparsers.add_parser("record-staged")
    record_parser.add_argument("--tool", required=True)
    record_parser.add_argument("--model")
    record_parser.set_defaults(func=cmd_record_staged)

    prepare_parser = subparsers.add_parser("prepare-commit-msg")
    prepare_parser.add_argument("message_file")
    prepare_parser.add_argument("source", nargs="?")
    prepare_parser.add_argument("commit_sha", nargs="?")
    prepare_parser.set_defaults(func=cmd_prepare_commit_msg)

    post_commit_parser = subparsers.add_parser("post-commit")
    post_commit_parser.set_defaults(func=cmd_post_commit)

    install_parser = subparsers.add_parser("install-hook")
    install_parser.add_argument("--repo-root")
    install_parser.set_defaults(func=cmd_install_hook)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or str(exc))
        return exc.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
