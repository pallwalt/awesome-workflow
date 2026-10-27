#!/usr/bin/env python3
"""Read-only package/content-identity checks using Python's standard library.

package_status describes the package itself. Provider and original checks have
separate statuses; ANY selected check failure makes the command exit 1. Invalid
CLI syntax (including an unpaired original/baseline flag) exits 2. Matching
provider bytes establishes content identity, never behavioral certification.

The metadata check intentionally covers this package's name/description only.
It is not a YAML validator; run the official skill-creator validator separately.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
from urllib.parse import unquote, urlsplit


REQUIRED_SKILLS = frozenset((
    "using-superpowers", "brainstorming", "writing-plans",
    "systematic-debugging", "test-driven-development", "receiving-code-review",
    "executing-plans", "subagent-driven-development", "verification-before-completion",
    "requesting-code-review", "using-git-worktrees", "finishing-a-development-branch",
))
SKILL = Path("skills/awesome-workflow/SKILL.md")
PROFILE = SKILL.parent / "references/superpowers-profile.json"
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
PERSONAL_PATH = re.compile(r"/(?:Users|home|root)/[^\s\"'<>]+|[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\s\"'<>]+")
TEXT_SUFFIXES = frozenset((".md", ".markdown", ".json", ".yaml", ".yml", ".toml",
                           ".txt", ".py", ".sh", ".js", ".ts", ".html", ".css"))


class CliError(ValueError):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CliError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def within(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError, RuntimeError):
        return False


def relative_profile_path(value):
    """Profile paths are portable, root-relative POSIX paths, never traversal."""
    return (isinstance(value, str) and bool(value) and "\x00" not in value
            and "\\" not in value and not PurePosixPath(value).is_absolute()
            and not PureWindowsPath(value).drive and ":" not in value
            and ".." not in PurePosixPath(value).parts
            and PurePosixPath(value) != PurePosixPath("."))


def without_fences(text):
    result = []
    fence_character = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence_character is not None:
            if marker and marker[1][0] == fence_character and len(marker[1]) >= fence_length and not marker[2].strip():
                fence_character = None
            result.append("\n" if line.endswith("\n") else "")
        elif marker:
            fence_character = marker[1][0]
            fence_length = len(marker[1])
            result.append("\n" if line.endswith("\n") else "")
        else:
            result.append(line)
    return "".join(result)


def markdown_destination(value):
    value = value.strip()
    if value.startswith("<"):
        end = value.find(">")
        return value[1:end] if end >= 0 else None
    # An unbracketed destination cannot contain unescaped whitespace. Balanced
    # parentheses are retained; a following optional title is excluded.
    match = re.match(r"((?:\\.|[^\s])+)", value)
    if not match:
        return None
    return re.sub(r"\\([\\ ()])", r"\1", match[1])


def markdown_links(text):
    """Yield local/external destinations, including reference definitions.

    Handles balanced parentheses and angle-bracket destinations. This checks
    resources, not Markdown rendering or heading/anchor existence.
    """
    text = without_fences(text)
    for start in re.finditer(r"!?\[[^\]\n]*\]\(", text):
        position = start.end()
        depth = 1
        escaped = False
        angle = False
        quote = None
        index = position
        while index < len(text):
            char = text[index]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif quote:
                if char == quote:
                    quote = None
            elif angle:
                if char == ">":
                    angle = False
            elif char == "<":
                angle = True
            elif char in ('"', "'") and index > position and text[index - 1].isspace():
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    target = markdown_destination(text[position:index])
                    if target is not None:
                        yield target, text.count("\n", 0, start.start()) + 1
                    break
            index += 1
    for definition in re.finditer(r"^ {0,3}\[[^\]\n]+\]:\s*(.+)$", text, re.MULTILINE):
        target = markdown_destination(definition[1])
        if target is not None:
            yield target, text.count("\n", 0, definition.start()) + 1


class Checker:
    def __init__(self, package_root):
        self.root = Path(package_root).resolve()
        self.errors = []
        self.package_errors = []
        self.checked = set()
        self.report = {
            "schema_version": 1, "package_status": "pass",
            "provider_status": "not_checked", "behavioral_status": None,
            "original_status": "not_checked", "errors": self.errors,
            "checked_files": 0,
        }

    def error(self, message, package=False):
        self.errors.append(message)
        if package:
            self.package_errors.append(message)

    def read(self, path):
        data = path.read_bytes()
        self.checked.add(str(path.resolve()))
        return data

    def read_json(self, path):
        return json.loads(self.read(path).decode("utf-8-sig"), object_pairs_hook=unique_object)

    @staticmethod
    def excluded(relative):
        parts = relative.parts
        return (bool(parts) and parts[0] == "checks"
                or parts[:2] == ("evals", "results")
                or any(part in (".git", "__pycache__") for part in parts))

    def package_files(self):
        if not self.root.is_dir():
            self.error(f"Package root is missing or not a directory: {self.root}", package=True)
            return
        def walk_error(error):
            self.error(f"Cannot inspect package directory: {error}", package=True)

        for directory, directories, files in os.walk(self.root, followlinks=False, onerror=walk_error):
            folder = Path(directory)
            for name in list(directories):
                path = folder / name
                if self.excluded(path.relative_to(self.root)):
                    directories.remove(name)
                elif path.is_symlink() and not within(path, self.root):
                    self.error(f"Package symlink resolves outside package: {path.relative_to(self.root)}", package=True)
                    directories.remove(name)
            for name in files:
                path = folder / name
                relative = path.relative_to(self.root)
                if self.excluded(relative):
                    continue
                if not within(path, self.root):
                    self.error(f"Package symlink resolves outside package: {relative}", package=True)
                elif path.suffix.lower() in TEXT_SUFFIXES:
                    yield path

    def check_package(self):
        skill_text = None
        for path in self.package_files():
            relative = path.relative_to(self.root)
            try:
                text = self.read(path).decode("utf-8-sig")
            except (OSError, UnicodeError) as exc:
                self.error(f"Cannot read distributable text {relative}: {exc}", package=True)
                continue
            if relative == SKILL:
                skill_text = text
            for match in PERSONAL_PATH.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                self.error(f"Absolute personal path in distributable text {relative}:{line}; use a portable placeholder or relative path", package=True)
            if path.suffix.lower() in (".md", ".markdown"):
                self.check_links(path, text)
        if skill_text is None:
            self.error(f"Required candidate skill is missing or unreadable: {SKILL}", package=True)
        else:
            self.check_metadata(skill_text)

    def check_metadata(self, text):
        match = re.match(r"\A---\s*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.DOTALL)
        if not match:
            self.error(f"Own-package metadata check: {SKILL} requires frontmatter; use official validator for full YAML validation", package=True)
            return
        metadata = match[1]
        names = re.findall(r"^name:\s*(.+)$", metadata, re.MULTILINE)
        if len(names) != 1 or names[0].strip().strip("\"'") != "awesome-workflow":
            self.error(f"Own-package metadata check: {SKILL} needs name: awesome-workflow", package=True)
        descriptions = list(re.finditer(r"^description:[ \t]*(.*)$", metadata, re.MULTILINE))
        valid_description = False
        if len(descriptions) == 1:
            value = descriptions[0][1].strip()
            if value in (">", "|", ">-", "|-", ">+", "|+"):
                following = metadata[descriptions[0].end():].splitlines()
                valid_description = any(line.startswith((" ", "\t")) and line.strip() for line in following)
            else:
                valid_description = bool(value.strip("\"'"))
        if not valid_description:
            self.error(f"Own-package metadata check: {SKILL} requires a nonempty description", package=True)

    def check_links(self, file, text):
        relative = file.relative_to(self.root)
        for target, line in markdown_links(text):
            if not target or target.startswith("#"):
                continue
            try:
                parsed = urlsplit(target)
                if parsed.scheme.lower() == "file":
                    self.error(f"Nonportable file: URI at {relative}:{line}: {target}; use a relative package link instead", package=True)
                    continue
                # Protocol-relative web URLs are external; local absolute paths
                # and Windows drives are not treated as external URI schemes.
                if parsed.netloc and target.startswith("//"):
                    continue
                if parsed.scheme and not PureWindowsPath(target).drive:
                    continue
                destination = unquote(parsed.path)
                if not destination:
                    continue
                path = file.parent / destination
                if (PurePosixPath(destination).is_absolute()
                        or PureWindowsPath(destination).drive
                        or not within(path, self.root)):
                    self.error(f"Local link resolves outside package at {relative}:{line}: {target}", package=True)
                elif not path.exists():
                    self.error(f"Broken local link at {relative}:{line}: {target} (missing resource)", package=True)
            except (OSError, ValueError, RuntimeError) as exc:
                self.error(f"Invalid local link at {relative}:{line}: {target!r}: {exc}", package=True)

    def load_profile(self):
        path = self.root / PROFILE
        try:
            if not within(path, self.root):
                raise ValueError("profile resolves outside package")
            profile = self.read_json(path)
            if not isinstance(profile, dict):
                raise ValueError("profile must be an object")
            if type(profile.get("schema_version")) is not int or profile["schema_version"] != 1:
                raise ValueError("schema_version must be integer 1")
            for key in ("profile_id", "behavioral_status"):
                if not isinstance(profile.get(key), str) or not profile[key].strip():
                    raise ValueError(f"{key} must be a nonempty string")
            self.report["behavioral_status"] = profile["behavioral_status"]
            provider = profile.get("provider")
            if not isinstance(provider, dict):
                raise ValueError("provider must be an object")
            for key in ("name", "upstream", "provenance"):
                if not isinstance(provider.get(key), str) or not provider[key].strip():
                    raise ValueError(f"provider.{key} must be a nonempty string")
            if "revision" not in provider or (provider["revision"] is not None and not isinstance(provider["revision"], str)):
                raise ValueError("provider.revision must be null or a string")
            for key in ("skills", "files"):
                if not isinstance(profile.get(key), dict) or not profile[key]:
                    raise ValueError(f"{key} must be a nonempty object")
            missing = REQUIRED_SKILLS.difference(profile["skills"])
            if missing:
                raise ValueError("skills missing required providers: " + ", ".join(sorted(missing)))
            for skill, entry in profile["skills"].items():
                if not isinstance(skill, str) or not skill.strip() or not relative_profile_path(entry):
                    raise ValueError(f"invalid skill entry path: {skill!r}: {entry!r}")
                if entry not in profile["files"]:
                    raise ValueError(f"skill entry {skill!r} must be declared in files: {entry}")
            for relative, digest in profile["files"].items():
                if not relative_profile_path(relative):
                    raise ValueError(f"invalid profile file path: {relative!r}")
                if not isinstance(digest, str) or not DIGEST.fullmatch(digest):
                    raise ValueError(f"malformed SHA256 digest for {relative!r}; expected 64 lowercase hexadecimal characters")
            return profile
        except (OSError, ValueError, UnicodeError, RuntimeError) as exc:
            self.error(f"Invalid dependency profile {PROFILE}: {exc}", package=True)
            self.report["provider_status"] = "invalid"
            return None

    def check_provider(self, root, profile):
        if profile is None or root is None:
            return
        try:
            root = Path(root).resolve(strict=True)
        except FileNotFoundError:
            self.error(f"Provider root is missing: {root}")
            self.report["provider_status"] = "missing"
            return
        except (OSError, ValueError, RuntimeError) as exc:
            self.error(f"Invalid provider root {root}: {exc}")
            self.report["provider_status"] = "invalid"
            return
        if not root.is_dir():
            self.error(f"Provider root is not a directory: {root}")
            self.report["provider_status"] = "invalid"
            return
        statuses = set()
        for relative, expected in profile["files"].items():
            path = root / relative
            if not within(path, root):
                self.error(f"Provider file resolves outside provider root: {relative}")
                statuses.add("invalid")
                continue
            try:
                actual = hashlib.sha256(self.read(path)).hexdigest()
            except (OSError, RuntimeError) as exc:
                self.error(f"Provider resource missing or unreadable: {relative}: {exc}")
                statuses.add("missing")
                continue
            if actual != expected:
                self.error(f"Provider hash drift: {relative}; expected {expected}, got {actual}")
                statuses.add("drift")
        self.report["provider_status"] = next((status for status in ("invalid", "missing", "drift") if status in statuses), "content_match")

    def check_original(self, original, baseline):
        if original is None:
            return
        try:
            baseline_data = self.read_json(Path(baseline))
            if not isinstance(baseline_data, dict) or not isinstance(baseline_data.get("sha256"), str) or not DIGEST.fullmatch(baseline_data["sha256"]):
                raise ValueError("baseline must contain a 64-character lowercase SHA256 digest")
            actual = hashlib.sha256(self.read(Path(original))).hexdigest()
            if actual == baseline_data["sha256"]:
                self.report["original_status"] = "unchanged"
            else:
                self.report["original_status"] = "changed"
                self.error(f"Original skill changed: {original}; SHA256 differs from baseline {baseline}")
        except (OSError, ValueError, UnicodeError, RuntimeError) as exc:
            self.report["original_status"] = "invalid"
            self.error(f"Cannot verify original skill {original} against baseline {baseline}: {exc}")

    def finish(self):
        self.report["package_status"] = "fail" if self.package_errors else "pass"
        self.report["checked_files"] = len(self.checked)
        return self.report


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = Parser(description=__doc__)
    parser.add_argument("--package-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--provider-root", help="Explicit dependency root; omitted means not_checked")
    parser.add_argument("--original-skill", help="Read-only original skill to compare with --baseline")
    parser.add_argument("--baseline", help="JSON baseline containing sha256; requires --original-skill")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object; statuses remain separate")
    try:
        args = parser.parse_args(argv)
        if bool(args.original_skill) != bool(args.baseline):
            raise CliError("--original-skill and --baseline must be provided together")
    except CliError as exc:
        report = {"schema_version": 1, "package_status": "fail", "provider_status": "not_checked",
                  "behavioral_status": None, "original_status": "invalid" if any(argument.split("=", 1)[0] in ("--original-skill", "--baseline") for argument in argv) else "not_checked",
                  "errors": [f"Invalid CLI arguments: {exc}"], "checked_files": 0}
        if "--json" in argv:
            print(json.dumps(report, ensure_ascii=False))
        else:
            print(report["errors"][0], file=sys.stderr)
        return 2
    checker = Checker(args.package_root)
    checker.check_package()
    profile = checker.load_profile()
    checker.check_provider(args.provider_root, profile)
    checker.check_original(args.original_skill, args.baseline)
    report = checker.finish()
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        for key in ("package_status", "provider_status", "behavioral_status", "original_status", "checked_files"):
            print(f"{key}: {report[key]}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
