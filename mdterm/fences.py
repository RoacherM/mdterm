"""Find fenced code blocks and decide what happens to each at a given width.

The pane replaces mermaid and over-wide diagrams with a placeholder.
The pager turns mermaid into box art and keeps over-wide blocks away from
glow, because glow hard-wraps code lines and breaks box drawing.
"""

from __future__ import annotations

import re
import subprocess
import unicodedata
from dataclasses import dataclass

# CommonMark 4.5: three or more backticks or tildes, optionally indented
# (the indent is the list item's content offset when the fence sits in a list).
OPEN = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")

BOX = set("┌┐└┘├┤┬┴┼─│╭╮╰╯►▼▲◀■□═║╔╗╚╝▬|")
MERMAID_PLACE = "> 〔流程图：回车全屏查看〕"
ART_PLACE = "> 〔示意图：回车全屏查看〕"
TOKEN = "MDTERMBLOCK"
SEP = "MDTERMSEP"


@dataclass
class Fence:
    start: int  # index of the opening line
    end: int  # index after the closing line
    indent: str
    lang: str
    body: list[str]  # lines with the fence indent removed


def display_width(text: str) -> int:
    """Terminal cells, not code points: CJK is two cells wide."""
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in "WF" else 1
    return width


def scan(lines: list[str]) -> list[Fence]:
    fences: list[Fence] = []
    i = 0
    while i < len(lines):
        opened = OPEN.match(lines[i])
        if not opened or ("`" in opened["fence"] and "`" in opened["info"]):
            i += 1
            continue
        fence, indent = opened["fence"], opened["indent"]
        lang = opened["info"].strip().split(" ")[0].lower()
        close = re.compile(rf"^[ \t]*{fence[0]}{{{len(fence)},}}[ \t]*$")
        body: list[str] = []
        j = i + 1
        while j < len(lines) and not close.match(lines[j]):
            line = lines[j]
            body.append(line[len(indent):] if line.startswith(indent) else line.lstrip())
            j += 1
        end = min(j + 1, len(lines))
        fences.append(Fence(i, end, indent, lang, body))
        i = end
    return fences


def is_wide_art(body: list[str], budget: int) -> bool:
    if max((display_width(line) for line in body), default=0) <= budget:
        return False
    text = "\n".join(body)
    if sum(ch in BOX for ch in text) >= 6:
        return True
    return text.count("─") >= 8 or "--------" in text


def collapse_for_pane(text: str, width: int) -> str:
    """Replace mermaid and over-wide diagrams with placeholders."""
    budget = max(24, width - 4)
    lines = text.splitlines()
    for f in reversed(scan(lines)):
        if f.lang == "mermaid":
            lines[f.start : f.end] = [f.indent + MERMAID_PLACE, ""]
        elif is_wide_art(f.body, budget):
            lines[f.start : f.end] = [f.indent + ART_PLACE, ""]
    return "\n".join(lines) + "\n"


def render_mermaid(bodies: list[list[str]], width: int, mmd2txt: str) -> list[list[str]]:
    """One mmd2txt call for every diagram; returns box-art lines per diagram."""
    if not bodies:
        return []
    doc = f"\n\n{SEP}\n\n".join(
        "```mermaid\n" + "\n".join(body) + "\n```" for body in bodies
    )
    proc = subprocess.run(
        [mmd2txt, "--md", "--max-width", str(max(width, 40))],
        input=doc + "\n",
        capture_output=True,
        text=True,
        check=False,
    )
    # 0 ok, 1 unsupported kind (source echoed in a box), 2 still too wide.
    if proc.returncode not in (0, 1, 2):
        raise RuntimeError(f"mmd2txt failed ({proc.returncode}): {proc.stderr.strip()}")
    parts = proc.stdout.split(SEP)
    if len(parts) != len(bodies):
        raise RuntimeError(f"mmd2txt returned {len(parts)} diagrams for {len(bodies)}")
    arts = []
    for part in parts:
        art = [ln for ln in part.splitlines() if not ln.startswith("```")]
        while art and not art[0].strip():
            art.pop(0)
        while art and not art[-1].strip():
            art.pop()
        arts.append(art)
    return arts


def prepare_for_pager(
    text: str, width: int, mmd2txt: str | None
) -> tuple[str, list[list[str]]]:
    """Markdown for glow plus the blocks glow must not touch.

    Each block is replaced by a `MDTERMBLOCK<n>` paragraph; `splice` puts the
    raw lines back after glow has rendered the rest.
    """
    lines = text.splitlines()
    fences = scan(lines)
    arts: dict[int, list[str]] = {}
    if mmd2txt:
        mermaid = [f for f in fences if f.lang == "mermaid"]
        arts = dict(zip(
            (f.start for f in mermaid),
            render_mermaid([f.body for f in mermaid], width, mmd2txt),
        ))
    blocks: list[list[str]] = []
    for f in reversed(fences):
        if f.start in arts:
            raw = arts[f.start]
        elif max((display_width(ln) for ln in f.body), default=0) > width - 2:
            raw = f.body
        else:
            continue
        blocks.append(raw)
        lines[f.start : f.end] = ["", f"{f.indent}{TOKEN}{len(blocks) - 1}", ""]
    return "\n".join(lines) + "\n", blocks


ANSI = re.compile(r"\x1b\[[0-9;]*m|\x1b\]8;[^\x07]*\x07")
TOKEN_RE = re.compile(rf"{TOKEN}(\d+)")


def splice(rendered: str, blocks: list[list[str]]) -> str:
    """Put raw blocks back where glow printed their tokens."""
    out: list[str] = []
    for line in rendered.splitlines():
        plain = ANSI.sub("", line)
        m = TOKEN_RE.search(plain)
        if not m:
            out.append(line)
            continue
        raw = blocks[int(m.group(1))]
        lead = plain[: m.start()]
        if lead.strip():
            out.append(lead.rstrip())
        margin = " " * (len(lead) - len(lead.lstrip()) or 1)
        out.extend(margin + ln for ln in raw)
    return "\n".join(out) + "\n"
