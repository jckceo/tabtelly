#!/usr/bin/env python3
"""Scan only publishable TabTelly sources for high-confidence release leaks."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.build_release import PROJECT_ROOT, release_files
except ModuleNotFoundError:  # Direct execution places scripts/ first on sys.path.
    from build_release import PROJECT_ROOT, release_files


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    kind: str
    description: str


PATTERNS = (
    ("private-key", "Private key material", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----")),
    ("aws-key", "AWS access key identifier", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("github-token", "GitHub access token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("gitlab-token", "GitLab access token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("slack-token", "Slack access token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "personal-path",
        "Personal absolute path",
        re.compile(r"(?:/Users/[A-Za-z0-9._-]+/|[A-Za-z]:\\\\Users\\\\[A-Za-z0-9._-]+\\\\)"),
    ),
)
TEXT_SUFFIXES = {"", ".html", ".json", ".md", ".mjs", ".py", ".svg", ".txt", ".yaml", ".yml"}


def audit(root: Path = PROJECT_ROOT) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    for relative in release_files(root):
        if relative.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            lines = (root / relative).read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            for kind, description, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(Finding(relative, number, kind, description))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=PROJECT_ROOT, help="source tree to audit")
    args = parser.parse_args()
    if not args.path.is_dir():
        parser.error("path must be an extracted TabTelly source directory")
    findings = audit(args.path)
    if findings:
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.description} [{finding.kind}]")
        print(f"Release audit found {len(findings)} high-confidence issue(s).")
        return 1
    print("No high-confidence credential or machine-specific artifacts found in publishable files.")
    print("This heuristic result is not proof that no secret exists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
