# Commit And Push Policy

After updating and verifying steering docs, ask the user in the same language and tone as the current conversation — via `ask_question` on a dashboard session (ending the turn) or a trailing `[OPTIONS: Commit and push | Just leave the changes]` otherwise:

```text
Do you want me to commit and push these steering-doc changes to origin?
```

## If The User Declines

- Do not commit.
- Summarize changed files and verification.

## If The User Agrees

1. Inspect `git status`.
2. Stage only files changed for this steering-doc task (prefer staging specific files over `git add .`, per this agent's own git-safety rules).
3. Do not stage unrelated user changes.
4. Use a Conventional Commits message such as:

```text
docs: refresh kiro steering guide
```

5. Do not include `Co-Worker`, `Co-Authored-By`, or similar attribution trailers.
6. Push the current branch to `origin`, naming the branch explicitly (never a bare `git push`); do not push directly to `main`/`master` unless the user explicitly asked for that.
7. Report the commit hash and push result.

## Safety Rules

- Never use destructive git commands to clean the worktree.
- If unrelated changes overlap the same files, inspect carefully and stage only intended hunks when possible.
- If push fails because no upstream is configured, ask before choosing the remote branch name unless the user's instruction clearly permits setting upstream.
