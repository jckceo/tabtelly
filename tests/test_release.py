import hashlib
import os
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

from scripts import audit_release, build_release


class ReleaseFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        files = {
            "server.py": "VERSION = '0.1.0'\n",
            "tabcast": "#!/bin/sh\nexec python3 server.py \"$@\"\n",
            "tabtelly": "#!/usr/bin/env python3\nprint('launcher')\n",
            "README.md": "# TabTelly\n",
            "RELEASE_READINESS.md": "# Release readiness\n",
            "LICENSE": "Test license\n",
            "package.json": '{"name":"tabtelly","version":"0.1.0"}\n',
            "package-lock.json": '{"name":"tabtelly","version":"0.1.0","lockfileVersion":3}\n',
            "assets/icon.svg": "<svg xmlns=\"http://www.w3.org/2000/svg\"/>\n",
            "docs/guide.md": "# Guide\n",
            "scripts/tool.py": "print('tool')\n",
            "tests/test_tool.py": "def test_example():\n    assert True\n",
            "web/sender.html": "<!doctype html><title>Sender</title>\n",
            "web/receiver.html": "<!doctype html><title>Receiver</title>\n",
            ".github/workflows/ci.yml": "name: CI\n",
        }
        for name, content in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        (self.root / "private.env").write_text("API_KEY=super-secret-value\n", encoding="utf-8")
        (self.root / "node_modules/pkg").mkdir(parents=True)
        (self.root / "node_modules/pkg/index.js").write_text("secret\n", encoding="utf-8")
        (self.root / "work").mkdir()
        (self.root / "work/notes.txt").write_text("private\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()


class ReleaseBuildTests(ReleaseFixture):
    def test_publishable_allowlist_excludes_secrets_and_generated_trees(self):
        names = {path.as_posix() for path in build_release.release_files(self.root)}
        self.assertIn("server.py", names)
        self.assertIn("tabtelly", names)
        self.assertIn("assets/icon.svg", names)
        self.assertIn("docs/guide.md", names)
        self.assertIn("RELEASE_READINESS.md", names)
        self.assertNotIn("private.env", names)
        self.assertFalse(any(name.startswith(("node_modules/", "work/", ".run/", "dist/")) for name in names))

    def test_build_is_deterministic_and_uses_server_version(self):
        first = self.root / "first"
        second = self.root / "second"
        result_one = build_release.build(self.root, first)

        now = time.time() + 10_000
        for path in build_release.release_files(self.root):
            os.utime(self.root / path, (now, now))
        result_two = build_release.build(self.root, second)

        expected = {"TabTelly-0.1.0.zip", "TabTelly-0.1.0.tar.gz", "SHA256SUMS"}
        self.assertEqual({path.name for path in result_one}, expected)
        self.assertEqual({path.name for path in result_two}, expected)
        for name in expected:
            one = (first / name).read_bytes()
            two = (second / name).read_bytes()
            self.assertEqual(hashlib.sha256(one).digest(), hashlib.sha256(two).digest())

        with zipfile.ZipFile(first / "TabTelly-0.1.0.zip") as archive:
            names = set(archive.namelist())
        self.assertIn("TabTelly-0.1.0/server.py", names)
        self.assertNotIn("TabTelly-0.1.0/private.env", names)


class ReleaseAuditTests(ReleaseFixture):
    def test_audit_reports_high_confidence_credentials_and_personal_paths(self):
        leak = self.root / "docs/leak.md"
        leak.write_text(
            "-----BEGIN " + "PRIVATE KEY-----\n"
            "placeholder\n"
            "-----END PRIVATE KEY-----\n"
            "Local path: /Users/" + "alice/private/tabtelly\n",
            encoding="utf-8",
        )

        findings = audit_release.audit(self.root)

        descriptions = "\n".join(finding.description for finding in findings)
        self.assertIn("private key", descriptions.lower())
        self.assertIn("personal absolute path", descriptions.lower())

    def test_audit_only_scans_publishable_allowlist(self):
        findings = audit_release.audit(self.root)
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
