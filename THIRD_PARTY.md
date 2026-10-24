# Sources and license boundaries

Original Dumbcane repository material is offered under the repository [MIT license](LICENSE). Third-party material retains its own terms. The repository does not vendor the complete Superpowers provider source.

## Superpowers

- Upstream: [obra/superpowers](https://github.com/obra/superpowers).
- Pinned version: **v7.0.1**, commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`.
- Upstream license: [MIT License at the pinned commit](https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/LICENSE), copyright 2025 Jesse Vincent.
- The [profile](skills/dumbcane-workflow/references/superpowers-profile.json) records required method entries and resource hashes. Hashes identify content and do not copy method implementation text or establish behavioral certification.
- Dumbcane's management tool obtains the public pinned archive, preserves the provider's source bytes and `LICENSE`, and stores it separately beside the installed package. The default download and an offline `--provider-archive` verify the full pinned archive digest. An offline `--provider-source` directory is checked only against declared resources; it is not whole-directory provenance authentication.
- Installation instructions in this repository describe Dumbcane's managed layout. They are not an official Superpowers installer, an endorsement, or a claim to replace upstream distribution advice.

The controller's adaptation documents describe routing, tool mapping, authorization boundaries, and recovery outside the upstream provider. They do not rewrite upstream files in place. Relevant upstream changes must be reviewed and validated before a new supported combination is released.

## Other material

The repository tools use Python's standard library. Public demonstrations, fixtures, and evaluation inputs are newly invented for this project and are not derived from private projects, personal histories, or local task transcripts. Illustrative interactions describe intended behavior; only explicitly recorded executed results are evidence.
