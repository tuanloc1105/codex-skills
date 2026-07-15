#!/usr/bin/env python3
"""Fail-closed Kafka CLI discovery, command classification, and plan hashing."""

from __future__ import annotations

import argparse
import hashlib
import json
import ntpath
import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterable, Sequence


POSIX_TOOL_SUFFIXES = ("", ".sh")
WINDOWS_TOOL_SUFFIXES = (".bat", ".cmd", ".exe", "")
SAFE_CLASSES = {"LOCAL_READ", "READ", "PREVIEW", "SENSITIVE_READ"}
KNOWN_KAFKA_TOOLS = {
    "kafka-acls",
    "kafka-broker-api-versions",
    "kafka-client-metrics",
    "kafka-cluster",
    "kafka-configs",
    "kafka-console-consumer",
    "kafka-console-producer",
    "kafka-console-share-consumer",
    "kafka-consumer-groups",
    "kafka-consumer-perf-test",
    "kafka-delegation-tokens",
    "kafka-delete-records",
    "kafka-features",
    "kafka-get-offsets",
    "kafka-groups",
    "kafka-leader-election",
    "kafka-log-dirs",
    "kafka-metadata-quorum",
    "kafka-producer-perf-test",
    "kafka-reassign-partitions",
    "kafka-server-start",
    "kafka-server-stop",
    "kafka-share-groups",
    "kafka-storage",
    "kafka-streams-application-reset",
    "kafka-topics",
    "kafka-transactions",
    "kafka-verifiable-consumer",
    "kafka-verifiable-producer",
}
SHELL_CONTROL_TOKENS = {"|", "||", "&", "&&", ";", ">", ">>", "<", "<<"}
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1f\x7f]")
BATCH_UNSAFE_PATTERN = re.compile(r"[%!^&|<>\"\x00-\x1f\x7f]")
SECRET_FLAGS = {
    "--password",
    "--secret",
    "--token",
    "--private-key",
    "--sasl-jaas-config",
    "--ssl-key-password",
    "--ssl-keystore-password",
    "--ssl-truststore-password",
}
SECRET_PATTERNS = (
    re.compile(r"(?i)(?:password|passwd|secret|token)="),
    re.compile(r"(?i)sasl\.jaas\.config="),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
MUTATION_HINT_FLAGS = {
    "--abort",
    "--add",
    "--add-controller",
    "--alter",
    "--cancel",
    "--create",
    "--delete",
    "--delete-offsets",
    "--disable",
    "--downgrade",
    "--execute",
    "--expire",
    "--force",
    "--remove",
    "--remove-controller",
    "--renew",
    "--upgrade",
    "--verify",
}
MUTATION_INPUT_FLAGS = (
    "--add-config-file",
    "--from-file",
    "--offset-json-file",
    "--path-to-json-file",
    "--payload-file",
    "--reassignment-json-file",
    "--topics-to-move-json-file",
)
FILE_PATH_FLAGS = MUTATION_INPUT_FLAGS + (
    "--command-config",
    "--config-file",
    "--consumer-config",
    "--consumer.config",
    "--producer.config",
)
MAX_HASHED_INPUT_BYTES = 100 * 1024 * 1024


def emit(payload: dict[str, Any]) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def canonical_tool(value: str) -> str:
    # Parse both separator styles so policy tests and copied approval surfaces
    # remain stable even when they are inspected on a different host OS.
    name = min(
        (ntpath.basename(value), posixpath.basename(value)),
        key=len,
    ).lower()
    for suffix in (".sh", ".bat", ".cmd", ".exe"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _platform_name(platform: str | None = None) -> str:
    return platform or os.name


def _tool_suffixes(platform: str | None = None) -> tuple[str, ...]:
    return WINDOWS_TOOL_SUFFIXES if _platform_name(platform) == "nt" else POSIX_TOOL_SUFFIXES


def _is_absolute_path(value: str, platform: str | None = None) -> bool:
    if _platform_name(platform) == "nt":
        return PureWindowsPath(value).is_absolute()
    return PurePosixPath(value).is_absolute()


def _is_batch_script(value: str | Path) -> bool:
    return str(value).lower().endswith((".bat", ".cmd"))


def _batch_unsafe_token(values: Sequence[str]) -> int | None:
    for index, value in enumerate(values):
        if not value or BATCH_UNSAFE_PATTERN.search(value):
            return index
    return None


def _cmd_batch_line(binary: str | Path, args: Sequence[str]) -> str:
    tokens = [str(binary), *args]
    unsafe_index = _batch_unsafe_token(tokens)
    if unsafe_index is not None:
        location = "binary path" if unsafe_index == 0 else f"argument {unsafe_index}"
        problem = "empty token" if not tokens[unsafe_index] else "unsafe cmd.exe metacharacter"
        raise ValueError(f"{problem} in {location}")
    quoted = " ".join(f'"{token}"' for token in tokens)
    return f'"{quoted}"'


def _is_runnable(path: Path, platform: str | None = None) -> bool:
    if not path.is_file():
        return False
    if _platform_name(platform) == "nt":
        return True
    return os.access(path, os.X_OK)


def _find_all_in_dir(bin_dir: Path, tool: str, platform: str | None = None) -> list[Path]:
    canonical = canonical_tool(tool)
    result: list[Path] = []
    seen: set[str] = set()
    for suffix in _tool_suffixes(platform):
        candidate = bin_dir / f"{canonical}{suffix}"
        if _is_runnable(candidate, platform):
            resolved = candidate.resolve()
            marker = os.path.normcase(str(resolved))
            if marker not in seen:
                seen.add(marker)
                result.append(resolved)
    return result


def _candidate_dirs(explicit_bin: str | None, platform: str | None = None) -> list[Path]:
    raw_dirs: list[Path] = []
    if explicit_bin:
        raw_dirs.append(Path(explicit_bin).expanduser())
    else:
        kafka_home = os.environ.get("KAFKA_HOME")
        if kafka_home:
            home = Path(kafka_home).expanduser()
            if _platform_name(platform) == "nt":
                raw_dirs.append(home / "bin" / "windows")
            raw_dirs.append(home / "bin")
        raw_dirs.extend(Path(entry).expanduser() for entry in os.environ.get("PATH", "").split(os.pathsep) if entry)

    result: list[Path] = []
    seen: set[str] = set()
    for path in raw_dirs:
        resolved = path.resolve()
        marker = os.path.normcase(str(resolved))
        if marker not in seen:
            seen.add(marker)
            result.append(resolved)
    return result


def _checked_location_fields(paths: Sequence[Path]) -> dict[str, Any]:
    limit = 10
    return {
        "checked_locations": [str(path) for path in paths[:limit]],
        "checked_location_count": len(paths),
        "checked_locations_truncated": max(0, len(paths) - limit),
    }


def _windows_system_cmd() -> str:
    import ctypes

    buffer_size = 32_768
    buffer = ctypes.create_unicode_buffer(buffer_size)
    length = ctypes.windll.kernel32.GetSystemDirectoryW(buffer, buffer_size)
    if length <= 0 or length >= buffer_size:
        raise OSError("cannot resolve the trusted Windows system directory")
    command_interpreter = (Path(buffer.value) / "cmd.exe").resolve(strict=True)
    if not command_interpreter.is_file():
        raise OSError("trusted Windows command interpreter is missing")
    return str(command_interpreter)


def _version_command(
    binary: Path,
    platform: str | None = None,
    command_interpreter: str | None = None,
) -> list[str]:
    if _platform_name(platform) == "nt" and _is_batch_script(binary):
        return [
            command_interpreter or _windows_system_cmd(),
            "/d",
            "/s",
            "/c",
            _cmd_batch_line(binary, ["--version"]),
        ]
    return [str(binary), "--version"]


def _first_clean_line(value: str) -> str:
    ansi = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
    for line in value.splitlines():
        clean = ansi.sub("", line).strip()
        if clean:
            return clean[:300]
    return ""


def preflight(required: Sequence[str], explicit_bin: str | None = None) -> dict[str, Any]:
    if explicit_bin and not _is_absolute_path(explicit_bin):
        return {
            "status": "blocked",
            "reason": "invalid_kafka_bin",
            "detail": "--kafka-bin must be an absolute path",
        }
    checked_dirs = _candidate_dirs(explicit_bin)
    checked_fields = _checked_location_fields(checked_dirs)
    anchors: dict[str, Path] = {}
    for bin_dir in checked_dirs:
        for anchor in _find_all_in_dir(bin_dir, "kafka-topics"):
            anchors[os.path.normcase(str(anchor))] = anchor

    if not anchors:
        return {
            "status": "blocked",
            "reason": "missing_cli",
            "missing": ["kafka-topics"],
            **checked_fields,
        }
    if len(anchors) > 1:
        return {
            "status": "blocked",
            "reason": "ambiguous_cli",
            "candidates": sorted(str(path) for path in anchors.values()),
            **checked_fields,
        }

    anchor = next(iter(anchors.values()))
    bin_dir = anchor.parent
    normalized_required: list[str] = []
    for item in required or ["kafka-topics"]:
        name = canonical_tool(item)
        if not re.fullmatch(r"kafka-[a-z0-9-]+", name):
            return {"status": "blocked", "reason": "invalid_required_tool", "tool": name}
        if name not in normalized_required:
            normalized_required.append(name)
    if "kafka-topics" not in normalized_required:
        normalized_required.insert(0, "kafka-topics")

    tools: dict[str, str] = {}
    missing: list[str] = []
    for name in normalized_required:
        found = _find_all_in_dir(bin_dir, name)
        if not found:
            missing.append(name)
        elif len(found) > 1:
            return {
                "status": "blocked",
                "reason": "ambiguous_cli",
                "bin_dir": str(bin_dir),
                "tool": name,
                "candidates": sorted(str(path) for path in found),
            }
        else:
            tools[name] = str(found[0])
    if missing:
        return {
            "status": "blocked",
            "reason": "missing_required_tools",
            "bin_dir": str(bin_dir),
            "missing": missing,
            "tools": tools,
        }

    try:
        version_command = _version_command(anchor)
        completed = subprocess.run(
            version_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        return {
            "status": "blocked",
            "reason": "unusable_cli",
            "bin_dir": str(bin_dir),
            "detail": str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
        }
    version = _first_clean_line(f"{completed.stdout}\n{completed.stderr}")
    if completed.returncode != 0 or not version:
        return {
            "status": "blocked",
            "reason": "unusable_cli",
            "bin_dir": str(bin_dir),
            "exit_code": completed.returncode,
            "detail": version or "version check returned no output",
        }
    return {
        "status": "ready",
        "reason": "ok",
        "platform": "windows" if os.name == "nt" else "posix",
        "script_family": anchor.suffix.lower() or "native",
        "bin_dir": str(bin_dir),
        "version": version,
        "tools": tools,
    }


def _present(args: Sequence[str], flag: str) -> bool:
    return any(arg == flag or arg.startswith(f"{flag}=") for arg in args)


def _value_after(args: Sequence[str], flag: str) -> str | None:
    value: str | None = None
    for index, arg in enumerate(args):
        if arg.startswith(f"{flag}="):
            value = arg.split("=", 1)[1]
        elif arg == flag and index + 1 < len(args):
            value = args[index + 1]
    return value


def _consumer_properties(args: Sequence[str]) -> dict[str, str]:
    properties: dict[str, str] = {}
    for index, arg in enumerate(args):
        raw: str | None = None
        if arg.startswith("--consumer-property="):
            raw = arg.split("=", 1)[1]
        elif arg == "--consumer-property" and index + 1 < len(args):
            raw = args[index + 1]
        if raw and "=" in raw:
            key, value = raw.split("=", 1)
            properties[key.strip().lower()] = value.strip().lower()
    return properties


def _has_inline_secret(args: Sequence[str]) -> bool:
    for index, arg in enumerate(args):
        flag = arg.split("=", 1)[0].lower()
        if flag in SECRET_FLAGS:
            return True
        if index > 0 and args[index - 1].split("=", 1)[0].lower() in SECRET_FLAGS:
            return True
        if any(pattern.search(arg) for pattern in SECRET_PATTERNS):
            return True
    return False


def _relative_file_flag(args: Sequence[str], tool: str, platform: str | None = None) -> str | None:
    for flag in FILE_PATH_FLAGS:
        value = _value_after(args, flag)
        if value and not _is_absolute_path(value, platform):
            return flag
    if tool == "kafka-storage":
        for flag in ("-c", "--config"):
            value = _value_after(args, flag)
            if value and not _is_absolute_path(value, platform):
                return flag
    if tool == "kafka-server-start":
        config_path = _server_start_config(args)
        if config_path and not _is_absolute_path(config_path, platform):
            return "positional server config"
    return None


def _classification(
    kind: str,
    tool: str,
    action: str,
    reason: str,
    risk: str = "none",
) -> dict[str, Any]:
    return {
        "classification": kind,
        "tool": tool,
        "action": action,
        "risk": risk,
        "reason": reason,
        "requires_mutation_confirmation": kind == "MUTATION",
        "requires_sensitive_read_request": kind == "SENSITIVE_READ",
        "recognized": kind != "UNKNOWN",
    }


def _single_read_action(args: Sequence[str], actions: Sequence[str]) -> str | None:
    present = [flag for flag in actions if _present(args, flag)]
    return present[0] if len(present) == 1 else None


def _classify_console_consumer(tool: str, args: Sequence[str]) -> dict[str, Any]:
    if _present(args, "--group") or _present(args, "--group-id"):
        return _classification(
            "MUTATION",
            tool,
            "consume-with-group",
            "consumer group membership or committed offsets can change cluster state",
            "standard",
        )
    properties = _consumer_properties(args)
    if properties.get("enable.auto.commit") not in {None, "false"}:
        return _classification("MUTATION", tool, "consume-with-auto-commit", "offset commits can change group state", "standard")

    required_flags = ("--topic", "--partition", "--offset", "--max-messages", "--timeout-ms")
    missing = [flag for flag in required_flags if _value_after(args, flag) is None]
    if missing:
        return _classification("UNKNOWN", tool, "consume", f"missing bounded direct-read flags: {', '.join(missing)}")
    if _present(args, "--from-beginning"):
        return _classification("UNKNOWN", tool, "consume", "--from-beginning is not allowed by the bounded direct-read policy")
    if properties.get("enable.auto.commit") != "false":
        return _classification("UNKNOWN", tool, "consume", "require explicit enable.auto.commit=false")
    if properties.get("allow.auto.create.topics") != "false":
        return _classification("UNKNOWN", tool, "consume", "require explicit allow.auto.create.topics=false")
    try:
        max_messages = int(_value_after(args, "--max-messages") or "")
        timeout_ms = int(_value_after(args, "--timeout-ms") or "")
        partition = int(_value_after(args, "--partition") or "")
    except ValueError:
        return _classification("UNKNOWN", tool, "consume", "partition, max-messages, and timeout-ms must be integers")
    if not 1 <= max_messages <= 100:
        return _classification("UNKNOWN", tool, "consume", "max-messages must be between 1 and 100")
    if not 1 <= timeout_ms <= 60_000:
        return _classification("UNKNOWN", tool, "consume", "timeout-ms must be between 1 and 60000")
    if partition < 0:
        return _classification("UNKNOWN", tool, "consume", "partition must be non-negative")
    return _classification(
        "SENSITIVE_READ",
        tool,
        "bounded-direct-consume",
        "direct partition read is bounded and disables commits and topic auto-creation",
        "sensitive",
    )


def _classify_command(command: Sequence[str], platform: str | None = None) -> dict[str, Any]:
    argv = list(command)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        return _classification("UNKNOWN", "", "", "missing command")
    if any(not arg for arg in argv):
        return _classification("UNKNOWN", canonical_tool(argv[0]), "", "empty token in argv is not allowed")
    if any(arg in SHELL_CONTROL_TOKENS or CONTROL_CHAR_PATTERN.search(arg) for arg in argv):
        return _classification("UNKNOWN", canonical_tool(argv[0]), "", "shell control tokens are not allowed")
    if _platform_name(platform) == "nt" and any('"' in arg for arg in argv):
        return _classification(
            "UNKNOWN",
            canonical_tool(argv[0]),
            "",
            "embedded quotes cannot be transported losslessly by the supported Windows PowerShell boundary",
        )
    if _has_inline_secret(argv[1:]):
        return _classification("UNKNOWN", canonical_tool(argv[0]), "", "inline secret-like argument detected")

    tool = canonical_tool(argv[0])
    args = argv[1:]
    if not _is_absolute_path(argv[0], platform):
        return _classification("UNKNOWN", tool, "", "Kafka binary path must be absolute")
    if _is_batch_script(argv[0]):
        unsafe_index = _batch_unsafe_token(argv)
        if unsafe_index is not None:
            location = "binary path" if unsafe_index == 0 else f"argument {unsafe_index}"
            problem = "empty token" if not argv[unsafe_index] else "unsafe cmd.exe metacharacter"
            return _classification(
                "UNKNOWN",
                tool,
                "",
                f"{problem} in {location}; native Windows batch execution must fail closed",
            )
    if not tool.startswith("kafka-"):
        return _classification("UNKNOWN", tool, "", "executable is not an Apache Kafka CLI")
    if tool not in KNOWN_KAFKA_TOOLS:
        return _classification("UNKNOWN", tool, "", "Kafka CLI is not on the recognized tool allowlist")
    relative_file_flag = _relative_file_flag(args, tool, platform)
    if relative_file_flag:
        return _classification("UNKNOWN", tool, "", f"{relative_file_flag} must use an absolute path")
    if tool in {"kafka-server-start", "kafka-server-stop"}:
        return _classification("MUTATION", tool, "server-lifecycle", "broker lifecycle scripts may ignore help/version flags", "high")
    if args and all(arg in {"--help", "-h", "--version"} for arg in args):
        return _classification("LOCAL_READ", tool, "help-or-version", "local help/version invocation")

    if tool == "kafka-console-consumer":
        return _classify_console_consumer(tool, args)
    if tool in {"kafka-console-producer", "kafka-producer-perf-test", "kafka-verifiable-producer"}:
        return _classification("MUTATION", tool, "produce-records", "producer tools write records", "high")
    if tool in {"kafka-consumer-perf-test", "kafka-verifiable-consumer", "kafka-console-share-consumer"}:
        return _classification("UNKNOWN", tool, "consume", "consumer tool can change group/share-group state and is not safely bounded")
    if tool == "kafka-topics":
        if _present(args, "--delete"):
            return _classification("MUTATION", tool, "delete-topic", "topic deletion changes cluster state and can destroy data", "high")
        if _present(args, "--alter"):
            return _classification("MUTATION", tool, "alter-topic", "topic alteration changes partition or topic state", "high")
        if _present(args, "--create"):
            return _classification("MUTATION", tool, "create-topic", "topic creation changes cluster state", "standard")
        action = _single_read_action(args, ("--list", "--describe"))
        if action:
            return _classification("READ", tool, action.removeprefix("--"), "recognized topic metadata read")
    elif tool == "kafka-configs":
        if _present(args, "--alter"):
            return _classification("MUTATION", tool, "alter-config", "dynamic configuration changes runtime behavior", "high")
        if _present(args, "--describe"):
            return _classification("READ", tool, "describe-config", "recognized config read")
    elif tool in {"kafka-consumer-groups", "kafka-share-groups"}:
        if _present(args, "--delete") or _present(args, "--delete-offsets"):
            return _classification("MUTATION", tool, "delete-group-or-offsets", "group or offset state will be deleted", "high")
        if _present(args, "--reset-offsets"):
            if _present(args, "--execute"):
                return _classification("MUTATION", tool, "execute-offset-reset", "committed offsets will change", "high")
            return _classification("PREVIEW", tool, "preview-offset-reset", "offset reset without --execute is a preview")
        action = _single_read_action(args, ("--list", "--describe"))
        if action:
            return _classification("READ", tool, action.removeprefix("--"), "recognized group metadata read")
    elif tool == "kafka-groups":
        if _present(args, "--list"):
            return _classification("READ", tool, "list-groups", "recognized group inventory read")
    elif tool == "kafka-acls":
        if _present(args, "--add") or _present(args, "--remove"):
            return _classification("MUTATION", tool, "alter-acls", "ACL state will change", "high")
        if _present(args, "--list"):
            return _classification("SENSITIVE_READ", tool, "list-acls", "ACL output exposes security policy", "sensitive")
    elif tool == "kafka-reassign-partitions":
        if _present(args, "--execute") or _present(args, "--cancel"):
            return _classification("MUTATION", tool, "change-reassignment", "partition assignment or throttle state will change", "high")
        if _present(args, "--verify"):
            return _classification("MUTATION", tool, "verify-reassignment", "verify can clear reassignment throttles", "high")
        if _present(args, "--generate"):
            return _classification("PREVIEW", tool, "generate-reassignment", "candidate assignment generation does not execute it")
    elif tool == "kafka-log-dirs":
        if _present(args, "--alter"):
            return _classification("MUTATION", tool, "alter-log-dirs", "replica log directory placement will change", "high")
        if _present(args, "--describe"):
            return _classification("READ", tool, "describe-log-dirs", "recognized log directory metadata read")
    elif tool == "kafka-delegation-tokens":
        if any(_present(args, flag) for flag in ("--create", "--renew", "--expire")):
            return _classification("MUTATION", tool, "alter-delegation-token", "delegation token state will change", "high")
        if _present(args, "--describe"):
            return _classification("SENSITIVE_READ", tool, "describe-delegation-token", "token metadata is security-sensitive", "sensitive")
    elif tool == "kafka-transactions":
        if _present(args, "--abort"):
            return _classification("MUTATION", tool, "abort-transaction", "transaction state will change", "high")
        action = _single_read_action(args, ("--list", "--describe"))
        if action:
            return _classification("SENSITIVE_READ", tool, action.removeprefix("--"), "transactional IDs are sensitive metadata", "sensitive")
    elif tool == "kafka-features":
        if any(_present(args, flag) for flag in ("--upgrade", "--downgrade", "--disable")):
            return _classification("MUTATION", tool, "alter-features", "cluster feature levels will change", "high")
        if _present(args, "--describe"):
            return _classification("READ", tool, "describe-features", "recognized feature metadata read")
    elif tool == "kafka-client-metrics":
        if _present(args, "--alter") or _present(args, "--delete"):
            return _classification("MUTATION", tool, "alter-client-metrics", "client metrics configuration will change", "standard")
        if _present(args, "--describe"):
            return _classification("READ", tool, "describe-client-metrics", "recognized client metrics config read")
    elif tool == "kafka-metadata-quorum":
        if _present(args, "--add-controller") or _present(args, "--remove-controller"):
            return _classification("MUTATION", tool, "alter-controller", "metadata quorum membership will change", "high")
        if _present(args, "--describe"):
            return _classification("READ", tool, "describe-metadata-quorum", "recognized quorum metadata read")
    elif tool == "kafka-cluster":
        lowered = {arg.lower() for arg in args}
        if "unregister" in lowered:
            return _classification("MUTATION", tool, "unregister-broker", "broker registration will be removed", "high")
        if "cluster-id" in lowered or _present(args, "--cluster-id"):
            return _classification("READ", tool, "cluster-id", "recognized cluster identity read")
    elif tool in {"kafka-get-offsets", "kafka-broker-api-versions"}:
        return _classification("READ", tool, "query", "recognized query-only Kafka CLI")
    elif tool == "kafka-leader-election":
        return _classification("MUTATION", tool, "leader-election", "partition leadership can change", "high")
    elif tool == "kafka-delete-records":
        return _classification("MUTATION", tool, "delete-records", "records will be deleted", "high")
    elif tool == "kafka-streams-application-reset":
        if _present(args, "--dry-run"):
            return _classification("PREVIEW", tool, "preview-streams-reset", "explicit dry-run previews the reset")
        return _classification("MUTATION", tool, "reset-streams-application", "offsets and internal topics can change", "high")
    elif tool == "kafka-storage":
        lowered = {arg.lower() for arg in args}
        if "format" in lowered:
            return _classification("MUTATION", tool, "format-storage", "local Kafka storage will be formatted", "high")
        if "info" in lowered:
            return _classification("SENSITIVE_READ", tool, "storage-info", "local storage metadata can expose deployment details", "sensitive")
        if "random-uuid" in lowered:
            return _classification("LOCAL_READ", tool, "random-uuid", "generates a local identifier without changing Kafka state")
    return _classification("UNKNOWN", tool, "", "tool/action combination is not on the allowlist")


def classify(command: Sequence[str], platform: str | None = None) -> dict[str, Any]:
    argv = list(command)
    if argv and argv[0] == "--":
        argv = argv[1:]
    result = _classify_command(argv, platform)
    if result["classification"] in SAFE_CLASSES and argv:
        args = argv[1:]
        unexpected = sorted(flag for flag in MUTATION_HINT_FLAGS if _present(args, flag))
        if unexpected:
            return _classification(
                "UNKNOWN",
                result["tool"],
                result["action"],
                f"safe action contains unexpected mutation-like flags: {', '.join(unexpected)}",
            )
    return result


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            if size > MAX_HASHED_INPUT_BYTES:
                raise ValueError(f"input file exceeds {MAX_HASHED_INPUT_BYTES} bytes")
            digest.update(chunk)
    return digest.hexdigest(), size


def _server_start_config(args: Sequence[str]) -> str | None:
    for arg in args:
        if arg in {"-daemon", "--daemon"}:
            continue
        if arg.startswith("-"):
            continue
        return arg
    return None


def _referenced_mutation_inputs(argv: Sequence[str]) -> list[str]:
    referenced = [value for flag in FILE_PATH_FLAGS if (value := _value_after(argv, flag))]
    tool = canonical_tool(argv[0]) if argv else ""
    if tool == "kafka-storage":
        for flag in ("-c", "--config"):
            value = _value_after(argv, flag)
            if value:
                referenced.append(value)
    if tool == "kafka-server-start":
        config_path = _server_start_config(argv[1:])
        if not config_path:
            raise ValueError("kafka-server-start requires an absolute positional server config")
        referenced.append(config_path)
    return referenced


def build_plan(
    cluster_id: str,
    environment: str,
    kafka_version: str,
    command: Sequence[str],
    input_files: Iterable[str],
) -> dict[str, Any]:
    argv = list(command)
    if argv and argv[0] == "--":
        argv = argv[1:]
    classification = classify(argv)
    if classification["classification"] != "MUTATION":
        raise ValueError(f"plan requires MUTATION classification, got {classification['classification']}")
    if not cluster_id.strip() or any(char in cluster_id for char in "\r\n\x00"):
        raise ValueError("cluster-id must be a non-empty single-line value")
    if not environment.strip() or any(char in environment for char in "\r\n\x00"):
        raise ValueError("environment must be a non-empty single-line value")
    if not kafka_version.strip() or any(char in kafka_version for char in "\r\n\x00"):
        raise ValueError("kafka-version must be a non-empty single-line value")

    inputs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_path in input_files:
        if not _is_absolute_path(raw_path):
            raise ValueError(f"--input-file must be absolute: {raw_path}")
        path = Path(raw_path).resolve(strict=True)
        if not path.is_file():
            raise ValueError(f"input is not a regular file: {path}")
        marker = os.path.normcase(str(path))
        if marker in seen:
            continue
        seen.add(marker)
        digest, size = _hash_file(path)
        inputs.append({"path": str(path), "sha256": digest, "size": size})

    pinned_inputs = {os.path.normcase(item["path"]) for item in inputs}
    referenced_pins: set[str] = set()
    missing_pins: list[str] = []
    for raw_path in _referenced_mutation_inputs(argv):
        if not _is_absolute_path(raw_path):
            raise ValueError(f"referenced mutation input must be absolute: {raw_path}")
        referenced = Path(raw_path).resolve(strict=True)
        referenced_marker = os.path.normcase(str(referenced))
        referenced_pins.add(referenced_marker)
        if referenced_marker not in pinned_inputs:
            missing_pins.append(str(referenced))
    if missing_pins:
        raise ValueError(f"referenced mutation inputs must be passed via --input-file: {', '.join(missing_pins)}")
    if canonical_tool(argv[0]) == "kafka-console-producer":
        payload_inputs = pinned_inputs - referenced_pins
        if len(payload_inputs) != 1:
            raise ValueError(
                "kafka-console-producer requires exactly one exact payload file passed via --input-file "
                "in addition to command-referenced files"
            )

    surface = {
        "cluster_id": cluster_id.strip(),
        "environment": environment.strip(),
        "kafka_version": kafka_version.strip(),
        "argv": argv,
        "inputs": inputs,
    }
    canonical = json.dumps(surface, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    change_id = hashlib.sha256(canonical).hexdigest()[:12]
    command_hash = hashlib.sha256(
        json.dumps(argv, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if classification["risk"] == "high":
        confirmation = f"XÁC NHẬN KAFKA NGUY HIỂM {cluster_id.strip()} {change_id}"
    else:
        confirmation = f"XÁC NHẬN KAFKA {change_id}"
    return {
        "status": "planned",
        "change_id": change_id,
        "command_sha256": command_hash,
        "classification": classification,
        "cluster_id": cluster_id.strip(),
        "environment": environment.strip(),
        "kafka_version": kafka_version.strip(),
        "argv": argv,
        "inputs": inputs,
        "confirmation_phrase": confirmation,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    preflight_parser = subparsers.add_parser("preflight", help="Locate and validate an Apache Kafka CLI installation")
    preflight_parser.add_argument("--require", action="append", default=[], help="Required canonical tool name; repeat as needed")
    preflight_parser.add_argument("--kafka-bin", help="Explicit absolute Kafka bin directory")

    classify_parser = subparsers.add_parser("classify", help="Classify an exact Kafka CLI argv")
    classify_parser.add_argument("command", nargs=argparse.REMAINDER)

    plan_parser = subparsers.add_parser("plan", help="Fingerprint an exact mutation approval surface")
    plan_parser.add_argument("--cluster-id", required=True)
    plan_parser.add_argument("--environment", required=True)
    plan_parser.add_argument("--kafka-version", required=True)
    plan_parser.add_argument("--input-file", action="append", default=[])
    plan_parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.subcommand == "preflight":
        payload = preflight(args.require, args.kafka_bin)
        emit(payload)
        return 0 if payload["status"] == "ready" else 2
    if args.subcommand == "classify":
        payload = classify(args.command)
        emit(payload)
        if payload["classification"] in SAFE_CLASSES:
            return 0
        return 10 if payload["classification"] == "MUTATION" else 20
    try:
        payload = build_plan(args.cluster_id, args.environment, args.kafka_version, args.command, args.input_file)
    except (OSError, ValueError) as exc:
        emit({"status": "blocked", "reason": str(exc)})
        return 2
    emit(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
