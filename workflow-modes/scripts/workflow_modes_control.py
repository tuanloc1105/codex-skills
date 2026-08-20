#!/usr/bin/env python3
"""Emit a workflow-mode lifecycle control call for the plugin hook to observe."""

from __future__ import annotations

import argparse


MARKER = "workflow-modes-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    activate = subparsers.add_parser("activate")
    activate.add_argument("mode", choices=("discuss", "plan", "execute"))
    activate.add_argument("--record")
    activate.add_argument("--marker", required=True)

    transition = subparsers.add_parser("transition")
    transition.add_argument("mode", choices=("plan", "execute"))
    transition.add_argument("--record", required=True)
    transition.add_argument("--marker", required=True)

    action_open = subparsers.add_parser("action-open")
    action_open.add_argument("--record", required=True)
    action_open.add_argument("--path", action="append", default=[])
    action_open.add_argument(
        "--impact", choices=("non-source", "source-confirmed"), required=True
    )
    action_open.add_argument("--marker", required=True)

    action_close = subparsers.add_parser("action-close")
    action_close.add_argument("--result", choices=("completed", "failed", "blocked"), required=True)
    action_close.add_argument("--marker", required=True)

    subparsers.add_parser("snapshot").add_argument("--marker", required=True)
    subparsers.add_parser("deactivate").add_argument("--marker", required=True)
    args = parser.parse_args()
    if args.marker != MARKER:
        parser.error("invalid workflow-modes marker")
    return args


def main() -> int:
    args = parse_args()
    print(
        f"Workflow mode control request sent: {args.action}. "
        "Verify that the lifecycle hook returned model-visible confirmation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
