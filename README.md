# Dumbcane Workflow

[简体中文](README.zh-CN.md)

**A development workflow for people building with an agent. Codex desktop App first.** Dumbcane helps turn an idea or maintenance request into a chosen route, clear acceptance criteria, scoped implementation, observed verification, and a useful continuation record.

The **0.2.0 candidate** uses the public, unmodified [Superpowers v7.0.1](https://github.com/obra/superpowers/tree/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b), pinned to commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`. Installation, dependency checks, updates, rollback, and removal use one repository tool. See [validation](docs/validation.md) for completed checks and open limits; this is not a claim of certified beginner usability.

## What it does

- **Research before a new build.** Look for complete alternatives and reusable components or reference implementations, within a bounded research budget.
- **Make consequential choices clear.** Explain reuse, differentiation, and tradeoffs, then use your overall route decision before product implementation. Reuse an existing decision while it still applies.
- **Maintain the project in front of you.** Start repairs from the actual code, changes, and evidence. Routine maintenance does not require a new product search.
- **Deliver something reviewable.** Report changes, meaningful checks, known gaps, and a continuation point. Preserve the project's existing work.

## Get started

Requirements: Git, Python **3.11 or newer**, and a macOS or Linux environment with symbolic-link support. Windows is not a supported installation target for this candidate.

```sh
git clone https://github.com/pallwalt/dumbcane-workflow.git
cd dumbcane-workflow
python3 -B scripts/manage.py install
python3 -B scripts/manage.py doctor
```

The installer downloads the pinned public Superpowers archive, verifies its archive digest and declared resources, and creates one discoverable Dumbcane entry. It refuses an unrecognized existing installation and leaves other skills and client settings alone. It is **Dumbcane's installation tool**, not the official Superpowers installer.

After installation, start a new Codex desktop App conversation and select or invoke `dumbcane-workflow`. Tell the agent the goal, the target project, and whether it should implement, design, or review. For example:

```text
Use dumbcane-workflow. Help me build a fictional lantern-festival schedule editor.
Work in the project folder I have opened. Start by clarifying the outcome and
comparing existing projects and reusable parts. Let me choose the overall route.
```

Automatic discovery in a clean Codex App session is a separate acceptance step; its current status is in [validation](docs/validation.md). [Installation help](docs/installation.md) includes an explicit-path fallback, offline setup, and recovery. All public examples and test inputs are newly invented; they are not records or rewrites of anyone's private projects.

## Update or go back

Run these in your downloaded source repository, at a suitable task boundary:

```sh
git pull --ff-only
python3 -B scripts/manage.py update
python3 -B scripts/manage.py doctor
```

An update validates a complete Dumbcane/provider combination before switching the entry. It does not automatically follow Superpowers' latest branch. If a previous managed combination exists:

```sh
python3 -B scripts/manage.py rollback
python3 -B scripts/manage.py doctor
```

To remove the managed entry while retaining version snapshots:

```sh
python3 -B scripts/manage.py uninstall
```

See [installation](docs/installation.md) for ownership checks and what each operation preserves.

## How it works with Superpowers

| Layer | Responsibility |
| --- | --- |
| Dumbcane | Task routing, scope, project and component selection, applicable user decisions, status, delivery, and continuation. |
| Superpowers | Engineering methods for design, planning, debugging, testing, implementation, review, and verification. |

Dumbcane loads methods from its pinned installation's physical provider directory. It does not scatter same-named Superpowers methods into your global skill directory. Unknown methods, missing required resources, drift, or unresolved conflicts block the affected stage. Matching hashes establish content identity, not proof that an agent follows a method correctly.

Upstream updates are reviewed as candidates, tested, then included in a new supported combination. Existing tasks retain their installed combination until you update. See [compatibility](skills/dumbcane-workflow/references/superpowers-compatibility.md).

## Read and contribute

- [Skill entry](skills/dumbcane-workflow/SKILL.md), [selection rules](skills/dumbcane-workflow/references/open-source-selection.md), and [optional decision card](skills/dumbcane-workflow/assets/reuse-decision.md)
- Fictional walkthroughs: [new project](docs/examples/new-project.md), [maintenance](docs/examples/maintenance.md), [continuation](docs/examples/continuation.md)
- [Checker contract](docs/checker-contract.md), [evaluation scenarios](evals/scenarios.md), and [validation limits](docs/validation.md)
- [Contributing](CONTRIBUTING.md) and [roadmap](ROADMAP.md)

The public repository must contain no private projects, logs, real-case summaries, or rewritten accounts of private activity. Report a defect using a newly invented, independent reproduction. No command in this package uploads task content or reports.

Original repository material uses the [MIT license](LICENSE). [Third-party notices](THIRD_PARTY.md) explain the separately downloaded provider and its license.
