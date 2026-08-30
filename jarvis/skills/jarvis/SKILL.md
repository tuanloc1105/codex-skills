---
name: jarvis
description: Explicitly supervise a Codex task with a frontier subagent that protects the user's goal, detects scope or reasoning drift, challenges unsupported assumptions, and guides the primary agent when it becomes stuck. Use only when the user invokes `$jarvis`; implicit invocation is disabled.
---

# Jarvis

Act as the primary-agent side of a supervised task. Establish one Jarvis supervisor, keep it informed at meaningful checkpoints, obey its evidence-backed corrections, and use it immediately when progress stalls.

## Make Jarvis Visible In The Main Thread

Keep every Jarvis interaction visible to the user in the main thread, using the user's language. Use a compact review block at the baseline review and every later checkpoint, including scope, rescue, workaround, and final review.

Immediately before contacting Jarvis, post the checkpoint and a one-line `Main → Jarvis` summary:

> **Jarvis review · Scope**
>
> **Main → Jarvis:** Review whether expanding the change into the cache module is justified.

After Jarvis responds and before taking the next material action, post the completed block:

> **Jarvis review · Scope**
>
> **Main → Jarvis:** Review whether expanding the change into the cache module is justified.
>
> **Jarvis:** `CHALLENGE`
>
> **Reason:** No evidence yet links the failure to the cache module.
>
> **Next:** Run the narrow cache probe first; do not expand the edit scope yet.

Every completed block must identify the checkpoint and contain:

- `Main → Jarvis`: the decision or direction reviewed;
- `Jarvis`: the exact verdict token;
- `Reason`: the actionable, evidence-backed reason;
- `Next`: what the primary agent will change, continue, or stop as a result.

Translate the surrounding labels and prose when appropriate, but keep `Main → Jarvis` recognizable and keep the verdict token unchanged. Do not paste the full supervisor exchange, expose hidden reasoning, or narrate routine mechanics. Do not leave supervisor calls visible only as subagent or tool activity. If Jarvis is unavailable, delayed, or conflicts with a higher-priority instruction, use the same checkpoint block to state that condition instead of implying that a review completed.

## Start Jarvis

1. Resolve `plugin_root` as the directory two levels above this skill directory.
2. Run this exact standalone command, replacing `<plugin_root>` with the absolute path:

   ```sh
   python3 "<plugin_root>/scripts/jarvis_control.py" activate --marker jarvis-explicit-v1
   ```

3. Confirm that the hook returns model-visible Jarvis activation context. If it does not, stop before mutation and tell the user to enable and trust the plugin hooks.
4. Read [references/supervisor-prompt.md](references/supervisor-prompt.md) completely.
5. Write a concise goal contract containing:
   - the user's requested outcome;
   - in-scope and out-of-scope work;
   - preservation requirements and approval boundaries;
   - current evidence, assumptions, and unknowns;
   - completion criteria and intended verification.
6. Spawn exactly one supervisor named `jarvis_supervisor` using the strongest capability-first model exposed by the subagent tool and the highest supported reasoning effort. Prefer `gpt-5.6-sol` with `max` reasoning when available. Never silently choose a speed- or cost-optimized model.
   - Use a read-only/default agent profile and explicitly forbid file edits, external mutations, and further delegation.
   - Give it the goal contract and the complete supervisor prompt.
   - If a model override cannot be combined with a full-history fork, prioritize the strongest model and pass a self-contained goal contract with the largest permitted recent-turn fork.
7. Wait for Jarvis's baseline verdict. Resolve every `CHALLENGE` before continuing.
8. After a `READY` verdict, run:

   ```sh
   python3 "<plugin_root>/scripts/jarvis_control.py" checkpoint baseline --marker jarvis-explicit-v1
   ```

If the subagent tools or required frontier model are unavailable, fail closed: report that Jarvis supervision could not be established and do not claim the skill is active.

## Keep Jarvis In The Loop

Reuse the same supervisor for the entire task. Send it a follow-up and wait for its verdict at these checkpoints:

- before the first material mutation;
- when the implementation path, touched area, or user goal changes materially;
- after a failed verification changes the diagnosis;
- before accepting a workaround, fallback, or weakened requirement;
- before declaring the task complete.

Use `send_message` when the supervisor is running and a follow-up task when it is idle. Send compact evidence, not raw logs: intended next action, relevant result, changed assumptions, affected paths, and the decision requested.

Treat Jarvis feedback as a review, not an unquestionable command. Follow evidence-backed corrections that preserve the user's request. If Jarvis conflicts with the user or higher-priority instructions, obey the higher-priority instruction and record the conflict in the next checkpoint.

## Detect And Correct Drift

Consult Jarvis immediately when any of these conditions appears:

- the next action no longer maps directly to the goal contract;
- the scope expands without user authority;
- a new abstraction, dependency, rewrite, or workaround is proposed without necessity;
- an assumption becomes load-bearing but remains unverified;
- implementation begins before relevant callers, tests, or conventions were inspected;
- a completion claim lacks direct verification.

After Jarvis approves a justified scope adjustment, run:

```sh
python3 "<plugin_root>/scripts/jarvis_control.py" checkpoint scope --marker jarvis-explicit-v1
```

## Rescue The Primary Agent When Stuck

Consider the primary agent stuck before it explicitly admits being stuck when any of these signals occurs:

- the same failure or rejected approach recurs;
- two plausible approaches fail without producing a stronger diagnosis;
- repeated searches or reads do not reduce uncertainty;
- the agent cannot explain the next step and the evidence supporting it;
- it starts guessing, thrashing, weakening the goal, or proposing a workaround;
- the hook emits a `JARVIS_STUCK` instruction.

Stop mutation, send Jarvis the goal contract plus the smallest useful failure evidence, and ask for:

1. the most likely false assumption or missing fact;
2. a ranked set of next diagnostic actions;
3. the narrowest action that can falsify the leading hypothesis;
4. explicit conditions for resuming implementation or declaring a blocker.

Do not ask Jarvis to solve the entire task in place of the primary agent. Jarvis guides the diagnosis and restores a grounded path. After applying its guidance and obtaining `RESUME`, run:

```sh
python3 "<plugin_root>/scripts/jarvis_control.py" checkpoint rescue --marker jarvis-explicit-v1
```

## Finish Under Review

Before the final answer, send Jarvis:

- the original goal contract;
- the resulting changes or answer;
- checks run and their outcomes;
- skipped checks, remaining uncertainty, and residual risk.

Wait for `PASS` or `CHANGES_REQUESTED`. Continue working on every in-scope `CHANGES_REQUESTED` item. Only after `PASS`, run:

```sh
python3 "<plugin_root>/scripts/jarvis_control.py" approve-final --marker jarvis-explicit-v1
```

The `Stop` hook forces one continuation when final approval is missing. It deliberately allows the next stop to avoid an infinite loop, so never treat that safety valve as approval.

## Stop Jarvis Early

Only when the user explicitly asks to stop supervision, stop or close the supervisor and run:

```sh
python3 "<plugin_root>/scripts/jarvis_control.py" deactivate --marker jarvis-explicit-v1
```
