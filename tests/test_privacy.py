import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import audit_privacy


class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.policy = {
            "approved_identities": [{"name": "public-alias", "email": "123+alias@users.noreply.github.com"}],
            "copyright_holder": "public-alias",
            "allowed_emails": [],
        }
        (self.root / ".privacy-policy.json").write_text(json.dumps(self.policy))

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args, env=None):
        return subprocess.check_output(["git", "-C", str(self.root), *args], env=env, stderr=subprocess.DEVNULL)

    def init_git(self):
        self.git("init", "-q")
        self.git("config", "user.name", "public-alias")
        self.git("config", "user.email", "123+alias@users.noreply.github.com")
        self.git("config", "commit.gpgsign", "false")

    def test_email_and_copyright_findings_never_echo_sensitive_values(self):
        private_email = "private-person" + "@mail.invalid-provider.com"
        private_name = "Private" + " Person"
        data = f"Copyright (c) 2026 {private_name}\nContact {private_email}\n".encode()
        findings = audit_privacy.scan_bytes("LICENSE", data, self.policy, [private_name])
        kinds = {f.kind for f in findings}
        self.assertTrue({"unapproved-email", "copyright-identity", "private-term"} <= kinds)
        rendered = "\n".join(str(f) for f in findings)
        self.assertNotIn(private_email, rendered)
        self.assertNotIn(private_name, rendered)

    def test_public_identity_and_reserved_examples_pass(self):
        data = b"123+alias@users.noreply.github.com alice@example.com user@evil.example"
        self.assertEqual(audit_privacy.scan_bytes("docs/guide.md", data, self.policy, []), [])
        self.assertEqual(audit_privacy.scan_bytes("LICENSE", b"Copyright (c) 2026 public-alias", self.policy, []), [])

    def test_third_party_notices_are_preserved_and_unapproved_email_requires_review(self):
        upstream_email = "contact" + "@upstream.org"
        data = ("Copyright (c) 2021 Another Upstream Author\n" + upstream_email).encode()
        findings = audit_privacy.scan_bytes("vendor/LICENSE", data, self.policy, [])
        self.assertEqual([f.kind for f in findings], ["unapproved-email"])
        policy = {**self.policy, "allowed_emails": [upstream_email]}
        self.assertEqual(audit_privacy.scan_bytes("vendor/LICENSE", data, policy, []), [])

    def test_staged_scan_reads_index_even_when_worktree_was_cleaned(self):
        self.init_git()
        path = self.root / "notes.txt"
        path.write_text("private-person" + "@mail.invalid-provider.com")
        self.git("add", "notes.txt")
        path.write_text("safe working copy")
        self.assertIn("unapproved-email", {f.kind for f in audit_privacy.audit_index(self.root, self.policy, [])})

    def test_history_finds_deleted_blob_and_author_email_on_non_head_branch(self):
        self.init_git()
        path = self.root / "notes.txt"
        path.write_text("safe")
        self.git("add", "notes.txt")
        self.git("commit", "-qm", "safe")
        self.git("checkout", "-qb", "other")
        path.write_text("private-person" + "@mail.invalid-provider.com")
        self.git("add", "notes.txt")
        env = {**os.environ, "GIT_AUTHOR_NAME": "Private Person", "GIT_AUTHOR_EMAIL": "private-person" + "@mail.invalid-provider.com"}
        self.git("commit", "-qm", "old disclosure", env=env)
        self.git("checkout", "-q", "-")
        findings = audit_privacy.audit_history(self.root, self.policy, [])
        self.assertTrue({"unapproved-email", "author-identity"} <= {f.kind for f in findings})

    def test_environment_identity_override_is_rejected(self):
        self.init_git()
        env = {"GIT_AUTHOR_EMAIL": "private-person" + "@mail.invalid-provider.com"}
        with patch.dict(os.environ, env):
            findings = audit_privacy.audit_future_identity(self.root, self.policy)
        self.assertIn("author-identity", {f.kind for f in findings})

    def test_annotated_tag_identity_and_message_are_audited(self):
        self.init_git()
        self.git("add", ".privacy-policy.json")
        self.git("commit", "-qm", "initial")
        env = {**os.environ, "GIT_COMMITTER_NAME": "Private Person"}
        self.git("tag", "-a", "v-test", "-m", "contact private-person" + "@mail.invalid-provider.com", env=env)
        kinds = {f.kind for f in audit_privacy.audit_history(self.root, self.policy, [])}
        self.assertTrue({"tagger-identity", "unapproved-email"} <= kinds)

    def test_staged_policy_cannot_be_bypassed_by_unstaged_allowlist(self):
        self.init_git()
        email = "private-person" + "@mail.invalid-provider.com"
        (self.root / "README.md").write_text(email)
        self.git("add", "README.md", ".privacy-policy.json")
        modified = {**self.policy, "allowed_emails": [email]}
        (self.root / ".privacy-policy.json").write_text(json.dumps(modified))
        with contextlib.redirect_stdout(io.StringIO()):
            result = audit_privacy.main(["--root", str(self.root), "--staged"])
        self.assertEqual(result, 1)

    def test_cli_output_is_redacted(self):
        (self.root / "README.md").write_text("Contact private-person" + "@mail.invalid-provider.com")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = audit_privacy.main(["--root", str(self.root)])
        self.assertEqual(result, 1)
        self.assertNotIn("private-person", output.getvalue())


if __name__ == "__main__":
    unittest.main()
