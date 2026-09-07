"""mdterm CLI: preview (narrow pane) and pager (full screen)."""

from __future__ import annotations

import argparse
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from mdterm.fences import collapse_for_pane, mermaid_to_boxart
from mdterm.glow import dump


def _cols() -> int:
    try:
        return max(40, shutil.get_terminal_size().columns)
    except OSError:
        return 80


def _mmd2txt() -> str | None:
    return shutil.which("mmd2txt")


def cmd_preview(path: Path, width: int) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = collapse_for_pane(text, width)
    try:
        sys.stdout.write(dump(text, width))
    except BrokenPipeError:
        return 0
    return 0


def cmd_pager(path: Path) -> int:
    """Render at current width, open less; restart when the terminal is resized."""
    mmd = _mmd2txt()
    while True:
        cols = _cols()
        if mmd:
            markdown = mermaid_to_boxart(path, cols, mmd)
        else:
            markdown = path.read_text(encoding="utf-8", errors="replace")
        rendered = dump(markdown, max(20, cols - 2))
        with tempfile.NamedTemporaryFile(
            prefix="mdterm.", suffix=".txt", delete=False
        ) as fh:
            fh.write(rendered.encode("utf-8"))
            out = Path(fh.name)
        less_cmd = ["less", "-R", "-S"]
        if _less_has_mouse():
            less_cmd.append("--mouse")
        less_cmd.append(str(out))
        proc = subprocess.Popen(less_cmd)
        resized = False
        try:
            while proc.poll() is None:
                time.sleep(0.25)
                if _cols() != cols:
                    resized = True
                    proc.send_signal(signal.SIGTERM)
                    break
            status = proc.wait()
        finally:
            try:
                out.unlink()
            except OSError:
                pass
        if resized:
            continue
        return 0 if status in (0, 15, -15) else status


def _less_has_mouse() -> bool:
    try:
        proc = subprocess.run(
            ["less", "--help"], capture_output=True, text=True, check=False
        )
    except OSError:
        return False
    return "--mouse" in (proc.stdout + proc.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mdterm",
        description="Terminal Markdown: narrow pane vs full-width pager.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_prev = sub.add_parser("preview", help="stdout for a narrow pane (Yazi piper)")
    p_prev.add_argument("file", type=Path)
    p_prev.add_argument("--width", type=int, default=80)

    p_page = sub.add_parser("pager", help="full-screen less; re-render on resize")
    p_page.add_argument("file", type=Path)

    args = parser.parse_args(argv)
    if args.cmd == "preview":
        if not args.file.is_file():
            print(f"mdterm: missing file: {args.file}", file=sys.stderr)
            return 1
        return cmd_preview(args.file, args.width)
    if not args.file.is_file():
        print(f"mdterm: missing file: {args.file}", file=sys.stderr)
        return 1
    return cmd_pager(args.file)


if __name__ == "__main__":
    raise SystemExit(main())
