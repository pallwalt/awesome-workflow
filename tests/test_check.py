"""Behavior tests for the read-only checker; no workflow-quality claims."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check.py"
STAGES = (
    "using-superpowers", "brainstorming", "writing-plans",
    "systematic-debugging", "test-driven-development", "receiving-code-review",
    "executing-plans", "subagent-driven-development", "verification-before-completion",
    "requesting-code-review", "using-git-worktrees", "finishing-a-development-branch",
)


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / "package"
        self.provider = self.root / "provider"
        self.skill = self.package / "skills/dumbcane-workflow/SKILL.md"
        self.profile_path = self.skill.parent / "references/superpowers-profile.json"
        self.skill.parent.mkdir(parents=True)
        self.profile_path.parent.mkdir()
        self.skill.write_text(
            "---\nname: dumbcane-workflow\ndescription: Test package metadata.\n---\n"
            "[Profile](references/superpowers-profile.json)\n", encoding="utf-8"
        )
        self.profile = {
            "schema_version": 1,
            "profile_id": "test-local",
            "provider": {"name": "Local test", "upstream": "https://example.org/upstream",
                         "revision": None, "provenance": "Synthetic fixture"},
            "behavioral_status": "not_certified",
            "skills": {}, "files": {},
        }
        for name in STAGES:
            relative = "skills/" + name + "/SKILL.md"
            file = self.provider / relative
            file.parent.mkdir(parents=True)
            data = ("Provider fixture " + name + "\n").encode()
            file.write_bytes(data)
            self.profile["skills"][name] = relative
            self.profile["files"][relative] = hashlib.sha256(data).hexdigest()
        self.save_profile()

    def save_profile(self):
        self.profile_path.write_text(json.dumps(self.profile), encoding="utf-8")

    def run_check(self, *args, provider=False, cwd=None, package_arg=None):
        command = [sys.executable, str(SCRIPT), "--package-root",
                   str(self.package if package_arg is None else package_arg), "--json"]
        if provider:
            command += ["--provider-root", str(self.provider)]
        command += list(map(str, args))
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self.fail(f"Expected one JSON object, exit={result.returncode}, "
                      f"stdout={result.stdout!r}, stderr={result.stderr!r}: {exc}")
        self.assertIsInstance(output["errors"], list)
        self.assertIs(type(output["checked_files"]), int)
        self.assertEqual(output["schema_version"], 1)
        return result, output

    def assert_failure(self, output, message):
        result, report = output
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(message.lower() in item.lower() for item in report["errors"]),
                        report["errors"])
        return report

    def original_pair(self):
        original = self.root / "original.md"
        original.write_bytes(b"Unchanged original\n")
        baseline = self.root / "baseline.json"
        baseline.write_text(json.dumps({"sha256": hashlib.sha256(original.read_bytes()).hexdigest()}))
        return original, baseline

    def snapshot(self):
        return {str(path.relative_to(self.root)): (path.read_bytes(), path.stat().st_mode)
                for path in self.root.rglob("*") if path.is_file()}

    def test_no_provider_is_not_checked_and_not_certified(self):
        result, report = self.run_check()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["package_status"], "pass")
        self.assertEqual(report["provider_status"], "not_checked")
        self.assertEqual(report["behavioral_status"], "not_certified")
        self.assertEqual(report["original_status"], "not_checked")
        self.assertEqual(report["errors"], [])

    def test_matching_bytes_do_not_certify_behavior(self):
        result, report = self.run_check(provider=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["provider_status"], "content_match")
        self.assertEqual(report["behavioral_status"], "not_certified")
        self.assertGreaterEqual(report["checked_files"], len(STAGES) + 2)

    def test_modified_provider_has_drift_and_nonzero_exit(self):
        (self.provider / self.profile["skills"][STAGES[0]]).write_bytes(b"changed")
        report = self.assert_failure(self.run_check(provider=True), "hash")
        self.assertEqual(report["provider_status"], "drift")
        self.assertEqual(report["package_status"], "pass")
        self.assertEqual(report["behavioral_status"], "not_certified")

    def test_missing_provider_resource(self):
        (self.provider / self.profile["skills"][STAGES[0]]).unlink()
        report = self.assert_failure(self.run_check(provider=True), "missing")
        self.assertEqual(report["provider_status"], "missing")

    def test_provider_root_does_not_exist(self):
        report = self.assert_failure(self.run_check("--provider-root", self.root / "absent"), "provider")
        self.assertEqual(report["provider_status"], "missing")

    def test_provider_root_symlink_loop_returns_structured_failure(self):
        loop = self.root / "provider-loop"
        loop.symlink_to(loop)
        report = self.assert_failure(self.run_check("--provider-root", loop), "provider")
        self.assertEqual(report["provider_status"], "invalid")

    def test_unknown_additional_provider_must_be_explicitly_locked(self):
        self.profile["skills"]["extra-stage"] = self.profile["skills"][STAGES[0]]
        self.save_profile()
        result, report = self.run_check(provider=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["provider_status"], "content_match")

    def test_missing_required_stage_is_invalid(self):
        del self.profile["skills"][STAGES[0]]
        self.save_profile()
        report = self.assert_failure(self.run_check(), STAGES[0])
        self.assertEqual(report["provider_status"], "invalid")
        self.assertEqual(report["package_status"], "fail")

    def test_undeclared_entry_is_invalid(self):
        self.profile["skills"][STAGES[0]] = "skills/new/SKILL.md"
        self.save_profile()
        self.assert_failure(self.run_check(), "files")

    def test_empty_maps_are_invalid(self):
        for key in ("skills", "files"):
            with self.subTest(key=key):
                saved = self.profile[key]
                self.profile[key] = {}
                self.save_profile()
                self.assert_failure(self.run_check(), key)
                self.profile[key] = saved

    def test_invalid_digest_rejected(self):
        self.profile["files"][next(iter(self.profile["files"]))] = "A" * 64
        self.save_profile()
        self.assert_failure(self.run_check(), "digest")

    def test_profile_traversal_rejected_even_without_provider(self):
        for path in ("../outside.md", "skills/../outside.md", "/absolute.md", "C:\\outside.md"):
            with self.subTest(path=path):
                self.profile["files"][path] = "0" * 64
                self.save_profile()
                self.assert_failure(self.run_check(), "path")
                del self.profile["files"][path]

    def test_duplicate_json_keys_rejected(self):
        text = json.dumps(self.profile)
        self.profile_path.write_text(text[:-1] + ', "schema_version": 1}')
        report = self.assert_failure(self.run_check(), "duplicate")
        self.assertEqual(report["provider_status"], "invalid")

    def test_malformed_profile_rejected(self):
        self.profile_path.write_text("{not json}")
        self.assert_failure(self.run_check(), "profile")

    def test_boolean_schema_version_is_not_integer_version(self):
        self.profile["schema_version"] = True
        self.save_profile()
        self.assert_failure(self.run_check(), "schema_version")

    def test_provider_symlink_escape_rejected(self):
        file = self.provider / self.profile["skills"][STAGES[0]]
        outside = self.root / "outside.md"
        outside.write_bytes(file.read_bytes())
        file.unlink()
        file.symlink_to(outside)
        report = self.assert_failure(self.run_check(provider=True), "outside")
        self.assertEqual(report["provider_status"], "invalid")

    def test_broken_skill_reference_rejected(self):
        with self.skill.open("a") as file:
            file.write("[Missing asset](assets/missing.txt)\n")
        self.assert_failure(self.run_check(), "missing.txt")

    def test_broken_doc_reference_rejected(self):
        (self.package / "README.md").write_text("[Missing](docs/missing.md)")
        self.assert_failure(self.run_check(), "missing.md")

    def test_parent_relative_and_encoded_asset_links_are_valid(self):
        docs = self.package / "docs"
        docs.mkdir()
        (docs / "asset (1).txt").write_bytes(b"asset")
        (docs / "readme.md").write_text("[Skill](../skills/dumbcane-workflow/SKILL.md#part)\n"
                                        "[Asset](asset%20(1).txt)\n"
                                        "[Asset with title](<asset (1).txt> \"title\")\n")
        result, report = self.run_check()
        self.assertEqual(result.returncode, 0, report)

    def test_reference_style_links_checked(self):
        (self.package / "README.md").write_text("[Example][ref]\n\n[ref]: missing.md \"Title\"\n")
        self.assert_failure(self.run_check(), "missing.md")

    def test_escape_link_rejected_even_when_target_exists(self):
        (self.root / "outside.md").write_text("exists")
        (self.package / "README.md").write_text("[Escape](../outside.md)")
        self.assert_failure(self.run_check(), "outside")

    def test_package_symlink_escape_rejected(self):
        outside = self.root / "outside.md"
        outside.write_text("exists")
        (self.package / "linked.md").symlink_to(outside)
        self.assert_failure(self.run_check(), "symlink")

    def test_package_symlink_directory_escape_rejected(self):
        (self.package / "outside").symlink_to(self.provider, target_is_directory=True)
        self.assert_failure(self.run_check(), "symlink")

    def test_external_anchor_and_fenced_links_ignored(self):
        (self.package / "README.md").write_text(
            "[External](https://example.org/missing) [HTTP](http://example.org/)\n"
            "[Email](mailto:fixture@example.org) [Anchor](#missing)\n"
            "```markdown\n[Not a link](missing.md)\n```\n"
            "~~~~md\n[Not a link](other.md)\n~~~~\n")
        result, report = self.run_check()
        self.assertEqual(result.returncode, 0, report)

    def test_relative_file_uri_is_rejected(self):
        (self.package / "README.md").write_text("[Missing](file:missing.md)\n")
        report = self.assert_failure(self.run_check(), "file:")
        self.assertEqual(report["package_status"], "fail")
        self.assertTrue(any("relative" in error for error in report["errors"]))

    def test_absolute_file_uri_is_rejected_without_following_target(self):
        (self.package / "README.md").write_text("[Outside](file:///etc/passwd)\n")
        report = self.assert_failure(self.run_check(), "file:")
        self.assertEqual(report["package_status"], "fail")

    def test_host_file_uri_is_rejected(self):
        (self.package / "README.md").write_text("[Host](file://host/path)\n")
        report = self.assert_failure(self.run_check(), "file:")
        self.assertEqual(report["package_status"], "fail")

    def test_generated_evidence_directories_ignored(self):
        personal = "/" + "Users" + "/fixture/private.txt"
        for relative in ("checks/evidence.md", "evals/results/run.md"):
            file = self.package / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(f"[Missing](absent.md)\n{personal}\n")
        result, report = self.run_check()
        self.assertEqual(result.returncode, 0, report)

    def test_personal_absolute_path_rejected_in_distributable_text(self):
        personal = "/" + "Users" + "/fixture/private.txt"
        (self.package / "README.md").write_text("Run command against " + personal)
        self.assert_failure(self.run_check(), "personal")

    def test_missing_skill_and_bad_metadata_rejected(self):
        self.skill.unlink()
        self.assert_failure(self.run_check(), "SKILL.md")
        self.skill.write_text("---\nname: wrong-name\ndescription: Fixture.\n---\n")
        self.assert_failure(self.run_check(), "name")

    def test_relative_package_and_provider_roots(self):
        result, report = self.run_check("--provider-root", "provider", cwd=self.root,
                                        package_arg="package")
        self.assertEqual(result.returncode, 0, report)
        self.assertEqual(report["provider_status"], "content_match")

    def test_unchanged_original_and_read_only_filesystem(self):
        original, baseline = self.original_pair()
        before = self.snapshot()
        result, report = self.run_check("--original-skill", original, "--baseline", baseline,
                                        provider=True)
        self.assertEqual(result.returncode, 0, report)
        self.assertEqual(report["original_status"], "unchanged")
        self.assertEqual(before, self.snapshot())

    def test_original_modification_detected_and_preserved(self):
        original, baseline = self.original_pair()
        original.write_bytes(b"Changed original remains present\n")
        changed = original.read_bytes()
        report = self.assert_failure(self.run_check("--original-skill", original,
                                                     "--baseline", baseline), "original")
        self.assertEqual(report["original_status"], "changed")
        self.assertEqual(original.read_bytes(), changed)

    def test_missing_original_and_malformed_baseline(self):
        original, baseline = self.original_pair()
        original.unlink()
        report = self.assert_failure(self.run_check("--original-skill", original,
                                                     "--baseline", baseline), "original")
        self.assertEqual(report["original_status"], "invalid")
        original.write_bytes(b"present")
        baseline.write_text('{"sha256":"not-a-digest"}')
        report = self.assert_failure(self.run_check("--original-skill", original,
                                                     "--baseline", baseline), "baseline")
        self.assertEqual(report["original_status"], "invalid")

    def test_absent_original_flag_pair_is_cli_error(self):
        original, baseline = self.original_pair()
        for flag, value in (("--original-skill", original), ("--baseline", baseline)):
            result, report = self.run_check(flag, value)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(report["original_status"], "invalid")
            self.assertTrue(report["errors"])

    def test_unknown_cli_argument_has_nonzero_structured_error(self):
        result, report = self.run_check("--invented-argument")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(report["errors"])

    def test_original_equals_syntax_still_requires_baseline(self):
        original, _ = self.original_pair()
        result, report = self.run_check("--original-skill=" + str(original))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["original_status"], "invalid")

    def test_default_root_is_parent_of_scripts(self):
        scripts = self.package / "scripts"
        scripts.mkdir()
        shutil.copyfile(SCRIPT, scripts / "check.py")
        result = subprocess.run([sys.executable, str(scripts / "check.py"), "--json"],
                                cwd=self.root, capture_output=True, text=True)
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, report)
        self.assertEqual(report["package_status"], "pass")


if __name__ == "__main__":
    unittest.main()
