---
name: discussion-only
description: Use when the user explicitly invokes $discussion-only or asks for a chat-only, planning-only, advisory-only, no-code-change, or discussion-only mode with a Markdown tracker. This skill makes Codex discuss, explain, reason, teach, plan, and ask questions while maintaining one user-specified Markdown file that tracks the discussion. If the user has not provided where to save the Markdown tracker, ask for the path before starting the discussion. By default, allow no mutation beyond the tracker; however, the user may explicitly authorize scoped non-source-code mutations without exiting the mode. Never modify source code while the mode remains active.
---

# Discussion Only

## Core Contract

Operate as a discussion partner and keep a Markdown tracker for the conversation. By default, the only allowed mutation is creating or updating the user-specified Markdown tracker file.

Keep the mode active until the user explicitly exits it with wording such as "exit discussion-only", "turn off discussion-only", "thoat che do chi thao luan", "bat dau sua code", or an equally clear instruction. The user may authorize a specific non-source-code mutation while keeping the mode active; such authorization is a scoped exception, not an exit from the mode.

## Scoped Mutation Authorization

Treat a clear instruction to make a non-source-code change as authorization for that change. Do not require the user to disable `discussion-only`, use special wording, or approve every individual step.

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
- If the parent directory does not exist, ask before creating it.
- If the file already exists, ask whether to continue updating that file unless the user explicitly says to reuse, continue, update, or append to it.

Once the destination is clear, create the tracker before continuing the discussion. Keep updating the same tracker after meaningful discussion turns.

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
- Use read-only inspection only when the user explicitly asks to inspect local or external context and the tool action is guaranteed not to mutate state.
- Create or update the user-specified Markdown tracker file for this discussion.
- Perform an explicitly authorized non-source-code mutation within the granted scope while keeping the mode active.

## Prohibited Work

Do not perform:

- Any source-code mutation while the mode remains active.
- Any mutation beyond the Markdown tracker unless the user has clearly authorized it.
- Any action outside or materially beyond the authorized scope.
- Unrequested cleanup, refactoring, collateral changes, or speculative follow-up work.
- Treating permission for one mutation as permission for later or unrelated mutations.
- Treating discussion, analysis, a hypothetical request, or approval of a plan as authorization to apply it unless the user clearly asks for the change to be made.

If the user clearly requests an in-scope non-source-code mutation, perform it without requiring an exit from the mode. If the requested task requires source-code mutation, explain the boundary and wait for the user to explicitly exit `discussion-only` before acting.

## Tool Discipline

Prefer answering from conversation context. Before any read-only tool use, confirm it is necessary for the discussion and that it will not change state.

Avoid commands or tools with side effects unless they maintain the approved Markdown tracker or are necessary for an explicitly authorized non-source-code mutation. Before using a mutating tool, verify that its target and effect fit the granted scope and cannot modify source code. If there is material doubt, do not run it; clarify the boundary instead.

## Question Style

Every question that requires a user response must include concrete options. Do not ask a bare open-ended question, including when requesting clarification, confirmation, approval, a tracker destination, a filename, permission to create a directory, reuse of an existing file, or permission to exit this mode.

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

This skill is a hard overlay on top of all other skills. Other skill instructions remain useful for teaching style, review structure, or reasoning process. Their mutation instructions are suspended unless the mutation maintains the Markdown tracker or the user explicitly authorizes a scoped non-source-code change. Source-code mutation remains suspended unconditionally until the user exits `discussion-only`.

When combined with `$teach-for-understanding`, teach incrementally and verify understanding in chat. Put learning checkpoints in the Markdown tracker instead of creating or updating a separate `understanding-checklist.md`.

## Response Pattern

When a user asks for something actionable while this mode is active:

1. Ensure the Markdown tracker destination is known; if not, ask for it and stop.
2. Create or update the Markdown tracker with the current discussion state.
3. Determine whether the requested action would mutate source code.
4. If it would mutate source code, explain that the user must explicitly exit `discussion-only`, then wait without making the change.
5. If it is a non-source-code mutation and the user's instruction clearly authorizes it, record the scope, perform the change, verify it proportionately, and update the tracker with the result.
6. If mutation has not been clearly authorized, provide analysis, options, pseudocode, or a step-by-step plan without applying it.
7. Clarify that `discussion-only` remains active when relevant; completing an authorized scoped mutation does not exit the mode.
8. Format every question that needs a user response as its own option block under the mandatory `Question Style` contract.
