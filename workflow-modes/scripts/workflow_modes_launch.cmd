@echo off
setlocal DisableDelayedExpansion
set "workflow_event=%~1"
if "%workflow_event%"=="PreToolUse" goto launch
if "%workflow_event%"=="Stop" goto launch
if "%workflow_event%"=="UserPromptSubmit" goto launch
if "%workflow_event%"=="PostCompact" goto launch
if "%workflow_event%"=="SessionEnd" goto launch
set "workflow_event=PreToolUse"
goto failure
:launch
where py >nul 2>&1
if errorlevel 1 goto failure
if not exist "%PLUGIN_ROOT%\scripts\workflow_modes_supervisor.py" goto failure
py -3 "%PLUGIN_ROOT%\scripts\workflow_modes_supervisor.py" "%workflow_event%"
set "workflow_result=%ERRORLEVEL%"
if "%workflow_result%"=="0" exit /b 0
if "%workflow_result%"=="2" if "%workflow_event%"=="PreToolUse" exit /b 2
:failure
>&2 echo WORKFLOW_HOOK_LAUNCH_FAILED: event=%workflow_event%. Next: from a terminal outside this task, check py -3 and PLUGIN_ROOT/scripts/workflow_modes_supervisor.py. Ask the owner to restore the installed bundle; close old-cache tasks before any requested reinstall. Do not edit hook scripts or reset the database. Report this blocker; after recovery run snapshot before retrying.
if "%workflow_event%"=="PreToolUse" exit /b 2
echo {"systemMessage":"WORKFLOW_HOOK_LAUNCH_FAILED: Report this blocker. Check py -3 and the installed plugin bundle from an external terminal; restore enforcement and run snapshot before retrying. Do not reset the database."}
exit /b 0
