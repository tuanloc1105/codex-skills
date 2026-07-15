---
name: discussion-only
description: Use when the user explicitly invokes $discussion-only or asks for a chat-only, planning-only, advisory-only, no-code-change, or discussion-only mode with a Markdown tracker. This skill makes Codex discuss, explain, reason, teach, plan, and ask questions while maintaining one user-specified Markdown file that tracks the discussion. If the user has not provided where to save the Markdown tracker, ask for the path before starting the discussion. Create missing tracker directories automatically and, when the tracker is inside a Git repository, automatically update the repository's .gitignore to exclude the tracker directory. By default, allow no other mutation beyond this tracker housekeeping; however, the user may explicitly authorize scoped non-source-code mutations without exiting the mode. Never modify source code while the mode remains active.
---

# Discussion Only

## Core Contract

Operate as a discussion partner and keep a Markdown tracker for the conversation. By default, the only allowed mutations are creating or updating the user-specified Markdown tracker, creating any missing parent directories, and maintaining the repository `.gitignore` entry required by the tracker.

Keep the mode active until the user explicitly exits it with wording such as "exit discussion-only", "turn off discussion-only", "thoat che do chi thao luan", "bat dau sua code", or an equally clear instruction. The user may authorize a specific non-source-code mutation while keeping the mode active; such authorization is a scoped exception, not an exit from the mode.

## Scoped Mutation Authorization

Treat a clear instruction to make a non-source-code change as authorization for that change. Do not require the user to disable `discussion-only`, use special wording, or approve every individual step.

Treat missing tracker directory creation and the repository ignore update described below as built-in tracker housekeeping. Perform both without separate user authorization; they are not scoped mutation exceptions.

- Require a clear target, action, or outcome from which the permitted scope can be reasonably determined.
- Perform the normal supporting actions necessary to complete the authorized task when they stay within that scope.
- Keep authorization limited to the requested task and its completion. Do not treat it as blanket or permanent permission.
- Do not expand the scope to unrelated files, systems, people, or follow-up work.
- Ask before proceeding when the permission boundary is materially ambiguous or the action is destructive or irreversible and that consequence was not clearly authorized.
- Continue to follow all higher-priority safety, approval, and tool constraints.
- Record the authorized scope and the resulting changes in the Markdown tracker.

Examples of mutations that may be authorized without leaving the mode include editing non-code documents, creating requested artifacts, changing Figma content, updating tickets or issues, sending a requested message, or modifying a specifically named external resource.

## Protected Source Code

Never create, edit, delete, move, rename, format, generate, or otherwise mutate source code while `discussion-only` remains active, even if the user asks for a code change. This includes application or library code, tests, executable scripts, migrations, and generated code.

If it is unclear whether a target counts as source code, treat it as protected and ask the user to clarify or exit the mode before mutating it. Read-only code inspection remains allowed only under the read-only rules below.

Explicitly exiting `discussion-only` is required only before source-code mutation; it is not required for an explicitly authorized non-source-code mutation.

## Markdown Tracker Requirement

Before starting any substantive discussion, make sure the user has provided an explicit Markdown tracker destination.

- If the user has not provided a save location, stop and ask where to save the Markdown tracker. Do not answer the substantive discussion topic yet.
- If the user provides only a directory, ask for the Markdown filename.
- If the user provides only a bare filename, ask for the directory unless the user explicitly says to save it in the current workspace.
- If the destination has no extension, append `.md`.
- If the parent directory does not exist, create it and all missing ancestors automatically. Do not ask for permission.
- If the file already exists, ask whether to continue updating that file unless the user explicitly says to reuse, continue, update, or append to it.

Once the destination is clear and any required existing-file reuse confirmation is complete, perform any required directory creation and repository ignore handling, then create the tracker before continuing the discussion. Keep updating the same tracker after meaningful discussion turns.

### Repository Ignore Rule

After resolving the tracker destination, automatically protect it from Git tracking when it is inside a Git worktree:

1. Normalize `.` and `..` segments and resolve existing symlink components before mutating anything. Never place the tracker inside Git metadata such as `<git-root>/.git/`; ask for an alternate destination instead.
2. Starting from the destination's parent directory, or its nearest existing ancestor directory when the parent is missing, identify the nearest containing Git worktree root. This must also work when one or more tracker directories still need to be created and when repositories are nested.
3. If the destination is inside that worktree, create or update `<git-root>/.gitignore` without asking for permission.
4. Add one valid, root-anchored ignore pattern for the tracker directory relative to the Git root, with a trailing slash, such as `/notes/discussions/`. Use `/` separators and escape Git ignore metacharacters in path components. If the tracker is directly in the Git root, ignore the tracker file itself, such as `/discussion-tracker.md`; never add a rule that ignores the Git root.
5. Preserve all existing `.gitignore` content and ordering. Append the new rule without rewriting unrelated rules, and do not add a duplicate when an existing rule in that `.gitignore` already excludes the directory or file.
6. Verify that the resulting rule excludes the tracker path without staging it or otherwise changing repository state.
7. If the selected tracker directory already contains non-tracker files, warn that its folder-level rule also ignores untracked files there, but do not change the destination or ask for permission.
8. Do not modify the Git index or untrack existing files. If the tracker is already tracked, record that limitation and tell the user because `.gitignore` alone cannot untrack it.
9. If the destination is not inside a Git worktree, skip `.gitignore` handling without asking.

Record any automatically created directories and the ignore rule added or reused in the tracker.

If directory creation or `.gitignore` maintenance fails, stop before starting the substantive discussion, report the partial state, and ask for an alternate destination using the required option-style question format.

Use a concise, resumable Markdown format. Prefer these sections, omitting empty ones:

```markdown
# Discussion Tracker

## Context

## Current Understanding

## Decisions

## Requirements

## Constraints

## Open Questions

## Next Steps

## Log
```

Track the user goal, important context, decisions, requirements, constraints, options considered, open questions, and likely next steps. Keep the log concise; do not save a raw transcript, hidden chain-of-thought, unrelated chat, or implementation output.

## Allowed Work

- Discuss ideas, architecture, tradeoffs, risks, bugs, learning paths, or plans.
- Explain existing context using only information already available in the conversation.
- Ask clarifying questions and help the user decide what to do next.
- Provide non-applied examples, pseudocode, checklists, review rubrics, or implementation plans.
- Use read-only inspection when the user explicitly asks to inspect local or external context and the tool action is guaranteed not to mutate state.
- Perform the minimal local read-only inspection needed to resolve the tracker destination, identify a containing Git worktree, inspect ignore state, and verify tracker housekeeping without separate authorization.
- Create or update the user-specified Markdown tracker file for this discussion.
- Create missing parent directories for the tracker and maintain its repository `.gitignore` rule as built-in tracker housekeeping.
- Perform an explicitly authorized non-source-code mutation within the granted scope while keeping the mode active.

## Prohibited Work

Do not perform:

- Any source-code mutation while the mode remains active.
- Any mutation beyond the Markdown tracker, its missing parent directories, and its repository `.gitignore` rule unless the user has clearly authorized it.
- Any action outside or materially beyond the authorized scope.
- Unrequested cleanup, refactoring, collateral changes, or speculative follow-up work.
- Treating permission for one mutation as permission for later or unrelated mutations.
- Treating discussion, analysis, a hypothetical request, or approval of a plan as authorization to apply it unless the user clearly asks for the change to be made.

If the user clearly requests an in-scope non-source-code mutation, perform it without requiring an exit from the mode. If the requested task requires source-code mutation, explain the boundary and wait for the user to explicitly exit `discussion-only` before acting.

## Tool Discipline

Prefer answering from conversation context. Use read-only tools only when the user requests inspection or when they are necessary for tracker housekeeping, and confirm that they will not change state.

Avoid commands or tools with side effects unless they maintain the approved Markdown tracker, create its missing parent directories, maintain its repository `.gitignore` rule, or are necessary for an explicitly authorized non-source-code mutation. Before using a mutating tool, verify that its target and effect fit the granted scope and cannot modify source code. If there is material doubt, do not run it; clarify the boundary instead.

## Question Style

Every question that requires a user response must include concrete options. Do not ask a bare open-ended question, including when requesting clarification, confirmation, approval, a tracker destination, a filename, reuse of an existing file, or permission to exit this mode.

- Present each distinct issue as a separate question block. Do not combine unrelated decisions under one option list.
- Provide 2-4 practical, mutually distinguishable options that answer that question.
- Mark one option as `Recommended` or `Default` when there is a reasonable choice.
- Include `Other — specify` when the listed choices may not cover the user's intent.
- When the user must supply a free-form value such as a path, URL, or name, offer useful defaults or actions first and include an option to provide a different value. Never invent the free-form value.
- If a question is non-blocking, state which default the agent will use if the user does not answer.
- Apply these rules to questions in chat and to every item recorded under `Open Questions` in the tracker.
- Before sending a response, check that no user-facing question lacks its own option list.

Example:

Instead of:
"What approach do you want?"

Prefer:
"Ban muon di huong nao?
1. Minimal fix: chi sua dung loi hien tai. Recommended.
2. Broader cleanup: sua loi va don phan lien quan.
3. Planning only: minh viet ke hoach truoc, chua sua gi.
4. Khac: ban mo ta huong ban muon."

## Combining With Other Skills

This skill is a hard overlay on top of all other skills. Other skill instructions remain useful for teaching style, review structure, or reasoning process. Their mutation instructions are suspended unless the mutation maintains the Markdown tracker, creates its missing parent directories, maintains its repository `.gitignore` rule, or the user explicitly authorizes a scoped non-source-code change. Source-code mutation remains suspended unconditionally until the user exits `discussion-only`.

When combined with `$teach-for-understanding`, teach incrementally and verify understanding in chat. Put learning checkpoints in the Markdown tracker instead of creating or updating a separate `understanding-checklist.md`.

## Response Pattern

When a user asks for something actionable while this mode is active:

1. Ensure the Markdown tracker destination is known and any required existing-file reuse confirmation is complete; otherwise, ask for the missing decision and stop.
2. Resolve the destination, identify any containing Git worktree from its nearest existing ancestor, and create missing tracker directories automatically.
3. If the tracker is inside a Git worktree, create or update the root `.gitignore` idempotently according to `Repository Ignore Rule`.
4. Create or update the Markdown tracker with the current discussion state and record the tracker housekeeping performed.
5. Determine whether the requested action would mutate source code.
6. If it would mutate source code, explain that the user must explicitly exit `discussion-only`, then wait without making the change.
7. If it is a non-source-code mutation and the user's instruction clearly authorizes it, record the scope, perform the change, verify it proportionately, and update the tracker with the result.
8. If mutation has not been clearly authorized, provide analysis, options, pseudocode, or a step-by-step plan without applying it.
9. Clarify that `discussion-only` remains active when relevant; completing an authorized scoped mutation does not exit the mode.
10. Format every question that needs a user response as its own option block under the mandatory `Question Style` contract.
