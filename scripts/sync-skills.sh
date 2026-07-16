#!/usr/bin/env bash

set -euo pipefail

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

if [[ -z ${HOME:-} ]]; then
  printf 'Error: HOME is not set.\n' >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  printf 'Error: rsync is required but was not found in PATH.\n' >&2
  exit 1
fi

destination_root="$HOME/.codex/skills"
skill_names=()

if (( $# > 0 )); then
  skill_names=("$@")
else
  for source in "$repo_root"/* "$repo_root"/.[!.]* "$repo_root"/..?*; do
    [[ -d "$source" && -f "$source/SKILL.md" ]] || continue
    skill_names+=("${source##*/}")
  done
fi

if (( ${#skill_names[@]} == 0 )); then
  printf 'Error: no skill directories containing SKILL.md were found.\n' >&2
  exit 1
fi

mkdir -p -- "$destination_root"

for skill_name in "${skill_names[@]}"; do
  case "$skill_name" in
    ''|.|..|*/*|*\\*)
      printf 'Error: skill names must be top-level directory names: %s\n' "$skill_name" >&2
      exit 1
      ;;
  esac

  source="$repo_root/$skill_name"
  destination="$destination_root/$skill_name"

  if [[ ! -f "$source/SKILL.md" ]]; then
    printf 'Error: skill not found or missing SKILL.md: %s\n' "$skill_name" >&2
    exit 1
  fi

  mkdir -p -- "$destination"
  rsync -a \
    --exclude '.git' \
    --exclude '.serena' \
    --exclude '.DS_Store' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    -- "$source/" "$destination/"

  printf 'Synced %s -> %s\n' "$skill_name" "$destination"
done

printf 'Done. Destination-only files were left unchanged.\n'
