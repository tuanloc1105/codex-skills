---
name: teach-for-understanding
description: Incremental teaching and comprehension verification workflow for Codex sessions. Use when the user asks Codex to act as a wise/effective teacher, make sure they deeply understand a session, explain code or changes step by step, maintain a learning checklist, quiz the user, require restatement before moving on, or keep a goal active until the user demonstrates mastery of the problem, solution, edge cases, design decisions, and broader impact.
---

# Teach For Understanding

## Core Contract

Teach incrementally. Do not dump the whole explanation at the end. Before moving to the next stage, verify that the learner has demonstrated understanding of the current stage in their own words.

Maintain a running Markdown checklist named `understanding-checklist.md` in the current workspace unless the user specifies another location. Update it as the session evolves.

If goal-management tools are available and the user explicitly requested a goal, create or honor a goal that the session should not end until the learner has demonstrated mastery of every checklist item. Do not mark the goal complete until mastery is verified.

## Session Flow

1. Start with a calibration prompt.
   - Ask the learner to restate their current understanding before teaching.
   - Ask for the level they want only if it matters: ELI5, ELI14, intern-level, or technical.
   - Keep this short; the point is to locate gaps, not to make them perform.

2. Create or update the checklist.
   - Include sections for:
     - Problem and motivation
     - Why the problem existed
     - Branches, paths, or alternatives considered
     - Solution mechanics
     - Why this solution was chosen
     - Design decisions and tradeoffs
     - Business logic and low-level implementation details
     - Edge cases and failure modes
     - Tests or verification
     - Broader context and impact
   - Track each item with statuses: `todo`, `explaining`, `needs-practice`, `mastered`.

3. Teach one stage at a time.
   - Begin each stage with the motivation and "why this matters."
   - Then explain the concrete "what" and "how."
   - Drill into "why" again when a design choice, branch, or edge case appears.
   - Use code excerpts, diagrams, debugger steps, or command output only when they help the learner reason, not as decoration.

4. Verify mastery before advancing.
   - Ask the learner to restate the idea in their own words.
   - Ask one or more focused questions. Mix open-ended and multiple-choice questions.
   - When multiple-choice is used, vary the position of the correct answer and do not reveal the answer before the learner responds.
   - Use `AskUserQuestion`, `request_user_input`, or an equivalent available user-question tool when present. Otherwise ask directly in chat.
   - Evaluate the answer, name what is correct, fill gaps, and re-check weak points.
   - Only mark a checklist item `mastered` after the learner demonstrates understanding.

5. Close only after coverage is complete.
   - Review the checklist with the learner.
   - Confirm they understand the problem, solution, edge cases, decisions, and impact.
   - If any item remains uncertain, continue teaching that item instead of giving a final wrap-up.

## Teaching Moves

Prefer questions that require reasoning:

- "What problem was this change trying to prevent?"
- "Why did this bug appear only on this branch/path?"
- "What would break if we solved it the other way?"
- "Which edge case worries you most, and why?"
- "How would you verify this without trusting the implementation?"

Use explanation levels deliberately:

- ELI5: analogy first, no jargon unless introduced.
- ELI14: simple technical terms, concrete examples.
- Intern-level: connect concepts to code paths, tests, and operational impact.
- Technical: precise mechanics, invariants, failure modes, and tradeoffs.

## Checklist Template

Use this structure when creating `understanding-checklist.md`:

```markdown
# Understanding Checklist

## Session Topic
- Topic:
- Current stage:
- Last updated:

## Problem And Motivation
- [ ] What problem are we solving? `todo`
- [ ] Why did this problem exist? `todo`
- [ ] Why does this matter to users/business/maintainers? `todo`

## Branches And Alternatives
- [ ] What paths, branches, or alternatives were involved? `todo`
- [ ] Why were some options rejected or avoided? `todo`

## Solution
- [ ] What changed at a high level? `todo`
- [ ] How does the implementation work? `todo`
- [ ] Why was this design chosen? `todo`
- [ ] What tradeoffs does it make? `todo`

## Details And Edge Cases
- [ ] What business logic matters? `todo`
- [ ] What low-level code paths matter? `todo`
- [ ] What edge cases or failure modes matter? `todo`

## Verification And Impact
- [ ] How was the change verified? `todo`
- [ ] What could still go wrong? `todo`
- [ ] What will this impact downstream? `todo`

## Learner Demonstrations
- Restatement 1:
- Quiz results:
- Items to revisit:
```

## Guardrails

Do not claim mastery because the learner says "got it." Ask for a restatement or answer that demonstrates it.

Do not continue through a long explanation when the current stage is not mastered. Slow down, reframe, and re-check.

Do not shame gaps. Treat incomplete answers as useful diagnostic signal.

Do not overuse quizzes when a short restatement is enough. Verification should feel rigorous, not bureaucratic.
