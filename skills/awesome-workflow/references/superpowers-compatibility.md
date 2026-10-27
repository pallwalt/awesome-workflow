# Official Superpowers dependency

This release pins unmodified public `obra/superpowers` v7.0.1 commit
`2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`. The [profile](superpowers-profile.json)
records twelve methods, their resources, source metadata and the official archive
digest. The [host adaptation](official-provider-adaptation.md) explains how real
platform and user instructions constrain their execution.

## Resolve before use

For a managed installation, resolve the skill symlink to its physical directory.
The package root is two levels above that directory; the provider is the sibling
`superpowers` directory of the package. Run that package's `scripts/manage.py doctor
--json` to report actual paths and checks. For an explicit source trial, use the
provider root supplied for the task. Never silently substitute a same-named global
skill.

Run `python3 -B scripts/check.py --provider-root <provider-root> --json` from the
matching package, or compare the profile's SHA256 entries with available read-only
tools. Read needed methods at `<provider-root>/<profile.skills[method]>`, including
their relevant supporting resources from the same root. Reuse identity checks while
the relevant files remain unchanged. The manager's whole-directory receipt also
detects changes outside the enumerated method set.

| Observation | Next action |
| --- | --- |
| Locked resources match | Use the pinned methods within the adaptation and actual evidence scope. |
| Missing or changed resource | Stop the dependent phase; name the missing item or drift. Continue independent investigation. |
| Another official version or unknown collection | Treat as untested. Compare changes and validate a new profile before claiming support. |
| Additional specialist method | Check its source and dependencies; the twelve-method lock does not certify arbitrary extensions. |
| No subagent tool | Use the official inline path when applicable; disclose the absence of independent review. |

Do not overwrite user files, install tools or change client settings merely to
obtain a match. The manager refuses a pre-existing skill entry it does not own.

## Evidence boundary

The archive digest identifies a reproducible download. Matching method bytes
identify source, not correct decisions or source trust by themselves. A directory
input verifies locked resources without authenticating every other file as official;
doctor reports that distinction. Behavior remains `not_certified`. Synthetic trials
are scoped observations, independent from clean App discovery and human usability.

## Upstream updates

Do not follow `main` during a task. A maintainer selects an upstream candidate,
reviews changed methods and resources, creates a new lock, reruns synthetic
scenarios, and releases a tested combination. Existing installs stay pinned until
an explicit update at a safe task boundary. Rollback restores package, profile,
adaptation and provider together. The official plugin marketplace is a separate
installation mechanism; it does not replace this lock.
