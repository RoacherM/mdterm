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

Optional: install [mmd2txt](https://github.com/RoacherM/mmd2txt) (`npm install -g github:RoacherM/mmd2txt`, Node 20+) and the pager draws mermaid fences as box art. Without it the pager shows the mermaid source.

Try it without installing:

```bash
./bin/mdterm preview example.md --width 48
./bin/mdterm pager example.md
```

Uninstall: `rm ~/.local/bin/mdterm` and delete the clone.

### Let an agent install it

Paste this into any coding agent (Claude Code, Codex, Cursor, ...) that runs on the machine where Yazi runs:

```text
Install mdterm, a Markdown previewer and pager for Yazi, from https://github.com/RoacherM/mdterm:
1. Make sure glow is installed (brew install glow on macOS). python3 and less must exist; on Linux install them with the system package manager.
2. git clone the repo into ~/.local/share/mdterm (or update it if present) and run ./install.sh there. It symlinks bin/mdterm into ~/.local/bin; make sure ~/.local/bin is on PATH in my shell rc.
3. Run `ya pkg add yazi-rs/plugins:piper` to install the piper plugin.
4. Merge the blocks in share/yazi.toml into ~/.config/yazi/yazi.toml: create the file from share/yazi.toml if it does not exist, otherwise append the two [[plugin.prepend_previewers]] blocks and the [opener] / [open] entries to the matching sections without duplicating any I already have.
5. Verify with `mdterm preview README.md --width 48` in the clone (it must print rendered ANSI text, nothing on stderr) and `yazi --version`.
6. Tell me to restart Yazi, and list every file you changed.
Optional: if I ask for mermaid box art, run `npm install -g github:RoacherM/mmd2txt` too (needs Node 20+).
```

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
tests/                # unit tests; tests/cases/ holds one Markdown file per shape that once rendered wrong
docs/troubleshooting.md
```

```bash
python3 -m unittest discover -s tests
```
