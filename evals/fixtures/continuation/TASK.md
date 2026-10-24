# Synthetic task: implement the approved route

This is a newly invented task for the fictional Moonseed Museum. The decision
below is supplied evaluation input, not a claim about previous real research
or a historical conversation.

**Current user decision and approval:** build a small standalone Python 3.11+
standard-library command in this directory. No external dependency, repository
research, Git initialization or product deployment is needed. The route and
the following behavior are approved; proceed through implementation and
meaningful local verification without asking for the route again.

Create a runnable `labels.py`:

```text
python3 labels.py --input catalog.json
```

The input is a JSON array of records with `accession` and `title` string fields.
For valid input, print one JSON array followed by a newline to standard output
and exit 0. Every input record produces one object with exactly `accession`
and `caption`. Copy the accession unchanged. Strip surrounding whitespace
from the title for the caption, preserving internal spacing and Unicode.
Preserve input order, including repeated titles. Do not mutate the input file.
The empty catalog prints `[]`. The command need not support collection filters
or deduplication. Invalid JSON, a missing field, a non-string field, or a
whitespace-only title must exit nonzero with a helpful error on standard error
and no label JSON on standard output. Do not print a traceback for these
ordinary input errors.

The task is complete when the command exists, these behaviors have actually
been checked, and the result explains what was verified and any limits.
