#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <input.mmd> <output.svg|output.png|output.pdf> [theme]" >&2
}

find_cached_browser() {
  local cache_root candidate
  cache_root=${PUPPETEER_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/puppeteer}

  for browser_directory in chrome-headless-shell chrome; do
    [[ -d "$cache_root/$browser_directory" ]] || continue
    candidate=$(find "$cache_root/$browser_directory" -type f \
      \( -name chrome-headless-shell -o -name chrome \) -perm -u+x -print 2>/dev/null \
      | sort -V | tail -n 1)
    if [[ -n "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

write_puppeteer_config() {
  local browser_path=$1
  local config_path=$2
  local browser_args='[]'

  if [[ "$browser_path" == *'"'* || "$browser_path" == *$'\n'* ]]; then
    echo "Browser path contains characters that cannot be written safely to Puppeteer config." >&2
    return 1
  fi

  if [[ ${CODEX_SHELL:-} == 1 || ${MERMAID_BROWSER_NO_SANDBOX:-} == 1 ]]; then
    browser_args='["--no-sandbox", "--disable-setuid-sandbox"]'
  fi

  printf '{\n  "executablePath": "%s",\n  "args": %s\n}\n' \
    "$browser_path" "$browser_args" >"$config_path"
}

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage
  exit 2
fi

input_path=$1
output_path=$2
theme=${3:-default}

if [[ ! -f "$input_path" ]]; then
  echo "Input file does not exist: $input_path" >&2
  exit 2
fi

case "$output_path" in
  *.svg|*.png|*.pdf) ;;
  *)
    echo "Output must end in .svg, .png, or .pdf: $output_path" >&2
    exit 2
    ;;
esac

case "$theme" in
  default|neutral|dark|forest) ;;
  *)
    echo "Unsupported Mermaid theme: $theme" >&2
    exit 2
    ;;
esac

if command -v mmdc >/dev/null 2>&1; then
  mermaid_command=(mmdc)
elif command -v npx >/dev/null 2>&1 && npx --no-install mmdc --version >/dev/null 2>&1; then
  mermaid_command=(npx --no-install mmdc)
else
  echo "Mermaid CLI is not installed locally. Install @mermaid-js/mermaid-cli, then retry." >&2
  exit 127
fi

puppeteer_arguments=()
temporary_directory=

if [[ -n ${MERMAID_PUPPETEER_CONFIG_FILE:-} ]]; then
  if [[ ! -f "$MERMAID_PUPPETEER_CONFIG_FILE" ]]; then
    echo "Puppeteer config does not exist: $MERMAID_PUPPETEER_CONFIG_FILE" >&2
    exit 2
  fi
  puppeteer_arguments=(--puppeteerConfigFile "$MERMAID_PUPPETEER_CONFIG_FILE")
else
  browser_path=${PUPPETEER_EXECUTABLE_PATH:-}
  if [[ -z "$browser_path" ]]; then
    browser_path=$(find_cached_browser || true)
  fi

  if [[ -n "$browser_path" ]]; then
    if [[ ! -x "$browser_path" ]]; then
      echo "Puppeteer browser is not executable: $browser_path" >&2
      exit 2
    fi
    temporary_directory=$(mktemp -d)
    trap 'rm -rf "$temporary_directory"' EXIT
    puppeteer_config="$temporary_directory/puppeteer-config.json"
    write_puppeteer_config "$browser_path" "$puppeteer_config"
    puppeteer_arguments=(--puppeteerConfigFile "$puppeteer_config")
  fi
fi

if ! "${mermaid_command[@]}" --input "$input_path" --output "$output_path" \
  --theme "$theme" --quiet "${puppeteer_arguments[@]}"; then
  if [[ ${CODEX_SHELL:-} == 1 ]]; then
    echo "Mermaid rendering failed in Codex. If the diagnostic shows a browser sandbox or launch error, request approval to rerun this same command outside the process sandbox." >&2
  else
    echo "Mermaid rendering failed. Check the syntax above and confirm that Mermaid CLI and its browser runtime are available." >&2
  fi
  exit 1
fi
