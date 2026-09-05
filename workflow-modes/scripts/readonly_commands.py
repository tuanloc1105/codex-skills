"""Argument-aware read forms for utilities with write/execute modes.

See ../references/read-only-commands.md for scope and primary sources.
Unknown options deliberately require scope; this is not a shell sandbox.
"""

from __future__ import annotations

import re


def operands(args: list[str], flags: str = "", values: str = "",
             long_flags: tuple[str, ...] = (), long_values: tuple[str, ...] = ()) -> list[str] | None:
    """Parse allowed options, including clusters, attached values and --.

    Continue after operands because GNU utilities permit trailing options.
    """
    result = []
    position = 0
    while position < len(args):
        token = args[position]
        position += 1
        if token == "--":
            return result + args[position:]
        if token.startswith("--"):
            name, separator, _value = token.partition("=")
            if name in long_flags and not separator:
                continue
            if name not in long_values:
                return None
            if not separator:
                if position == len(args):
                    return None
                position += 1
        elif token.startswith("-") and token != "-":
            for offset, option in enumerate(token[1:], 2):
                if option in values:
                    if offset == len(token):
                        if position == len(args):
                            return None
                        position += 1
                    break
                if option not in flags:
                    return None
        else:
            result.append(token)
    return result


def readonly_sort(args: list[str]) -> bool:
    return operands(
        args, "bdfghimnMrsuVzcCs", "ktST",
        ("--reverse", "--numeric-sort", "--unique", "--stable", "--version-sort",
         "--human-numeric-sort", "--general-numeric-sort", "--month-sort",
         "--ignore-case", "--ignore-leading-blanks", "--dictionary-order",
         "--ignore-nonprinting", "--merge", "--check", "--zero-terminated", "--debug"),
        ("--key", "--field-separator", "--buffer-size", "--temporary-directory", "--parallel"),
    ) is not None


def readonly_uniq(args: list[str]) -> bool:
    files = operands(args, "cduiz", "fsw", ("--count", "--repeated", "--unique",
        "--ignore-case", "--zero-terminated"), ("--skip-fields", "--skip-chars", "--check-chars"))
    # The second positional operand is an output file, not another input.
    return files is not None and len(files) <= 1


def readonly_encoding(args: list[str]) -> bool:
    # GNU and BSD base64 differ: BSD -o writes, while -i reads an input.
    files = operands(args, "dDbi", "w", ("--decode", "--ignore-garbage"), ("--wrap",))
    return files is not None and len(files) <= 1


def readonly_jq(args: list[str]) -> bool:
    # jq filters transform JSON and emit stdout; assignments modify the value,
    # not the input file. Do not extend this to unrelated yq implementations.
    position = 0
    ordinary = []
    arities = {"--arg": 2, "--argjson": 2, "--slurpfile": 2, "--rawfile": 2,
               "--indent": 1, "--from-file": 1, "--library-path": 1}
    while position < len(args):
        token = args[position]
        if token in arities:
            count = arities[token]
            if position + count >= len(args):
                return False
            position += count + 1
        else:
            ordinary.append(token)
            position += 1
            if token == "--":
                ordinary.extend(args[position:])
                break
    return operands(ordinary, "nRsrcjaSCMebVh", "fL",
        ("--null-input", "--raw-input", "--slurp", "--compact-output", "--raw-output",
         "--raw-output0", "--join-output", "--ascii-output", "--sort-keys", "--color-output",
         "--monochrome-output", "--exit-status", "--tab", "--unbuffered", "--stream",
         "--stream-errors", "--seq", "--binary", "--version", "--help", "--build-configuration"),
    ) is not None


def readonly_find(args: list[str]) -> bool:
    flags = {"-H", "-L", "-P", "-X", "-d", "-s", "-x", "-a", "-and", "-o", "-or",
             "!", "-not", "(", ")", ",", "-print", "-print0", "-ls", "-prune", "-quit",
             "-empty", "-readable", "-writable", "-executable", "-true", "-false",
             "-depth", "-xdev", "-mount", "-daystart", "-follow", "-noleaf",
             "-ignore_readdir_race", "-noignore_readdir_race"}
    values = {"-name", "-iname", "-path", "-ipath", "-wholename", "-iwholename",
              "-regex", "-iregex", "-regextype", "-type", "-xtype", "-size", "-perm",
              "-user", "-group", "-uid", "-gid", "-inum", "-links", "-mtime", "-mmin",
              "-atime", "-amin", "-ctime", "-cmin", "-newer", "-anewer", "-cnewer",
              "-maxdepth", "-mindepth", "-fstype", "-printf"}
    expression = False
    position = 0
    while position < len(args):
        token = args[position]
        position += 1
        if not expression and token in {"-H", "-L", "-P", "-X", "-d", "-s", "-x"}:
            continue
        if token in flags:
            expression = True
        elif token in values:
            expression = True
            if position == len(args):
                return False
            position += 1
        elif token.startswith("-") or expression:
            return False
    return True


def readonly_date(args: list[str]) -> bool:
    # A bare numeric operand can set the clock on BSD; -s/--set on GNU.
    files = operands(args, "uR", "r", ("--utc", "--universal", "--rfc-email"), ("--reference",))
    return files is not None and all(value.startswith("+") for value in files) and len(files) <= 1


def readonly_sed(args: list[str]) -> bool:
    if len(args) < 2 or args[0] != "-n":
        return False
    program = args[1]
    return bool(re.fullmatch(
        r"\s*\d+(?:,(?:\d+|\$))?p(?:\s*;\s*\d+(?:,(?:\d+|\$))?p)*\s*;?\s*", program
    )) and all(not token.startswith("-") or token == "-" for token in args[2:])
