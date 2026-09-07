# Troubleshooting

Seen on macOS with Yazi 26.9.1, piper 4dc7f1b, glow 3.0.0, less 668, ghostty 1.3 with herdr panes.

## Yazi setup

- `ya pkg add` creates only `package.toml` and `plugins/`. There is no `yazi.toml` until you make one; nothing tells you that.
- piper shows the command's **stderr instead of the preview** whenever anything is written there. `sh: mdterm: command not found` in the pane means the shell that launched Yazi has no `~/.local/bin` on its PATH (a Yazi started from a launcher can have a shorter PATH than your interactive shell). `mdterm: glow is not on PATH` means glow is missing. mdterm keeps stderr silent otherwise, so any text there is a real error.
- To tell "not on PATH" from "previewer block missing", run `mdterm preview README.md --width 48` in a shell: if that renders, the config is at fault.
- Enter opens mdterm and `o` shows the menu with `edit`; that is what `use = [ "mdterm", "edit" ]` means. Swap the order if you want Enter to edit.
- Yazi 26 openers take `%s`; Yazi 0.4 and earlier used `"$@"`. The snippet is for 26. Paths with spaces or CJK are fine, Yazi quotes `%s` itself.
- piper passes `$t` (`dark` / `light`) but mdterm does not read it yet, so on a light terminal the grey text is faint.

## Why glow is never given a TTY

`glow file.md` opens its own TUI whenever stdin is a TTY. Its `notty` style draws invisible text on a dark background, and the TUI does not recompute mermaid on resize. mdterm therefore always feeds glow Markdown on stdin and pages the ANSI output with `less -R -S`. Glow hard-wraps code lines at `-w`, which breaks box drawing, so mermaid art and over-wide fences bypass glow and are spliced in afterwards.

## Pager flickers and needs several `q` to quit

Symptom: after pressing `q` the screen flashes twice, then the pager comes back; it takes several `q` to leave.

Cause: the pager polls the terminal width every 250 ms and restarts `less` when it changes. In a herdr pane (and any multiplexer that hides its pane scrollbar on the alternate screen) the pane is one column wider on the alternate screen than on the main screen. `less` switches to the alternate screen on start and back on exit, so every start and exit looked like a resize: `q` exited less, the width flipped, mdterm restarted less, the width flipped again, and so on. A bare ghostty window does not do this, which is why the bug only showed inside herdr.

Fix (in `cmd_pager`): mdterm holds the alternate screen itself for the whole session and runs `less -X`, so less never switches screens and the width stays constant across restarts. A real window resize still restarts less exactly once.

How it was found: wrapping Yazi in `script -q -k` made the bug vanish, because macOS `script` does not forward window-size changes to the inner pty. A width logger inside the pane then showed the column count flipping 141↔140 in lockstep with less starting and exiting. A headless pty that adds a column on `ESC[?1049h` and removes it on `ESC[?1049l` reproduces it: the old code restarted less three times before the first `q` was seen, the new code once.
