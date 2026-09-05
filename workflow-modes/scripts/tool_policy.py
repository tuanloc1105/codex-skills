"""Conservative tool classification, not a sandbox or proof of side effects."""

from __future__ import annotations

from pathlib import Path
import re
import shlex
from typing import Any


MUTATING_VERBS = {
    "add", "approve", "archive", "close", "comment", "commit", "create",
    "delete", "deploy", "edit", "install", "merge", "move", "publish",
    "push", "remove", "rename", "reopen", "send", "set", "transition",
    "update", "write",
}
COORDINATION_TOOLS = {
    "followup_task", "get_goal", "interrupt_agent", "list_agents",
    "request_user_input", "request_user_input_async", "send_message",
    "spawn_agent", "update_goal", "update_plan", "wait_agent",
}
READ_COMMANDS = {"cat", "head", "tail", "wc", "pwd", "ls", "rg", "grep", "diff", "stat", "file", "which", "type", "true"}
GIT_READ_COMMANDS = {"status", "diff", "log", "show", "rev-parse", "ls-files", "ls-tree", "check-ignore", "merge-base", "remote"}
FILE_TOOLS = {"write", "edit", "multiedit", "write_file", "edit_file", "delete_file", "move_file", "rename_file"}
OPAQUE_TOOLS = {"exec", "js", "eval", "evaluate", "run_code", "run_script", "use_figma", "write_stdin"}


def tool_leaf(payload: dict[str, Any]) -> str:
    name = str(payload.get("tool_name", "")).lower()
    leaf = re.split(r"__|[./:]", name)[-1]
    supported = FILE_TOOLS | OPAQUE_TOOLS | COORDINATION_TOOLS | {"apply_patch", "exec_command", "bash"}
    if leaf in supported:
        return leaf
    for candidate in sorted(supported, key=len, reverse=True):
        if leaf.endswith(("_" + candidate, "-" + candidate)):
            return candidate
    return leaf


def tool_command(payload: dict[str, Any]) -> str:
    value = payload.get("tool_input")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("command", "cmd", "input", "patch"):
            if isinstance(value.get(key), str):
                return value[key]
    return ""


def is_shell_tool(payload: dict[str, Any]) -> bool:
    return tool_leaf(payload) in {"bash", "exec_command"}


def shell_segments(command: str) -> list[list[str]] | None:
    # Expansions, redirection, and multiline scripts require explicit action scope.
    if re.search(r"[\n\r`<>]|\$[({]", command):
        return None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        segments: list[list[str]] = [[]]
        for token in lexer:
            if token and set(token) <= {";", "&", "|"}:
                segments.append([])
            else:
                segments[-1].append(token)
        return [segment for segment in segments if segment]
    except ValueError:
        return None


def git_subcommand(tokens: list[str]) -> tuple[str, list[str]] | None:
    if not tokens or Path(tokens[0]).name != "git":
        return None
    position = 1
    while position < len(tokens):
        token = tokens[position]
        if token in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
            position += 2
        elif token.startswith(("--git-dir=", "--work-tree=", "--namespace=", "--no-pager", "--no-optional-locks")):
            position += 1
        elif token.startswith("-"):
            return None
        else:
            return token, tokens[position + 1:]
    return None


def readonly_segment(tokens: list[str]) -> bool:
    executable = Path(tokens[0]).name
    if executable in READ_COMMANDS:
        # User-configured preprocessors and output paths can mutate state.
        return not any(
            token in {"--pre", "--search-zip", "-z", "--output"}
            or token.startswith(("--pre=", "--output=")) for token in tokens[1:]
        )
    if executable == "sed":
        # Limit this exception to simple line-range printing, not sed programs.
        return len(tokens) >= 4 and tokens[1] == "-n" and bool(re.fullmatch(r"\d+(?:,\d+|,\$)?p", tokens[2]))
    git = git_subcommand(tokens)
    if git:
        command, args = git
        if "-c" in tokens or any(token.startswith("--output") or token in {"--ext-diff", "--textconv"} for token in args):
            return False
        if command == "remote":
            return not args or args == ["-v"]
        if command == "worktree":
            return bool(args) and args[0] == "list"
        if command == "branch":
            return args == ["--show-current"] or bool(args) and args[0] == "--list"
        if command == "config":
            return bool(args) and args[0] in {"--get", "--get-all", "--get-regexp", "--list"}
        return command in GIT_READ_COMMANDS
    if executable in {"gh", "glab", "tea"}:
        return (len(tokens) >= 3 and tokens[1] in {"pr", "mr", "issue", "repo", "run", "release"}
                and tokens[2] in {"view", "list", "status", "checks"}
                and not any(token in {"--web", "--watch"} for token in tokens[3:]))
    if executable == "acli":
        return len(tokens) >= 4 and tokens[1:3] == ["jira", "workitem"] and tokens[3] in {"view", "search"}
    return False


def mutation_classes(payload: dict[str, Any]) -> set[str]:
    """All visible classes in a compound shell command must be authorized."""
    if not is_shell_tool(payload):
        return {"shell"} if tool_leaf(payload) in {"exec", "write_stdin"} else {"external"}
    segments = shell_segments(tool_command(payload))
    if segments is None:
        # Keep visible Git/external operations classified even inside opaque scripts.
        command = tool_command(payload)
        classes = {"shell"}
        if re.search(r"\bgit\s", command):
            classes.add("git")
        if re.search(r"\b(?:gh|glab|tea|acli)\s", command):
            classes.add("external")
        return classes
    classes = set()
    for segment in segments:
        if readonly_segment(segment):
            continue
        executable = Path(segment[0]).name
        classes.add("git" if executable == "git" else "external" if executable in {"gh", "glab", "tea", "acli", "curl", "wget"} else "shell")
    return classes


def is_mutating_tool(payload: dict[str, Any]) -> bool:
    leaf = tool_leaf(payload)
    if leaf in COORDINATION_TOOLS:
        return False
    if leaf == "write_stdin":
        value = payload.get("tool_input")
        return not isinstance(value, dict) or value.get("chars", "") not in {"", "\x03"}
    if leaf == "apply_patch" or leaf in FILE_TOOLS or leaf in OPAQUE_TOOLS:
        return True
    if is_shell_tool(payload):
        return bool(mutation_classes(payload))
    return bool(set(re.split(r"[_\W]+", leaf)) & MUTATING_VERBS)


def paths_for_tool(payload: dict[str, Any]) -> set[str]:
    leaf = tool_leaf(payload)
    if leaf == "apply_patch":
        command = tool_command(payload)
        paths = re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", command, re.MULTILINE)
        paths += re.findall(r"^\*\*\* Move to: (.+)$", command, re.MULTILINE)
        return {path.strip() for path in paths if path.strip()}
    value = payload.get("tool_input")
    if leaf in FILE_TOOLS and isinstance(value, dict):
        return {
            value[field] for field in ("path", "file_path", "source", "destination", "old_path", "new_path")
            if isinstance(value.get(field), str) and value[field]
        }
    return set()
