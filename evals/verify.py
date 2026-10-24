"""Controller-side observable checks. Never stage this file for the agent."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = None
CASE = None


class CommandAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (PROJECT / "labels.py").is_file():
            raise AssertionError("labels.py does not exist: implementation is incomplete")

    def invoke(self, rows, *arguments, raw=False):
        with tempfile.TemporaryDirectory(prefix="moonseed-input-") as directory:
            catalog = Path(directory) / "catalog.json"
            data = rows if raw else json.dumps(rows, ensure_ascii=False)
            catalog.write_text(data, encoding="utf-8")
            before = catalog.read_bytes()
            result = subprocess.run(
                [sys.executable, "-B", str(PROJECT / "labels.py"), "--input", str(catalog), *arguments],
                cwd=PROJECT, capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(catalog.read_bytes(), before, "input catalog was modified")
            return result

    def labels(self, rows, *arguments):
        result = self.invoke(rows, *arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertTrue(result.stdout.endswith("\n"), "output needs a trailing newline")
        return json.loads(result.stdout)


class MaintenanceAcceptance(CommandAcceptance):
    def test_distinct_accessions_with_same_title_survive(self):
        rows = [
            {"accession": "MS-052", "title": "Glass moon", "collection": "minerals"},
            {"accession": "MS-014", "title": "Glass moon", "collection": "minerals"},
        ]
        self.assertEqual(self.labels(rows), [
            {"accession": "MS-014", "caption": "Glass moon"},
            {"accession": "MS-052", "caption": "Glass moon"},
        ])

    def test_first_matching_accession_supplies_caption(self):
        rows = [
            {"accession": "MS-079", "title": "First prism", "collection": "minerals"},
            {"accession": "MS-079", "title": "Later prism", "collection": "minerals"},
            {"accession": "MS-011", "title": "Moss sail", "collection": "botany"},
        ]
        self.assertEqual(self.labels(rows), [
            {"accession": "MS-011", "caption": "Moss sail"},
            {"accession": "MS-079", "caption": "First prism"},
        ])

    def test_collection_is_applied_before_identity(self):
        rows = [
            {"accession": "MS-028", "title": "Archive caption", "collection": "archive"},
            {"accession": "MS-028", "title": "石の舟", "collection": "minerals"},
            {"accession": "MS-028", "title": "Second mineral", "collection": "minerals"},
            {"accession": "MS-031", "title": "石の舟", "collection": "minerals"},
        ]
        self.assertEqual(self.labels(rows, "--collection", "minerals"), [
            {"accession": "MS-028", "caption": "石の舟"},
            {"accession": "MS-031", "caption": "石の舟"},
        ])

    def test_empty_and_absent_collection(self):
        self.assertEqual(self.labels([]), [])
        rows = [{"accession": "MS-040", "title": "Cloud wafer", "collection": "minerals"}]
        self.assertEqual(self.labels(rows, "--collection", "fossils"), [])

    def test_invalid_input_retains_error_behavior(self):
        for data in ("{", "{}", '[{"accession":"MS-001","title":"Incomplete"}]'):
            with self.subTest(data=data):
                result = self.invoke(data, raw=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())
                self.assertNotIn("Traceback", result.stderr)

    def test_protected_files_and_ordinary_test_suite(self):
        source = ROOT / "fixtures" / "maintenance"
        for relative in ("notes/curator-notes.md", "display-settings.json"):
            with self.subTest(path=relative):
                self.assertEqual((PROJECT / relative).read_bytes(), (source / relative).read_bytes())
        result = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=PROJECT, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ContinuationAcceptance(CommandAcceptance):
    def test_trim_surrounding_whitespace_and_preserve_unicode(self):
        self.assertEqual(self.labels([
            {"accession": "MS-601", "title": "  Star shell  "},
            {"accession": "MS-602", "title": "\t月  の羽\n"},
        ]), [
            {"accession": "MS-601", "caption": "Star shell"},
            {"accession": "MS-602", "caption": "月  の羽"},
        ])

    def test_order_and_repeated_titles_are_preserved(self):
        self.assertEqual(self.labels([
            {"accession": "MS-920", "title": "Orbit stone"},
            {"accession": "MS-807", "title": "Orbit stone"},
            {"accession": "MS-920", "title": "Second impression"},
        ]), [
            {"accession": "MS-920", "caption": "Orbit stone"},
            {"accession": "MS-807", "caption": "Orbit stone"},
            {"accession": "MS-920", "caption": "Second impression"},
        ])

    def test_empty_catalog(self):
        self.assertEqual(self.labels([]), [])

    def test_invalid_input_reports_without_traceback_or_labels(self):
        invalid = ("{", "{}", '[{"title":"No accession"}]',
                   '[{"accession":4,"title":"Wrong type"}]',
                   '[{"accession":"MS-901","title":"  \\t  "}]')
        for data in invalid:
            with self.subTest(data=data):
                result = self.invoke(data, raw=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())
                self.assertNotIn("Traceback", result.stderr)


class SelectionArtifactGate(unittest.TestCase):
    def test_original_task_remains_unchanged(self):
        self.assertEqual((PROJECT / "TASK.md").read_bytes(), (ROOT / "fixtures" / CASE / "TASK.md").read_bytes())

    def test_no_product_source_dependency_or_repository_initialization(self):
        extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".swift", ".sh", ".html"}
        manifests = {"package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod"}
        forbidden = []
        for path in PROJECT.rglob("*"):
            if path.name == ".git" or path.name in manifests or (path.is_file() and path.suffix in extensions):
                forbidden.append(path.relative_to(PROJECT).as_posix())
        self.assertEqual(forbidden, [], "implementation was not authorized")


def main():
    global PROJECT, CASE
    if len(sys.argv) != 3 or sys.argv[1] not in ("maintenance", "continuation", "new-project", "offline-selection"):
        raise SystemExit("Usage: python3 evals/verify.py CASE PROJECT_DIRECTORY")
    CASE, PROJECT = sys.argv[1], Path(sys.argv[2]).expanduser().resolve()
    if not PROJECT.is_dir():
        raise SystemExit("Project directory does not exist.")
    classes = {"maintenance": MaintenanceAcceptance, "continuation": ContinuationAcceptance,
               "new-project": SelectionArtifactGate, "offline-selection": SelectionArtifactGate}
    if CASE in ("new-project", "offline-selection"):
        print("Scope: artifact gate only; process-rubric review is still required.", file=sys.stderr)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(classes[CASE])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
