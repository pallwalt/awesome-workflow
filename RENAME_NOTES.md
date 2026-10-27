# Rename notes

The public product name is Awesome Workflow (`awesome-workflow`). The previous product name was dumbcane-workflow. The repository skill path is `skills/awesome-workflow`. New installs use `~/.local/share/awesome-workflow/` and `~/.agents/skills/awesome-workflow`. The clone URL is `https://github.com/pallwalt/awesome-workflow`.

## Migration choice

`scripts/manage.py` moves an owned previous install on `install`, `update`, `rollback`, and `uninstall`. `doctor` stays read-only: it checks a not-yet-migrated install and does not rename it.

The data directory `~/.local/share/dumbcane-workflow` is renamed to `~/.local/share/awesome-workflow` only when its state records manager id `dumbcane-workflow`. The discoverable skill link is moved from `~/.agents/skills/dumbcane-workflow` to `~/.agents/skills/awesome-workflow` only when that link is a symlink into the managed releases directory. The link target is rewritten to the renamed data directory.

The tool does not merge the two data directories. If both exist, it stops and preserves both. It does not adopt, delete, or overwrite a skill entry that is not an owned symlink. Snapshots already on disk keep their receipt bytes, including manager id `dumbcane-workflow` and package paths under `skills/dumbcane-workflow`. A later transaction writes manager id `awesome-workflow` into new state. A same-release update migrates the directories and leaves the recorded snapshot unchanged.

Interrupted journals may still name a parking directory `.dumbcane-workflow.<32 hex>.switch`. New journals use `.awesome-workflow.<32 hex>.switch`. Comparisons accept a release path that still uses the previous data-directory prefix.

Task notes stored outside the installer under `dumbcane-workflow/tasks/` are not moved.

## Intentional remaining matches

A case-insensitive search for `dumbcane`, excluding `.git`, remains only in:

- `RENAME_NOTES.md` (this file)
- `scripts/manage.py` (previous directory, manager id, skill path, parking-name acceptance, and migration messages)

No other path should contain the previous name.
