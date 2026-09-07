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
| `pager` | current terminal columns | mermaid → box art at that width | glow CLI (stdin, no TTY) → `less -R -S`; resize re-renders |

Glow only ever sees Markdown on stdin and writes ANSI on stdout.

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

You paste this. The installer will not.

```bash
ya pkg add yazi-rs/plugins:piper
```

Merge `share/yazi.toml` into `~/.config/yazi/yazi.toml`:

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

In the pane: mermaid and over-wide ASCII become `〔流程图/示意图：回车全屏查看〕`. Enter opens `less` (not glow TUI). `q` leaves the pager. Resize the window and the pager re-renders at the new width.

## Layout

```
mdterm/
  bin/mdterm          # launcher; repo-relative, no hardcoded home
  mdterm/
    fences.py         # placeholders, unwrap ```text, call mmd2txt
    glow.py           # glow CLI dump, monochrome style
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

`mmd2txt` on `PATH` turns ` ```mermaid ` fences into box art in **pager** mode. Without it, pager shows the mermaid source; preview still replaces the fence with a placeholder.

`mmd2txt` is the grok-mermaid CLI (flowchart / sequence / state / class / ER). Pie and gantt are unsupported.
