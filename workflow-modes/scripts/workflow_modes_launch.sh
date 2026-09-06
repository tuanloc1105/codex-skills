#!/bin/sh
# Keep this fallback independent of Python and the plugin's import graph.
event=$1
fail() {
    message="WORKFLOW_HOOK_LAUNCH_FAILED: event=$event. Next: from a terminal outside this task, check python3 and PLUGIN_ROOT/scripts/workflow_modes_supervisor.py. Ask the owner to restore the installed bundle; close old-cache tasks before any requested reinstall. Do not edit hook scripts or reset the database. Report this blocker; after recovery run snapshot before retrying."
    printf '%s\n' "$message" >&2
    if [ "$event" = PreToolUse ]; then exit 2; fi
    printf '{"systemMessage":"%s"}\n' "$message"
    exit 0
}
case "$event" in PreToolUse|Stop|UserPromptSubmit|PostCompact|SessionEnd) ;; *) event=PreToolUse; fail ;; esac
command -v python3 >/dev/null 2>&1 || fail
[ -f "$PLUGIN_ROOT/scripts/workflow_modes_supervisor.py" ] || fail
python3 "$PLUGIN_ROOT/scripts/workflow_modes_supervisor.py" "$event"
result=$?
case "$result" in 0) exit 0 ;; 2) [ "$event" = PreToolUse ] && exit 2 ;; esac
fail
