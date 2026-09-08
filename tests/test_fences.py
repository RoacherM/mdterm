import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mdterm.fences import (
    TOKEN,
    collapse_for_pane,
    display_width,
    prepare_for_pager,
    render_mermaid,
    scan,
    splice,
)

WIDE_BOX = "┌" + "─" * 70 + "┐\n│ hello" + " " * 60 + "│\n└" + "─" * 70 + "┘\n"
CJK_BOX = "┌" + "─" * 28 + "┐\n│" + "中" * 28 + "│\n└" + "─" * 28 + "┘\n"


class ScanTests(unittest.TestCase):
    def test_backtick_tilde_and_indented(self):
        src = "```py\na\n```\n~~~\nb\n~~~\n- item\n\n  ```\n  c\n  ```\n"
        fences = scan(src.splitlines())
        self.assertEqual([f.lang for f in fences], ["py", "", ""])
        self.assertEqual([f.body for f in fences], [["a"], ["b"], ["c"]])
        self.assertEqual(fences[2].indent, "  ")

    def test_longer_fence_swallows_inner_fence(self):
        src = "````md\n```mermaid\nA-->B\n```\n````\n"
        fences = scan(src.splitlines())
        self.assertEqual(len(fences), 1)
        self.assertEqual(fences[0].body, ["```mermaid", "A-->B", "```"])

    def test_unclosed_fence_runs_to_end(self):
        fences = scan("```\nx\ny".splitlines())
        self.assertEqual(fences[0].body, ["x", "y"])


class WidthTests(unittest.TestCase):
    def test_cjk_is_two_cells(self):
        self.assertEqual(display_width("中a"), 3)


class CollapseTests(unittest.TestCase):
    def test_mermaid_becomes_placeholder(self):
        out = collapse_for_pane("# T\n\n```mermaid\nflowchart LR\n  A-->B\n```\n\nend\n", 40)
        self.assertIn("流程图", out)
        self.assertNotIn("flowchart", out)

    def test_wide_ascii_becomes_placeholder(self):
        out = collapse_for_pane(f"```\n{WIDE_BOX}```\n", 40)
        self.assertIn("示意图", out)
        self.assertNotIn("hello", out)

    def test_cjk_box_measured_in_cells(self):
        out = collapse_for_pane(f"```\n{CJK_BOX}```\n", 40)
        self.assertIn("示意图", out)

    def test_indented_fence_in_list(self):
        src = "- item\n\n  ```\n" + CJK_BOX.replace("\n", "\n  ") + "```\n"
        out = collapse_for_pane(src, 40)
        self.assertIn("  > 〔示意图", out)

    def test_table_in_fence_is_not_art(self):
        table = "| " + "a" * 30 + " | " + "b" * 30 + " |\n| --- | --- |\n| x | y |\n"
        out = collapse_for_pane(f"```\n{table}```\n", 40)
        self.assertNotIn("示意图", out)
        self.assertIn("aaaa", out)

    def test_narrow_code_kept(self):
        out = collapse_for_pane("# T\n\n```\necho hi\n```\n", 80)
        self.assertIn("echo hi", out)


class PagerTests(unittest.TestCase):
    def test_wide_block_leaves_glow_and_comes_back(self):
        src = f"a\n\n```\n{WIDE_BOX}```\n\n```text\n<repo>/x\n```\n"
        markdown, blocks = prepare_for_pager(src, 60, None)
        self.assertNotIn("hello", markdown)
        self.assertIn(f"{TOKEN}0", markdown)
        self.assertIn("```text\n<repo>/x\n```", markdown)  # narrow: glow keeps it
        self.assertEqual(len(blocks), 1)
        rendered = f" a\n\n \x1b[38;5;252m{TOKEN}0\x1b[m   \n"
        out = splice(rendered, blocks)
        self.assertIn(" │ hello", out)
        self.assertNotIn(TOKEN, out)

    def test_splice_keeps_unknown_index(self):
        self.assertEqual(splice(f"{TOKEN}7\n", []), f"{TOKEN}7\n")

    def test_splice_token_glued_to_list_item(self):
        out = splice(f"   • item {TOKEN}0\n", [["┌┐", "└┘"]])
        self.assertEqual(out, "   • item\n   ┌┐\n   └┘\n")

    @unittest.skipUnless(shutil.which("mmd2txt"), "mmd2txt not on PATH")
    def test_mermaid_batch_keeps_order_and_unsupported(self):
        arts = render_mermaid(
            [["flowchart LR", "A-->B"], ["pie", '"a": 1'], ["flowchart LR", "C-->D"]],
            80,
            shutil.which("mmd2txt"),
        )
        self.assertEqual(len(arts), 3)
        self.assertTrue(any("A" in ln for ln in arts[0]))
        self.assertTrue(any("pie" in ln for ln in arts[1]))
        self.assertTrue(any("D" in ln for ln in arts[2]))
        self.assertFalse(any(ln.startswith("```") for art in arts for ln in art))


if __name__ == "__main__":
    unittest.main()
