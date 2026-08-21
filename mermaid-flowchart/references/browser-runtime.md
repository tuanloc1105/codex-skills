# Mermaid Browser Runtime

Read this reference only when Mermaid CLI cannot find or launch its Puppeteer browser.

## Resolution order

`scripts/render_mermaid.sh` resolves Puppeteer configuration in this order:

1. Use the file named by `MERMAID_PUPPETEER_CONFIG_FILE`.
2. Use the executable named by `PUPPETEER_EXECUTABLE_PATH` and generate a temporary config.
3. Discover the newest executable under the Puppeteer cache, preferring `chrome-headless-shell` over full Chrome, and generate a temporary config.
4. Invoke Mermaid CLI without a config and allow Puppeteer to perform its normal resolution.

The cache root is `PUPPETEER_CACHE_DIR` when set, otherwise `${XDG_CACHE_HOME:-$HOME/.cache}/puppeteer`. The script does not install packages or download browsers.

## Sandbox behavior

When `CODEX_SHELL=1`, the generated config includes `--no-sandbox` and `--disable-setuid-sandbox`, because Chrome's own sandbox cannot initialize inside some managed execution environments. These flags do not grant permission to escape the surrounding Codex process sandbox. If Chrome still fails with a sandbox or browser-launch diagnostic, request approval immediately before rerunning the same render command outside that process sandbox.

Outside Codex, the generated config preserves Chrome's sandbox. Set `MERMAID_BROWSER_NO_SANDBOX=1` only when the execution environment itself requires it and the user accepts that reduced browser isolation.

## Custom configuration

Set `MERMAID_PUPPETEER_CONFIG_FILE` when a project already owns a Puppeteer JSON configuration. The renderer passes that file through unchanged and does not combine it with auto-discovered settings.
