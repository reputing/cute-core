#!/usr/bin/env bash
# Install the cutecore skill for Claude Code.
#   curl -fsSL https://raw.githubusercontent.com/reputing/cute-core/main/install.sh | bash
#   bash install.sh --project     # into ./.claude/skills of the current project instead of ~/.claude/skills
#   bash install.sh --with-browser  # also installs Playwright + Chromium for dissect.cjs and variant screenshots
set -euo pipefail
REPO="${CUTECORE_REPO:-https://github.com/reputing/cute-core.git}"
BRANCH="${CUTECORE_BRANCH:-main}"
DEST="$HOME/.claude/skills"
WITH_BROWSER=0
for arg in "$@"; do
  case "$arg" in
    --project) DEST="$(pwd)/.claude/skills" ;;
    --with-browser) WITH_BROWSER=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

say() { printf '\033[38;5;211m%s\033[0m %s\n' "♡" "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || { echo "cutecore needs $1 ($2)" >&2; exit 1; }; }
need python3 "the helper scripts use Python 3.9 or newer, standard library only"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
if [ -n "$SRC_DIR" ] && [ -f "$SRC_DIR/skills/cutecore/SKILL.md" ]; then
  SKILL_SRC="$SRC_DIR/skills/cutecore"
else
  need git "to download the skill"
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  say "downloading cutecore"
  git clone --depth 1 --branch "$BRANCH" "$REPO" "$TMP/cute-core" >/dev/null 2>&1
  SKILL_SRC="$TMP/cute-core/skills/cutecore"
fi

mkdir -p "$DEST"
if [ -d "$DEST/cutecore" ]; then
  say "updating existing install at $DEST/cutecore"
  rm -rf "$DEST/cutecore.bak" && mv "$DEST/cutecore" "$DEST/cutecore.bak"
fi
cp -R "$SKILL_SRC" "$DEST/cutecore"
rm -rf "$DEST/cutecore/evals"
chmod +x "$DEST/cutecore/scripts/"*.py "$DEST/cutecore/scripts/dissect.cjs" 2>/dev/null || true
rm -rf "$DEST/cutecore.bak"

if [ "$WITH_BROWSER" = 1 ]; then
  need npm "for Playwright"
  say "installing Playwright + Chromium (for dissect.cjs and screenshots)"
  (cd "$DEST/cutecore" && npm init -y >/dev/null 2>&1 && npm i -D playwright >/dev/null 2>&1 && npx playwright install chromium)
fi

say "installed to $DEST/cutecore"
say "try: claude \"make my guestbook cutecore\"  (it will ask how far to deviate, 1 to 10)"
