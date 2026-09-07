#!/usr/bin/env python3
"""Emit a workflow-mode lifecycle control call for the plugin hook to observe."""

from __future__ import annotations

import argparse
import json
import shlex
import sys


MARKER = "workflow-modes-v1"


class ControlError(ValueError):
    pass


class ControlHelp(Exception):
    pass


def shell_arguments(command: str, windows: bool = False) -> list[str]:
    """Accept literal standalone argv only; never evaluate shell expressions.

    Windows output uses PowerShell's call operator and single-quoted literals.
    Also accept the simple double-quoted native argv used by existing callers.
    """
    if "\n" in command or "\r" in command:
        raise ControlError("Run one lifecycle command without line breaks.")
    if windows:
        text = command.strip()
        if text.startswith("& "):
            text = text[2:].lstrip()
        tokens = []
        i = 0
        while i < len(text):
            if text[i].isspace():
                i += 1
                continue
            token = ""
            quote = text[i] if text[i] in "\"'" else None
            if quote:
                i += 1
                while i < len(text):
                    if text[i] == quote:
                        if quote == "'" and i + 1 < len(text) and text[i + 1] == "'":
                            token += "'"
                            i += 2
                            continue
                        i += 1
                        break
                    if quote == '"' and text[i] in "$`":
                        raise ControlError("Use literal single-quoted arguments, without interpolation.")
                    token += text[i]
                    i += 1
                else:
                    raise ControlError("Unclosed shell quote.")
                if i < len(text) and not text[i].isspace():
                    raise ControlError("Separate each quoted argument with whitespace.")
            else:
                while i < len(text) and not text[i].isspace():
                    if text[i] in ";&|<>()$`%\"'":
                        raise ControlError("Run a standalone lifecycle command with literal arguments.")
                    token += text[i]
                    i += 1
            tokens.append(token)
        return tokens
    # shlex preserves literal operators inside quotes but does not identify
    # expansion. Check expansion separately before discarding quoting syntax.
    quote = None
    escaped = False
    for character in command:
        if escaped:
            escaped = False
            continue
        if quote == "'":
            if character == "'":
                quote = None
            continue
        if character == "\\":
            escaped = True
            continue
        if character in "$`" or (quote is None and character in ";&|<>()"):
            raise ControlError("Run a standalone lifecycle command without shell expansion or operators.")
        if quote == '"':
            if character == '"':
                quote = None
        elif character in "\"'":
            quote = character
    try:
        return shlex.split(command, posix=True)
    except ValueError as error:
        raise ControlError(str(error)) from error


class ControlParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs["allow_abbrev"] = False
        super().__init__(*args, **kwargs)

    def error(self, message):
        raise ControlError(message)

    def exit(self, status=0, message=None):
        if status:
            raise ControlError(message or "invalid arguments")
        raise ControlHelp()

    def print_help(self, file=None):
        raise ControlHelp(self.format_help())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = ControlParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    activate = subparsers.add_parser("activate")
    activate.add_argument("mode", choices=("discuss", "plan", "execute"))
    activate.add_argument("--record")
    activate.add_argument("--marker", required=True)

    transition = subparsers.add_parser("transition")
    transition.add_argument("mode", choices=("discuss", "plan", "execute"))
    transition.add_argument("--record", required=True)
    transition.add_argument("--user-authorized", action="store_true",
                            help="Attest to explicit user permission for plan revision; only for transition discuss.")
    transition.add_argument("--marker", required=True)

    plan_init = subparsers.add_parser("plan-init")
    plan_init.add_argument("--record", required=True)
    plan_init.add_argument("--target", required=True)
    plan_init.add_argument("--marker", required=True)

    action_open = subparsers.add_parser("action-open")
    action_open.add_argument("--record", required=True)
    action_open.add_argument("--evidence-id")
    action_open.add_argument("--path", action="append", default=[])
    action_open.add_argument(
        "--unscoped", action="append", choices=("git", "external", "shell"), default=[]
    )
    action_open.add_argument(
        "--impact", choices=("non-source", "source-confirmed"), required=True
    )
    action_open.add_argument("--marker", required=True)

    action_close = subparsers.add_parser("action-close")
    action_close.add_argument("--result", choices=("completed", "failed", "blocked"), required=True)
    action_close.add_argument("--marker", required=True)

    action_abort = subparsers.add_parser("action-abort")
    action_abort.add_argument("--reason", choices=("record-unreadable",), required=True)
    action_abort.add_argument("--marker", required=True)

    sync = subparsers.add_parser("sync")
    sync.add_argument("--record", required=True)
    sync.add_argument("--scope", choices=("record", "snapshot"), default="record")
    sync.add_argument("--marker", required=True)

    rules_sync = subparsers.add_parser("rules-sync")
    rules_sync.add_argument("--record", required=True)
    rules_sync.add_argument("--reference", action="append", default=[])
    rules_sync.add_argument("--marker", required=True)

    write_open = subparsers.add_parser("write-open")
    write_open.add_argument("--record", required=True)
    write_open.add_argument("--previous-revision", required=True)
    write_open.add_argument("--path", action="append", default=[])
    write_open.add_argument("--recover", action="store_true")
    write_open.add_argument("--observed-revision")
    write_open.add_argument("--marker", required=True)

    write_close = subparsers.add_parser("write-close")
    write_close.add_argument("--record", required=True)
    write_close.add_argument("--marker", required=True)

    checkpoint = subparsers.add_parser("checkpoint")
    checkpoint.add_argument("--record", required=True)
    checkpoint.add_argument("--no-change", action="store_true")
    checkpoint.add_argument("--marker", required=True)

    subparsers.add_parser("snapshot").add_argument("--marker", required=True)
    subparsers.add_parser("deactivate").add_argument("--marker", required=True)
    diagnose = subparsers.add_parser("diagnose", help="Read-only bundle diagnostics; no session database is opened.")
    diagnose.add_argument("--record", required=True)
    diagnose.add_argument("--json", action="store_true")
    diagnose.add_argument("--marker", default=MARKER)
    args = parser.parse_args(argv)
    if args.marker != MARKER:
        parser.error("invalid workflow-modes marker")
    if args.action == "activate" and args.mode != "plan" and not args.record:
        parser.error("--record is required except for initial plan activation")
    if args.action == "transition" and args.user_authorized and args.mode != "discuss":
        parser.error("--user-authorized is only valid for transition discuss")
    if args.action == "write-open":
        if args.recover and (not args.observed_revision or args.path):
            parser.error("--recover requires --observed-revision and forbids --path")
        if args.observed_revision and not args.recover:
            parser.error("--observed-revision requires --recover")
    return args


def main() -> int:
    try:
        args = parse_args()
    except ControlHelp as help_result:
        print(str(help_result))
        return 0
    except ControlError as error:
        print(f"WORKFLOW_CONTROL_ARGUMENT_INVALID: {error}\nNext: run this command with --help, correct the arguments, and check snapshot before retrying a prior uncertain request.", file=sys.stderr)
        return 2
    if args.action == "diagnose":
        try:
            from workflow_modes_record import diagnose_bundle
            report = diagnose_bundle(args.record)
        except Exception as error:
            print(f"WORKFLOW_DIAGNOSE_FAILED: {type(error).__name__}. Next: ask the owner to restore the installed runtime files and record access; do not edit scripts or reset session state.", file=sys.stderr)
            return 2
        print(json.dumps(report, indent=2) if args.json else format_diagnosis(report))
        return 0 if report["valid"] else 1
    print(
        f"Workflow mode control request sent: {args.action}. "
        "Verify that the lifecycle hook returned model-visible confirmation."
    )
    return 0


def format_diagnosis(report: dict) -> str:
    lines = [f"WORKFLOW_DIAGNOSIS: record={report['record']}; valid={str(report['valid']).lower()}",
             f"observed_revision={report['observed_revision']}"]
    for issue in report["issues"]:
        lines.extend((f"{issue['code']}: {issue['path']}: {issue['detail']}", f"Next: {issue['next_step']}"))
    if report["valid"]:
        lines.append("Next: read the bundle and run sync in the hooked session; diagnostics alone do not acknowledge it.")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
