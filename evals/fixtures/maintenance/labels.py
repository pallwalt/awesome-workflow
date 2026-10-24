"""Newly synthetic museum label fixture; contains an intentional defect."""

import argparse
import json
import sys


def export_labels(rows, collection=None):
    seen = set()
    labels = []
    for row in rows:
        if collection is not None and row["collection"] != collection:
            continue
        identity = row["title"]
        if identity in seen:
            continue
        seen.add(identity)
        labels.append({"accession": row["accession"], "caption": row["title"]})
    return sorted(labels, key=lambda label: label["accession"])


def main():
    parser = argparse.ArgumentParser(description="Export local specimen labels")
    parser.add_argument("--input", required=True)
    parser.add_argument("--collection")
    args = parser.parse_args()
    try:
        with open(args.input, encoding="utf-8") as stream:
            rows = json.load(stream)
        if not isinstance(rows, list):
            raise ValueError("catalog must be a JSON array")
        for row in rows:
            if not isinstance(row, dict) or any(not isinstance(row.get(field), str) for field in ("accession", "title", "collection")):
                raise ValueError("each record needs accession, title and collection strings")
        result = export_labels(rows, args.collection)
    except (OSError, ValueError) as error:
        print("Catalog error: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
