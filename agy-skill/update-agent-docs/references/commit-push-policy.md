# Commit And Push Policy

After updating and verifying agent docs, ask the user in the same language and tone as the current conversation:

```text
Do you want me to commit and push these agent-doc changes to origin?
```

## If The User Declines

- Do not commit.
- Summarize changed files and verification.

## If The User Agrees

1. Inspect `git status`.
2. Stage only files changed for this agent-doc task.
3. Do not stage unrelated user changes.
4. Use a concise commit message such as:

```text
docs: update agent guide
```

5. Do not include `Co-Worker`, `Co-Authored-By`, or similar attribution trailers.
6. Push the current branch to `origin`.
7. Report the commit hash and push result.

## Safety Rules

- Never use destructive git commands to clean the worktree.
- If unrelated changes overlap the same files, inspect carefully and stage only intended hunks when possible.
- If push fails because no upstream is configured, ask before choosing the remote branch name unless the user's instruction clearly permits setting upstream.
