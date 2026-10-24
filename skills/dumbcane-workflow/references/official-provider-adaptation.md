# Codex adaptation of official v7.0.1

Applies to the [pinned official source](superpowers-profile.json). Provider files
stay unmodified. These integration rules belong to Dumbcane; they do not describe
changes to upstream defaults. Follow the real instruction hierarchy. Official
`using-superpowers` explicitly gives user instructions precedence.

| Area | Official default and integration rule |
| --- | --- |
| Design and planning | Brainstorming requires design approval and writing-plans requires plan review before execution. Retain these gates unless a higher-priority instruction explicitly resolves them. Reuse approval only when it actually covers the current design/plan. General implementation intent does not prove an unseen plan was reviewed. |
| Workspace and Git | Consume the user's workspace preference; official worktree guidance permits in-place work when isolation is declined. Do not create a worktree, initialize Git, commit or publish merely because a helper expects Git. For authorized non-Git work, apply task/spec/test discipline with an ordinary progress record, identify unavailable Git helper steps and never claim they ran. |
| Tools and models | Use the live Codex interface and real parameters. Upstream's Codex reference assumes particular tools and model controls. Governing platform/user restrictions take precedence; do not edit configuration or force a model override to imitate that reference. |
| TDD | Official TDD applies to code and repairs; its proposed exceptions require applicable user permission. Do not label an automatic configuration exemption as upstream behavior. Preserve valid existing work; do not delete it to manufacture RED. Pure prose can be inspected without claiming a behavioral test. |
| Verification | Upstream asks for fresh command evidence. If governing project/user instructions explicitly permit unchanged evidence reuse, record the basis and matching state; otherwise follow upstream. Never call an unrun test passed. |
| Review and recovery | Keep one execution/review loop. SDD's review-loop limit differs from debugging's three failed fixes to the same fault; discuss architecture before a fourth repair. Preserve failures across handoffs. Do not park an acceptance failure and report the requested behavior complete. |
| Cleanup | Use actual ownership and retention requirements. A directory name is not ownership proof. Do not delete user work, evidence or logs because upstream calls a workspace scratch. Task records remain private by default; publication needs separate authorization. |

## Diagnostic source observations

Pinned `systematic-debugging/find-polluter.sh` uses `npm test`, suppresses its
failure, and may print clean with zero selected tests. Inspect selection, execution
and before/after state. Its exit code alone is not successful testing. Use the
project's real stack rather than installing npm to force this helper to run.

The root-cause-tracing diagram includes a dead-end symptom-fix branch, while its
prose and main debugging method require finding the source. Follow the main method.
An unresolved cause stays unresolved; mitigation is not proof of root-cause repair.

## Resources and data

Optional brainstorming visuals may launch a server or contact external services.
Inspect helpers first and keep the feature optional. Follow actual browser,
network, cost and cleanup controls; this adapter grants none. Dumbcane's installer
and workflow do not automatically upload task content or enable telemetry.
