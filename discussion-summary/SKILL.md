---
name: discussion-summary
description: "Summarize an active discussion and save it to a Markdown file. Use when the user explicitly invokes $discussion-summary or asks to capture, save, export, or hand off the current discussion, decisions, plan, requirements, assumptions, or open questions as Markdown, especially while $discussion-only is active. If the user has not provided an explicit destination path or filename, stop and ask where to save before creating or editing any file."
---

# Discussion Summary

## Core Contract

Summarize the current conversation context into one Markdown file. This skill is for capturing discussion state, not for implementing the plan being discussed.

When combined with `$discussion-only`, treat the user's explicit invocation of `$discussion-summary` as permission for exactly one narrow mutation: creating or updating the requested Markdown summary file. After that file operation, return to the `discussion-only` constraints.

If the active `discussion-only` instructions in the current session are stricter and do not allow this narrow exception, explain the conflict and ask the user to explicitly exit `discussion-only` before saving.

## Destination Rule

Before writing, confirm the user has provided a clear save destination.

- If the user provides a file path, use it.
- If the user provides only a directory, ask for the Markdown filename.
- If the user provides only a filename, save it in the current workspace unless that is ambiguous.
- If the destination has no extension, append `.md`.
- If the destination is missing, vague, or ambiguous, stop and ask where to save. Do not create a default file.
- If the target file already exists, ask before overwriting unless the user explicitly requested an update or overwrite.
- If the parent directory does not exist, ask before creating it.

Ask for the missing destination with a short, concrete question. Offer examples when useful, but do not choose a default path on the user's behalf.

## Summary Content

Write a concise Markdown document in the user's language unless they request another language.

Prefer this structure:

```markdown
# Discussion Summary

## Context

## Decisions

## Requirements

## Constraints

## Open Questions

## Suggested Next Steps
```

Adapt the headings to the conversation. Omit empty sections. Use bullets for scanability.

Capture:

- The main topic being discussed.
- User goals and non-negotiable requirements.
- Decisions already made.
- Options considered and tradeoffs that matter.
- Open questions or blockers.
- Next steps that are ready to execute later.

Do not include a transcript, excessive quotes, hidden chain-of-thought, unrelated chat, or implementation that the user did not ask to save.

## File Operation Discipline

Create or update only the requested Markdown summary file and any explicitly approved parent directory. Do not edit code, configs, plans, skill files, branches, tickets, external systems, or other artifacts.

Use normal file-editing tools rather than shell redirection. Keep the saved document self-contained enough that a future agent can resume the discussion from it.

After saving, reply with the saved path and a one-sentence description of what was captured.
