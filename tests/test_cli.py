import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mdterm import cli
from mdterm.fences import TOKEN

EXAMPLE = Path(__file__).resolve().parent.parent / "example.md"


class BrokenStdout(io.StringIO):
    def write(self, _text):
        raise BrokenPipeError


class PreviewTests(unittest.TestCase):
    def test_broken_pipe_keeps_stderr_silent(self):
        # piper replaces the preview with stderr whenever anything lands there.
        err = io.StringIO()
        with mock.patch("mdterm.cli.dump", return_value="rendered"), \
                contextlib.redirect_stdout(BrokenStdout()), contextlib.redirect_stderr(err):
            self.assertEqual(cli.cmd_preview(EXAMPLE, 48), 0)
        self.assertEqual(err.getvalue(), "")


@unittest.skipUnless(shutil.which("glow"), "glow not on PATH")
class RenderPageTests(unittest.TestCase):
    def test_round_trip_through_glow(self):
        out = cli.render_page(EXAMPLE, 60)
        self.assertNotIn(TOKEN, out)
        self.assertIn("Frontend / API Callers", out)  # wide fence back, unwrapped
        self.assertIn("echo hi", out)
        if shutil.which("mmd2txt"):
            self.assertNotIn("-->", out)  # mermaid became box art
            self.assertIn("Render", out)


class FakeLess:
    def __init__(self, *_args, **_kwargs):
        self.terminated = False
        self.interrupted = False

    def wait(self, timeout=None):
        if not self.interrupted:  # the first wait is where Ctrl-C lands
            self.interrupted = True
            raise KeyboardInterrupt
        return 0

    def terminate(self):
        self.terminated = True


class PagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.old_tempdir = tempfile.tempdir
        tempfile.tempdir = self.tmp
        self.out = io.StringIO()

    def tearDown(self):
        tempfile.tempdir = self.old_tempdir
        shutil.rmtree(self.tmp)

    def test_temp_file_removed_when_less_is_missing(self):
        with mock.patch("mdterm.cli.render_page", return_value="page"), \
                mock.patch("mdterm.cli._less_has_mouse", return_value=False), \
                mock.patch("subprocess.Popen", side_effect=FileNotFoundError("less")), \
                contextlib.redirect_stdout(self.out):
            with self.assertRaises(FileNotFoundError):
                cli.cmd_pager(EXAMPLE)
        self.assertEqual(os.listdir(self.tmp), [])
        self.assertTrue(self.out.getvalue().endswith(cli.ALT_OFF))

    def test_ctrl_c_kills_less_and_restores_screen(self):
        fake = FakeLess()
        with mock.patch("mdterm.cli.render_page", return_value="page"), \
                mock.patch("mdterm.cli._less_has_mouse", return_value=False), \
                mock.patch("subprocess.Popen", return_value=fake), \
                contextlib.redirect_stdout(self.out):
            with self.assertRaises(KeyboardInterrupt):
                cli.cmd_pager(EXAMPLE)
        self.assertTrue(fake.terminated)
        self.assertEqual(os.listdir(self.tmp), [])
        self.assertTrue(self.out.getvalue().endswith(cli.ALT_OFF))

    def test_main_returns_130_on_ctrl_c(self):
        with mock.patch("mdterm.cli.cmd_pager", side_effect=KeyboardInterrupt):
            self.assertEqual(cli.main(["pager", str(EXAMPLE)]), 130)


if __name__ == "__main__":
    unittest.main()
