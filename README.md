# mdterm

Markdown for the terminal, rendered two ways:

- `mdterm preview FILE --width N`: a narrow pane (Yazi's preview). Mermaid and over-wide ASCII diagrams become a one-line placeholder; long files are cut.
- `mdterm pager FILE`: full width in `less`. Mermaid becomes box art, wide diagrams scroll sideways, and a window resize re-renders at the new width.

Glow does the Markdown rendering. Fences that glow would wrap (mermaid art, box drawing wider than the window) are taken out before glow runs and spliced back afterwards. Fence detection follows CommonMark and measures width in terminal cells, so CJK box art counts double.

## Install

```bash
brew install glow           # python3 and less ship with macOS
git clone https://github.com/RoacherM/mdterm.git
cd mdterm
./install.sh                # symlinks bin/mdterm into ~/.local/bin, nothing else
```

Optional: put `mmd2txt` (the grok-mermaid CLI) on PATH and the pager draws mermaid fences as box art. Flowchart, sequence, state, class and ER are supported; without it the pager shows the mermaid source.

Try it without installing:

```bash
./bin/mdterm preview example.md --width 48
./bin/mdterm pager example.md
```

Uninstall: `rm ~/.local/bin/mdterm` and delete the clone.

## Yazi

1. Run `./install.sh` so that `mdterm` is on PATH. Yazi runs it by name.
2. Install piper, the plugin that pipes a command's stdout into the preview pane:

   ```bash
   ya pkg add yazi-rs/plugins:piper
   ```

3. Add the blocks from `share/yazi.toml` to `~/.config/yazi/yazi.toml` (copy the file whole if you have none):

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

Restart Yazi. Hovering a `.md` file shows the rendered text in the right pane; Enter opens the pager, `q` returns to Yazi; `o` offers `edit`.

## Behaviour to know

- The pager runs `less -S`: lines wider than the window are cut, not wrapped. Scroll right with `→`, or type `-S` inside less to toggle wrapping.
- Resizing the window restarts `less` from the top of the file.
- Colours assume a dark background.

If the pane shows raw Markdown, an error message, or the pager flickers, see [docs/troubleshooting.md](docs/troubleshooting.md).

## Layout

```
bin/mdterm            # launcher; repo-relative
mdterm/
  fences.py           # find fences (CommonMark), placeholders, mmd2txt batch, splice
  glow.py             # glow CLI dump; errors are raised, never hidden
  cli.py              # preview | pager
share/glow-mono.json  # pager style
share/glow-pane.json  # preview style
share/yazi.toml       # snippet to paste
install.sh
tests/test_fences.py
docs/troubleshooting.md
```

```bash
python3 -m unittest discover -s tests
```
