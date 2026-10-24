# Checker interface contract

The repository checker is a read-only Python 3.11+ standard-library tool. It performs no installation, network requests, or writes. The separate [installation tool](installation.md) manages version transitions.

```sh
python3 -B scripts/check.py --package-root PATH --json
python3 -B scripts/check.py --package-root PATH --provider-root PATH --json
```

The default package root is the parent of `scripts/`. Optional original-preservation checks use `--original-skill PATH --baseline PATH` together; they compare supplied bytes without creating a baseline. Public test inputs for this interface must be newly synthetic.

## Package checks

Inspect `skills/dumbcane-workflow/SKILL.md`, local Markdown references and assets, and local Markdown links throughout the distributable package. Exclude generated `checks/`, `evals/results/`, `.git`, and bytecode caches. Ignore external destinations, anchors, and links inside fenced code blocks. Reject broken local references, paths escaping the package, symlinks escaping the package, and personal absolute paths in distributable text.

The own-package metadata check covers this package's required name and description. It is not a general YAML parser or a replacement for an applicable full skill validator.

## Provider profile

The actual [profile](../skills/dumbcane-workflow/references/superpowers-profile.json) declares schema version, profile identity, public provider provenance and fixed revision, behavior status, method entry paths, and required file SHA-256 values. It identifies official `obra/superpowers` v7.0.1 at commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`.

Provider-relative paths must be portable and remain inside an explicitly supplied provider root. Reject absolute paths, traversal, malformed hashes, duplicate JSON keys, empty maps, undeclared method entries, and files resolving outside that root. Each method entry must also be present in the file map.

Required method keys are:

- `using-superpowers`
- `brainstorming`
- `writing-plans`
- `systematic-debugging`
- `test-driven-development`
- `receiving-code-review`
- `executing-plans`
- `subagent-driven-development`
- `verification-before-completion`
- `requesting-code-review`
- `using-git-worktrees`
- `finishing-a-development-branch`

A profile hash identifies content. Neither a match nor an upstream tag proves runtime behavior, permission to take an action, or successful completion of a project.

## JSON and exit status

`--json` emits one JSON object on stdout. Fields:

| Field | Values / meaning |
| --- | --- |
| `schema_version` | `1` |
| `package_status` | `pass` or `fail` for package checks |
| `provider_status` | `not_checked`, `content_match`, `drift`, `missing`, or `invalid` |
| `behavioral_status` | The profile's explicitly declared behavior boundary; not promoted by matching bytes |
| `original_status` | `not_checked`, `unchanged`, `changed`, or `invalid` |
| `errors` | Actionable error strings |
| `checked_files` | Count of files actually read |

Without `--provider-root`, provider status remains `not_checked`; this is not a dependency pass. With a root, missing files, changed bytes, and invalid provider inputs are distinct failures. A package pass does not erase a selected provider or original-preservation failure.

Exit code `0` means the selected checks succeeded. `1` means a detected check failure. `2` means invalid CLI syntax, including an unpaired original/baseline argument. The helper does not silently repair inputs or weaken assertions.

## Verification scope

Tests use temporary directories, actual bytes, and CLI subprocess results to cover successful and negative cases: resource drift and absence, invalid and traversing profiles, link failures, relative roots, read-only operation, and preservation checks. The installation lifecycle has separate tests and ownership semantics. Assertions about headings or wording are not workflow-quality evidence.

Actual executed results belong in [validation](validation.md). Keep fixture definitions, observed tool results, native agent behavior, App discovery, and human usability distinct.
