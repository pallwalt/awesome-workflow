#!/usr/bin/env python3
"""Install one pinned Dumbcane/Superpowers combination without running its code.

Python 3.11+, macOS/Linux. A release manifest is an integrity inventory, not a
signature: obtain this script and release.json from a trusted reviewed release.
Use -B so Python does not add unlisted cache files to an immutable installation.
Downloads use system curl when available, with a standard-library HTTP fallback.
"""

import argparse
import contextlib
import hashlib
from http.client import HTTPException
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

try:
    import fcntl
except ImportError:  # Installation is intentionally unsupported on Windows.
    fcntl = None


MANAGER = "dumbcane-workflow"
PROFILE = "skills/dumbcane-workflow/references/superpowers-profile.json"
ENTRY = "skills/dumbcane-workflow"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
REVISION = re.compile(r"[0-9a-f]{40}\Z")
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_EXPANDED = 256 * 1024 * 1024
MAX_FILES = 10000
METHODS = frozenset((
    "using-superpowers", "brainstorming", "writing-plans", "systematic-debugging",
    "test-driven-development", "receiving-code-review", "executing-plans",
    "subagent-driven-development", "verification-before-completion",
    "requesting-code-review", "using-git-worktrees", "finishing-a-development-branch",
))


class ManagerError(ValueError):
    pass


class RetryableDownload(ManagerError):
    """A bounded retry is allowed only for a network error or short transfer."""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ManagerError("Duplicate JSON key")
        result[key] = value
    return result


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regular_bytes(path, maximum=None):
    """Do not follow a final-component symlink, including JSON control files."""
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                             | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(descriptor, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                raise ManagerError("Expected a regular file")
            if maximum is not None and metadata.st_size > maximum:
                raise ManagerError("File exceeds its size limit")
            data = stream.read() if maximum is None else stream.read(maximum + 1)
            if maximum is not None and len(data) > maximum:
                raise ManagerError("File exceeds its size limit")
            return data
    except OSError as exc:
        raise ManagerError(f"Cannot read regular file: {path.name}: {exc.strerror}") from exc


def read_json(path):
    try:
        return json.loads(regular_bytes(path, 8 * 1024 * 1024),
                          object_pairs_hook=unique_object)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ManagerError(f"Invalid JSON: {path.name}") from exc


def relative_path(value):
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or "\x00" in value or value.startswith("/")
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ManagerError("Manifest contains an unsafe relative path")
    return PurePosixPath(value)


def hash_map(value):
    if not isinstance(value, dict) or not value or len(value) > MAX_FILES:
        raise ManagerError("Expected a nonempty bounded file inventory")
    for name, digest in value.items():
        path = relative_path(name)
        if path.parts[0] == ".git" or not isinstance(digest, str) or not HEX64.fullmatch(digest):
            raise ManagerError("Invalid file inventory entry")
    return value


def inventory(root, source=False):
    """Inventory every ordinary file; no links/special files, no cache exclusion."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ManagerError("Source or installed directory is missing or a symlink")
    result = {}

    def walk_error(error):
        raise ManagerError(f"Cannot inspect directory: {error.strerror}")

    for directory, directories, files in os.walk(root, followlinks=False, onerror=walk_error):
        parent = Path(directory)
        for name in list(directories):
            path = parent / name
            if source and parent == root and name == ".git":
                directories.remove(name)
                continue
            if path.is_symlink() or not stat.S_ISDIR(path.lstat().st_mode):
                raise ManagerError("Symlink or special directory is not allowed")
        for name in files:
            if source and parent == root and name == ".git":
                continue
            path = parent / name
            relative = path.relative_to(root).as_posix()
            relative_path(relative)
            result[relative] = sha(regular_bytes(path))
            if len(result) > MAX_FILES:
                raise ManagerError("Too many files")
    return result


def exact_inventory(root, expected, source=False):
    actual = inventory(root, source=source)
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        changed = sorted(name for name in actual.keys() & expected.keys()
                         if actual[name] != expected[name])
        # Only relative paths are reported; never print file contents.
        raise ManagerError(f"Content mismatch: missing={missing[:3]}, extra={extra[:3]}, changed={changed[:3]}")


def archive_url(url, revision):
    if not isinstance(url, str):
        raise ManagerError("Missing official archive URL")
    parsed = urlsplit(url)
    paths = {
        "codeload.github.com": f"/obra/superpowers/tar.gz/{revision}",
        "github.com": f"/obra/superpowers/archive/{revision}.tar.gz",
    }
    if (parsed.scheme != "https" or parsed.netloc not in paths
            or parsed.path != paths.get(parsed.netloc) or parsed.query or parsed.fragment):
        raise ManagerError("Archive URL must name the pinned official HTTPS archive")
    return url


def load_profile(root):
    profile = read_json(root / PROFILE)
    if not isinstance(profile, dict) or profile.get("schema_version") != 1:
        raise ManagerError("Unsupported provider profile")
    provider = profile.get("provider")
    if (not isinstance(provider, dict)
            or provider.get("upstream") != "https://github.com/obra/superpowers"
            or not isinstance(provider.get("revision"), str)
            or not REVISION.fullmatch(provider["revision"])
            or not isinstance(provider.get("archive_sha256"), str)
            or not HEX64.fullmatch(provider["archive_sha256"])):
        raise ManagerError("Profile must pin an official revision and archive hash")
    archive_url(provider.get("archive_url"), provider["revision"])
    files = hash_map(profile.get("files"))
    skills = profile.get("skills")
    if not isinstance(skills, dict) or set(skills) != METHODS:
        raise ManagerError("Profile must identify the twelve supported methods")
    for method, path in skills.items():
        relative_path(path)
        if path != f"skills/{method}/SKILL.md" or path not in files:
            raise ManagerError("A provider method is absent from the pinned inventory")
    return profile


def load_source(root):
    root = Path(root).absolute()
    release = read_json(root / "release.json")
    if (not isinstance(release, dict)
            or set(release) != {"schema_version", "version", "files"}
            or release.get("schema_version") != 1
            or not isinstance(release.get("version"), str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,63}", release["version"])):
        raise ManagerError("Unsupported release manifest")
    expected = dict(hash_map(release["files"]))
    if "release.json" in expected or not {PROFILE, f"{ENTRY}/SKILL.md", "scripts/manage.py"} <= expected.keys():
        raise ManagerError("Release inventory is incomplete or contains itself")
    release_bytes = regular_bytes(root / "release.json")
    expected["release.json"] = sha(release_bytes)
    exact_inventory(root, expected, source=True)
    profile = load_profile(root)
    return root, release, expected, sha(release_bytes), profile


def copy_files(source, target, expected):
    target.mkdir()
    for name in sorted(expected):
        source_path = source / name
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = regular_bytes(source_path)
        if sha(data) != expected[name]:
            raise ManagerError("Source changed while being copied")
        with destination.open("xb") as stream:
            stream.write(data)
        mode = source_path.stat().st_mode
        destination.chmod(0o755 if mode & 0o111 else 0o644)
    exact_inventory(target, expected)


class PinnedRedirect(HTTPRedirectHandler):
    def __init__(self, revision):
        self.revision = revision
        super().__init__()

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        archive_url(newurl, self.revision)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def download_with_curl(executable, provider, output):
    """Use an available system transport; never give curl an output pathname."""
    url = archive_url(provider["archive_url"], provider["revision"])
    footer = "\nDUMBCANE_HTTP_STATUS:%{http_code}\n"
    arguments = [
        executable, "--disable", "--silent", "--show-error", "--fail",
        "--proto", "=https", "--proto-redir", "=https", "--max-redirs", "0",
        "--connect-timeout", "10", "--max-time", "30", "--max-filesize", str(MAX_ARCHIVE),
        "--output", "-", "--write-out", footer,
        "--user-agent", "Dumbcane-Workflow/1 (system curl installer)",
        "--header", "Accept-Encoding: identity", "--url", url,
    ]
    # --disable is the first option: local .curlrc cannot inject output files,
    # redirects, private headers, cookies or a different source. No --location.
    try:
        process = subprocess.Popen(arguments, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, shell=False, close_fds=True)
    except OSError as exc:
        raise ManagerError(f"Cannot start available system curl: {type(exc).__name__}") from exc
    buffer = b""
    wire_total = 0
    checksum = hashlib.sha256()
    deadline = time.monotonic() + 40
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RetryableDownload("System curl exceeded its bounded transport timeout")
                if not selector.select(min(remaining, 1)):
                    continue
                chunk = os.read(process.stdout.fileno(), 128 * 1024)
                if not chunk:
                    break
                wire_total += len(chunk)
                if wire_total > MAX_ARCHIVE + 64:
                    raise ManagerError("Archive exceeds the download size limit")
                buffer += chunk
                # Hold only a small tail so curl's fixed status footer is not
                # written into the archive or included in its digest.
                if len(buffer) > 64:
                    body, buffer = buffer[:-64], buffer[-64:]
                    checksum.update(body)
                    output.write(body)
        try:
            returncode = process.wait(timeout=max(0.01, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as exc:
            raise RetryableDownload("System curl did not finish within its bounded timeout") from exc
        status_match = re.search(rb"\nDUMBCANE_HTTP_STATUS:([0-9]{3})\n\Z", buffer)
        status = int(status_match[1]) if status_match else 0
        if status >= 500:
            raise RetryableDownload(f"Official archive server returned HTTP {status}")
        if status >= 300:
            raise ManagerError(f"Official archive request failed with HTTP {status}; redirects are disabled")
        if returncode:
            if returncode in (5, 6, 7, 18, 28, 35, 52, 55, 56, 92, 95):
                raise RetryableDownload(f"System curl transfer interrupted (exit {returncode})")
            raise ManagerError(f"System curl download failed (exit {returncode})")
        if status_match is None or not 200 <= status < 300:
            raise ManagerError("System curl response has no successful fixed HTTP status footer")
        body = buffer[:status_match.start()]
        if wire_total - (status_match.end() - status_match.start()) > MAX_ARCHIVE:
            raise ManagerError("Archive exceeds the download size limit")
        checksum.update(body)
        output.write(body)
        if checksum.hexdigest() != provider["archive_sha256"]:
            raise ManagerError("Official archive SHA256 mismatch")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()


def download_archive(provider, destination):
    curl = shutil.which("curl")
    opener = None if curl else build_opener(PinnedRedirect(provider["revision"]))
    request = Request(archive_url(provider["archive_url"], provider["revision"]), headers={
        "User-Agent": "Dumbcane-Workflow/1 (Python standard-library installer)",
        "Accept-Encoding": "identity",
    })
    for attempt in range(1, 4):
        owned_identity = None
        complete = False
        try:
            # Opening exclusively before any network operation gives this call
            # explicit ownership of the partial file. An existing path is never
            # deleted or reused, including when opening the response fails.
            with destination.open("xb") as output:
                metadata = os.fstat(output.fileno())
                owned_identity = (metadata.st_dev, metadata.st_ino)
                if curl:
                    download_with_curl(curl, provider, output)
                else:
                    try:
                        response = opener.open(request, timeout=30)
                    except HTTPError as exc:
                        exc.close()
                        if 500 <= exc.code <= 599:
                            raise RetryableDownload(f"Official archive server returned HTTP {exc.code}") from exc
                        raise ManagerError(f"Official archive request failed with HTTP {exc.code}") from exc
                    except (URLError, OSError, HTTPException) as exc:
                        raise RetryableDownload(f"Official archive connection interrupted: {type(exc).__name__}") from exc
                    with response:
                        archive_url(response.geturl(), provider["revision"])
                        declared = response.headers.get("Content-Length")
                        if declared is not None:
                            if not isinstance(declared, str) or not re.fullmatch(r"[0-9]{1,12}", declared.strip()):
                                raise ManagerError("Official archive response has an invalid Content-Length")
                            declared = int(declared.strip())
                            if declared > MAX_ARCHIVE:
                                raise ManagerError("Archive exceeds the declared download size limit")
                        total = 0
                        checksum = hashlib.sha256()
                        while True:
                            try:
                                chunk = response.read(128 * 1024)
                            except (URLError, OSError, HTTPException) as exc:
                                raise RetryableDownload(f"Official archive transfer interrupted: {type(exc).__name__}") from exc
                            if not chunk:
                                break
                            total += len(chunk)
                            if total > MAX_ARCHIVE:
                                raise ManagerError("Archive exceeds the download size limit")
                            if declared is not None and total > declared:
                                raise ManagerError("Archive exceeds its declared Content-Length")
                            checksum.update(chunk)
                            output.write(chunk)
                        if declared is not None and total < declared:
                            raise RetryableDownload(f"Official archive transfer truncated ({total} of {declared} bytes)")
                        # No Content-Length is also safe: the pinned full archive
                        # digest is still mandatory. A complete wrong body is never
                        # retried as a transport problem.
                        if checksum.hexdigest() != provider["archive_sha256"]:
                            raise ManagerError("Official archive SHA256 mismatch")
                output.flush()
                os.fsync(output.fileno())
            complete = True
            return
        except RetryableDownload as exc:
            if attempt == 3:
                raise ManagerError(f"Official archive download failed after 3 attempts: {exc}") from exc
        finally:
            if not complete and owned_identity is not None:
                try:
                    current = destination.lstat()
                except FileNotFoundError:
                    pass
                else:
                    if (current.st_dev, current.st_ino) == owned_identity:
                        destination.unlink()
        # Fixed source and bounded backoff; no mirror, latest-version lookup or
        # unlimited retries are hidden inside installation.
        time.sleep(attempt * 0.25)


def extract_archive(archive, target, provider):
    data = regular_bytes(archive, MAX_ARCHIVE)
    if sha(data) != provider["archive_sha256"]:
        raise ManagerError("Official archive SHA256 mismatch")
    target.mkdir()
    root_name = f"superpowers-{provider['revision']}"
    seen = set()
    total = 0
    try:
        # Extract precisely the already hashed bytes, never reopen a mutable
        # caller-supplied archive path after checking its digest.
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as bundle:
            for member in bundle:
                name = member.name.rstrip("/") if member.isdir() else member.name
                path = relative_path(name)
                if (path.parts[0] != root_name or name in seen
                        or not (member.isdir() or member.isfile()) or member.issym()
                        or member.islnk() or member.sparse):
                    raise ManagerError("Archive has unsafe, duplicate, linked or special entries")
                seen.add(name)
                if len(seen) > MAX_FILES:
                    raise ManagerError("Too many archive entries")
                if len(path.parts) == 1:
                    if not member.isdir():
                        raise ManagerError("Archive root must be a directory")
                    continue
                relative = Path(*path.parts[1:])
                destination = target / relative
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                if member.size < 0:
                    raise ManagerError("Invalid archive member size")
                total += member.size
                if total > MAX_EXPANDED:
                    raise ManagerError("Expanded archive exceeds its size limit")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with contextlib.closing(bundle.extractfile(member)) as stream, destination.open("xb") as output:
                    shutil.copyfileobj(stream, output)
                destination.chmod(0o755 if member.mode & 0o111 else 0o644)
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise ManagerError(f"Cannot safely extract official archive: {type(exc).__name__}") from exc
    if not seen:
        raise ManagerError("Official archive is empty")


def verify_provider(root, profile):
    actual = inventory(root)
    for name, expected in profile["files"].items():
        if actual.get(name) != expected:
            raise ManagerError(f"Pinned provider content mismatch: {name}")
    return actual


def validate_descriptor(value):
    if (not isinstance(value, dict) or set(value) != {"release_id", "receipt_sha256"}
            or any(not isinstance(value[key], str) or not HEX64.fullmatch(value[key])
                   for key in ("release_id", "receipt_sha256"))):
        raise ManagerError("Invalid managed release descriptor")
    return value


def validate_state(value):
    if (not isinstance(value, dict)
            or set(value) != {"schema_version", "manager", "installed", "current", "previous"}
            or value["schema_version"] != 1 or value["manager"] != MANAGER
            or not isinstance(value["installed"], bool)):
        raise ManagerError("Invalid manager state; preserve it for manual inspection")
    validate_descriptor(value["current"])
    if value["previous"] is not None:
        validate_descriptor(value["previous"])
    return value


def lexists(path):
    return os.path.lexists(path)


class Manager:
    def __init__(self, home):
        self.home = Path(home).expanduser().absolute().resolve()
        self.base = self.home / ".local/share/dumbcane-workflow"
        self.releases = self.base / "releases"
        self.entry = self.home / ".agents/skills/dumbcane-workflow"
        self.state_file = self.base / "state.json"
        self.journal = self.base / "transaction.json"
        self.recovery = None

    def check_ancestors(self, path):
        relative = path.relative_to(self.home)
        current = self.home
        for part in relative.parts:
            current = current / part
            if lexists(current) and (current.is_symlink() or not current.is_dir()):
                raise ManagerError("Managed directory path contains a symlink or non-directory")

    def mkdir(self, path):
        self.check_ancestors(path)
        current = self.home
        if not current.is_dir():
            raise ManagerError("The selected home directory must already exist")
        for part in path.relative_to(self.home).parts:
            current /= part
            try:
                current.mkdir()
            except FileExistsError:
                if current.is_symlink() or not current.is_dir():
                    raise ManagerError("Managed directory changed during creation")

    @contextlib.contextmanager
    def lock(self):
        if fcntl is None:
            raise ManagerError("This manager currently supports macOS and Linux only")
        self.mkdir(self.base)
        lock_path = self.base / "manager.lock"
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                os.close(descriptor)
                raise ManagerError("Manager lock is not an ordinary file")
        except OSError as exc:
            raise ManagerError("Cannot safely open the manager lock") from exc
        with os.fdopen(descriptor, "rb") as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ManagerError("Another lifecycle operation is already running") from exc
            try:
                self.check_ancestors(self.releases)
                self.check_ancestors(self.entry.parent)
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def state(self):
        if not lexists(self.state_file):
            return None
        return validate_state(read_json(self.state_file))

    def target(self, descriptor):
        return str(self.releases / validate_descriptor(descriptor)["release_id"] / "package" / ENTRY)

    def entry_matches(self, target):
        if target is None:
            return not lexists(self.entry)
        return self.entry.is_symlink() and os.readlink(self.entry) == target

    def expected_target(self, state):
        return self.target(state["current"]) if state and state["installed"] else None

    def require_entry(self, state):
        if not self.entry_matches(self.expected_target(state)):
            raise ManagerError("Skill entry is absent, changed or owned by another installation; nothing was replaced")

    def receipt(self, descriptor):
        validate_descriptor(descriptor)
        folder = self.releases / descriptor["release_id"]
        self.check_ancestors(folder)
        expected_names = {"package", "superpowers", "receipt.json"}
        if set(path.name for path in folder.iterdir()) != expected_names:
            raise ManagerError("Managed release contains unknown or missing top-level items")
        raw = regular_bytes(folder / "receipt.json")
        if sha(raw) != descriptor["receipt_sha256"]:
            raise ManagerError("Managed receipt changed or is corrupt")
        receipt = read_json(folder / "receipt.json")
        keys = {"schema_version", "manager", "release_id", "version", "package_files",
                "provider_files", "provider_revision", "archive_sha256", "archive_verified", "provider_source"}
        if (not isinstance(receipt, dict) or set(receipt) != keys
                or receipt["schema_version"] != 1 or receipt["manager"] != MANAGER
                or receipt["release_id"] != descriptor["release_id"]
                or not isinstance(receipt["archive_verified"], bool)
                or receipt["provider_source"] not in ("download", "archive", "local_directory")):
            raise ManagerError("Malformed managed receipt")
        hash_map(receipt["package_files"])
        hash_map(receipt["provider_files"])
        return folder, receipt

    def verify_release(self, descriptor):
        folder, receipt = self.receipt(descriptor)
        exact_inventory(folder / "package", receipt["package_files"])
        package, release, expected, identity, profile = load_source(folder / "package")
        if (identity != descriptor["release_id"] or expected != receipt["package_files"]
                or release["version"] != receipt["version"]
                or profile["provider"]["revision"] != receipt["provider_revision"]
                or profile["provider"]["archive_sha256"] != receipt["archive_sha256"]):
            raise ManagerError("Receipt does not describe the installed release")
        exact_inventory(folder / "superpowers", receipt["provider_files"])
        verify_provider(folder / "superpowers", profile)
        return receipt

    def atomic_json(self, path, value):
        if lexists(path) and (path.is_symlink() or not path.is_file()):
            raise ManagerError("Control file is not an ordinary file")
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(canonical(value))
                stream.flush()
                os.fsync(stream.fileno())
            temporary.chmod(0o600)
            os.replace(temporary, path)
        finally:
            if lexists(temporary):
                temporary.unlink()

    @staticmethod
    def path_matches(path, target):
        return path.is_symlink() and target is not None and os.readlink(path) == target

    def park(self, expected, destination):
        """Move, then inspect the object actually moved; never replace an entry.

        A noncooperating writer may replace the discoverable entry after our
        last check. Parking preserves that object instead of overwriting it.
        """
        self.require_target(expected)
        if lexists(destination):
            raise ManagerError("Parking slot is unexpectedly occupied; preserved it")
        os.rename(self.entry, destination)
        if not self.path_matches(destination, expected):
            self.restore_unknown(destination)
            raise ManagerError(f"An independent entry changed during switching; retained it at {destination}")

    def restore_unknown(self, path):
        # Hard-link creation is exclusive and preserves the moved inode. Keep
        # the parking copy as well; no unknown user object is ever unlinked.
        if not lexists(self.entry) and lexists(path):
            try:
                os.link(path, self.entry, follow_symlinks=False)
            except OSError:
                pass  # Report its retained parking location for manual recovery.

    def switch(self, old_target, new_target, parking):
        self.require_target(old_target)
        if old_target == new_target:
            return
        if old_target is not None:
            self.park(old_target, parking / "before")
        if new_target is not None:
            # An independent writer wins this race without being overwritten.
            # The old link remains in parking until the transaction completes.
            os.symlink(new_target, self.entry)

    def require_target(self, target):
        if not self.entry_matches(target):
            raise ManagerError("Skill entry changed during the operation; preserved it")

    def load_transaction(self):
        value = read_json(self.journal)
        if (not isinstance(value, dict) or set(value) != {"schema_version", "manager", "old", "new", "parking"}
                or value["schema_version"] != 1 or value["manager"] != MANAGER
                or not isinstance(value["parking"], str)
                or not re.fullmatch(r"\.dumbcane-workflow\.[0-9a-f]{32}\.switch", value["parking"])):
            raise ManagerError("Invalid recovery journal; manual inspection is required")
        if value["old"] is not None:
            validate_state(value["old"])
        validate_state(value["new"])
        return value

    def inspect_parking(self, parking, targets):
        if not lexists(parking):
            return
        if parking.is_symlink() or not parking.is_dir():
            raise ManagerError(f"Recovery parking directory was independently changed: {parking}")
        for path in parking.iterdir():
            if path.name not in ("before", "after") or not any(self.path_matches(path, target) for target in targets):
                if path.name in ("before", "after"):
                    self.restore_unknown(path)
                raise ManagerError(f"Unknown parked content retained for inspection: {path}")

    def clean_parking(self, parking, targets):
        self.inspect_parking(parking, targets)
        if lexists(parking):
            for path in parking.iterdir():
                path.unlink()  # Only verified manager-created symlinks in the private transaction directory.
            parking.rmdir()

    def recover(self, force_old=False):
        if not lexists(self.journal):
            return
        journal = self.load_transaction()
        old, new = journal["old"], journal["new"]
        actual = self.state()
        old_target, new_target = self.expected_target(old), self.expected_target(new)
        parking = self.entry.parent / journal["parking"]
        self.inspect_parking(parking, (old_target, new_target))
        if actual not in (old, new):
            raise ManagerError("Recovery state was independently changed; preserved all files")
        if not force_old and actual == new and self.entry_matches(new_target):
            self.verify_release(new["current"])
            self.clean_parking(parking, (old_target, new_target))
            self.journal.unlink()
            self.recovery = "Completed an interrupted transaction already committed on disk"
            return
        interrupted_gap = (not lexists(self.entry) and lexists(parking)
                           and any(parking.iterdir()))
        if not (self.entry_matches(old_target) or self.entry_matches(new_target) or interrupted_gap):
            raise ManagerError("Recovery entry was independently changed; preserved all files")
        if old is not None:
            self.verify_release(old["current"])
        if not self.entry_matches(old_target):
            if lexists(self.entry):
                if not lexists(parking):
                    parking.mkdir(mode=0o700)
                self.park(new_target, parking / "after")
            if old_target is not None:
                os.symlink(old_target, self.entry)
        if actual != old:
            if old is None:
                self.state_file.unlink()
            else:
                self.atomic_json(self.state_file, old)
        self.clean_parking(parking, (old_target, new_target))
        self.journal.unlink()
        self.recovery = "Restored the previous entry and state after an interrupted transaction"

    def transaction(self, old, new):
        if lexists(self.journal):
            raise ManagerError("An unresolved recovery journal already exists")
        parking = self.entry.parent / f".dumbcane-workflow.{uuid.uuid4().hex}.switch"
        self.atomic_json(self.journal, {"schema_version": 1, "manager": MANAGER,
                                       "old": old, "new": new, "parking": parking.name})
        try:
            parking.mkdir(mode=0o700)
            self.switch(self.expected_target(old), self.expected_target(new), parking)
            self.atomic_json(self.state_file, new)
            self.clean_parking(parking, (self.expected_target(old), self.expected_target(new)))
            self.journal.unlink()
        except BaseException as exc:
            try:
                self.recover(force_old=True)
            except (ManagerError, OSError) as recovery_error:
                raise ManagerError("Operation interrupted; recovery journal retained. Run doctor and preserve all files: "
                                   + str(recovery_error)) from exc
            raise

    def prepare(self, source, provider_source=None, provider_archive=None):
        root, release, package_files, identity, profile = load_source(source)
        self.mkdir(self.releases)
        destination = self.releases / identity
        if lexists(destination):
            # Never overwrite a previous release or somebody else's directory.
            raw = regular_bytes(destination / "receipt.json")
            descriptor = {"release_id": identity, "receipt_sha256": sha(raw)}
            receipt = self.verify_release(descriptor)
            if receipt["package_files"] != package_files:
                raise ManagerError("An existing release has a different package inventory")
            return descriptor
        stage = Path(tempfile.mkdtemp(prefix=".stage-", dir=self.releases))
        try:
            copy_files(root, stage / "package", package_files)
            if provider_source is not None:
                provider_root = Path(provider_source).absolute()
                source_inventory = inventory(provider_root, source=True)
                verify_provider_subset = {name: source_inventory.get(name) for name in profile["files"]}
                if verify_provider_subset != profile["files"]:
                    raise ManagerError("Offline provider does not match the pinned method files")
                copy_files(provider_root, stage / "superpowers", source_inventory)
                origin, archive_verified = "local_directory", False
            else:
                archive = Path(provider_archive).absolute() if provider_archive else stage / "archive.tar.gz"
                if provider_archive is None:
                    download_archive(profile["provider"], archive)
                extract_archive(archive, stage / "superpowers", profile["provider"])
                if provider_archive is None:
                    archive.unlink()
                origin = "archive" if provider_archive else "download"
                archive_verified = True
            provider_files = verify_provider(stage / "superpowers", profile)
            receipt = {
                "schema_version": 1, "manager": MANAGER, "release_id": identity,
                "version": release["version"], "package_files": package_files,
                "provider_files": provider_files, "provider_revision": profile["provider"]["revision"],
                "archive_sha256": profile["provider"]["archive_sha256"],
                "archive_verified": archive_verified, "provider_source": origin,
            }
            raw = canonical(receipt)
            (stage / "receipt.json").write_bytes(raw)
            descriptor = {"release_id": identity, "receipt_sha256": sha(raw)}
            # Cooperating manager processes are serialized by the lock. Refuse
            # an independently created destination rather than merging content.
            if lexists(destination):
                raise ManagerError("Release directory appeared during preparation; preserved it")
            os.rename(stage, destination)
            self.verify_release(descriptor)
            return descriptor
        finally:
            if stage.exists():
                shutil.rmtree(stage)  # Only this invocation's freshly created staging directory.

    def mutate(self, command, source=None, provider_source=None, provider_archive=None):
        with self.lock():
            self.recover()
            old = self.state()
            self.require_entry(old)
            if command == "install":
                if old and old["installed"]:
                    raise ManagerError("Already installed; use update from a reviewed new release")
                if old:
                    self.verify_release(old["current"])
                current = self.prepare(source, provider_source, provider_archive)
                new = {"schema_version": 1, "manager": MANAGER, "installed": True,
                       "current": current,
                       "previous": (old["current"] if old["current"] != current else old["previous"]) if old else None}
                self.mkdir(self.entry.parent)
            else:
                if not old or not old["installed"]:
                    raise ManagerError("No active installation owned by this manager")
                self.verify_release(old["current"])
                if command == "update":
                    current = self.prepare(source, provider_source, provider_archive)
                    if current == old["current"]:
                        return self.result(command, old, "Already at this exact release")
                    new = dict(old, current=current, previous=old["current"])
                elif command == "rollback":
                    if old["previous"] is None:
                        raise ManagerError("No previous release is recorded")
                    self.verify_release(old["previous"])
                    new = dict(old, current=old["previous"], previous=old["current"])
                elif command == "uninstall":
                    new = dict(old, installed=False)
                else:
                    raise ManagerError("Unsupported lifecycle command")
            self.transaction(old, new)
            return self.result(command, new)

    def result(self, command, state, message=None):
        return {"schema_version": 1, "command": command, "status": "pass",
                "installed": state["installed"], "release_id": state["current"]["release_id"],
                "behavioral_status": "not_certified", "recovery": self.recovery,
                "message": message or ("Owned entry removed; releases and receipts retained"
                                       if command == "uninstall" else "Managed combination selected")}

    def doctor(self):
        report = {"schema_version": 1, "command": "doctor", "status": "fail",
                  "state_status": "not_installed", "package_status": "not_checked",
                  "provider_status": "not_checked", "entry_status": "not_checked",
                  "behavioral_status": "not_certified", "archive_verified": None,
                  "recovery_required": False, "errors": []}
        try:
            self.check_ancestors(self.base)
            self.check_ancestors(self.entry.parent)
            if lexists(self.journal):
                report["recovery_required"] = True
                report["errors"].append("A transaction journal exists; rerun a lifecycle command to recover when safe")
            state = self.state()
            if state is None:
                report["entry_status"] = "absent" if not lexists(self.entry) else "unmanaged_conflict"
                report["errors"].append("No installation is recorded; existing entries are never adopted automatically")
                return report
            report["state_status"] = "installed" if state["installed"] else "uninstalled"
            report["release_id"] = state["current"]["release_id"]
            report["entry_status"] = "pass" if self.entry_matches(self.expected_target(state)) else "fail"
            if report["entry_status"] == "fail":
                report["errors"].append("The discoverable entry differs from manager state")
            folder, receipt = self.receipt(state["current"])
            report["version"] = receipt["version"]
            report["package_root"] = str(folder / "package")
            report["provider_root"] = str(folder / "superpowers")
            report["skill_root"] = str(folder / "package" / ENTRY)
            report["archive_verified"] = receipt["archive_verified"]
            report["provider_source"] = receipt["provider_source"]
            profile = None
            try:
                exact_inventory(folder / "package", receipt["package_files"])
                _, release, expected, identity, profile = load_source(folder / "package")
                if (identity != state["current"]["release_id"] or expected != receipt["package_files"]
                        or release["version"] != receipt["version"]
                        or profile["provider"]["revision"] != receipt["provider_revision"]
                        or profile["provider"]["archive_sha256"] != receipt["archive_sha256"]):
                    raise ManagerError("Package metadata differs from its receipt")
                report["package_status"] = "pass"
            except (ManagerError, OSError) as exc:
                report["package_status"] = "fail"
                report["errors"].append(str(exc))
            try:
                exact_inventory(folder / "superpowers", receipt["provider_files"])
                if profile is not None:
                    verify_provider(folder / "superpowers", profile)
                    report["provider_status"] = "pass"
                else:
                    report["provider_status"] = "receipt_match_profile_unavailable"
                    report["errors"].append("Provider snapshot matches its receipt, but the damaged package cannot supply a trusted profile")
            except (ManagerError, OSError) as exc:
                report["provider_status"] = "fail"
                report["errors"].append(str(exc))
            if not report["errors"]:
                report["status"] = "pass"
        except (ManagerError, OSError) as exc:
            report["state_status"] = "fail"
            report["errors"].append(str(exc))
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("install", "doctor", "update", "rollback", "uninstall"))
    parser.add_argument("--home", type=Path, default=Path.home(), help="Selected home directory; no environment variables are changed")
    parser.add_argument("--source", type=Path, default=None, help="Reviewed public package directory (install/update only)")
    providers = parser.add_mutually_exclusive_group()
    providers.add_argument("--provider-source", type=Path, help="Offline official source directory; only profile closure has official fingerprints")
    providers.add_argument("--provider-archive", type=Path, help="Offline pinned official tar.gz; complete archive SHA256 is checked")
    parser.add_argument("--json", action="store_true", help="Machine-readable result")
    args = parser.parse_args(argv)
    if args.command not in ("install", "update") and any((args.source, args.provider_source, args.provider_archive)):
        parser.error("--source/--provider-source/--provider-archive apply only to install/update")
    manager = Manager(args.home)
    try:
        if args.command == "doctor":
            result = manager.doctor()
        else:
            source = args.source or Path(__file__).resolve().parent.parent
            result = manager.mutate(args.command, source, args.provider_source, args.provider_archive)
    except (ManagerError, OSError, KeyboardInterrupt) as exc:
        result = {"schema_version": 1, "command": args.command, "status": "fail",
                  "behavioral_status": "not_certified", "error": str(exc) or type(exc).__name__}
    if args.json:
        print(json.dumps(result, sort_keys=True, indent=2))
    else:
        print(f"{result['command']}: {result['status']}")
        if result.get("error"):
            print(result["error"])
        if result.get("message"):
            print(result["message"])
        for error in result.get("errors", []):
            print(error)
        print("Behavioral certification: not certified")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
