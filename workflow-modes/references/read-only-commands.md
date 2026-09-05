# Read-only command coverage

Researched 2026-09-06. This is an explicit, tested subset for direct POSIX-shell
tool calls on macOS/BSD and GNU systems, not an exhaustive list of every read-only
program or a guarantee of zero side effects. Unknown executables, options in
argument-aware handlers, scripts, and opaque evaluation wrappers still require
scope. Shell aliases/functions, user configuration, pagers, filesystem access
times, temporary sorting files, and implicit Git maintenance/fetching are outside
the lexical guard. Do not describe this as an OS sandbox.

## Supported families

| Family | Commands/forms | Boundary |
| --- | --- | --- |
| Read/search/compare | `cat`, `head`, `tail`, `wc`, `ls`, `grep`, `rg`, `diff`, `cmp`, `stat`, `file` | `rg` preprocessors/decompression and `file` compile/decompression modes are rejected. |
| Text pipelines | `nl`, `tac`, `cut`, `tr`, `paste`, `join`, `comm`, `fold`, `fmt`, `expand`, `unexpand`, `od` | Shell output redirection is rejected. `join -o` is field selection, not an output path. |
| Sorting | `sort` with common ordering, key, separator, check, merge, buffer/temp directory and parallel options | Reject output paths, compression programs, and unknown options. Sorting may spill to temporary files. |
| Unique lines | `uniq` with count, repeated/unique, case, zero termination, skip and width options | At most one positional file; a second operand would be output. |
| Line ranges | `sed -n '1,20p' file`, `sed -n '1,20p;40,60p'`, `sed -n '1,$p'` | Only print ranges; no extra option/program files, in-place editing, `w`, or `e`. Stdin pipelines are supported. |
| Labels | `echo`, stdout `printf` with simple string/numeric formats | No printf variable assignment via `-v` or `%n`. |
| JSON | `jq` inline/file filters, normal output flags, `--arg`, `--argjson`, `--slurpfile`, `--rawfile`, `-L` | JSON assignment transforms emitted values; it does not edit the input file. Unknown CLI options are rejected. This rule does not apply to `yq`. |
| Encoding/hashes | `base32`, `base64` stdout forms; `cksum`, `md5sum`, `sha1sum`, `sha224sum`, `sha256sum`, `sha384sum`, `sha512sum`, `shasum` | Base encoders use an option allowlist and at most one input; output flags are rejected, including BSD `-o`. |
| Paths/space | `pwd`, `readlink`, `realpath`, `basename`, `dirname`, `du`, `df` | These query paths and usage; shell `cd` remains unsupported because shell hooks can run. |
| Identity/system | `id`, `groups`, `whoami`, `uname`, `arch`, `nproc`, `printenv`, `ps`, `uptime`, `which`, `type` | Read-only classification does not authorize exposing sensitive environment/process contents. |
| Predicates/sequences | `test`, `[`, `true`, `false`, `seq` | Ordinary direct arguments only. |
| Clock | `date`, `date -u +FORMAT`, `date -r VALUE +FORMAT`, long UTC/reference forms | Reject bare numeric setters, `-s`, `--set`, and unknown options. |
| Filesystem search | `find` paths, name/path/type/size/permission/time tests, depth limits, escaped grouping, logical operators, print/printf/ls/prune/quit | Reject unrecognized predicates and write/execute actions such as `-delete`, `-exec`, `-execdir`, `-ok`, `-fprint`, `-fprintf`, `-fls`. |
| Git inspection | Existing status/diff/log/show/path queries; blame/annotate/shortlog/describe/rev-list/for-each-ref/count-objects/cat-file/diff-files/diff-index/diff-tree | No output paths, explicit external diff/textconv/filter execution or `-c` configuration. |
| Git mixed subcommands | `worktree list`, `remote`/`remote -v`, `branch --show-current`, `branch --list [patterns]`, config reads, `stash list/show`, tag listing, one-operand `symbolic-ref` | Listing must not unlock appended mutation flags. Other forms require scope. |

Existing `gh`/`glab`/`tea` view/list/status/checks and `acli jira workitem`
view/search forms remain as before. This change does not extend network/API
authorization or infer that all HTTP GET requests have no side effects.

## Shell composition and diagnostics

Pipelines, `;`, `&&`, `||`, and newlines are classified segment by segment.
Quoted/escaped metacharacters stay arguments, including literal `>` or `|` in
search patterns. Backslash-newline continuation is normalized. Unsupported
expansions, redirection, shell grouping, comments, and malformed quoting remain
opaque. Read-only compound calls must contain only recognized read segments.

Discuss shell denials identify the executable whose command/options were not
recognized, or state that shell syntax is unsupported. Arguments are not copied
into the diagnostic. A denial means the classifier cannot allow the form; it
does not prove the command modifies source.

Do not blanket-allow `awk`, `perl`, Python, Node, `xargs`, `env` command execution,
shell wrappers, pagers, archive tools, `tee`, or package managers based on their
names. They can execute code or write data. Even `--help` is not a universal
exemption. The workflow control CLI retains its dedicated marker-backed help
route and interpreter/content checks.

## Primary sources

- [GNU Coreutils manual](https://www.gnu.org/software/coreutils/manual/coreutils.html): text, path, system and checksum utilities; distinguish stdout filters from output operands and clock setters.
- [GNU sort](https://www.gnu.org/software/coreutils/manual/html_node/sort-invocation.html): output, compression helper and temporary storage options.
- [GNU Findutils actions](https://www.gnu.org/software/findutils/manual/html_node/find_html/Actions.html): printing versus file output, execution and deletion.
- [GNU sed](https://www.gnu.org/software/sed/manual/sed.html): additional programs, in-place writes and `w`/`e` commands.
- [GNU Awk redirection](https://www.gnu.org/software/gawk/manual/html_node/Redirection.html): file output and subprocess pipelines explain why arbitrary awk programs stay opaque.
- [jq manual](https://jqlang.org/manual/): invocation, variables, filter files, and JSON input/output semantics.
- [Git command reference](https://git-scm.com/docs/git) and [cat-file](https://git-scm.com/docs/git-cat-file): inspection commands and filter/textconv execution modes.
- [ripgrep flag definitions](https://github.com/BurntSushi/ripgrep/blob/master/crates/core/flags/defs.rs): preprocessing and compressed-file search.
- [FreeBSD stat](https://man.freebsd.org/cgi/man.cgi?query=stat&sektion=1): BSD formatting options differ from GNU options.

Tests pair realistic read calls with nearby output/execute variants. Hook tests
use temporary state, never the active conversation's workflow database. Installed
runtime routing still requires a separate explicitly requested plugin install
and a fresh task; source validation alone does not change the running cache.
