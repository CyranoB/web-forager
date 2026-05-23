#!/usr/bin/env bash
set -euo pipefail

# Links all skills in this repository to a local Claude Code skills directory
# for dogfooding edits without publishing a new version.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${SKILLS_DEST:-$HOME/.claude/skills}"

resolve_path() {
  if command -v realpath >/dev/null 2>&1; then
    realpath "$1"
  elif command -v greadlink >/dev/null 2>&1; then
    greadlink -f "$1"
  else
    readlink -f "$1"
  fi
}

# If the destination directory itself points into this repo, writing per-skill
# symlinks would pollute the working copy. Stop instead.
if [ -L "$DEST" ]; then
  resolved="$(resolve_path "$DEST")"
  case "$resolved" in
    "$REPO"|"$REPO"/*)
      echo "error: $DEST is a symlink into this repo ($resolved)." >&2
      echo "Remove it or set SKILLS_DEST to a real directory, then re-run." >&2
      exit 1
      ;;
  esac
fi

mkdir -p "$DEST"

find_skill_files() {
  find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -not -path '*/deprecated/*' -print0
}

while IFS= read -r -d '' skill_md; do
  name="$(basename "$(dirname "$skill_md")")"
  target="$DEST/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "error: $target already exists and is not a symlink." >&2
    echo "Move or remove it before linking $name." >&2
    exit 1
  fi
done < <(find_skill_files)

while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  target="$DEST/$name"

  ln -sfn "$src" "$target"
  echo "linked $name -> $src"
done < <(find_skill_files)
