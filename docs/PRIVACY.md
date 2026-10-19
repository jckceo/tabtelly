# Maintainer and contributor privacy

The public maintainer identity is **jckceo**. The project's MIT notice uses that alias. This does not change ownership or the license terms. Preserve third-party copyright and license notices.

## Before committing

Choose a public alias and copy your exact GitHub noreply address from **GitHub → Settings → Emails**. Do not infer an address from an example or use someone else's identity. For the maintainer of this repository, the account ID and existing GitHub-attributed commits were verified against this pair:

```bash
git config --local user.name jckceo
git config --local user.email 49846464+jckceo@users.noreply.github.com
git config --local user.useConfigOnly true
git config --local core.hooksPath .githooks
```

These settings affect only this checkout. GitHub website edits and merges use account settings separately. Account settings are never changed by these commands. Environment variables and `--author` can override Git configuration; the checks inspect effective identities and committed history too.

Contributors should use their own public alias and exact noreply address. A maintainer must review additions to `approved_identities` in `.privacy-policy.json`; do not add private names or private addresses to that public file. The history check intentionally rejects unreviewed identities, including bots. Required third-party contact addresses may be explicitly reviewed under `allowed_emails`; preserve the original license notice rather than silently deleting it.

## Checks

```bash
python3 scripts/audit_privacy.py --check-identity
python3 scripts/audit_privacy.py --staged --check-identity
python3 scripts/audit_privacy.py --history
python3 scripts/audit_release.py
```

The default privacy check scans publishable source files, including binary file metadata represented as bytes. `--staged` reads the complete Git index and its staged policy, so cleaning only the working copy cannot hide a staged disclosure. `--history` checks every reachable local reference, historical blob, commit message, author, committer, and annotated tagger. It refuses shallow history; CI fetches full history. History checks use the committed policy unless an explicit policy is supplied for an isolated remediation rehearsal.

For additional private identifiers, keep a UTF-8 file with one literal per line under `.run/privacy-remediation/blocked-terms.txt`. This ignored file is loaded by local checks and the source builder. It must never be committed, uploaded, or copied into CI logs. Alternatively, supply `--blocked-terms-file` to the audit CLI. Do not put personal values in shell arguments or example fixtures. Diagnostics print locations and categories, never the matched values.

Source builds refuse unapproved email/copyright identities and detected credentials before writing archives. CI checks history before building. Hooks are local safeguards and must be enabled in each checkout; they are not a server-side guarantee. Reviews of policy changes remain necessary.

These checks are heuristics, not a general personal-data detector. Reserved example domains and GitHub noreply addresses are allowed in text; actual author/committer/tagger pairs require explicit approval. CI does not receive private blocked terms. Arbitrary names outside the project's copyright notices need private local checks and manual review. Image pixels, compressed/encoded payloads, external links, downloaded dependencies, untracked files and third-party services require separate inspection. The history check covers reachable local refs, not GitHub caches, unadvertised server refs, other clones, or unreachable objects retained in backups.

## Publication review

- Inspect LICENSE, README, package metadata, screenshots, image metadata, archive member names, release notes, commit identities and tags.
- Review staged paths explicitly; never stage `.run/`, `dist/`, environment files, private maps, backups, logs or local configuration.
- Review workflow logs and artifacts before sharing links. Secret scanning does not reliably detect names or personal email addresses.
- Download and inspect the actual release assets; changing source files does not update existing archives.
- Keep backups permission-restricted and offline from publication. Retain them only as long as needed for recovery and evidence.

## If information was already public

Stop publication, preserve private evidence, identify all affected branches/tags and public surfaces, then correct current files. A normal commit leaves earlier versions visible. `.mailmap` changes display attribution and does not erase historical data.

Prepare and test an exact `git-filter-repo` replacement in an isolated local copy after backing up the source and complete Git directory. Inspect changes to file contents, messages, author/committer/tagger metadata and all refs. Preserve third-party notices. Rewriting changes commit IDs and invalidates signatures. Coordinate with collaborators before any rewrite; use an explicit expected remote SHA for each approved ref instead of a blind mirror push.

Remote history rewrites, force pushes, repository deletion, and GitHub account changes require explicit owner approval. After an approved rewrite, review draft/public release assets and CI artifacts separately, retarget drafts, and verify a fresh remote read. Keep old refs out of subsequent merges and pushes.

GitHub may retain old commit views and pull-request references. A force push cannot erase existing clones, forks or search-engine caches. Request review through the [GitHub Support portal](https://support.github.com/) with the affected repository, first changed commits, PR count, and any orphaned LFS information, following [GitHub's sensitive-data removal procedure](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository). Support decides whether the information qualifies; removal is not guaranteed. Do not submit private backup archives or replacement maps to public issues. Existing fork/clone owners must clean their own copies; stale search results may need separate removal requests after the origin is corrected.

Reference: [GitHub commit email settings](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address) and the upstream [git-filter-repo manual](https://github.com/newren/git-filter-repo/blob/main/Documentation/git-filter-repo.txt).
