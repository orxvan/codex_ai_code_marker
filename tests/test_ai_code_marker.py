import os
import subprocess
import tempfile
import textwrap
import unittest
from unittest.mock import patch
from pathlib import Path

from ai_code_marker import cli as marker_cli


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = [os.environ.get("PYTHON", "python"), "-m", "ai_code_marker.cli"]
AI_PREFIX_LABEL = "[AI\u534f\u540c]"
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

    def test_prepare_commit_msg_adds_prefix_and_trailers(self):
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
        self.assertTrue(content.startswith(f"{AI_PREFIX_LABEL}(ai:4/total:4/ratio:100.00%) feat: add git-ai style support"))
        self.assertIn("AI-Code-Lines: 4", content)
        self.assertIn("AI-Total-Lines: 4", content)
        self.assertIn("AI-Code-Ratio: 100.00%", content)
        self.assertIn("AI-Tools: Codex", content)
        self.assertIn("AI-Files: main.py", content)

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
        self.assertIn(f"{AI_PREFIX_LABEL}(ai:2/total:2/ratio:100.00%) feat: stale", content)
        self.assertEqual(content.count("AI-Code-Lines:"), 1)
        self.assertIn("AI-Code-Lines: 2", content)
        self.assertIn("AI-Tools: Tongyi-Lingma", content)
        self.assertIn("AI-Files: src/app.py", content)

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

    def test_install_hook_writes_prepare_and_post_commit_hooks(self):
        hook_dir = self.repo / ".git" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)

        result = self.cli("install-hook")

        self.assertEqual(result.returncode, 0, result.stderr)
        prepare_hook = hook_dir / "prepare-commit-msg"
        post_hook = hook_dir / "post-commit"
        self.assertTrue(prepare_hook.exists())
        self.assertTrue(post_hook.exists())
        prepare_content = prepare_hook.read_text(encoding="utf-8")
        post_content = post_hook.read_text(encoding="utf-8")
        self.assertIn("#!/bin/sh", prepare_content)
        self.assertNotIn("PYTHONPATH=", prepare_content)
        self.assertIn('exec "$PYTHON_BIN" "$REPO_ROOT/src/ai_code_marker/cli.py" prepare-commit-msg "$@"', prepare_content)
        self.assertIn('exec "$PYTHON_BIN" "$REPO_ROOT/src/ai_code_marker/cli.py" post-commit "$@"', post_content)


if __name__ == "__main__":
    unittest.main()
