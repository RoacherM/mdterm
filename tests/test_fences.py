import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mdterm.fences import collapse_for_pane, unwrap_text_fences


class CollapseTests(unittest.TestCase):
    def test_mermaid_becomes_placeholder(self):
        src = "# T\n\n```mermaid\nflowchart LR\n  A-->B\n```\n\nend\n"
        out = collapse_for_pane(src, 40)
        self.assertIn("流程图", out)
        self.assertNotIn("flowchart", out)

    def test_wide_ascii_becomes_placeholder(self):
        box = "┌" + "─" * 70 + "┐\n│ hello" + " " * 60 + "│\n└" + "─" * 70 + "┘\n"
        src = f"# T\n\n```\n{box}```\n"
        out = collapse_for_pane(src, 40)
        self.assertIn("示意图", out)
        self.assertNotIn("hello", out)

    def test_narrow_code_kept(self):
        src = "# T\n\n```\necho hi\n```\n"
        out = collapse_for_pane(src, 80)
        self.assertIn("echo hi", out)

    def test_unwrap_text_fence(self):
        src = "pre\n```text\n┌─┐\n```\npost\n"
        out = unwrap_text_fences(src)
        self.assertIn("┌─┐", out)
        self.assertNotIn("```text", out)


if __name__ == "__main__":
    unittest.main()
