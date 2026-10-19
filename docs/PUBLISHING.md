# Publishing checklist

This runbook describes the owner-approved publication workflow. The owner authorized recreating [jckceo/tabtelly](https://github.com/jckceo/tabtelly) after deleting the original repository; preparation and publication use the original local project directory and its sanitized history. Public announcements and a public release require separate authorization.

**Recreation status:** the new empty public repository has a different repository ID. The current source and reachable history passed privacy checks before publication. After the owner deleted the original repository, all 15 checked original commit/LICENSE/README URLs returned 404. Recheck those same URLs after pushing the sanitized history; record any renewed exposure and seek GitHub Support review if needed. This is an access check, not a claim about all retained data or external copies. The repository already exists; do not repeat repository creation or initial Git setup. Follow [Privacy](PRIVACY.md) for identity checks, backups, history review and release-asset inspection.

## Phase 1: verify the local release

```bash
python3 -m unittest discover -s tests -v
npm ci
npx playwright install chromium
npm run check
npm run test:web
npm run test:e2e
python3 scripts/build_release.py
python3 scripts/audit_privacy.py --history
```

The browser tests use `@playwright/test`. On Linux, use `npx playwright install --with-deps chromium` when browser system dependencies are missing.

Inspect the source and release archive. Confirm `.run/`, logs, pairing codes, tokens, peer IDs, IP and MAC addresses, private device names, editor files, and OS metadata are absent. Confirm all launch drafts contain the actual repository URL and no unresolved publication placeholders.

The [CI workflow](https://github.com/jckceo/tabtelly/actions/workflows/ci.yml) runs 11 jobs across Linux, macOS, Windows, and Chromium. Review its actual result for the commit being released. Native capture pickers and physical televisions remain separate manual checks.

## Phase 2: review the release contents

Review every file that will be published, including the MIT license, security policy, generated archive, vector artwork, and exported `assets/social-preview.png`. Do not initialize Git or stage files until this review is complete.

## Phase 3: create an empty GitHub repository

Create the repository only. Stop after GitHub returns its final URL; do not initialize the local repository, add a remote, commit, tag, or push yet.

With GitHub CLI, first verify the active account:

```bash
gh auth status
GITHUB_OWNER="$(gh api user -q .login)"
printf 'Creating empty repository: https://github.com/%s/tabtelly\n' "$GITHUB_OWNER"
gh repo create "$GITHUB_OWNER/tabtelly" --public --description "Cast a Chrome tab with audio to a compatible TV browser over local Wi-Fi."
```

Read the printed owner before running `gh repo create`. Use `--private` instead of `--public` if a private staging repository is intended.

To use GitHub's website instead:

1. Choose **New repository**.
2. Select the intended owner and enter `tabtelly`.
3. Paste the description from [LAUNCH.md](LAUNCH.md).
4. Choose the intended visibility.
5. Leave README, `.gitignore`, and license initialization disabled so the repository remains empty.
6. Create the repository and copy its exact HTTPS URL.

At this point, stop and provide the final repository URL for the release files. Nothing should have been pushed.

## Phase 4: insert the supplied URL

The supplied repository URL is `https://github.com/jckceo/tabtelly`. Use it in [LAUNCH.md](LAUNCH.md). Review the complete documentation again and confirm no placeholder remains in content intended for publication.

## Phase 5: create history and push

Only after Phase 4 is complete, initialize the local repository and create its first commit:

```bash
git init
git branch -M main
git add .
git status --short
git diff --cached --check
git commit -m "Initial TabTelly release"
```

Do not add generated attribution or any AI/LLM co-author trailer. Verify that the user is the sole commit author.

Add the exact URL supplied in Phase 3, inspect it, then push:

```bash
git remote add origin https://github.com/jckceo/tabtelly.git
git remote -v
git push -u origin main
```

Check that the remote is the owner-supplied URL before running the command. Tag the commit only after the push succeeds and GitHub shows the expected files:

```bash
git tag -a v0.1.0 -m "TabTelly 0.1.0"
git push origin v0.1.0
```

## Phase 6: configure and release

In GitHub settings, enable **Private vulnerability reporting**, add the suggested topics, confirm `main` is the default branch, and upload `assets/social-preview.png` as the social preview. Verify the issue forms, pull request template, license, security policy, and rendered links.

Then:

1. Open **Releases → Draft a new release**.
2. Select `v0.1.0`.
3. Use the release title and notes from [LAUNCH.md](LAUNCH.md).
4. Attach the inspected release archive if one was produced.
5. Consider marking it as a pre-release to emphasize experimental status.
6. Preview every link, then publish.

Use the remaining launch drafts only after checking current community rules. Update [COMPATIBILITY.md](COMPATIBILITY.md) from reproducible device observations rather than anecdotes.
