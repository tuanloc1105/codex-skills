#!/usr/bin/env bash
#
# sync-kiro-skill.sh — sync the Kiro-native skills under kiro-skill/ in this
# repository into ~/.kiro/crew/skills/kiro-skill/<name>/.
#
# Source of truth: <repo>/kiro-skill/<name>/           (this repository)
# Destination:      ~/.kiro/crew/skills/kiro-skill/<name>/
#
# This mirrors the same one-way, source-wins sync pattern used by
# scripts/sync-skills.sh for the top-level Codex skills, but targets Kiro's
# own skills directory instead of ~/.codex/skills. It never touches
# ~/.kiro/crew/skills/imported/codex/, which is KiroCrew's own mirror of the
# original Codex skills these were ported from.
#
# Usage:
#   ./scripts/sync-kiro-skill.sh              # sync every skill under kiro-skill/
#   ./scripts/sync-kiro-skill.sh discuss plan  # sync only the named skill(s)
#
# Requires: rsync
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
src_root="$repo_root/kiro-skill"
dest_root="${KIRO_SKILLS_DEST:-$HOME/.kiro/crew/skills/kiro-skill}"

if ! command -v rsync >/dev/null 2>&1; then
  echo "error: rsync is required but was not found on PATH." >&2
  exit 1
fi

if [ ! -d "$src_root" ]; then
  echo "error: source directory not found: $src_root" >&2
  exit 1
fi

# Discover every skill: a direct child of kiro-skill/ containing a SKILL.md.
available_skills=()
for dir in "$src_root"/*/; do
  name="$(basename "$dir")"
  if [ -f "${dir}SKILL.md" ]; then
    available_skills+=("$name")
  fi
done

if [ "${#available_skills[@]}" -eq 0 ]; then
  echo "error: no skill directories with a SKILL.md found under $src_root" >&2
  exit 1
fi

is_available() {
  local target="$1"
  for s in "${available_skills[@]}"; do
    [ "$s" = "$target" ] && return 0
  done
  return 1
}

# Resolve the requested skill list, validating all names before copying
# anything — an invalid name must not leave a partially synced selection.
selected_skills=()
if [ "$#" -eq 0 ]; then
  selected_skills=("${available_skills[@]}")
else
  invalid=()
  for name in "$@"; do
    if is_available "$name"; then
      selected_skills+=("$name")
    else
      invalid+=("$name")
    fi
  done
  if [ "${#invalid[@]}" -gt 0 ]; then
    echo "error: unknown skill name(s): ${invalid[*]}" >&2
    echo "available skills: ${available_skills[*]}" >&2
    exit 1
  fi
fi

mkdir -p "$dest_root"

echo "Syncing ${#selected_skills[@]} skill(s) from $src_root to $dest_root"

for name in "${selected_skills[@]}"; do
  src="$src_root/$name/"
  dest="$dest_root/$name/"
  mkdir -p "$dest"
  echo "  - $name"
  rsync -a \
    --exclude '.git' \
    --exclude '.serena' \
    --exclude '.DS_Store' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    "$src" "$dest"
done

echo "Done. Verifying no drift for the synced skill(s)..."

drift_found=0
diff_tmp="$(mktemp)"
trap 'rm -f "$diff_tmp"' EXIT

for name in "${selected_skills[@]}"; do
  if ! diff -qr \
      -x '.git' \
      -x '.serena' \
      -x '.DS_Store' \
      -x '__pycache__' \
      -x '*.pyc' \
      "$src_root/$name" "$dest_root/$name" >"$diff_tmp" 2>&1; then
    echo "warning: drift detected for '$name':" >&2
    cat "$diff_tmp" >&2
    drift_found=1
  fi
done

if [ "$drift_found" -ne 0 ]; then
  echo "Sync completed with drift warnings above — inspect before trusting the mirror." >&2
  exit 2
fi

echo "All synced skills verified identical to the repository source."
