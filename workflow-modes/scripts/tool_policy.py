"""Conservative tool classification, not a sandbox or proof of side effects."""

from __future__ import annotations

from pathlib import Path
import re
import shlex
from typing import Any

from readonly_commands import (readonly_date, readonly_encoding, readonly_find,
                               readonly_jq, readonly_sed, readonly_sort, readonly_uniq)

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
READ_COMMANDS = {
    "cat", "head", "tail", "wc", "pwd", "ls", "grep", "diff", "stat", "which", "type",
    "true", "false", "echo", "nl", "tac", "cut", "tr", "paste", "join", "comm", "cmp",
    "fold", "fmt", "expand", "unexpand", "od", "cksum", "md5sum", "sha1sum", "sha224sum",
    "sha256sum", "sha384sum", "sha512sum", "shasum", "readlink", "realpath", "basename",
    "dirname", "du", "df", "id", "groups", "whoami", "uname", "arch", "nproc", "printenv",
    "test", "[", "seq", "ps", "uptime",
}
ARGUMENT_READERS = {
    "sort": readonly_sort, "uniq": readonly_uniq, "base32": readonly_encoding,
    "base64": readonly_encoding, "jq": readonly_jq, "find": readonly_find,
    "date": readonly_date, "sed": readonly_sed,
}
GIT_READ_COMMANDS = {
    "status", "diff", "log", "show", "rev-parse", "ls-files", "ls-tree", "check-ignore",
    "merge-base", "remote", "blame", "annotate", "shortlog", "describe", "rev-list",
    "for-each-ref", "count-objects", "cat-file", "diff-files", "diff-index", "diff-tree",
}
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
    # Split only unquoted operators. Literal patterns (including >, $, and |)
    # must not be confused with shell syntax. Unsupported syntax stays opaque.
    parts: list[str] = []
    current: list[str] = []
    quote = ""
    position = 0
    while position < len(command):
        char = command[position]
        if char == "\\" and quote != "'":
            if position + 1 == len(command):
                return None
            following = command[position + 1]
            if following != "\n":
                current.extend((char, following))
            position += 2
            continue
        if quote:
            if char == quote:
                quote = ""
            elif quote == '"' and char in "$`":
                return None
        elif char in "'\"":
            quote = char
        elif char in "$`<>(){}#\r":
            return None
        elif char in ";&|\n":
            parts.append("".join(current))
            current = []
            position += 1
            continue
        current.append(char)
        position += 1
    if quote:
        return None
    parts.append("".join(current))
    try:
        return [tokens for part in parts if (tokens := shlex.split(part))]
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
        elif token in {"--no-pager", "--no-optional-locks", "--literal-pathspecs"} or token.startswith(("--git-dir=", "--work-tree=", "--namespace=")):
            position += 1
        elif token.startswith("-"):
            return None
        else:
            return token, tokens[position + 1:]
    return None


def readonly_segment(tokens: list[str]) -> bool:
    executable = Path(tokens[0]).name
    if executable in ARGUMENT_READERS:
        return ARGUMENT_READERS[executable](tokens[1:])
    if executable in READ_COMMANDS:
        return True
    if executable in {"rg", "file"}:
        # Preprocessors, decompression helpers, and compiled magic databases.
        return not any(
            token.split("=", 1)[0] in {"--pre", "--search-zip", "--uncompress", "--uncompress-noreport", "--compile"}
            or (token.startswith("-") and not token.startswith("--")
                and any(flag in token[1:] for flag in ("z" if executable == "rg" else "zZC")))
            for token in tokens[1:]
        )
    if executable == "printf":
        args = tokens[1:]
        if args[:1] == ["--"]:
            args = args[1:]
        # Shell printf can assign variables via -v or %n. Only stdout forms
        # with simple string/numeric formats are recognized here.
        return bool(args) and not args[0].startswith("-") and bool(re.fullmatch(
            r"(?:[^%]|%%|%[-+ #0]*\d*(?:\.\d+)?[sdbouxXfFeEgGc])*", args[0]
        ))
    git = git_subcommand(tokens)
    if git:
        command, args = git
        if "-c" in tokens or any(token.startswith("--output") or token.split("=", 1)[0] in {"--ext-diff", "--textconv", "--filters"} for token in args):
            return False
        if command == "remote":
            return not args or args == ["-v"]
        if command == "worktree":
            return bool(args) and args[0] == "list"
        if command == "branch":
            return args == ["--show-current"] or (bool(args) and args[0] == "--list"
                and all(not arg.startswith("-") for arg in args[1:]))
        if command == "config":
            return (args == ["--list"] or len(args) == 2 and args[0] in {"--get", "--get-all", "--get-regexp"}
                    and not args[1].startswith("-"))
        if command == "stash":
            return bool(args) and args[0] in {"list", "show"}
        if command == "tag":
            return not args or (args[0] in {"-l", "--list"} and all(not arg.startswith("-") for arg in args[1:]))
        if command == "symbolic-ref":
            return len(args) == 1 and not args[0].startswith("-")
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


def classification_detail(payload: dict[str, Any]) -> str:
    """Explain uncertainty without copying command arguments into diagnostics."""
    if not is_shell_tool(payload):
        return " Tool contents are not inspectable as a direct shell command."
    segments = shell_segments(tool_command(payload))
    if segments is None:
        return " Shell syntax is unsupported (expansion, redirection, grouping, comments, or invalid quoting)."
    names = sorted({Path(segment[0]).name for segment in segments if not readonly_segment(segment)})
    names = [re.sub(r"[^a-zA-Z0-9_.-]", "?", name)[:40] for name in names[:5]]
    return " Commands/options not recognized as read-only: " + ", ".join(names) + "."


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
