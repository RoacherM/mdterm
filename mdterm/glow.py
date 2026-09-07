"""Glow CLI dump. Never attach a TTY to glow — it would open its TUI."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLE = ROOT / "share" / "glow-mono.json"
# Same style with link URLs hidden: a 40-column pane has no room for them.
PANE_STYLE = ROOT / "share" / "glow-pane.json"


def which_glow() -> str:
    path = shutil.which("glow")
    if not path:
        raise FileNotFoundError("glow is not on PATH; install: brew install glow")
    return path


def dump(markdown: str, width: int, style: Path = STYLE) -> str:
    proc = subprocess.run(
        [which_glow(), "-s", str(style), "-w", str(max(20, width))],
        input=markdown,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"glow failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout
