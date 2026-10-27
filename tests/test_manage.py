"""New synthetic lifecycle fixtures; no personal projects, histories or logs."""

import hashlib
from http.client import IncompleteRead
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/manage.py"
SPEC = importlib.util.spec_from_file_location("awesome_workflow_manage", SCRIPT)
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        # Every test defaults to the simulated standard-library path. Curl
        # cases explicitly select a local synthetic executable; no live HTTP.
        curl_lookup = mock.patch.object(manage.shutil, "which", return_value=None)
        curl_lookup.start()
        self.addCleanup(curl_lookup.stop)
        self.temporary = tempfile.TemporaryDirectory(prefix="awesome-workflow-synthetic-lifecycle-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.provider = self.root / "provider"
        self.provider.mkdir()
        self.revision = "1" * 40
        for name in manage.METHODS:
            path = self.provider / "skills" / name / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(f"Synthetic method {name}\n", encoding="utf-8")
        (self.provider / "LICENSE").write_text("Synthetic license fixture\n", encoding="utf-8")
        # Non-closure files test that the manager snapshots the whole provider.
        (self.provider / "EXTRA.md").write_text("Synthetic extra upstream file\n", encoding="utf-8")
        self.archive = self.root / "provider.tar.gz"
        with tarfile.open(self.archive, "w:gz") as archive:
            archive.add(self.provider, arcname=f"superpowers-{self.revision}")
        self.source = self.make_source("one", "0.1.0")
        self.source_two = self.make_source("two", "0.2.0")
        self.manager = manage.Manager(self.home)

    def make_source(self, name, version, entry=None):
        source = self.root / name
        source.mkdir()
        entry = entry or manage.ENTRY
        skill = source / entry / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(f"Entirely synthetic skill fixture {version}\n", encoding="utf-8")
        script = source / "scripts/manage.py"
        script.parent.mkdir()
        script.write_text("# Synthetic fixture; never executed\n", encoding="utf-8")
        (source / "README.md").write_text(f"Synthetic release {version}\n", encoding="utf-8")
        profile = {
            "schema_version": 1, "profile_id": f"synthetic-{version}",
            "provider": {"upstream": "https://github.com/obra/superpowers",
                         "revision": self.revision,
                         "archive_url": f"https://codeload.github.com/obra/superpowers/tar.gz/{self.revision}",
                         "archive_sha256": digest(self.archive.read_bytes())},
            "behavioral_status": "not_certified",
            "skills": {name: f"skills/{name}/SKILL.md" for name in manage.METHODS},
            "files": {path.relative_to(self.provider).as_posix(): digest(path.read_bytes())
                      for path in self.provider.rglob("*")
                      if path.is_file() and path.name != "EXTRA.md"},
        }
        profile_path = source / entry / "references/superpowers-profile.json"
        profile_path.parent.mkdir(parents=True)
        write_json(profile_path, profile)
        self.manifest(source, version)
        return source

    def manifest(self, source, version=None):
        if version is None:
            version = json.loads((source / "release.json").read_text())["version"]
        release = {"schema_version": 1, "version": version,
                   "files": {path.relative_to(source).as_posix(): digest(path.read_bytes())
                             for path in source.rglob("*")
                             if path.is_file() and path.name != "release.json"
                             and ".git" not in path.relative_to(source).parts}}
        write_json(source / "release.json", release)

    def run_cli(self, command, source=None, archive=None, provider=None, success=True):
        args = [sys.executable, "-B", str(SCRIPT), command, "--home", str(self.home), "--json"]
        if source is not None:
            args.extend(("--source", str(source)))
        if archive is not None:
            args.extend(("--provider-archive", str(archive)))
        if provider is not None:
            args.extend(("--provider-source", str(provider)))
        result = subprocess.run(args, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0 if success else 1, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def install(self):
        return self.run_cli("install", self.source, self.archive)

    def current_directory(self, component="package"):
        state = json.loads(self.manager.state_file.read_text())
        return self.manager.releases / state["current"]["release_id"] / component

    def snapshot_active(self):
        return self.manager.state_file.read_bytes(), os.readlink(self.manager.entry)

    def test_clean_install_and_read_only_doctor(self):
        report = self.install()
        self.assertEqual(report["behavioral_status"], "not_certified")
        self.assertTrue(self.manager.entry.is_symlink())
        self.assertEqual(len(list((self.home / ".agents/skills").iterdir())), 1)
        self.assertEqual(self.run_cli("doctor")["status"], "pass")

    def test_doctor_does_not_create_home_files(self):
        self.assertEqual(list(self.home.iterdir()), [])
        report = self.run_cli("doctor", success=False)
        self.assertEqual(report["state_status"], "not_installed")
        self.assertEqual(list(self.home.iterdir()), [])

    def test_doctor_preserves_installed_files_and_reports_scopes(self):
        self.install()
        paths = {str(path): (path.lstat().st_mtime_ns, path.lstat().st_size)
                 for path in self.home.rglob("*")}
        report = self.run_cli("doctor")
        after = {str(path): (path.lstat().st_mtime_ns, path.lstat().st_size)
                 for path in self.home.rglob("*")}
        self.assertEqual(paths, after)
        self.assertEqual(report["package_status"], "pass")
        self.assertEqual(report["provider_status"], "pass")
        self.assertTrue(report["archive_verified"])
        self.assertEqual(report["provider_source"], "archive")

    def test_unmanaged_directory_is_never_overwritten(self):
        self.manager.entry.mkdir(parents=True)
        note = self.manager.entry / "user.txt"
        note.write_text("Keep synthetic preexisting content")
        self.run_cli("install", self.source, self.archive, success=False)
        self.assertEqual(note.read_text(), "Keep synthetic preexisting content")
        self.assertFalse(self.manager.state_file.exists())

    def test_unmanaged_broken_symlink_is_never_overwritten(self):
        self.manager.entry.parent.mkdir(parents=True)
        self.manager.entry.symlink_to(self.root / "absent")
        before = os.readlink(self.manager.entry)
        self.run_cli("install", self.source, self.archive, success=False)
        self.assertEqual(os.readlink(self.manager.entry), before)

    def test_source_unknown_file_and_changed_manifest_content_fail(self):
        (self.source / "private-extra.txt").write_text("Synthetic unknown file")
        self.run_cli("install", self.source, self.archive, success=False)
        self.assertFalse(self.manager.entry.exists())
        (self.source / "private-extra.txt").unlink()
        (self.source / "README.md").write_text("Synthetic modified file")
        self.run_cli("install", self.source, self.archive, success=False)
        self.assertFalse(self.manager.entry.exists())

    def test_git_metadata_is_excluded_from_source_copy(self):
        (self.source / ".git").mkdir()
        (self.source / ".git/config").write_text("Synthetic Git metadata")
        self.install()
        self.assertFalse((self.current_directory() / ".git").exists())

    def test_source_manifest_traversal_and_duplicate_keys_rejected(self):
        release_path = self.source / "release.json"
        original = release_path.read_bytes()
        release = json.loads(original)
        release["files"]["../escape"] = "0" * 64
        write_json(release_path, release)
        self.run_cli("install", self.source, self.archive, success=False)
        release_path.write_text('{"schema_version":1,"schema_version":1}')
        self.run_cli("install", self.source, self.archive, success=False)
        self.assertFalse(self.manager.state_file.exists())

    def test_source_symlink_is_rejected_even_when_manifest_hash_matches(self):
        external = self.root / "external.txt"
        external.write_bytes((self.source / "README.md").read_bytes())
        (self.source / "README.md").unlink()
        (self.source / "README.md").symlink_to(external)
        self.run_cli("install", self.source, self.archive, success=False)
        self.assertFalse(self.manager.state_file.exists())

    def test_archive_hash_failure_does_not_change_active_release(self):
        self.install()
        before = self.snapshot_active()
        broken = self.root / "broken.tar.gz"
        broken.write_bytes(b"Synthetic wrong archive")
        self.run_cli("update", self.source_two, broken, success=False)
        self.assertEqual(self.snapshot_active(), before)

    def test_complete_upgrade_rollback_and_uninstall_retain_versions(self):
        first = self.install()["release_id"]
        old_target = os.readlink(self.manager.entry)
        second = self.run_cli("update", self.source_two, self.archive)["release_id"]
        self.assertNotEqual(first, second)
        self.assertNotEqual(os.readlink(self.manager.entry), old_target)
        self.assertEqual(self.run_cli("rollback")["release_id"], first)
        self.assertEqual(os.readlink(self.manager.entry), old_target)
        self.run_cli("doctor")
        before = set(path.name for path in self.manager.releases.iterdir())
        self.run_cli("uninstall")
        self.assertFalse(os.path.lexists(self.manager.entry))
        self.assertEqual(set(path.name for path in self.manager.releases.iterdir()), before)
        self.assertTrue(self.manager.state_file.exists())
        self.assertEqual(self.run_cli("doctor")["state_status"], "uninstalled")
        self.run_cli("install", self.source, self.archive)
        self.run_cli("doctor")
        self.assertEqual(self.run_cli("rollback")["release_id"], second)

    def test_package_edit_blocks_update_and_keeps_user_content(self):
        self.install()
        path = self.current_directory() / "README.md"
        path.write_text("Synthetic user modification")
        before = self.snapshot_active()
        self.run_cli("update", self.source_two, self.archive, success=False)
        self.assertEqual(self.snapshot_active(), before)
        self.assertEqual(path.read_text(), "Synthetic user modification")
        report = self.run_cli("doctor", success=False)
        self.assertEqual(report["package_status"], "fail")

    def test_provider_extra_file_change_blocks_update(self):
        self.install()
        path = self.current_directory("superpowers") / "EXTRA.md"
        path.write_text("Synthetic modified file outside method closure")
        before = self.snapshot_active()
        self.run_cli("update", self.source_two, self.archive, success=False)
        self.assertEqual(self.snapshot_active(), before)
        report = self.run_cli("doctor", success=False)
        self.assertEqual(report["package_status"], "pass")
        self.assertEqual(report["provider_status"], "fail")

    def test_unknown_installed_file_blocks_uninstall_and_is_retained(self):
        self.install()
        note = self.current_directory() / "user.txt"
        note.write_text("Synthetic user file")
        self.run_cli("uninstall", success=False)
        self.assertTrue(self.manager.entry.is_symlink())
        self.assertEqual(note.read_text(), "Synthetic user file")

    def test_tampered_receipt_blocks_mutation(self):
        self.install()
        receipt = self.current_directory().parent / "receipt.json"
        value = json.loads(receipt.read_text())
        value["provider_revision"] = "2" * 40
        write_json(receipt, value)
        before = self.snapshot_active()
        self.run_cli("update", self.source_two, self.archive, success=False)
        self.assertEqual(self.snapshot_active(), before)

    def test_replaced_entry_is_preserved_on_uninstall(self):
        self.install()
        self.manager.entry.unlink()
        self.manager.entry.mkdir()
        note = self.manager.entry / "user.txt"
        note.write_text("Synthetic independent entry")
        self.run_cli("uninstall", success=False)
        self.assertEqual(note.read_text(), "Synthetic independent entry")

    def test_tampered_state_unsafe_identifier_and_control_symlink_rejected(self):
        self.install()
        original = self.manager.state_file.read_bytes()
        state = json.loads(original)
        state["current"]["release_id"] = "../../elsewhere"
        write_json(self.manager.state_file, state)
        self.run_cli("uninstall", success=False)
        external = self.root / "external-state.json"
        external.write_bytes(original)
        self.manager.state_file.unlink()
        self.manager.state_file.symlink_to(external)
        self.run_cli("uninstall", success=False)
        self.assertEqual(external.read_bytes(), original)

    def test_symlinked_management_parent_is_rejected(self):
        foreign = self.root / "foreign"
        foreign.mkdir()
        (self.home / ".local").symlink_to(foreign)
        self.run_cli("install", self.source, self.archive, success=False)
        self.assertEqual(list(foreign.iterdir()), [])

    def test_offline_directory_reports_archive_identity_unverified(self):
        self.run_cli("install", self.source, provider=self.provider)
        report = self.run_cli("doctor")
        self.assertFalse(report["archive_verified"])
        self.assertEqual(report["provider_source"], "local_directory")

    def test_offline_directory_rejects_unlisted_symlink(self):
        (self.provider / "unexpected-link").symlink_to(self.root / "outside")
        self.run_cli("install", self.source, provider=self.provider, success=False)
        self.assertFalse(self.manager.state_file.exists())

    def test_unsafe_archive_entries_rejected_even_with_matching_archive_hash(self):
        for number, kind in enumerate(("traversal", "symlink", "hardlink", "absolute", "duplicate")):
            archive = self.root / f"unsafe-{number}.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                prefix = f"superpowers-{self.revision}"
                name = {"traversal": f"{prefix}/../../escaped",
                        "absolute": "/escaped"}.get(kind, f"{prefix}/unsafe")
                member = tarfile.TarInfo(name)
                if kind == "symlink":
                    member.type, member.linkname = tarfile.SYMTYPE, "../../outside"
                elif kind == "hardlink":
                    member.type, member.linkname = tarfile.LNKTYPE, "../../outside"
                else:
                    member.size = 1
                bundle.addfile(member, io.BytesIO(b"x") if member.isfile() else None)
                if kind == "duplicate":
                    bundle.addfile(member, io.BytesIO(b"x"))
            profile_path = self.source / manage.PROFILE
            profile = json.loads(profile_path.read_text())
            profile["provider"]["archive_sha256"] = digest(archive.read_bytes())
            write_json(profile_path, profile)
            self.manifest(self.source)
            self.run_cli("install", self.source, archive, success=False)
            self.assertFalse(self.manager.state_file.exists())
            self.assertFalse((self.root / "escaped").exists())

    def test_official_url_is_pinned_and_redirect_cannot_escape(self):
        for bad in ("http://codeload.github.com/obra/superpowers/tar.gz/" + self.revision,
                    "https://codeload.github.com.evil.invalid/obra/superpowers/tar.gz/" + self.revision,
                    "https://github.com/obra/superpowers/archive/main.tar.gz",
                    "https://codeload.github.com/obra/superpowers/tar.gz/" + self.revision + "?token=x"):
            with self.assertRaises(manage.ManagerError):
                manage.archive_url(bad, self.revision)
        handler = manage.PinnedRedirect(self.revision)
        with self.assertRaises(manage.ManagerError):
            handler.redirect_request(None, None, 302, "Found", {}, "https://elsewhere.invalid/archive")

    def test_concurrent_manager_refuses_without_changing_active_release(self):
        self.install()
        before = self.snapshot_active()
        with self.manager.lock():
            report = self.run_cli("update", self.source_two, self.archive, success=False)
        self.assertIn("already running", report["error"])
        self.assertEqual(self.snapshot_active(), before)

    def test_write_failure_after_entry_switch_restores_active_combination(self):
        self.install()
        before = self.snapshot_active()
        original = self.manager.atomic_json

        def failing_state_write(path, value):
            if path == self.manager.state_file:
                raise OSError("Synthetic injected disk failure")
            return original(path, value)

        with mock.patch.object(self.manager, "atomic_json", side_effect=failing_state_write):
            with self.assertRaises(OSError):
                self.manager.mutate("update", self.source_two, provider_archive=self.archive)
        self.assertEqual(self.snapshot_active(), before)
        self.assertFalse(self.manager.journal.exists())

    def test_interrupted_transaction_is_reported_readonly_and_recovered(self):
        self.install()
        old = self.manager.state()
        with self.manager.lock():
            descriptor = self.manager.prepare(self.source_two, provider_archive=self.archive)
            new = dict(old, current=descriptor, previous=old["current"])
            parking = self.manager.entry.parent / (".awesome-workflow." + "a" * 32 + ".switch")
            parking.mkdir(mode=0o700)
            write_json(self.manager.journal, {"schema_version": 1, "manager": manage.MANAGER,
                                              "old": old, "new": new, "parking": parking.name})
            self.manager.switch(self.manager.expected_target(old), self.manager.expected_target(new), parking)
        journal_before = self.manager.journal.read_bytes()
        report = self.run_cli("doctor", success=False)
        self.assertTrue(report["recovery_required"])
        self.assertEqual(self.manager.journal.read_bytes(), journal_before)
        self.run_cli("update", self.source, self.archive)
        self.assertEqual(self.manager.state(), old)
        self.assertFalse(self.manager.journal.exists())

    def test_unknown_entry_during_recovery_is_not_replaced(self):
        self.install()
        old = self.manager.state()
        write_json(self.manager.journal, {"schema_version": 1, "manager": manage.MANAGER,
                                          "old": old, "new": dict(old, installed=False),
                                          "parking": ".awesome-workflow." + "b" * 32 + ".switch"})
        self.manager.entry.unlink()
        self.manager.entry.mkdir()
        note = self.manager.entry / "synthetic-user.txt"
        note.write_text("Synthetic independent content")
        self.run_cli("uninstall", success=False)
        self.assertEqual(note.read_text(), "Synthetic independent content")
        self.assertTrue(self.manager.journal.exists())

    def test_entry_replaced_after_last_check_is_retained_and_restored(self):
        self.install()
        before_state = self.manager.state_file.read_bytes()
        original = self.manager.require_target
        calls = 0

        def racing_check(target):
            nonlocal calls
            original(target)
            calls += 1
            if calls == 2:
                self.manager.entry.unlink()
                self.manager.entry.write_text("Synthetic independent file after last check")

        with mock.patch.object(self.manager, "require_target", side_effect=racing_check):
            with self.assertRaises(manage.ManagerError):
                self.manager.mutate("update", self.source_two, provider_archive=self.archive)
        self.assertFalse(self.manager.entry.is_symlink())
        self.assertEqual(self.manager.entry.read_text(), "Synthetic independent file after last check")
        self.assertEqual(self.manager.state_file.read_bytes(), before_state)
        self.assertTrue(self.manager.journal.exists())
        self.run_cli("doctor", success=False)
        self.run_cli("uninstall", success=False)
        self.assertEqual(self.manager.entry.read_text(), "Synthetic independent file after last check")

    def test_new_entry_conflict_after_parking_keeps_both_objects(self):
        self.install()
        original = self.manager.park
        before_state = self.manager.state_file.read_bytes()

        def racing_park(expected, destination):
            original(expected, destination)
            self.manager.entry.write_text("Synthetic independent file after parking")

        with mock.patch.object(self.manager, "park", side_effect=racing_park):
            with self.assertRaises(manage.ManagerError):
                self.manager.mutate("update", self.source_two, provider_archive=self.archive)
        self.assertEqual(self.manager.entry.read_text(), "Synthetic independent file after parking")
        self.assertEqual(self.manager.state_file.read_bytes(), before_state)
        journal = json.loads(self.manager.journal.read_text())
        parked = self.manager.entry.parent / journal["parking"] / "before"
        self.assertTrue(parked.is_symlink())
        self.run_cli("uninstall", success=False)
        self.assertEqual(self.manager.entry.read_text(), "Synthetic independent file after parking")
        self.assertTrue(parked.is_symlink())

    def test_fifo_source_is_rejected_promptly(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("POSIX FIFO required")
        os.mkfifo(self.source / "unexpected-fifo")
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "install", "--home", str(self.home),
                                 "--source", str(self.source), "--provider-archive", str(self.archive), "--json"],
                                capture_output=True, text=True, check=False, timeout=3)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse(self.manager.state_file.exists())

    def test_archive_extraction_uses_verified_bytes_despite_path_replacement(self):
        original_open = manage.tarfile.open
        replacement = self.root / "replacement.tar.gz"
        extra = self.provider / "RACE-EXTRA.md"
        extra.write_text("Synthetic replacement archive extra file")
        with original_open(replacement, "w:gz") as bundle:
            bundle.add(self.provider, arcname=f"superpowers-{self.revision}")
        source_archive = self.archive

        def replacing_open(*args, **kwargs):
            source_archive.write_bytes(replacement.read_bytes())
            return original_open(*args, **kwargs)

        with mock.patch.object(manage.tarfile, "open", side_effect=replacing_open):
            self.manager.mutate("install", self.source, provider_archive=self.archive)
        self.assertFalse((self.current_directory("superpowers") / "RACE-EXTRA.md").exists())
        self.assertTrue(self.run_cli("doctor")["archive_verified"])

    def download_response(self, data, declared="automatic"):
        response = io.BytesIO(data)
        response.headers = {} if declared is None else {
            "Content-Length": str(len(data) if declared == "automatic" else declared)}
        response.geturl = lambda: f"https://codeload.github.com/obra/superpowers/tar.gz/{self.revision}"
        return response

    def download_provider(self):
        return json.loads((self.source / manage.PROFILE).read_text())["provider"]

    def test_download_short_content_length_retries_same_pinned_source(self):
        data = self.archive.read_bytes()
        partial = self.download_response(data[:20], declared=len(data))
        complete = self.download_response(data)
        opener = mock.Mock()
        opener.open.side_effect = [partial, complete]
        destination = self.root / "download.tar.gz"
        with mock.patch.object(manage, "build_opener", return_value=opener), mock.patch.object(manage.time, "sleep"):
            manage.download_archive(self.download_provider(), destination)
        self.assertEqual(opener.open.call_count, 2)
        self.assertEqual(destination.read_bytes(), data)
        requests = [call.args[0] for call in opener.open.call_args_list]
        self.assertEqual({request.full_url for request in requests}, {self.download_provider()["archive_url"]})
        self.assertTrue(requests[0].get_header("User-agent").startswith(manage.USER_AGENT))
        self.assertEqual(requests[0].get_header("Accept-encoding"), "identity")

    def test_download_incomplete_read_and_network_error_have_bounded_retries(self):
        data = self.archive.read_bytes()
        interrupted = self.download_response(data)
        interrupted.read = mock.Mock(side_effect=IncompleteRead(b"synthetic partial", len(data)))
        opener = mock.Mock()
        opener.open.side_effect = [URLError("synthetic network interruption"), interrupted, self.download_response(data)]
        destination = self.root / "download.tar.gz"
        with mock.patch.object(manage, "build_opener", return_value=opener), mock.patch.object(manage.time, "sleep") as pause:
            manage.download_archive(self.download_provider(), destination)
        self.assertEqual(opener.open.call_count, 3)
        self.assertEqual(pause.call_count, 2)
        self.assertEqual(destination.read_bytes(), data)

    def test_download_retry_exhaustion_removes_only_owned_partial(self):
        data = self.archive.read_bytes()
        opener = mock.Mock()
        opener.open.side_effect = [self.download_response(data[:10], declared=len(data)) for _ in range(3)]
        destination = self.root / "download.tar.gz"
        with mock.patch.object(manage, "build_opener", return_value=opener), mock.patch.object(manage.time, "sleep"):
            with self.assertRaisesRegex(manage.ManagerError, "after 3 attempts"):
                manage.download_archive(self.download_provider(), destination)
        self.assertEqual(opener.open.call_count, 3)
        self.assertFalse(destination.exists())

    def test_download_http_404_and_complete_bad_hash_are_not_retried(self):
        for failure in (HTTPError(self.download_provider()["archive_url"], 404, "Synthetic missing archive", {}, None),
                        self.download_response(b"Synthetic complete wrong archive")):
            opener = mock.Mock()
            opener.open.side_effect = [failure]
            destination = self.root / "download.tar.gz"
            with mock.patch.object(manage, "build_opener", return_value=opener), mock.patch.object(manage.time, "sleep") as pause:
                with self.assertRaises(manage.ManagerError):
                    manage.download_archive(self.download_provider(), destination)
            self.assertEqual(opener.open.call_count, 1)
            self.assertFalse(pause.called)
            self.assertFalse(destination.exists())

    def test_download_without_length_still_requires_complete_archive_hash(self):
        data = self.archive.read_bytes()
        opener = mock.Mock()
        opener.open.return_value = self.download_response(data, declared=None)
        destination = self.root / "download.tar.gz"
        with mock.patch.object(manage, "build_opener", return_value=opener):
            manage.download_archive(self.download_provider(), destination)
        self.assertEqual(destination.read_bytes(), data)

    def test_download_existing_destination_is_never_removed(self):
        opener = mock.Mock()
        destination = self.root / "download.tar.gz"
        destination.write_text("Synthetic unrelated existing file")
        with mock.patch.object(manage, "build_opener", return_value=opener):
            with self.assertRaises(FileExistsError):
                manage.download_archive(self.download_provider(), destination)
        self.assertFalse(opener.open.called)
        self.assertEqual(destination.read_text(), "Synthetic unrelated existing file")

    def test_online_update_retry_exhaustion_preserves_active_combination(self):
        self.install()
        before = self.snapshot_active()
        data = self.archive.read_bytes()
        opener = mock.Mock()
        opener.open.side_effect = [self.download_response(data[:10], declared=len(data)) for _ in range(3)]
        with mock.patch.object(manage, "build_opener", return_value=opener), mock.patch.object(manage.time, "sleep"):
            with self.assertRaisesRegex(manage.ManagerError, "after 3 attempts"):
                self.manager.mutate("update", self.source_two)
        self.assertEqual(self.snapshot_active(), before)
        self.assertFalse(self.manager.journal.exists())
        self.assertFalse(any(path.name.startswith(".stage-") for path in self.manager.releases.iterdir()))

    def fake_curl(self, mode):
        path = self.root / "synthetic-curl"
        counter = self.root / "curl-attempts"
        script = f'''#!{sys.executable}
import sys
from pathlib import Path
args = sys.argv[1:]
assert args[0] == "--disable"
assert "--location" not in args and "-L" not in args
assert args[args.index("--output") + 1] == "-"
assert args[args.index("--proto") + 1] == "=https"
assert args[args.index("--max-redirs") + 1] == "0"
assert args[args.index("--url") + 1] == {self.download_provider()["archive_url"]!r}
counter = Path({str(counter)!r})
attempt = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(attempt))
body = Path({str(self.archive)!r}).read_bytes()
status, code = 200, 0
mode = {mode!r}
if mode == "short_retry" and attempt == 1:
    body, code = body[:10], 18
elif mode == "retry_exhaust":
    body, status, code = b"", 0, 28
elif mode == "404":
    body, status, code = b"", 404, 22
elif mode == "wrong_hash":
    body = b"Synthetic complete wrong archive"
elif mode == "oversize":
    body = b"x" * 512
sys.stdout.buffer.write(body)
if mode != "no_footer":
    sys.stdout.buffer.write(("\\n{manage.HTTP_STATUS_LABEL}:%03d\\n" % status).encode())
sys.stdout.buffer.flush()
raise SystemExit(code)
'''
        path.write_text(script, encoding="utf-8")
        path.chmod(0o755)
        return path, counter

    def test_system_curl_is_preferred_without_shell_or_output_path(self):
        executable, counter = self.fake_curl("valid")
        destination = self.root / "curl-download.tar.gz"
        with mock.patch.object(manage.shutil, "which", return_value=str(executable)), \
                mock.patch.object(manage, "build_opener", side_effect=AssertionError("HTTP fallback must not run")):
            manage.download_archive(self.download_provider(), destination)
        self.assertEqual(destination.read_bytes(), self.archive.read_bytes())
        self.assertEqual(counter.read_text(), "1")

    def test_system_curl_partial_transfer_retries_from_empty_owned_file(self):
        executable, counter = self.fake_curl("short_retry")
        destination = self.root / "curl-download.tar.gz"
        with mock.patch.object(manage.shutil, "which", return_value=str(executable)), \
                mock.patch.object(manage.time, "sleep"):
            manage.download_archive(self.download_provider(), destination)
        self.assertEqual(counter.read_text(), "2")
        self.assertEqual(destination.read_bytes(), self.archive.read_bytes())

    def test_system_curl_retry_exhaustion_is_bounded_and_removes_partial(self):
        executable, counter = self.fake_curl("retry_exhaust")
        destination = self.root / "curl-download.tar.gz"
        with mock.patch.object(manage.shutil, "which", return_value=str(executable)), \
                mock.patch.object(manage.time, "sleep"):
            with self.assertRaisesRegex(manage.ManagerError, "after 3 attempts"):
                manage.download_archive(self.download_provider(), destination)
        self.assertEqual(counter.read_text(), "3")
        self.assertFalse(destination.exists())

    def test_system_curl_404_complete_wrong_hash_and_missing_status_do_not_retry(self):
        for mode in ("404", "wrong_hash", "no_footer"):
            executable, counter = self.fake_curl(mode)
            if counter.exists():
                counter.unlink()
            destination = self.root / "curl-download.tar.gz"
            with mock.patch.object(manage.shutil, "which", return_value=str(executable)), \
                    mock.patch.object(manage.time, "sleep") as pause:
                with self.assertRaises(manage.ManagerError):
                    manage.download_archive(self.download_provider(), destination)
            self.assertEqual(counter.read_text(), "1")
            self.assertFalse(destination.exists())
            self.assertFalse(pause.called)

    def test_system_curl_stream_enforces_size_limit_even_without_trusted_transport(self):
        executable, counter = self.fake_curl("oversize")
        destination = self.root / "curl-download.tar.gz"
        with mock.patch.object(manage.shutil, "which", return_value=str(executable)), \
                mock.patch.object(manage, "MAX_ARCHIVE", 256):
            with self.assertRaisesRegex(manage.ManagerError, "size limit"):
                manage.download_archive(self.download_provider(), destination)
        self.assertEqual(counter.read_text(), "1")
        self.assertFalse(destination.exists())

    def move_install_to_legacy_name(self):
        """Relocate a synthetic install onto the previous product paths and manager id."""
        state = json.loads(self.manager.state_file.read_text())
        receipt_path = self.manager.releases / state["current"]["release_id"] / "receipt.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["manager"] = manage.LEGACY_MANAGER
        write_json(receipt_path, receipt)
        state["manager"] = manage.LEGACY_MANAGER
        state["current"]["receipt_sha256"] = digest(receipt_path.read_bytes())
        write_json(self.manager.state_file, state)
        os.rename(self.manager.new_base, self.manager.legacy_base)
        if not self.manager.new_entry.is_symlink():
            self.assertFalse(os.path.lexists(self.manager.new_entry))
            return
        target = os.readlink(self.manager.new_entry)
        prefix = str(self.manager.new_base)
        self.assertTrue(target.startswith(prefix + os.sep), target)
        rewritten = str(self.manager.legacy_base) + target[len(prefix):]
        self.manager.new_entry.unlink()
        self.manager.legacy_entry.symlink_to(rewritten)

    def test_doctor_reads_legacy_install_and_update_migrates_it(self):
        source = self.make_source("legacy-layout", "0.0.9", entry=manage.LEGACY_ENTRY)
        self.run_cli("install", source, self.archive)
        self.move_install_to_legacy_name()
        before = {str(path): path.lstat().st_mtime_ns for path in self.home.rglob("*")}
        report = self.run_cli("doctor")
        after = {str(path): path.lstat().st_mtime_ns for path in self.home.rglob("*")}
        self.assertEqual(before, after)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["skill_root"].endswith("/" + manage.LEGACY_ENTRY))
        self.assertFalse(self.manager.new_base.exists())
        migrated = self.run_cli("update", source, self.archive)
        self.assertIn(manage.LEGACY_MANAGER, migrated["recovery"])
        self.assertFalse(self.manager.legacy_base.exists())
        self.assertTrue(self.manager.new_base.is_dir())
        self.assertFalse(os.path.lexists(self.manager.legacy_entry))
        self.assertTrue(os.readlink(self.manager.new_entry).endswith("/" + manage.LEGACY_ENTRY))
        state = json.loads((self.manager.new_base / "state.json").read_text())
        self.assertEqual(state["manager"], manage.LEGACY_MANAGER)
        receipt_path = self.manager.new_base / "releases" / state["current"]["release_id"] / "receipt.json"
        self.assertEqual(json.loads(receipt_path.read_text())["manager"], manage.LEGACY_MANAGER)
        self.assertEqual(self.run_cli("doctor")["status"], "pass")
        self.run_cli("update", self.source_two, self.archive)
        state = json.loads((self.manager.new_base / "state.json").read_text())
        self.assertEqual(state["manager"], manage.MANAGER)
        self.assertTrue(os.readlink(self.manager.new_entry).endswith("/" + manage.ENTRY))
        previous = self.manager.new_base / "releases" / state["previous"]["release_id"] / "receipt.json"
        self.assertEqual(json.loads(previous.read_text())["manager"], manage.LEGACY_MANAGER)
        self.assertEqual(self.run_cli("doctor")["status"], "pass")

    def test_uninstalled_legacy_home_migrates_on_install(self):
        source = self.make_source("legacy-removed", "0.0.8", entry=manage.LEGACY_ENTRY)
        self.run_cli("install", source, self.archive)
        self.run_cli("uninstall")
        self.move_install_to_legacy_name()
        self.assertFalse(os.path.lexists(self.manager.legacy_entry))
        self.run_cli("install", self.source, self.archive)
        self.assertFalse(self.manager.legacy_base.exists())
        self.assertTrue(os.readlink(self.manager.new_entry).endswith("/" + manage.ENTRY))
        state = json.loads((self.manager.new_base / "state.json").read_text())
        self.assertEqual(state["manager"], manage.MANAGER)
        self.assertEqual(self.run_cli("doctor")["status"], "pass")

    def test_foreign_legacy_skill_entry_is_preserved(self):
        source = self.make_source("legacy-foreign-entry", "0.0.7", entry=manage.LEGACY_ENTRY)
        self.run_cli("install", source, self.archive)
        self.move_install_to_legacy_name()
        self.manager.legacy_entry.unlink()
        self.manager.legacy_entry.mkdir()
        note = self.manager.legacy_entry / "synthetic-user.txt"
        note.write_text("Synthetic independent legacy entry")
        report = self.run_cli("update", self.source_two, self.archive, success=False)
        self.assertIn("preserved", report["error"])
        self.assertEqual(note.read_text(), "Synthetic independent legacy entry")
        self.assertTrue(self.manager.legacy_base.is_dir())
        self.assertFalse(self.manager.new_base.exists())

    def test_unrecognized_legacy_directory_is_preserved(self):
        self.manager.legacy_base.mkdir(parents=True)
        note = self.manager.legacy_base / "keep.txt"
        note.write_text("Synthetic unrelated directory")
        report = self.run_cli("install", self.source, self.archive, success=False)
        self.assertIn("preserved", report["error"])
        self.assertEqual(note.read_text(), "Synthetic unrelated directory")
        self.assertFalse(self.manager.new_base.exists())

    def test_legacy_directory_with_other_manager_id_is_preserved(self):
        source = self.make_source("legacy-other-manager", "0.0.6", entry=manage.LEGACY_ENTRY)
        self.run_cli("install", source, self.archive)
        self.move_install_to_legacy_name()
        state_path = self.manager.legacy_base / "state.json"
        state = json.loads(state_path.read_text())
        state["manager"] = "other-tool"
        write_json(state_path, state)
        link = os.readlink(self.manager.legacy_entry)
        report = self.run_cli("update", self.source_two, self.archive, success=False)
        self.assertIn("preserve", report["error"])
        self.assertEqual(os.readlink(self.manager.legacy_entry), link)
        self.assertTrue(self.manager.legacy_base.is_dir())
        self.assertFalse(self.manager.new_base.exists())

    def test_both_product_directories_are_preserved(self):
        self.install()
        self.manager.legacy_base.mkdir()
        note = self.manager.legacy_base / "keep.txt"
        note.write_text("Synthetic second directory")
        before = self.snapshot_active()
        report = self.run_cli("update", self.source_two, self.archive, success=False)
        self.assertIn("preserved", report["error"])
        self.assertEqual(note.read_text(), "Synthetic second directory")
        self.assertEqual(self.snapshot_active(), before)
        doctor = self.run_cli("doctor", success=False)
        self.assertIn("preserved", " ".join(doctor["errors"]))
        self.assertTrue(self.manager.legacy_base.is_dir())

    def test_legacy_parking_name_and_manager_id_can_recover(self):
        self.install()
        old = dict(self.manager.state(), manager=manage.LEGACY_MANAGER)
        write_json(self.manager.state_file, old)
        with self.manager.lock():
            descriptor = self.manager.prepare(self.source_two, provider_archive=self.archive)
            new = dict(old, current=descriptor, previous=old["current"])
            parking = self.manager.entry.parent / ("." + manage.LEGACY_MANAGER + "." + "c" * 32 + ".switch")
            parking.mkdir(mode=0o700)
            write_json(self.manager.journal, {"schema_version": 1, "manager": manage.LEGACY_MANAGER,
                                              "old": old, "new": new, "parking": parking.name})
            self.manager.switch(self.manager.expected_target(old), self.manager.expected_target(new), parking)
        self.run_cli("doctor", success=False)
        self.run_cli("update", self.source, self.archive)
        self.assertEqual(self.manager.state()["manager"], manage.LEGACY_MANAGER)
        self.assertEqual(self.manager.state()["current"], old["current"])
        self.assertFalse(self.manager.journal.exists())
        self.assertFalse(parking.exists())


if __name__ == "__main__":
    unittest.main()
