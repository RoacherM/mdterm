"""mdterm CLI: preview (narrow pane) and pager (full screen)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from mdterm.fences import collapse_for_pane, prepare_for_pager, splice
from mdterm.glow import PANE_STYLE, dump

# glow is linear in input size (~2 s for 40k lines); a pane never shows that much.
PANE_MAX_LINES = 1500
TRUNCATED = "> 〔已截断：回车全屏查看〕"


def _cols() -> int:
    try:
        return max(40, shutil.get_terminal_size().columns)
    except OSError:
        return 80


def cmd_preview(path: Path, width: int) -> int:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) > PANE_MAX_LINES:
        lines = lines[:PANE_MAX_LINES] + ["", TRUNCATED]
    text = collapse_for_pane("\n".join(lines), width)
    try:
        sys.stdout.write(dump(text, width, PANE_STYLE))
    except BrokenPipeError:
        pass
    return 0


def render_page(path: Path, cols: int) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    width = max(20, cols - 2)
    markdown, blocks = prepare_for_pager(text, width, shutil.which("mmd2txt"))
    return splice(dump(markdown, width), blocks)


ALT_ON = "\x1b[?1049h"
ALT_OFF = "\x1b[?1049l"
CLEAR = "\x1b[2J\x1b[H"


def cmd_pager(path: Path) -> int:
    """Render at current width, open less; restart when the terminal is resized.

    mdterm holds the alternate screen itself and runs less with -X so that less
    never switches screens. Some terminal multiplexers (herdr panes) change the
    column count when the screen switches, because the pane scrollbar goes away
    on the alternate screen; a less restart that switched screens would then
    read as yet another resize, forever.
    """
    less_cmd = ["less", "-R", "-S", "-X"]
    if _less_has_mouse():
        less_cmd.append("--mouse")
    tty = sys.stdout
    tty.write(ALT_ON)
    tty.flush()
    try:
        time.sleep(0.1)  # the terminal may still be applying the screen switch
        while True:
            cols = _cols()
            page = render_page(path, cols)
            with tempfile.NamedTemporaryFile(
                "w", prefix="mdterm.", suffix=".txt", delete=False, encoding="utf-8"
            ) as fh:
                fh.write(page)
            out = Path(fh.name)
            try:
                tty.write(CLEAR)
                tty.flush()
                proc = subprocess.Popen(less_cmd + [str(out)])
                status = _wait_unless_resized(proc, cols)
            finally:
                out.unlink(missing_ok=True)
            if status is None:
                continue
            return 0 if status in (0, 15, -15) else status
    finally:
        tty.write(ALT_OFF)
        tty.flush()


def _wait_unless_resized(proc: subprocess.Popen, cols: int) -> int | None:
    """Exit status of less, or None once it was killed because the width changed."""
    try:
        while True:
            try:
                return proc.wait(timeout=0.25)
            except subprocess.TimeoutExpired:
                pass
            if _cols() != cols:
                proc.terminate()
                proc.wait()
                return None
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        raise


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
    if not args.file.is_file():
        print(f"mdterm: missing file: {args.file}", file=sys.stderr)
        return 1
    try:
        if args.cmd == "preview":
            return cmd_preview(args.file, args.width)
        return cmd_pager(args.file)
    except (FileNotFoundError, RuntimeError) as err:
        print(f"mdterm: {err}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
