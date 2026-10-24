# Task records, recovery and delivery

## One small continuation record

Use the [task record asset](../assets/task-record.md) when a task needs cross-phase coordination, handoff or later continuation. Simple one-step edits do not automatically need a new file. Reuse an existing task record where possible.

Prefer an explicitly private project artifact location. Otherwise keep real task records outside the repository, under the user's local application-data directory in `dumbcane-workflow/tasks/<opaque-task-id>/`. Do not put personal cases, runtime logs or rewritten summaries in a public repository, even as a sanitized example. Link to existing Superpowers designs, plans, ledgers and reports instead of copying them. A public contribution or bug reproduction uses newly authored unrelated fictional data. Fill or remove placeholders before treating a record as evidence.

Record the requested deliverable, acceptance, source of decisions, active workspace, actual dependency profile, relevant baseline/user edits, current phase, artifact pointers, checks, failures and next step. Add owned processes/resources only if the task starts them. Do not store secrets, access tokens or model reasoning traces.

## Resume and changes

1. Read the task record and referenced relevant artifacts.
2. Compare them with current files and user updates. A record is historical evidence, not proof of current state.
3. Preserve applicable completed work, decisions, approvals and passing checks.
4. Revisit only affected plans/checks when content, dependencies, configuration, inputs or environment changed.
5. Continue at the first unmet requirement. Ask only when missing information materially blocks it.

Distinguish a clarification, a bounded implementation correction, a material product change and an independent new objective. Replan affected parts as needed; do not automatically restart the entire lifecycle or reopen the workspace choice.

## Failure and handoff

Keep the original symptom, attempted action, observed failure, affected artifacts and current next step. Prefer the same implementer when its context helps. If it cannot continue, reconcile its actual output and hand off through the provider's supported method. Never start a second writer while the first can still mutate the same files.

Use the execution method's supported review/fix loop and task/host resource limits. Repeated failures without new information trigger a changed diagnostic approach. When needed information, access or a real limit prevents further progress, finish independent work and report the specific dependency. Do not weaken checks or silently broaden the scope to make a task pass.

Track what can actually be measured. If the host does not expose complete cost accounting or a monetary stop control, label cost unknown/unenforced and use only the observable authorized limits available. Count subagent attempts and failures when records permit; do not claim complete accounting from a main-agent-only number.

## Verification record

For each important acceptance condition, record the command or inspection, relevant artifact/revision or diff, inputs/environment, observed result, and limits. Use real runtime evidence for runtime claims. Manual or visual inspection is a different form of evidence from an automated regression test.

Separate baseline failures, new regressions, external environment failures and unrun checks. An unrelated baseline failure may be reported without claiming the entire suite passed. An unresolved failure affecting a required acceptance condition prevents completion of that condition. Do not erase failures when appending a later successful result.

## Delivery

Use the user's language and provide:

```text
Result: complete / partial / needs input / blocked
Delivered: what the user can now use or review
Run/use/review: concrete applicable steps
Verified: actual checks and what they establish
Limits: unfinished, failed or unverified requirements
Continue: next step and existing task/artifact entry
```

Choose `complete` only for the requested deliverable and its applicable acceptance. A design-only task can complete without implementation; an implementation task cannot complete from a design or passing scaffold check alone. `Partial` describes delivered work with unmet requirements; `needs input` names a necessary user decision; `blocked` identifies an unavailable external prerequisite. Explain the reason rather than treating the label as evidence.

Before final delivery, stop task-owned services/browser sessions no longer needed and confirm exit. Do not clean unknown files or unrelated user resources. Commits, publishing, installation and uploads remain separate actions requiring their applicable authorization.
