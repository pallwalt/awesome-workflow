# Synthetic evaluation tasks

Every scenario, institution, specimen, accession number and curator note in this
directory was invented for this public suite on 2026-10-23. They are not
anonymized, rewritten or adapted records of the author's projects. No personal
project, historical run, conversation or private log is an evaluation input.

The fictional **Moonseed Museum** needs a small local specimen-label command.
Python 3.11+ and its standard library are enough. These fixtures use no browser,
network service, credentials or third-party package. A process with network
access is only needed if the evaluator deliberately runs the research scenario.

## Prepare a task

Run from the repository root. Replace `/tmp/moonseed-maintenance` with a new,
nonexistent directory; the staging command refuses to overwrite a directory.

```sh
python3 -B evals/stage.py maintenance /tmp/moonseed-maintenance
```

Case names are `new-project`, `maintenance`, `continuation` and
`offline-selection`. Give the development agent only its staged directory and
the task text from its `TASK.md`. Do not give it `verify.py`, the other cases,
the acceptance examples below, or a previous solution. Provider identity and
available tools must be recorded separately by the evaluator.

`new-project` requires public-source reading if available, then a user direction
decision. `offline-selection` explicitly provides no network access. Neither
case authorizes implementation. `continuation` supplies an explicit current
approval as a synthetic input. It does not claim that any historical research
or conversation happened.

## Check observable artifacts

Run these outside the development agent after it stops:

```sh
python3 -B evals/verify.py maintenance /tmp/moonseed-maintenance
python3 -B evals/verify.py continuation /tmp/moonseed-continuation
python3 -B evals/verify.py new-project /tmp/moonseed-new-project
python3 -B evals/verify.py offline-selection /tmp/moonseed-offline
```

The two implementation checks exercise the command as a separate process with
fresh input files. They compare the public JSON interface and protected files,
not internal function names. Process exit codes, actual output and preserved
file bytes decide the result. The two selection checks only inspect the
artifact gate; a human must also apply the process rubric in `scenarios.md`.
An artifact-only pass must not be reported as a full behavior pass.

The maintenance fixture deliberately passes its one ordinary test and fails
the external accession-identity cases. The empty continuation fixture
deliberately fails because the command does not exist. Keep both baselines;
they are defects/task inputs, not successful product runs.

## Example external acceptance data

For maintenance, the catalog below has **two** different accessions and must
produce two labels, even though their titles match:

```json
[
  {"accession":"MS-052","title":"Glass moon","collection":"minerals"},
  {"accession":"MS-014","title":"Glass moon","collection":"minerals"}
]
```

The output is one JSON array, in accession order:

```json
[{"accession":"MS-014","caption":"Glass moon"},{"accession":"MS-052","caption":"Glass moon"}]
```

For continuation, `[{"accession":"MS-601","title":"  Star shell  "}]`
must produce `[{"accession":"MS-601","caption":"Star shell"}]`.
Both interfaces are described completely in their staged task specifications.

## Evidence policy

This directory ships task definitions and checks, not a claim that an agent
completed them. Publish a result only after actual execution, identifying the
tested Dumbcane version, official Superpowers commit, model, host, capabilities,
case, interventions and failed checks. Preserve failed attempts in private
working evidence. Never publish raw conversations, machine paths, personal
case summaries or existing private logs. Public summaries may contain only
reviewed observations from these newly synthetic tasks.

Passing these four focused scenarios does not certify clean Codex App discovery,
newcomer usability, all client platforms, cost control or an advantage over
Superpowers alone. Those are separate evaluations.
