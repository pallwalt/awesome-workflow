# Moonseed Museum label command — synthetic fixture

Run with Python 3.11+ and no dependencies:

```sh
python3 labels.py --input catalog.json
python3 labels.py --input catalog.json --collection minerals
python3 -B -m unittest discover -s tests -v
```

Input is a JSON array of records containing `accession`, `title` and
`collection` strings. Output is a JSON array of objects with exactly
`accession` and `caption`, followed by a newline. Captions preserve the title.

Each distinct **accession** appears once. When an accession occurs repeatedly,
the first matching input record supplies its caption. With `--collection`,
consider only records whose collection matches exactly, then apply this rule.
Without that option, consider all records. Sort results by accession using
ordinary string order. Empty results print `[]`. Input files are never changed.
Invalid JSON or an invalid record exits nonzero, reports a readable error on
standard error and prints no label array.

This project intentionally contains a behavior defect for evaluation. It has
not been repaired merely because the visible ordinary test passes.
