import argparse
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass
# AI-GENERATED-BEGIN (by Codex)
from datetime import date, datetime, time
# AI-GENERATED-END
from pathlib import Path
from typing import Iterable


AI_PREFIX_LABEL = "[AI\u534f\u540c]"
AI_NOTES_REF = "refs/notes/ai"
PENDING_ATTRIBUTION_FILE = Path(".git") / "ai-code-marker" / "staged-attribution.json"
# AI-GENERATED-BEGIN (by Codex)
DEFAULT_TOOL = "Codex"
DEFAULT_TOOL_ENV = "AI_CODE_MARKER_TOOL"
DEFAULT_MODEL_ENV = "AI_CODE_MARKER_MODEL"
# AI-GENERATED-END
TRAILER_KEYS = [
    "AI-Code-Lines",
    "AI-Total-Lines",
    "AI-Code-Ratio",
    "AI-Tools",
    "AI-Files",
]
PREFIX_RE = re.compile(r"^\[[^\]]+\]\(ai:\d+/total:\d+/ratio:\d+(?:\.\d+)?%\)\s+")
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
# AI-GENERATED-BEGIN (by Codex)
BEGIN_MARKER_RE = re.compile(r"^\s*(?:#|//|--|<!--)\s*AI-GENERATED-BEGIN(?:\s+\(by\s+(.+?)\))?\s*(?:-->|)$")
END_MARKER_RE = re.compile(r"^\s*(?:#|//|--|<!--)\s*AI-GENERATED-END\s*(?:-->|)$")
# AI-GENERATED-END


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


# AI-GENERATED-BEGIN (by Codex)
def git_in_repo(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )


# AI-GENERATED-END
def get_git_dir() -> Path:
    return Path(git("rev-parse", "--git-dir").strip())


def get_pending_attr_path() -> Path:
    return get_git_dir() / "ai-code-marker" / "staged-attribution.json"


def parse_staged_diff() -> list[dict]:
    diff = git("diff", "--cached", "--unified=0", "--no-color", "--no-ext-diff")
    # AI-GENERATED-BEGIN (by Codex)
    return parse_diff_output(diff)


def parse_diff_output(diff: str) -> list[dict]:
    # AI-GENERATED-END
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
    # AI-GENERATED-BEGIN (by Codex)
    changes = parse_staged_diff()
    pending = load_pending_attribution()
    if not pending:
        pending = build_pending_payload_from_markers(changes)
    return build_stats(changes, pending)
    # AI-GENERATED-END


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


# AI-GENERATED-BEGIN (by Codex)
def render_hook(command: str, python_executable: str | None = None) -> str:
    installed_python = Path(python_executable or sys.executable).resolve().as_posix()
# AI-GENERATED-END
    return (
        "#!/bin/sh\n"
        "set -eu\n\n"
        # AI-GENERATED-BEGIN (by Codex)
        f'INSTALLED_PYTHON="{installed_python}"\n'
        'PYTHON_BIN="${PYTHON_BIN:-$INSTALLED_PYTHON}"\n'
        f'exec "$PYTHON_BIN" -m ai_code_marker.cli {command} "$@"\n'
        # AI-GENERATED-END
    )


def install_hook(repo_root: Path) -> list[Path]:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        raise FileNotFoundError(f"Current directory is not a Git repository: {repo_root}")

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # AI-GENERATED-BEGIN (by Codex)
    pre_hook = hooks_dir / "pre-commit"
    pre_hook.write_text(render_hook("pre-commit"), encoding="utf-8", newline="\n")

    # AI-GENERATED-END
    prepare_hook = hooks_dir / "prepare-commit-msg"
    # AI-GENERATED-BEGIN (by Codex)
    prepare_hook.write_text(render_hook("prepare-commit-msg"), encoding="utf-8", newline="\n")
    # AI-GENERATED-END

    post_hook = hooks_dir / "post-commit"
    # AI-GENERATED-BEGIN (by Codex)
    post_hook.write_text(render_hook("post-commit"), encoding="utf-8", newline="\n")
    # AI-GENERATED-END

    if os.name != "nt":
        # AI-GENERATED-BEGIN (by Codex)
        pre_hook.chmod(0o755)
        # AI-GENERATED-END
        prepare_hook.chmod(0o755)
        post_hook.chmod(0o755)

    # AI-GENERATED-BEGIN (by Codex)
    return [pre_hook, prepare_hook, post_hook]


def default_tool() -> str:
    return os.environ.get(DEFAULT_TOOL_ENV, DEFAULT_TOOL)


def default_model() -> str | None:
    return os.environ.get(DEFAULT_MODEL_ENV)


def marker_tokens(path: str) -> tuple[str, str] | None:
    suffix = Path(path).suffix.lower()
    if suffix in {".py", ".sh", ".rb", ".pl", ".ps1", ".yml", ".yaml", ".toml", ".ini", ".cfg"}:
        return "#", ""
    if suffix in {".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".cs", ".kt", ".kts", ".swift", ".rs", ".php", ".scala", ".dart"}:
        return "//", ""
    if suffix in {".sql", ".lua"}:
        return "--", ""
    if suffix in {".html", ".htm", ".xml", ".svg", ".vue"}:
        return "<!--", " -->"
    return None


def begin_marker_line(path: str, tool: str) -> str | None:
    tokens = marker_tokens(path)
    if not tokens:
        return None
    prefix, suffix = tokens
    return f"{prefix} AI-GENERATED-BEGIN (by {tool}){suffix}"


def end_marker_line(path: str) -> str | None:
    tokens = marker_tokens(path)
    if not tokens:
        return None
    prefix, suffix = tokens
    return f"{prefix} AI-GENERATED-END{suffix}"


def build_blocks_from_changes(changes: list[dict]) -> dict[str, list[tuple[int, int]]]:
    blocks: dict[str, list[tuple[int, int]]] = {}
    by_file: dict[str, list[int]] = {}
    for change in changes:
        by_file.setdefault(change["file"], [])
        by_file[change["file"]].append(change["line_number"])

    for path, line_numbers in by_file.items():
        sorted_lines = sorted(set(line_numbers))
        if not sorted_lines:
            continue
        start = sorted_lines[0]
        end = sorted_lines[0]
        file_blocks: list[tuple[int, int]] = []
        for line_number in sorted_lines[1:]:
            if line_number == end + 1:
                end = line_number
                continue
            file_blocks.append((start, end))
            start = end = line_number
        file_blocks.append((start, end))
        blocks[path] = file_blocks

    return blocks


def insert_markers(repo_root: Path, path: str, blocks: list[tuple[int, int]], tool: str) -> bool:
    begin_marker = begin_marker_line(path, tool)
    end_marker = end_marker_line(path)
    if not begin_marker or not end_marker:
        return False

    full_path = repo_root / path
    original = full_path.read_text(encoding="utf-8")
    trailing_newline = original.endswith("\n")
    lines = original.splitlines()
    changed = False

    for start, end in sorted(blocks, reverse=True):
        start_index = start - 1
        end_index = end - 1
        if start_index < 0 or end_index >= len(lines):
            continue
        if (
            start_index > 0
            and end_index + 1 < len(lines)
            and lines[start_index - 1].strip() == begin_marker
            and lines[end_index + 1].strip() == end_marker
        ):
            continue
        indent_source = lines[start_index]
        indent = indent_source[: len(indent_source) - len(indent_source.lstrip())]
        lines.insert(end_index + 1, f"{indent}{end_marker}")
        lines.insert(start_index, f"{indent}{begin_marker}")
        changed = True

    if not changed:
        return False

    updated = "\n".join(lines)
    if trailing_newline:
        updated += "\n"
    full_path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def build_pending_payload_from_markers(changes: list[dict], model: str | None = None) -> dict | None:
    files = OrderedDict()
    tool: str | None = None
    in_ai = False
    current_file: str | None = None

    for change in changes:
        if change["file"] != current_file:
            current_file = change["file"]
            in_ai = False

        begin_match = BEGIN_MARKER_RE.match(change["content"])
        if begin_match:
            in_ai = True
            tool = tool or begin_match.group(1) or default_tool()
            continue

        if END_MARKER_RE.match(change["content"]):
            in_ai = False
            continue

        if in_ai and not change["is_blank"]:
            files.setdefault(change["file"], [])
            files[change["file"]].append(change["line_number"])

    if not files:
        return None

    return {
        "version": 1,
        "tool": tool or default_tool(),
        "model": model,
        "files": [{"path": path, "added_lines": lines} for path, lines in files.items()],
    }


def stage_paths(paths: Iterable[str]) -> None:
    normalized = list(OrderedDict.fromkeys(paths))
    if normalized:
        git("add", "--", *normalized)


def cmd_pre_commit(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    staged_changes = parse_staged_diff()
    if not staged_changes:
        return 0

    pending = load_pending_attribution()
    tool = pending.get("tool") if pending else default_tool()
    model = pending.get("model") if pending else default_model()

    if pending:
        selected_line_numbers = attribution_line_set(pending)
        selected_changes = [
            change
            for change in staged_changes
            if change["line_number"] in selected_line_numbers.get(change["file"], set())
        ]
    else:
        selected_changes = staged_changes

    touched_paths = []
    for path, blocks in build_blocks_from_changes(selected_changes).items():
        if insert_markers(repo_root, path, blocks, tool):
            touched_paths.append(path)

    if touched_paths:
        stage_paths(touched_paths)

    final_changes = parse_staged_diff()
    final_payload = build_pending_payload_from_markers(final_changes, model=model)
    if final_payload:
        save_pending_attribution(final_payload)
    elif pending:
        save_pending_attribution(pending)
    else:
        save_pending_attribution(build_pending_payload(tool, model, final_changes))
    return 0
    # AI-GENERATED-END


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


# AI-GENERATED-BEGIN (by Codex)
def local_timezone():
    return datetime.now().astimezone().tzinfo


def parse_datetime_arg(value: str, *, is_end: bool) -> datetime:
    normalized = value.replace("Z", "+00:00")
    if "T" not in normalized and " " not in normalized:
        parsed_date = date.fromisoformat(normalized)
        parsed_time = time.max if is_end else time.min
        return datetime.combine(parsed_date, parsed_time, tzinfo=local_timezone())

    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=local_timezone())
    return parsed


def default_since_now_range() -> tuple[datetime, datetime]:
    now = datetime.now().astimezone()
    monday = now.date().toordinal() - now.weekday()
    monday_date = date.fromordinal(monday)
    since = datetime.combine(monday_date, time.min, tzinfo=now.tzinfo)
    return since, now


def get_commit_note_payload(repo_root: Path, commit_sha: str) -> dict | None:
    result = git_in_repo(repo_root, "notes", "--ref", AI_NOTES_REF, "show", commit_sha, check=False)
    if result.returncode != 0:
        return None
    note_text = result.stdout.strip()
    if not note_text:
        return None
    try:
        payload = json.loads(note_text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def parse_commit_total_lines(repo_root: Path, commit_sha: str) -> tuple[int, list[str]]:
    diff = git_in_repo(
        repo_root,
        "show",
        "--format=",
        "--unified=0",
        "--no-color",
        "--no-ext-diff",
        commit_sha,
    ).stdout
    changes = parse_diff_output(diff)
    total_lines = sum(0 if change["is_blank"] else 1 for change in changes)
    files = list(OrderedDict((change["file"], True) for change in changes).keys())
    return total_lines, files


def parse_commit_marker_payload(repo_root: Path, commit_sha: str) -> dict | None:
    diff = git_in_repo(
        repo_root,
        "show",
        "--format=",
        "--unified=0",
        "--no-color",
        "--no-ext-diff",
        commit_sha,
    ).stdout
    return build_pending_payload_from_markers(parse_diff_output(diff))


def build_commit_report(repo_root: Path, commit_sha: str, committed_at: str, author: str, subject: str) -> dict:
    note_payload = get_commit_note_payload(repo_root, commit_sha)
    marker_payload = parse_commit_marker_payload(repo_root, commit_sha) if not note_payload else None
    payload = note_payload or marker_payload
    ai_lines = 0
    tools: list[str] = []
    ai_files: list[str] = []
    if payload:
        ai_lines = sum(len(file_entry.get("added_lines", [])) for file_entry in payload.get("files", []))
        tool = payload.get("tool")
        if tool:
            tools.append(tool)
        ai_files = [file_entry["path"] for file_entry in payload.get("files", [])]

    total_lines, files = parse_commit_total_lines(repo_root, commit_sha)
    ai_ratio = 0.0 if total_lines == 0 else round((ai_lines / total_lines) * 100, 2)

    return {
        "commit": commit_sha,
        "committed_at": committed_at,
        "author": author,
        "subject": subject,
        "ai_lines": ai_lines,
        "total_lines": total_lines,
        "ai_ratio": ai_ratio,
        "tools": tools,
        "files": files,
        "ai_files": ai_files,
    }


def cmd_range_report(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path.cwd()
    default_since, default_until = default_since_now_range()
    since = parse_datetime_arg(args.since, is_end=False) if args.since else default_since
    until = parse_datetime_arg(args.until, is_end=True) if args.until else default_until

    log_output = git_in_repo(
        repo_root,
        "log",
        "--since",
        since.isoformat(),
        "--until",
        until.isoformat(),
        "--format=%H%x1f%cI%x1f%an%x1f%s",
    ).stdout

    commits = []
    tool_counts: dict[str, int] = OrderedDict()
    ai_commit_count = 0
    ai_lines = 0
    total_lines = 0

    for line in log_output.splitlines():
        if not line.strip():
            continue
        commit_sha, committed_at, author, subject = line.split("\x1f", 3)
        report = build_commit_report(repo_root, commit_sha, committed_at, author, subject)
        commits.append(report)
        ai_lines += report["ai_lines"]
        total_lines += report["total_lines"]
        if report["ai_lines"] > 0:
            ai_commit_count += 1
        for tool in report["tools"]:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

    payload = {
        "repo_root": str(repo_root),
        "since": since.isoformat(),
        "until": until.isoformat(),
        "summary": {
            "commit_count": len(commits),
            "ai_commit_count": ai_commit_count,
            "ai_lines": ai_lines,
            "total_lines": total_lines,
            "ai_ratio": 0.0 if total_lines == 0 else round((ai_lines / total_lines) * 100, 2),
            "tools": tool_counts,
        },
        "commits": commits,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Repo: {payload['repo_root']}")
        print(f"Since: {payload['since']}")
        print(f"Until: {payload['until']}")
        print(f"Commits: {payload['summary']['commit_count']}")
        print(f"AI commits: {payload['summary']['ai_commit_count']}")
        print(f"AI lines: {payload['summary']['ai_lines']}")
        print(f"Total lines: {payload['summary']['total_lines']}")
        print(f"AI ratio: {payload['summary']['ai_ratio']:.2f}%")
        print(f"Tools: {', '.join(f'{tool}={count}' for tool, count in tool_counts.items()) if tool_counts else 'none'}")
        for commit in commits:
            print(
                f"{commit['committed_at']} {commit['commit'][:7]} "
                f"ai:{commit['ai_lines']}/total:{commit['total_lines']}/ratio:{commit['ai_ratio']:.2f}% "
                f"{commit['subject']}"
            )
    return 0


# AI-GENERATED-END
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

    # AI-GENERATED-BEGIN (by Codex)
    pre_commit_parser = subparsers.add_parser("pre-commit")
    pre_commit_parser.set_defaults(func=cmd_pre_commit)

    # AI-GENERATED-END
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

    # AI-GENERATED-BEGIN (by Codex)
    range_report_parser = subparsers.add_parser("range-report")
    range_report_parser.add_argument("--since")
    range_report_parser.add_argument("--until")
    range_report_parser.add_argument("--repo-root")
    range_report_parser.add_argument("--json", action="store_true")
    range_report_parser.set_defaults(func=cmd_range_report)

    # AI-GENERATED-END
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
