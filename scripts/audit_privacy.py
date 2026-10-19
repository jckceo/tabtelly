#!/usr/bin/env python3
"""Check publishable files, the Git index or all reachable history without echoing matches."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.build_release import PROJECT_ROOT, release_files
except ModuleNotFoundError:
    from build_release import PROJECT_ROOT, release_files


EMAIL = re.compile(r"[A-Za-z0-9][A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NOREPLY = re.compile(r"(?:\d+\+)?[A-Za-z0-9-]+@users\.noreply\.github\.com", re.I)
IDENTITY = re.compile(r"^(.+) <([^<>]+)> \d+ [+-]\d{4}$")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)


def reserved_email(value: str) -> bool:
    domain = value.rsplit("@", 1)[1].lower()
    return domain in {"example.com", "example.org", "example.net"} or domain.endswith((".example", ".invalid", ".test"))


def scan_bytes(path: str, data: bytes, policy: dict, blocked: list[str]) -> list[Finding]:
    """Binary metadata is checked as bytes decoded with replacement; image pixels need review."""
    text = data.decode("utf-8", errors="replace")
    allowed = {x["email"].lower() for x in policy["approved_identities"]} | {
        x.lower() for x in policy.get("allowed_emails", [])
    }
    findings = []
    for number, line in enumerate(text.splitlines(), 1):
        if any(term.casefold() in line.casefold() for term in blocked):
            findings.append(Finding(path, number, "private-term"))
        for address in set(EMAIL.findall(line)):
            if address.lower() not in allowed and not reserved_email(address) and not NOREPLY.fullmatch(address):
                findings.append(Finding(path, number, "unapproved-email"))
        if path in {"LICENSE", "README.md"}:
            notice = re.search(r"(?:Copyright \(c\)|©)\s+\d{4}\s+(.+)", line)
            if notice and notice.group(1).rstrip(". ") != policy["copyright_holder"]:
                findings.append(Finding(path, number, "copyright-identity"))
    if any(term.casefold() in path.casefold() for term in blocked):
        # Avoid including an offending filename in output.
        findings.append(Finding("[redacted filename]", 0, "private-filename"))
    return findings


def approved_identity(name: str, email: str, policy: dict) -> bool:
    return {"name": name, "email": email} in policy["approved_identities"]


def audit_future_identity(root: Path, policy: dict) -> list[Finding]:
    findings = []
    for role in ("author", "committer"):
        raw = git(root, "var", f"GIT_{role.upper()}_IDENT").decode().strip()
        match = IDENTITY.fullmatch(raw)
        if not match or not approved_identity(match[1], match[2], policy):
            findings.append(Finding("Git identity", 0, role + "-identity"))
    return findings


def audit_index(root: Path, policy: dict, blocked: list[str]) -> list[Finding]:
    findings = []
    for record in git(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not record:
            continue
        info, path = record.split(b"\t", 1)
        mode, oid, stage = info.split()
        if stage != b"0":
            findings.append(Finding("Git index", 0, "unmerged-index"))
            continue
        if mode == b"160000":
            findings.append(Finding("Git index", 0, "submodule-needs-review"))
            continue
        findings.extend(scan_bytes(path.decode(errors="replace"), git(root, "cat-file", "blob", oid.decode()), policy, blocked))
    return findings


def audit_tree(root: Path, policy: dict, blocked: list[str]) -> list[Finding]:
    findings = []
    for path in release_files(root):
        findings.extend(scan_bytes(path.as_posix(), (root / path).read_bytes(), policy, blocked))
    return findings


def private_terms(root: Path) -> list[str]:
    path = root / ".run/privacy-remediation/blocked-terms.txt"
    return [x.strip() for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def audit_history(root: Path, policy: dict, blocked: list[str]) -> list[Finding]:
    findings = []
    for sha in git(root, "rev-list", "--all").decode().split():
        fields = git(root, "show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce%x00%B", sha).decode().split("\0", 4)
        for role, name, email in (("author", fields[0], fields[1]), ("committer", fields[2], fields[3])):
            if not approved_identity(name, email, policy):
                findings.append(Finding(sha[:12], 0, role + "-identity"))
        findings.extend(scan_bytes("commit " + sha[:12], fields[4].encode(), policy, blocked))
    seen = set()
    for record in git(root, "rev-list", "--objects", "--all").splitlines():
        oid, _, path = record.partition(b" ")
        if oid in seen:
            continue
        seen.add(oid)
        kind = git(root, "cat-file", "-t", oid.decode()).strip()
        if kind == b"blob":
            findings.extend(scan_bytes(path.decode(errors="replace"), git(root, "cat-file", "blob", oid.decode()), policy, blocked))
        elif kind == b"tag":
            data = git(root, "cat-file", "tag", oid.decode()).decode(errors="replace")
            for line in data.splitlines():
                if line.startswith("tagger "):
                    match = IDENTITY.fullmatch(line[7:])
                    if not match or not approved_identity(match[1], match[2], policy):
                        findings.append(Finding(oid.decode()[:12], 0, "tagger-identity"))
            findings.extend(scan_bytes("tag " + oid.decode()[:12], data.encode(), policy, blocked))
    refs = git(root, "for-each-ref", "--format=%(refname)")
    findings.extend(scan_bytes("Git reference names", refs, policy, blocked))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--policy", type=Path, help="explicit policy, useful for an isolated history rehearsal")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true", help="scan complete index, not working copies")
    mode.add_argument("--history", action="store_true", help="scan every reachable ref, blob and identity")
    parser.add_argument("--check-identity", action="store_true", help="check effective author/committer, including environment overrides")
    parser.add_argument("--blocked-terms-file", type=Path, help="private file: one literal per line; never commit it")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.policy:
            policy = json.loads(args.policy.read_text())
        elif args.staged:
            policy = json.loads(git(root, "show", ":.privacy-policy.json"))
        elif args.history:
            policy = json.loads(git(root, "show", "HEAD:.privacy-policy.json"))
        else:
            policy = json.loads((root / ".privacy-policy.json").read_text())
        blocked_file = args.blocked_terms_file or PROJECT_ROOT / ".run/privacy-remediation/blocked-terms.txt"
        blocked = [x.strip() for x in blocked_file.read_text().splitlines() if x.strip()] if blocked_file.exists() else []
        if args.history:
            if git(root, "rev-parse", "--is-shallow-repository").strip() == b"true":
                print("Privacy audit refused: full history is required (fetch-depth: 0).")
                return 1
            findings = audit_history(root, policy, blocked)
        elif args.staged:
            findings = audit_index(root, policy, blocked)
        else:
            findings = audit_tree(root, policy, blocked)
        if args.check_identity:
            findings.extend(audit_future_identity(root, policy))
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError):
        print("Privacy audit could not complete; verify policy, private blocklist and Git access.")
        return 1
    for finding in findings:
        # Match values and private filename contents are never emitted.
        safe_path = finding.path
        if any(term.casefold() in safe_path.casefold() for term in blocked):
            safe_path = "[redacted filename]"
        print(f"{safe_path}:{finding.line}: [{finding.kind}]")
    print(f"Privacy audit: {len(findings)} finding(s). No matched values are printed.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
