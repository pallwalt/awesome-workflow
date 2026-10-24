# Entry routing and phase handoff

## Scope before project type

Interpret the user's requested output first:

- Investigation/review: read and assess within scope. Do not turn it into implementation.
- Design only: produce goals, tradeoffs, acceptance and implementation direction. Save files only when requested or appropriate to the authorized deliverable. Stop at a requested design review.
- Implementation: continue from necessary investigation and planning to the deliverable; do not stop merely because a plan exists.
- Resume: reconcile current files and existing records, then continue at the first unmet requirement.

Explicit invocation does not erase any of those boundaries. New information within the same goal normally updates the affected step; a new objective or side effect requires a fresh scope/authorization assessment.

## Two equally supported entry paths

| Entry | Investigate first | Acceptance focus |
| --- | --- | --- |
| New project | User/use case and constraints; [GitHub selection](open-source-selection.md) across complete alternatives and critical reusable parts; user's chosen route | A repeatably runnable result, agreed data behavior and a clear way to continue maintenance. |
| Existing project | Current versus expected behavior; local instructions and patterns; relevant edits; test/run baseline; compatibility boundaries | The intended change works, relevant existing behavior is checked, and user work is preserved. |
| Mixed | Which pieces are new and which depend on existing behavior | Explicit boundaries for both, with one integrated acceptance contract. |

A repository can contain a new independent app. An empty directory can contain a design-only request. Infer from the goal and dependencies, not directory shape.

For new work, prefer a complete vertical slice before optional breadth. Do not add login, cloud infrastructure, payments or deployment by default. Do not reduce a requested usable product to a throwaway demo. For maintenance, preserve the existing stack and conventions unless the task warrants a change; a bug report is not permission for unrelated refactoring.

New-project selection belongs to the initial design decision, before detailed architecture/planning. Keep one controller and the existing design record. Routine maintenance does not trigger a whole-product search; investigate a genuinely new independent subsystem only to the extent its missing choices warrant it. Learning work can use a lightweight scan while preserving the learning goal. A valid existing route decision/approved plan is consumed on resume, not reopened merely because this skill has been upgraded.

## Select depth without inventing permission gates

| Depth | Indicators | Appropriate coordination |
| --- | --- | --- |
| Light | Clear, low-impact, reversible; established local pattern | Short approach and applicable checks. Avoid duplicate artifacts. |
| Standard | New behavior, meaningful integration, reproducible defect | Acceptance criteria, applicable design/plan, implementation and review/checks. |
| Increased | Material unknowns, important data or permissions, costly rollback | Resolve consequential choices, describe failure/recovery and retain required approval/verification. |

File count is not the deciding factor. These labels select an applicable provider path; they do not waive a provider's hard gate. If the profile and desired depth conflict, resolve the compatibility issue before the dependent action.

## Provider route

| Task | Method to resolve and read when needed |
| --- | --- |
| Skill discovery and provider orientation | `using-superpowers`; do not restart discovery in every bounded child. |
| New-project reuse and differentiation | Dumbcane's [selection reference](open-source-selection.md) supplies evidence to the existing design discussion; no second orchestration loop. |
| Unresolved design or new behavior | `brainstorming`, then `writing-plans` when the supported method calls for a plan. |
| Failure, bug or unexpected behavior | `systematic-debugging`; use `test-driven-development` for the applicable repair. |
| Review feedback | `receiving-code-review` before acting on findings. |
| Existing approved plan | `executing-plans`, or `subagent-driven-development` when beneficial and supported. |
| Behavior implementation | Applicable `test-driven-development` practice; choose appropriate checks for documentation/static work. |
| Existing isolation or authorized creation | `using-git-worktrees`, consuming the existing contract. In-place work does not need worktree creation. |
| Substantial review and completion | `requesting-code-review` and `verification-before-completion`. |
| Authorized branch integration decision | `finishing-a-development-branch`; no forced Git action for a non-Git deliverable. |

Names identify methods, not authority to invent invocation APIs. The [profile and compatibility rules](superpowers-compatibility.md) determine which actual installed entries implement them.

## Phase exits

1. **Investigation:** enough relevant facts to choose the next action; facts, assumptions and missing input are distinct.
2. **Acceptance/design:** observable success conditions and no unresolved product choice that blocks the next step; for new projects, selection coverage or its explicit limits and the user's applicable route decision are recorded; any required design approval covers the actual proposed description.
3. **Planning:** executable slices, dependencies and checks, reusing existing plan artifacts.
4. **Execution:** a slice is ready to verify, or a specific failure is recorded and routed to diagnosis.
5. **Verification:** applicable acceptance has evidence, or the failed/missing part is accurately identified.
6. **Delivery:** the user can run, use or review the requested result and understand its limits.

These are evidence conditions, not six mandatory user confirmations. Existing valid approvals remain valid while their subject and scope remain applicable.
