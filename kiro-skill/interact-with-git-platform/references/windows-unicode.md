# Non-ASCII text on Windows (`gh`, `glab`, `tea`)

Read this reference whenever the `shell` tool runs on Windows and a payload contains
non-ASCII characters: Vietnamese, other diacritics, CJK, emoji, or typographic
punctuation. It applies to pull/merge request titles and bodies, issue titles and
bodies, comments, review bodies, inline review comments, release notes, commit
messages consumed by `--fill`, and JSON sent through `gh api` / `glab api` / `tea`.

`gh`, `glab`, and `tea` are Go programs: they read files and standard input as raw
bytes and pass them through unchanged. Corruption therefore never originates inside
the client. It happens in the shell before the bytes reach the client, or in the
console after the bytes leave it. Diagnose and fix it on those two boundaries.

## Detect the platform and shell before composing a payload

- Confirm Windows rather than assuming it: `$env:OS` / `%OS%` equals `Windows_NT`, or
  read `[System.Environment]::OSVersion`. Do not apply these steps on macOS or Linux,
  where the default UTF-8 locale already handles this correctly.
- Identify the shell, because the failure modes differ: Windows PowerShell 5.1
  (`$PSVersionTable.PSVersion.Major` is `5`), PowerShell 7+ (`6` or higher), `cmd.exe`,
  or a Git Bash / MSYS2 shell (`uname` succeeds, `$MSYSTEM` is set). Git Bash is
  UTF-8 by default and usually needs no adjustment beyond a UTF-8 `LANG`/`LC_ALL`.
- Record the detected shell in the report. A body that survived one Windows shell
  proves nothing about another.

## Read a `?` correctly: it means data was already destroyed

- A literal `?` where a diacritic belongs (`ti?ng Vi?t`) means a lossy code-page
  conversion replaced unmappable characters with the default substitution character.
  The original text is gone; re-encoding the result cannot recover it. Find the
  boundary that converted it and re-send the payload from the original source.
- Mojibake (`tiÃªu Ä‘á»`, `â€™`) means the bytes survived but were decoded with the
  wrong code page. That is usually a display or read-back problem and is recoverable.
- A `?` or mojibake in console output is not proof that the remote object is wrong.
  Verify the remote content by bytes, not by what the terminal renders — see
  "Verify the remote object without trusting the console".
- Never repair mangled text by stripping diacritics, transliterating to ASCII, or
  rewriting the user's wording. Fix the encoding path and re-send the original text.
  If it cannot be sent intact, stop and report the limitation.

## Hard rule: send non-ASCII through a UTF-8 file, not a pipe or an inline argument

Write the payload to a UTF-8 file with no BOM, then pass it with the leaf command's
file option (for example `gh pr create --body-file <path>`, `gh pr comment
--body-file <path>`, `gh issue create --body-file <path>`, or the equivalent the
local `--help` advertises for `glab` and `tea`). This bypasses both console code
pages and pipeline encoding, and it is the only route that behaves identically in
`cmd.exe`, PowerShell 5.1, PowerShell 7, and Git Bash.

- PowerShell of any version — write the file through .NET so encoding is explicit:

  ```powershell
  [System.IO.File]::WriteAllText($path, $body, (New-Object System.Text.UTF8Encoding $false))
  ```

  The `$false` argument means "no BOM". This is required on PowerShell 5.1 and is
  still the safest form on PowerShell 7.
- Do not use `>`, `>>`, or `Out-File` on PowerShell 5.1: they default to UTF-16LE,
  which the client reads as binary garbage. Do not use `Set-Content` without an
  explicit encoding there either: it defaults to the ANSI code page and produces `?`.
  `-Encoding UTF8` on 5.1 writes a BOM, which appears as stray characters at the
  start of the published body. On PowerShell 7+, `Set-Content -Encoding utf8NoBOM`
  is acceptable.
- Never author the file with `cmd.exe` `echo` redirection, and never embed non-ASCII
  text in a `.bat`/`.cmd` file. Batch content is read through the console/OEM code
  page and loses the characters before redirection happens.
- A UTF-8 BOM is not harmless: the clients forward those three bytes into the body
  text. Always write without a BOM, and if a file came from another tool, check for
  and strip a leading `EF BB BF`.
- Keep the file under the session scratch directory, not in the user's repository,
  and confirm the written file is valid UTF-8 before invoking the client — for
  example by reading it back with an explicit UTF-8 decoder and comparing the text to
  the intended body.

## When a pipe or an inline argument is unavoidable

- Prefer the leaf command's standard-input form (`--body-file -` where local help
  advertises it) only after making the pipeline UTF-8 in the current session:

  ```powershell
  $OutputEncoding = New-Object System.Text.UTF8Encoding $false
  [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
  [Console]::InputEncoding  = New-Object System.Text.UTF8Encoding $false
  ```

  On Windows PowerShell 5.1 `$OutputEncoding` defaults to ASCII, so every non-ASCII
  character piped to a native program becomes `?` without the assignment above.
  PowerShell 7+ already defaults to UTF-8, but setting it explicitly costs nothing.
- In `cmd.exe`, run `chcp 65001` in the same session before the client command, and
  confirm the console font can render the script. `chcp` fixes the console code page
  only; it does not fix an ANSI-encoded batch file or `echo`-written file.
- Treat these as per-session, in-scope adjustments. Enabling the machine-wide
  "Beta: Use Unicode UTF-8 for worldwide language support" region option changes the
  system ANSI code page and needs a reboot: that is a host configuration change, so
  request the user's explicit authorization instead of doing it to unblock a command.

## Pure-ASCII fallback through the API

When no leaf command can preserve the payload, send the text through the authenticated
API with a JSON body read from a file (`gh api --input <file>`, `glab api` with its
advertised input flag). Escaping every non-ASCII character as a `\uXXXX` sequence makes
the request bytes pure ASCII and therefore immune to every code page on the path, while
the platform stores the decoded characters. Build such a file with a JSON serializer,
never by hand-editing escapes, and keep the endpoint, method, and repository explicit.

## Commit messages feeding `--fill`

`--fill`, `--fill-first`, and `--fill-verbose` derive the title and body from commit
messages, so a message already mangled at commit time yields a mangled PR/MR and no
platform-side edit recovers the original. On Windows, create such commits with
`git commit -F <utf8-no-bom-file>` rather than `-m` in `cmd.exe`, keep
`i18n.commitEncoding` at `utf-8`, and set `i18n.logOutputEncoding=utf-8` when reading
history back. Inspect the resolved title and body before submitting a filled PR/MR.

## Verify the remote object without trusting the console

1. Fetch the stored value into a file instead of reading it off the screen, for
   example `gh pr view <id> --repo <repo> --json title,body --jq .body` redirected to a
   file, or the equivalent `glab`/`tea` view or API call.
2. Decode that file explicitly as UTF-8 and compare it to the body file that was sent.
   Compare after Unicode NFC normalization: Vietnamese text can be precomposed (NFC)
   or decomposed (NFD), and a normalization difference is a false alarm, not corruption.
3. Also confirm no `?` runs appeared where diacritics belonged and that the body kept
   real line breaks, headings, and lists, per this skill's existing read-back rule.
4. Report which shell and which transport (file option, stdin, or API) produced the
   verified result, so the same route can be reused.

Apply the same verification to inline review comments, thread replies, and release
notes. Location and encoding are separate properties: an inline comment can be
anchored correctly and still have a destroyed body, so check both before reporting
success.
