#!/usr/bin/env bash
# Install mdterm onto PATH. Does not edit Yazi or glow config.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BIN="${MDTERM_BIN_DIR:-$HOME/.local/bin}"

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing dependency: $1" >&2
    echo "  $2" >&2
    return 1
  fi
}

echo "==> checking dependencies"
need python3 "macOS: already present, or brew install python"
need glow "brew install glow"
need less "ships with macOS"
if ! command -v mmd2txt >/dev/null 2>&1; then
  echo "optional: mmd2txt not found (mermaid stays as source in pager)"
  echo "  put mmd2txt on PATH if you want mermaid → box art"
fi

mkdir -p "$BIN"
chmod +x "$ROOT/bin/mdterm"
ln -sfn "$ROOT/bin/mdterm" "$BIN/mdterm"
echo "==> linked $BIN/mdterm -> $ROOT/bin/mdterm"

case ":$PATH:" in
  *":$BIN:"*) ;;
  *)
    echo "note: $BIN is not on PATH. Add this to your shell rc:"
    echo "  export PATH=\"$BIN:\$PATH\""
    ;;
esac

echo
echo "==> Yazi (optional, you paste this yourself)"
echo "    1. ya pkg add yazi-rs/plugins:piper"
echo "    2. merge share/yazi.toml into ~/.config/yazi/yazi.toml"
echo
echo "try: mdterm preview README.md --width 48"
echo "     mdterm pager README.md"
