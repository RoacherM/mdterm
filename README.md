# mdterm

Terminal Markdown with two render paths: a **narrow pane** (Yazi preview) and a **full-width pager** (Enter). Do not force both through one renderer.

Yazi only picks the file. Width, mermaid, and ASCII diagrams are this repo's job.

The installer never writes `~/.config/yazi` or glow's config. You paste the Yazi snippet yourself.

## Why two paths

Yazi's right pane is ~40 columns. A 60-column box diagram or mermaid graph wraps, the box lines break, and glow paints `─│` as syntax operators (pink).

Full screen can render at `tput cols`, but `glow file.md` opens its own TUI whenever stdin is a TTY. The `notty` style draws invisible text on a dark background. The TUI also will not recompute mermaid when you resize.

So:

| Entry | Width | Diagrams | Output |
| --- | --- | --- | --- |
| `preview` | caller (`--width`) | mermaid / over-wide ASCII → placeholder | glow dump to stdout (piper) |
| `pager` | current terminal columns | mermaid → box art at that width; any fence wider than the terminal bypasses glow | glow CLI (stdin, no TTY) → `less -R -S`; resize re-renders |

Glow only ever sees Markdown on stdin and writes ANSI on stdout. Glow hard-wraps code lines at `-w`, which breaks box drawing, so the pager pulls mermaid art and over-wide fences out before glow runs and splices them back into the ANSI afterwards; `less -S` then scrolls them sideways. Fence detection follows CommonMark (backtick or tilde, indented inside lists) and measures width in terminal cells, so CJK box art counts double.

## Install

Dependencies:

```bash
brew install glow less
# python3 is already on macOS
# optional, for mermaid → box art: put `mmd2txt` on PATH
```

Clone. You can run from the tree with no PATH change:

```bash
git clone https://github.com/RoacherM/mdterm.git
cd mdterm
./bin/mdterm preview README.md --width 48
./bin/mdterm pager README.md
```

To put `mdterm` on PATH (the only file the installer touches):

```bash
./install.sh
```

`install.sh` checks `python3` / `glow` / `less`, then:

```text
ln -sfn <repo>/bin/mdterm ~/.local/bin/mdterm
```

It does **not** edit `~/.config/yazi` or glow's config. If `~/.local/bin` is missing from `PATH`, the script prints the `export` line to add.

Uninstall: `rm ~/.local/bin/mdterm` and delete the clone.

## Yazi

You paste this. The installer will not. Three steps, in order:

1. `./install.sh` (above), so `mdterm` is on PATH. Yazi runs `mdterm` by name; a bare clone is not enough.
2. Install piper, the plugin that pipes a command's stdout into the preview pane:

   ```bash
   ya pkg add yazi-rs/plugins:piper
   ```

3. Put the snippet below into `~/.config/yazi/yazi.toml`. If that file does not exist yet, copy it whole:

   ```bash
   cp share/yazi.toml ~/.config/yazi/yazi.toml
   ```

   If it exists, append the two `[[plugin.prepend_previewers]]` blocks and the `[opener]` / `[open]` entries to the matching sections:

```toml
[[plugin.prepend_previewers]]
url = "*.md"
run = 'piper -- mdterm preview "$1" --width $w'

[[plugin.prepend_previewers]]
mime = "text/markdown"
run = 'piper -- mdterm preview "$1" --width $w'

[opener]
mdterm = [
  { run = 'mdterm pager %s', desc = "Markdown (mdterm)", block = true, for = "unix" },
]

[open]
prepend_rules = [
  { url = "*.md", use = [ "mdterm", "edit" ] },
  { mime = "text/markdown", use = [ "mdterm", "edit" ] },
]
```

Yazi 26 openers take `%s`, not `"$@"`. `$w` is the preview pane width (piper sets it). Quit Yazi (`q`) and start it again after editing the config.

Check it works: hover any `.md` in Yazi. The right pane shows rendered text, with `〔流程图：回车全屏查看〕` where a mermaid fence was. Press Enter: `less` opens full width; `q` returns to Yazi. If the pane shows raw Markdown instead, `mdterm` is not on PATH or the previewer block is missing; run `mdterm preview README.md --width 48` in a shell to tell the two apart.

In the pane: mermaid and over-wide ASCII become `〔流程图/示意图：回车全屏查看〕`, link URLs are hidden (only the link text shows), and files longer than 1500 lines are cut with `〔已截断〕`. Enter opens `less` (not glow TUI). `q` leaves the pager. Resize the window and the pager re-renders at the new width.

## Pitfalls

Seen while walking the steps above on macOS with Yazi 26.9.1, piper 4dc7f1b, glow 3.0.0, less 668, ghostty (dark theme).

- `ya pkg add` creates only `package.toml` and `plugins/`. There is no `yazi.toml` until you make one; nothing tells you that. Step 3 above covers it.
- piper shows the command's **stderr instead of the preview** whenever anything is written there. So `sh: mdterm: command not found` in the pane means the shell that launched Yazi has no `~/.local/bin` on its PATH (a Yazi started from a launcher or app can have a shorter PATH than your interactive shell). `mdterm: glow is not on PATH` means glow is missing. mdterm keeps stderr silent otherwise, so any text there is a real error.
- Enter opens mdterm; `o` shows the menu with `edit`. That is what `use = [ "mdterm", "edit" ]` means. Swap the order if you want Enter to edit.
- Paths with spaces or CJK are fine; Yazi quotes `%s` itself.
- The pager runs `less -S`: lines wider than the window are cut, not wrapped. Scroll right with `→` (or the mouse), or type `-S` inside less to toggle wrapping. This is deliberate, wrapping is what breaks box drawing.
- Resizing the window restarts `less` from the top of the file; less has no way to hand back the current position.
- Colours assume a dark background. On a light terminal the grey text is faint; piper passes `$t` (`dark` / `light`) but mdterm does not read it yet.
- Yazi 26 openers take `%s`; Yazi 0.4 and earlier used `"$@"`. The snippet is for 26.

## Layout

```
mdterm/
  bin/mdterm          # launcher; repo-relative, no hardcoded home
  mdterm/
    fences.py         # find fences (CommonMark), placeholders, mmd2txt batch, splice
    glow.py           # glow CLI dump, monochrome style; errors are raised, never hidden
    cli.py            # preview | pager
  share/glow-mono.json
  share/yazi.toml     # snippet to paste
  install.sh
  tests/test_fences.py
```

```bash
python3 -m unittest discover -s tests
```

## Optional mermaid

`mmd2txt` on `PATH` turns ` ```mermaid ` fences into box art in **pager** mode: all diagrams in a file go through one `mmd2txt --md` call on stdin, and the art is spliced in after glow, so your own ` ```text ` fences are never touched. Without it, pager shows the mermaid source; preview still replaces the fence with a placeholder.

`mmd2txt` is the grok-mermaid CLI (flowchart / sequence / state / class / ER). Pie and gantt are unsupported.
