"""Rewrite Markdown fences for a given display width."""

from __future__ import annotations

import re
from pathlib import Path

FENCE = re.compile(r"^```([^\n]*)\n(.*?)^```[ \t]*\n?", re.M | re.S)
TEXT_FENCE = re.compile(r"^```text\n(.*?)^```[ \t]*\n?", re.M | re.S)

BOX = set("┌┐└┘├┤┬┴┼─│╭╮╰╯►▼▲◀■□═║╔╗╚╝▬─|")
MERMAID_PLACE = "> 〔流程图：回车全屏查看〕\n\n"
ART_PLACE = "> 〔示意图：回车全屏查看〕\n\n"


def _max_line_width(body: str) -> int:
    lines = body.splitlines() or [""]
    return max(len(line) for line in lines)


def is_wide_art(body: str, budget: int) -> bool:
    if _max_line_width(body) <= budget:
        return False
    box_n = sum(ch in BOX for ch in body)
    if box_n >= 6:
        return True
    if body.count("─") >= 8 or ("--------" in body):
        return True
    if sum(line.count("|") for line in body.splitlines()) >= 8:
        return True
    return False


def collapse_for_pane(text: str, width: int) -> str:
    """Replace mermaid and over-wide ASCII diagrams with placeholders."""
    budget = max(24, width - 4)

    def repl(match: re.Match[str]) -> str:
        lang = (match.group(1) or "").strip().split()
        lang = lang[0].lower() if lang else ""
        body = match.group(2)
        if lang == "mermaid":
            return MERMAID_PLACE
        if is_wide_art(body, budget):
            return ART_PLACE
        return match.group(0)

    return FENCE.sub(repl, text)


def unwrap_text_fences(text: str) -> str:
    """mmd2txt wraps box-art in ```text; glow then syntax-highlights it."""
    return TEXT_FENCE.sub(lambda m: m.group(1) + "\n", text)


def mermaid_to_boxart(src: Path, width: int, mmd2txt: str) -> str:
    """Rewrite mermaid fences to box-art. Keep output even if one graph is too wide."""
    import subprocess

    proc = subprocess.run(
        [mmd2txt, "--md", "--max-width", str(max(width, 40)), str(src)],
        capture_output=True,
        text=True,
        check=False,
    )
    body = proc.stdout or src.read_text(encoding="utf-8", errors="replace")
    return unwrap_text_fences(body)
