#!/usr/bin/env python3
"""Emit explicit Jarvis lifecycle control calls for the hook to observe."""

from __future__ import annotations

import argparse


MARKER = "jarvis-explicit-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("activate", "checkpoint", "approve-final", "deactivate", "snapshot"),
    )
    parser.add_argument(
        "checkpoint",
        nargs="?",
        choices=("baseline", "scope", "rescue"),
    )
    parser.add_argument("--marker", required=True)
    args = parser.parse_args()
    if args.action == "checkpoint" and args.checkpoint is None:
        parser.error("checkpoint action requires baseline, scope, or rescue")
    if args.action != "checkpoint" and args.checkpoint is not None:
        parser.error("checkpoint name is only valid with the checkpoint action")
    return args


def main() -> int:
    args = parse_args()
    if args.marker != MARKER:
        raise SystemExit("invalid Jarvis activation marker")
    detail = f" {args.checkpoint}" if args.checkpoint else ""
    print(
        f"Jarvis control request sent: {args.action}{detail}. "
        "Verify that the lifecycle hook returned model-visible confirmation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
