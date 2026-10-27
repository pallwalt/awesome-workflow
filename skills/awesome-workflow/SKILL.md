---
name: awesome-workflow
description: Coordinate development in Codex with Superpowers, including new-project GitHub reuse and differentiation review, implementation, maintenance, review feedback and resumption. Preserve investigation or design-only scope.
---

# Awesome Workflow

Help the user turn a development request into a runnable, checkable result that another session can continue. Superpowers is a required method provider. This skill coordinates its methods; it does not implement another development framework or confer tool permissions.

## Start with the requested outcome

1. Identify the requested deliverable and restrictions before taking action: investigate, design, review, implement, or resume. A skill invocation is not permission to implement when the user asked only for a design.
2. Read relevant project instructions and existing work. Distinguish a new project, a change to existing behavior, and a mixed task. Do not infer the route solely from an empty directory or a Git repository.
3. Before a dependent phase, read [Superpowers compatibility](references/superpowers-compatibility.md), resolve the pinned official provider and check its content identity. Read methods from that provider by explicit physical path; a same-named global skill is not a substitute. Missing required methods block the dependent phase, not independent investigation. Never pretend that an absent skill ran.
4. Read [Codex App adaptation](references/codex-app.md) when choosing tools or execution capabilities. Use the live interface. Lack of an optional subagent is not lack of Superpowers.
5. For a new project, use [open-source selection](references/open-source-selection.md) after understanding the core needs and before committing to architecture or writing product code. Research both complete alternatives and useful modules/components; weigh reuse and differentiation equally. Present a recommendation and tradeoffs for the user's route decision. Reuse an already explicit, applicable decision instead of asking again.
6. Use [routing](references/routing.md) to select one primary method and reuse applicable prior work. Match depth to uncertainty, consequences and reversibility, within the dependency's supported rules.

Read [task, delivery and recovery](references/task-delivery-recovery.md) for multi-stage work, a handoff, recovery, or final delivery. Do not load every dependency and reference at startup.

## One controller and one source of task constraints

The current main agent remains the controller. Invoking a Superpowers execution skill changes the controller's method; it does not create another orchestrator. During SDD, use its implementation/review loop, not a simultaneous Awesome Workflow loop for the same task.

Keep one source for the goal, acceptance criteria, workspace, authorization boundaries and artifact locations. Reuse the project's design, plan and execution ledger. Create a short record using [the task record asset](assets/task-record.md) only when continuation or cross-phase coordination needs it. Link to existing artifacts instead of duplicating them.

Distinguish user decisions, agent defaults and unresolved questions. Investigate facts before asking. Recommend reversible technical choices; ask about missing product decisions that materially change the result. Preserve a user-requested approval checkpoint and carry forward valid approvals without asking again merely because a phase changed.

## Workspace contract

Resolve the workspace before implementation; read-only investigation does not need an isolation decision.

- `reuse`: use the existing linked or host-managed worktree.
- `in-place`: use the current project when there is no concrete isolation requirement.
- `isolated`: create one worktree only when this task has explicitly authorized it and the host permits it.

A main branch, a dirty checkout, task complexity or delegation alone does not require isolation. Investigate overlapping edits and concrete concurrency risks. If safe implementation cannot proceed, record the blocker rather than inventing another checkout.

The controller alone handles approved Git topology changes. Preserve user edits and untracked content. Before writing a file that changed during the task, reread it and reconcile the change. Do not commit, push, publish, install tools or change access merely to satisfy a method's default convention; apply the actual task authorization and instruction hierarchy.

## Bounded delegation

Delegate only when the host supports it and a bounded assignment benefits. Include the goal, exact scope, relevant facts, acceptance criteria, applicable authorization and report format. Do not assume conversation inheritance or a particular subagent tool name.

Every implementation or review dispatch carries the resolved absolute workspace path and mode, and states: operate only in this workspace; do not create/remove worktrees, clone, switch branches or rewrite Git topology; report conflicts to the controller. Assign one implementation writer per file. Follow project resource limits for parallel read-only work.

Do not force a model change, enablement setting or new user-owned chat to obtain delegation. Use a supported inline execution path when available. If an independent review is required and no equivalent exists, report that specific missing gate instead of labelling self-review independent.

## Recovery and evidence

Preserve completed work, failures and the actual execution state. Resume the original implementer when useful; if unavailable, use the provider's supported handoff or inline path. Repeated failures require new evidence or a changed approach, not an unlimited identical retry loop. A handoff does not reset the same fault's failed-fix count; honor the provider's applicable architecture-discussion gate before further fixes. Reconcile current files before redispatch.

The skill cannot enforce file isolation or a monetary budget by prose. Use actual host controls when available. Track observable limits and stop dependent expenditure when a real limit is reached; do not claim a hard money cap when cost accounting or a stop control is unavailable.

Select verification for the acceptance criteria and change: behavior tests, build/schema checks, actual runtime or visual checks, or direct inspection as appropriate. Reuse evidence only while the relevant artifacts, dependencies, configuration, inputs and environment remain unchanged. Missing evidence stays missing; do not weaken a check, erase a failure or borrow another version's result.

## Deliver for the user

Explain progress through outcomes, decisions and remaining uncertainty, not a list of skill names. Preserve the user's language and explain necessary technical terms.

Finish with the result status, what changed, how to run/use or review it, actual verification, remaining limits, and where to continue. A design-only task completes when its design deliverable is ready; an implementation request is not complete just because its plan is ready. See the [delivery contract](references/task-delivery-recovery.md#delivery).

This release pins official Superpowers v7.0.1, with unmodified provider bytes and a separate [host adaptation](references/official-provider-adaptation.md). Content matching proves identity only. Consult the public validation report for the actual synthetic trials; clean App discovery, comparative improvement and human usability require their own evidence. User projects, cases, logs and rewritten summaries stay private; do not upload task records as examples or telemetry. Public demonstrations must be newly authored fictional material.
