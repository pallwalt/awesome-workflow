"""Copy exactly one newly synthetic task, without the controller's checks."""

import json
import shutil
import sys
from pathlib import Path


CASES = ("new-project", "maintenance", "continuation", "offline-selection")


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in CASES:
        raise SystemExit("Usage: python3 evals/stage.py CASE NEW_DIRECTORY; cases: " + ", ".join(CASES))
    case, destination = sys.argv[1], Path(sys.argv[2]).expanduser().resolve()
    evaluation_root = Path(__file__).resolve().parent
    if destination == evaluation_root or evaluation_root in destination.parents:
        raise SystemExit("Stage outside evals/ so the source fixtures remain unchanged.")
    if destination.exists():
        raise SystemExit("Destination already exists; use a new directory.")
    source = evaluation_root / "fixtures" / case
    shutil.copytree(source, destination)
    files = sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file())
    print(json.dumps({"case": case, "directory": str(destination), "files": files}, ensure_ascii=False))


if __name__ == "__main__":
    main()
