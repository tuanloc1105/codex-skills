# OCB Composition and Resume

Read before combining OCB delivery with discuss, plan, or execute, handing off its record, or resuming after compaction or a new session. This reference belongs only to deliver-ocb-change; generic workflow skills and hooks need no OCB dependency.

## Responsibility and Precedence

Discuss, plan, and execute manage conversation, record persistence, mutation boundaries, and technical execution. Deliver OCB Change owns the applicable company delivery requirements: Jira traceability, branch topology, Git authorization, commit cadence, PR size, domain verification, evidence, review ownership, and merge readiness.

Apply the precedence and permitted override rules in core policy. General workflow defaults cannot silently waive a specific OCB requirement. A discussion action or execute action-open is bookkeeping, not approval of an OCB gate. Passing an OCB gate does not authorize mutation while the surrounding workflow is read-only. Both boundaries must permit the action; resolve a real conflict before the dependent action rather than choosing whichever instruction permits more work.

All existing commit rules remain unchanged. In particular, retain exact pre-source branch/local-commit authorization, the first-ticket-owned LinearB init commit before source edits, its clean-index and naming requirements, and immediate smallest-complete-verified-unit implementation commits. Retain the delivery timing choice and the separation of push, MR, and scheduler authorization. Generic guidance making commits optional or allowing later commit grouping does not apply to this OCB delivery scope. Do not implement first and defer those gates until completion. This reference introduces no new commit exception or override.

## Bind OCB Policy to the Existing Record

As soon as an OCB delivery record is established, populate the OCB Policy Binding and Resume section of the workflow contract. Identify this skill, required policy files, resolved domain, affected repositories/paths, profile sources, agreed endpoint, and their source revisions or content fingerprints. Record exact locators rather than copying whole policies or secrets into the bundle.

For a version 4 bundle, keep ownership clear:

| File | OCB content |
| --- | --- |
| `context.md` | Policy binding and source locators; repository/profile and domain boundaries. Link the authoritative contract. |
| `plan.md` | Complete OCB Delivery Workflow Contract and agreed delivery endpoint. In a discussion bundle without plan.md, keep the contract in context.md until a valid handoff adds plan.md, then move it and retain a link. |
| `decisions.md` | User decisions and override records, linked from the corresponding contract gates. |
| `verification.md` | Applicable common/domain checks and results, linked from the contract. Before this file exists in discuss, retain evidence in its existing manifest files. |
| `evidence.md` | Authorization sources, gate observations, commit/MR evidence, handoffs, policy reloads, and remaining owners. |
| Phase files | Executable tasks and acceptance gates for the agreed delivery scope, with links to OCB gates. |
| `index.md` | A short Active Snapshot reminder that OCB policy applies, the contract locator, and an OCB-aware Resume instruction alongside the host workflow's required instruction. |

Use host write transactions and manifest rules when adding or moving content. Keep exactly one authoritative contract; links in other files are navigation, not competing copies. If discuss transitions to a separate plan bundle, carry the policy binding and contract into the destination and mark the source's handoff to that exact destination. Direct discuss-to-execute retains the same bundle. Do not manufacture execute readiness while OCB planning gates remain unresolved.

Keep the host's `Required references` field and rules-sync arguments within its supported reference set. Put OCB policy locators in the binding and resume instruction instead; do not inject company paths into a generic hook allowlist. The hook can enforce record/action bookkeeping, but cannot prove that OCB policies were read or that Jira, GitLab, and domain gates are satisfied. The executing agent must verify those conditions from evidence.

Without a host workflow, retain the same policy binding and contract in the task's existing approved execution record. An explicitly accepted no-plan exception continues under the entrypoint's existing rules; it does not authorize creating a second lifecycle tracker or dropping OCB gates. If the user explicitly excludes OCB delivery, do not reactivate it merely because an old record mentions it; record the scope change when needed and do not claim company delivery completion.

## Resume and Policy Drift

On a handoff, new session, compaction, or material policy/scope change:

1. Read the host record's required scope and locate the OCB binding before dependent planning, implementation, or delivery actions. Treat the recorded OCB scope as an instruction to restore the delivery policies for that task; the user need not repeat the skill name every turn.
2. Resolve the installed deliver-ocb-change directory on the current machine. Read its complete entrypoint, this reference, core policy, repository-profile reference, workflow contract, and the applicable domain policy or both for mixed. Follow the entrypoint's other mandatory reads. A path recorded on another machine is a locator to reconcile, not permission to skip a missing policy.
3. Compare live policy/profile sources with the recorded revisions or fingerprints. Inspect material differences, update source locators and affected gates, and resolve outcome/authority conflicts before dependent work. Do not require identical absolute paths across machines or silently replace a company policy with generic defaults. If the required policy cannot be obtained, report the missing source and pause dependent OCB work.
4. Revalidate relevant repository identity, branch/HEAD/diff, Jira relationships, domain classification, overrides, and MR evidence. Never treat recorded observations as fresh approval, pipeline, or merge evidence.
5. Reconcile authorization action by action under the unchanged core policy. An existing exact authorization covering the action in this session needs no duplicate confirmation after compaction or a mode handoff. Compaction does not itself start a new session. In a genuinely new session, honor OCB's explicit current-session branch/local-commit requirement; older evidence alone does not satisfy it. Do not extend authorization to new repositories, paths, actions, or targets. Scheduled workers continue to use their separately authorized pinned contract under scheduled-delivery policy, not the interactive session's generic permission defaults.
6. Record the reload checkpoint, drift findings, surviving authority, unresolved gates, and next safe action. Continue independent authorized read-only work where useful; do not perform the dependent mutation until both OCB and host boundaries allow it.

After an ordinary prompt within unchanged context, reuse the loaded policies and revalidate only evidence affected by drift. Do not reread the whole policy set or repeat authorization questions on every tool call. After a policy reload, check the actual OCB contract rather than relying solely on a generic mode-restoration message.

## Delivery Outcome and Pause

Keep OCB Workflow State separate from the host's implementation Status and active/paused mode. The default delivery endpoint remains MERGED, unless the user explicitly narrows it; available authorization limits actions but does not silently redefine the endpoint as completed.

| Situation | Record and report |
| --- | --- |
| Code accepted, remaining delivery actions can proceed | CODE_READY with technical checks; continue authorized delivery work. Do not claim the full OCB task is complete. |
| Push/MR/approval or another external prerequisite is unavailable | Record WAITING_EXTERNAL, last achieved state, exact operation, owner, and resume condition. Use the host's Blocked status only when its blocker definition is met. |
| MR exists but Tech Lead approval or merge prerequisites are pending | Retain verified MR_READY evidence and record the external wait. Jira Done and MR_READY are not MERGED. |
| User explicitly requested only preparation or another limited endpoint | Complete only that agreed scope and report its actual OCB state plus remaining delivery owner; do not label it MERGED. |
| User pauses, cancels, or exits | Honor the stop immediately, preserve the last achieved OCB state and unfinished gates, and apply the host's pause/exit procedure. Do not schedule more work or merge to satisfy a completion gate. |
| Merge succeeded and current evidence verifies it | Record MERGED with approver, source/target, checks, merge result, and remaining non-delivery ownership. Stop before deployment or release. |

A pause of the chat workflow does not automatically disable or authorize a separately installed delivery job. Disclose any recorded live job and its cancellation path, and follow scheduled-delivery authorization for changes to it. Do not claim cancellation without verifying the scheduler state.

On completion or handoff, include the exact record path, OCB state, agreed endpoint, evidence limitations, remaining gate owner, and resume condition. Resume prompts must restore OCB policies as well as the host workflow; they must not direct execute to treat technical completion as company delivery completion.
