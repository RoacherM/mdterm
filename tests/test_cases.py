"""Documents shaped like ones that once rendered wrong. One file per shape in tests/cases."""

import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mdterm.cli import render_page
from mdterm.fences import ANSI, ART_PLACE, MERMAID_PLACE, TOKEN, collapse_for_pane

CASES = Path(__file__).resolve().parent / "cases"
PANE_WIDTH = 40
PAGER_COLS = 60
MERMAID = bool(shutil.which("mmd2txt"))

TREE_LINE = "│   │   └── presets.ts              # preset state, selection and the creator session"
BOX_LINE = "│                    Frontend / API Callers                     │"
CJK_LINE = "│中文中文中文中文中文中文中文中文中文中文│"
ASCII_LINE = "+----+----------------------------------------------+-----------+"

# name: (pane keeps, pane drops, pager keeps, pager drops)
EXPECT = {
    "table-in-fence": (["npm latest"], [ART_PLACE], ["npm latest"], []),
    "pipeline-in-fence": (["grep -rn"], [ART_PLACE], ["grep -rn"], []),
    "unicode-tree": ([ART_PLACE], ["presets.ts"], [TREE_LINE], []),
    "wide-box": ([ART_PLACE], ["Frontend"], [BOX_LINE], []),
    "ascii-box": ([ART_PLACE], ["preset state"], [ASCII_LINE], []),
    "mermaid": (
        [MERMAID_PLACE],
        ["flowchart"],
        ["Render"] if MERMAID else ["flowchart LR"],
        ["-->"] if MERMAID else [],
    ),
    "nested-fence": (["flowchart LR"], [MERMAID_PLACE, ART_PLACE], ["flowchart LR"], []),
    "list-fence-cjk": (["  " + ART_PLACE], ["中文中文"], [CJK_LINE], []),
    "token-lookalike": (["MDTERMBLOCK0"], [], ["MDTERMBLOCK0", "MDTERMBLK00000000_1"], []),
}


class CaseTests(unittest.TestCase):
    def test_every_case_file_has_expectations(self):
        self.assertEqual(sorted(p.stem for p in CASES.glob("*.md")), sorted(EXPECT))

    def test_pane(self):
        for name, (keeps, drops, _, _) in EXPECT.items():
            with self.subTest(name):
                out = collapse_for_pane((CASES / f"{name}.md").read_text(), PANE_WIDTH)
                for s in keeps:
                    self.assertIn(s, out)
                for s in drops:
                    self.assertNotIn(s, out)

    @unittest.skipUnless(shutil.which("glow"), "glow not on PATH")
    def test_pager(self):
        for name, (_, _, keeps, drops) in EXPECT.items():
            with self.subTest(name):
                out = ANSI.sub("", render_page(CASES / f"{name}.md", PAGER_COLS))
                self.assertNotIn(TOKEN, out)
                for s in keeps:
                    self.assertIn(s, out)
                for s in drops:
                    self.assertNotIn(s, out)


if __name__ == "__main__":
    unittest.main()
