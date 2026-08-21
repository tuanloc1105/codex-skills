#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <input.mmd>" >&2
  exit 2
fi

input_path=$1
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
temporary_dir=$(mktemp -d)
trap 'rm -rf "$temporary_dir"' EXIT

"$script_dir/render_mermaid.sh" "$input_path" "$temporary_dir/validated.svg"
echo "Valid Mermaid flowchart: $input_path"
