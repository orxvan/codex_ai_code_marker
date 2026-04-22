import os
# AI-GENERATED-BEGIN (by Codex)
import json
# AI-GENERATED-END
import subprocess
# AI-GENERATED-BEGIN (by Codex)
import sys
# AI-GENERATED-END
import tempfile
import textwrap
import unittest
# AI-GENERATED-BEGIN (by Codex)
from datetime import datetime
# AI-GENERATED-END
from unittest.mock import patch
from pathlib import Path

from ai_code_marker import cli as marker_cli


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = [os.environ.get("PYTHON", "python"), "-m", "ai_code_marker.cli"]
AI_NOTES_REF = "refs/notes/ai"


def run(cmd, cwd, check=True, env=None):
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
        env=env,
    )


class AiCodeMarkerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        self.env = os.environ.copy()
        src_path = str(REPO_ROOT / "src")
        existing = self.env.get("PYTHONPATH")
        self.env["PYTHONPATH"] = src_path if not existing else os.pathsep.join([src_path, existing])
        run(["git", "init"], cwd=self.repo)
        run(["git", "config", "user.name", "Test User"], cwd=self.repo)
        run(["git", "config", "user.email", "test@example.com"], cwd=self.repo)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_file(self, relpath, content):
        path = self.repo / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        return path

    def stage_all(self):
        run(["git", "add", "."], cwd=self.repo)

    def cli(self, *args):
        return run(CLI + list(args), cwd=self.repo, env=self.env)

    def git(self, *args, check=True):
        return run(["git", *args], cwd=self.repo, check=check, env=self.env)

    def commit_all(self, message):
        self.stage_all()
        self.git("commit", "-m", message)

    # AI-GENERATED-BEGIN (by Codex)
    def commit_all_at(self, message, when):
        self.stage_all()
        env = self.env.copy()
        timestamp = when.strftime("%Y-%m-%dT%H:%M:%S+08:00")
        env["GIT_AUTHOR_DATE"] = timestamp
        env["GIT_COMMITTER_DATE"] = timestamp
        return run(["git", "commit", "-m", message], cwd=self.repo, env=env)

    # AI-GENERATED-END
    def test_stats_returns_zero_ai_lines_without_recorded_note(self):
        self.write_file(
            "demo.py",
            """
            def human_line():
                return "human"

            def ai_func():
                value = 1
                return value

            def another_human_line():
                return "still-human"
            """,
        )
        self.commit_all("feat: initial import")

        self.write_file(
            "demo.py",
            """
            def human_line():
                return "human"

            def ai_func():
                value = 1
                return value

            def another_human_line():
                return "still-human"

            def followup():
                return "later"
            """,
        )
        self.stage_all()

        result = self.cli("stats", "--staged", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"ai_lines": 0', result.stdout)
        self.assertIn('"total_lines": 2', result.stdout)
        self.assertIn('"ai_ratio": 0.0', result.stdout)
        self.assertNotIn('"tool":', result.stdout)

    def test_record_staged_counts_ai_lines_for_staged_note_ranges(self):
        self.write_file(
            "main.py",
            """
            def keep():
                return "human"
            """,
        )
        self.commit_all("feat: baseline")

        self.write_file(
            "main.py",
            """
            def keep():
                return "human"

            def generated():
                return "ai"
            """,
        )
        self.stage_all()

        result = self.cli("record-staged", "--tool", "Codex", "--model", "gpt-5.4")

        self.assertEqual(result.returncode, 0, result.stderr)

        stats = self.cli("stats", "--staged", "--json")
        self.assertEqual(stats.returncode, 0, stats.stderr)
        self.assertIn('"ai_lines": 2', stats.stdout)
        self.assertIn('"total_lines": 2', stats.stdout)
        self.assertIn('"ai_ratio": 100.0', stats.stdout)
        self.assertIn('"tool": "Codex"', stats.stdout)

    def test_git_helper_forces_utf8_decoding_for_git_output(self):
        completed = subprocess.CompletedProcess(args=["git", "status"], returncode=0, stdout="ok", stderr="")

        with patch("ai_code_marker.cli.subprocess.run", return_value=completed) as run_mock:
            output = marker_cli.git("status")

        self.assertEqual(output, "ok")
        kwargs = run_mock.call_args.kwargs
        self.assertTrue(kwargs["text"])
        self.assertEqual(kwargs["encoding"], "utf-8")
        self.assertEqual(kwargs["errors"], "replace")

    # AI-GENERATED-BEGIN (by Codex)
    def test_prepare_commit_msg_appends_chinese_summary_line(self):
    # AI-GENERATED-END
        self.write_file(
            "main.py",
            """
            def keep():
                return "human"
            """,
        )
        self.commit_all("chore: seed")

        self.write_file(
            "main.py",
            """
            def keep():
                return "human"

            def generated():
                return "ai"

            def another():
                return "ship"
            """,
        )
        self.stage_all()
        self.cli("record-staged", "--tool", "Codex", "--model", "gpt-5.4")

        msg = self.repo / "COMMIT_EDITMSG"
        msg.write_text("feat: add git-ai style support\n", encoding="utf-8")

        result = self.cli("prepare-commit-msg", str(msg))

        self.assertEqual(result.returncode, 0, result.stderr)
        content = msg.read_text(encoding="utf-8")
        # AI-GENERATED-BEGIN (by Codex)
        self.assertTrue(content.startswith("feat: add git-ai style support"))
        self.assertIn("AI生成代码行数：[4]，总提交代码行数：[4]，占比：100.00%，AI主导", content)
        # AI-GENERATED-END

    def test_prepare_commit_msg_replaces_old_metadata_in_place(self):
        self.write_file(
            "src/app.py",
            """
            def calc():
                return 42
            """,
        )
        self.commit_all("feat: seed")

        self.write_file(
            "src/app.py",
            """
            def calc():
                return 42

            def calc2():
                return 84
            """,
        )
        self.stage_all()
        self.cli("record-staged", "--tool", "Tongyi-Lingma", "--model", "qwen")

        msg = self.repo / "COMMIT_EDITMSG"
        msg.write_text(
            textwrap.dedent(
                """
                [AI鍗忓悓](ai:99/total:100/ratio:99.00%) feat: stale

                AI-Code-Lines: 99
                AI-Total-Lines: 100
                AI-Code-Ratio: 99.00%
                AI-Tools: OldTool
                AI-Files: old.py
                """
            ).lstrip(),
            encoding="utf-8",
        )

        result = self.cli("prepare-commit-msg", str(msg))

        self.assertEqual(result.returncode, 0, result.stderr)
        content = msg.read_text(encoding="utf-8")
        # AI-GENERATED-BEGIN (by Codex)
        self.assertTrue(content.startswith("feat: stale"))
        self.assertEqual(content.count("AI生成代码行数："), 1)
        self.assertIn("AI生成代码行数：[2]，总提交代码行数：[2]，占比：100.00%，AI主导", content)
        self.assertNotIn("AI-Code-Lines:", content)
        self.assertNotIn("AI-Tools:", content)
        # AI-GENERATED-END

    def test_post_commit_attaches_note_to_head(self):
        self.write_file(
            "src/app.py",
            """
            def hello():
                return "world"
            """,
        )
        self.stage_all()
        self.cli("record-staged", "--tool", "Tongyi-Lingma", "--model", "qwen")
        self.git("commit", "-m", "feat: add app")
        self.cli("post-commit")

        note = self.git("notes", "--ref", AI_NOTES_REF, "show", "HEAD")

        self.assertIn('"tool": "Tongyi-Lingma"', note.stdout)
        self.assertIn('"path": "src/app.py"', note.stdout)
        self.assertIn('"added_lines": [', note.stdout)
        self.assertIn("1", note.stdout)
        self.assertIn("2", note.stdout)

    # AI-GENERATED-BEGIN (by Codex)
    def test_pre_commit_auto_marks_staged_ai_blocks_and_updates_stats(self):
        self.write_file(
            "main.py",
            """
            def keep():
                return "human"
            """,
        )
        self.commit_all("feat: baseline")

        self.write_file(
            "main.py",
            """
            def keep():
                return "human"

            def generated():
                value = "ai"
                return value
            """,
        )
        self.stage_all()

        result = self.cli("pre-commit")

        self.assertEqual(result.returncode, 0, result.stderr)
        content = (self.repo / "main.py").read_text(encoding="utf-8")
        self.assertIn("# AI-GENERATED-BEGIN (by Codex)", content)
        self.assertIn("# AI-GENERATED-END", content)

        staged = self.git("show", ":main.py")
        self.assertIn("# AI-GENERATED-BEGIN (by Codex)", staged.stdout)
        self.assertIn("# AI-GENERATED-END", staged.stdout)

        stats = self.cli("stats", "--staged", "--json")
        self.assertEqual(stats.returncode, 0, stats.stderr)
        self.assertIn('"ai_lines": 3', stats.stdout)
        self.assertIn('"total_lines": 5', stats.stdout)
        self.assertIn('"ai_ratio": 60.0', stats.stdout)
        self.assertIn('"tool": "Codex"', stats.stdout)

    def test_install_hook_writes_pre_prepare_and_post_commit_hooks(self):
    # AI-GENERATED-END
        hook_dir = self.repo / ".git" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)

        result = self.cli("install-hook")

        self.assertEqual(result.returncode, 0, result.stderr)
        # AI-GENERATED-BEGIN (by Codex)
        pre_hook = hook_dir / "pre-commit"
        # AI-GENERATED-END
        prepare_hook = hook_dir / "prepare-commit-msg"
        post_hook = hook_dir / "post-commit"
        # AI-GENERATED-BEGIN (by Codex)
        self.assertTrue(pre_hook.exists())
        # AI-GENERATED-END
        self.assertTrue(prepare_hook.exists())
        self.assertTrue(post_hook.exists())
        # AI-GENERATED-BEGIN (by Codex)
        pre_content = pre_hook.read_text(encoding="utf-8")
        # AI-GENERATED-END
        prepare_content = prepare_hook.read_text(encoding="utf-8")
        post_content = post_hook.read_text(encoding="utf-8")
        # AI-GENERATED-BEGIN (by Codex)
        self.assertIn("#!/bin/sh", pre_content)
        # AI-GENERATED-END
        self.assertIn("#!/bin/sh", prepare_content)
        self.assertNotIn("PYTHONPATH=", prepare_content)
        # AI-GENERATED-BEGIN (by Codex)
        self.assertNotIn("REPO_ROOT=", prepare_content)
        self.assertIn(f'INSTALLED_PYTHON="{Path(sys.executable).resolve().as_posix()}"', prepare_content)
        self.assertIn('PYTHON_BIN="${PYTHON_BIN:-$INSTALLED_PYTHON}"', prepare_content)
        self.assertIn('exec "$PYTHON_BIN" -m ai_code_marker.cli pre-commit "$@"', pre_content)
        self.assertIn('exec "$PYTHON_BIN" -m ai_code_marker.cli prepare-commit-msg "$@"', prepare_content)
        self.assertIn('exec "$PYTHON_BIN" -m ai_code_marker.cli post-commit "$@"', post_content)

    def test_range_report_returns_summary_and_commit_details_for_time_window(self):
        self.write_file(
            "main.py",
            """
            def baseline():
                return "human"
            """,
        )
        self.commit_all_at("feat: baseline", datetime(2026, 4, 20, 9, 0, 0))

        self.write_file(
            "main.py",
            """
            def baseline():
                return "human"

            def generated():
                value = "ai"
                return value
            """,
        )
        self.stage_all()
        self.cli("pre-commit")
        self.commit_all_at("feat: codex block", datetime(2026, 4, 21, 10, 0, 0))
        self.cli("post-commit")

        self.write_file(
            "notes.txt",
            """
            human only
            """,
        )
        self.commit_all_at("docs: human note", datetime(2026, 4, 22, 11, 0, 0))

        result = self.cli(
            "range-report",
            "--since",
            "2026-04-21T00:00:00+08:00",
            "--until",
            "2026-04-22T23:59:59+08:00",
            "--json",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["commit_count"], 2)
        self.assertEqual(payload["summary"]["ai_commit_count"], 1)
        self.assertEqual(payload["summary"]["ai_lines"], 3)
        self.assertEqual(payload["summary"]["total_lines"], 6)
        self.assertEqual(payload["summary"]["ai_ratio"], 50.0)
        self.assertEqual(payload["summary"]["tools"], {"Codex": 1})
        self.assertEqual(len(payload["commits"]), 2)
        self.assertEqual(payload["commits"][0]["subject"], "docs: human note")
        self.assertEqual(payload["commits"][0]["ai_lines"], 0)
        self.assertEqual(payload["commits"][1]["subject"], "feat: codex block")
        self.assertEqual(payload["commits"][1]["ai_lines"], 3)
        self.assertEqual(payload["commits"][1]["total_lines"], 5)
        self.assertEqual(payload["commits"][1]["ai_ratio"], 60.0)
        self.assertEqual(payload["commits"][1]["tools"], ["Codex"])

    def test_range_report_ignores_non_json_git_note(self):
        self.write_file(
            "main.py",
            """
            def baseline():
                return "human"
            """,
        )
        self.commit_all_at("feat: baseline", datetime(2026, 4, 22, 9, 0, 0))

        head = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("notes", "--ref", AI_NOTES_REF, "add", "-f", "-m", "legacy-note", head)

        result = self.cli(
            "range-report",
            "--since",
            "2026-04-22T00:00:00+08:00",
            "--until",
            "2026-04-22T23:59:59+08:00",
            "--json",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["commit_count"], 1)
        self.assertEqual(payload["summary"]["ai_commit_count"], 0)
        self.assertEqual(payload["summary"]["ai_lines"], 0)
        self.assertEqual(payload["commits"][0]["ai_lines"], 0)

    def test_range_report_uses_begin_end_markers_when_git_note_missing(self):
        self.write_file(
            "main.py",
            """
            def baseline():
                return "human"
            """,
        )
        self.commit_all_at("feat: baseline", datetime(2026, 4, 21, 9, 0, 0))

        self.write_file(
            "main.py",
            """
            def baseline():
                return "human"

            def generated():
                value = "ai"
                return value
            """,
        )
        self.stage_all()
        self.cli("pre-commit")
        self.commit_all_at("feat: codex block without note", datetime(2026, 4, 22, 10, 0, 0))

        result = self.cli(
            "range-report",
            "--since",
            "2026-04-22T00:00:00+08:00",
            "--until",
            "2026-04-22T23:59:59+08:00",
            "--json",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["commit_count"], 1)
        self.assertEqual(payload["summary"]["ai_commit_count"], 1)
        self.assertEqual(payload["summary"]["ai_lines"], 3)
        self.assertEqual(payload["summary"]["total_lines"], 5)
        self.assertEqual(payload["summary"]["ai_ratio"], 60.0)
        self.assertEqual(payload["summary"]["tools"], {"Codex": 1})
        self.assertEqual(payload["commits"][0]["ai_lines"], 3)
        self.assertEqual(payload["commits"][0]["tools"], ["Codex"])
        # AI-GENERATED-END


if __name__ == "__main__":
    unittest.main()
