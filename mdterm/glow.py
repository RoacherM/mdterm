"""Glow CLI dump. Never attach a TTY to glow — it would open its TUI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLE = ROOT / "share" / "glow-mono.json"


def which_glow() -> str:
    path = shutil.which("glow")
    if not path:
        raise FileNotFoundError("glow is not on PATH; install: brew install glow")
    return path


def dump(markdown: str, width: int) -> str:
    glow = which_glow()
    width = max(20, width)
    for style in (str(STYLE), "ascii"):
        proc = subprocess.run(
            [glow, "-s", style, "-w", str(width)],
            input=markdown,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
    return markdown
