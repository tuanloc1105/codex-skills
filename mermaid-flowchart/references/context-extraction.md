# Extracting a Flow from Session Context

Use this guidance when the requested diagram depends on work already discussed, inspected, or changed in the current task.

## Source priority

Resolve facts in this order:

1. The user's current request and explicit target.
2. The latest confirmed decisions in the conversation.
3. Named or currently discussed code and artifacts.
4. Older discussion that has not been superseded.

More recent confirmed decisions override earlier alternatives. Exclude proposals the user rejected, abandoned approaches, incidental debugging hypotheses, and unrelated session material.

## Choose the context boundary

- **Focused context:** When the user names a function, file, endpoint, subsystem, or step, diagram only that target and the connections needed to understand it.
- **Session context:** When the user says “the flow we discussed” or similar, collect the smallest coherent process supported by the recent conversation.
- **Existing diagram:** Treat its node IDs, established terminology, and unaffected layout as content to preserve. Apply only the requested semantic changes.

Do not scan broadly when the conversation already provides enough evidence. Inspect named code when behavior must be exact or when the conversation contains only a summary.

## Evidence and assumptions

Classify each material step as one of:

- **Confirmed:** stated by the user, demonstrated by inspected code, or established by verified output.
- **Inferred:** necessary to connect confirmed steps but not directly established.
- **Unknown:** a branch or condition whose outcome cannot be represented responsibly.

Put confirmed behavior in the main flow. Use the narrowest possible wording for inferred steps and disclose meaningful assumptions outside the diagram. Represent an unknown explicitly only when it is itself useful; otherwise ask the user if it changes the diagram's purpose.

Never present the assistant's earlier suggestion as an approved decision unless the user accepted it or later work implemented it.
