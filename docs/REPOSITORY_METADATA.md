# Repository handoff — TabTelly 0.1.0

The owner authorized recreating the public repository [jckceo/tabtelly](https://github.com/jckceo/tabtelly) after deleting the original repository. The new repository has a different repository ID. Publication proceeds from the same reviewed local project directory and sanitized history. Public release publication remains a separate step.

| Field | Recommendation |
| --- | --- |
| Product/repository display name | TabTelly |
| Repository slug | `jckceo/tabtelly` |
| Description | Cast a Chrome tab with audio to a compatible TV browser over local Wi-Fi. No TV app or cloud relay. |
| Visibility | Public |
| License | MIT — included locally; do not generate a second license |
| Initial version/tag | `0.1.0` / `v0.1.0` |
| Release title | TabTelly 0.1.0 — first experimental release |
| Release status | Pre-release, reflecting limited physical-device validation |
| Homepage | Leave blank until a real project/docs URL exists; no website is deployed |

The description is below GitHub's requested 160-character limit.

Recommended topics:

```text
webrtc screen-sharing screen-casting browser-casting smart-tv chrome macos python local-network peer-to-peer audio-streaming vidaa
```

## Initial empty-repository creation (completed)

1. Open [GitHub's new repository form](https://github.com/new).
2. Select your account or intended organization as owner.
3. Enter `tabtelly` and paste the description above.
4. Select **Public**.
5. Leave **Add a README file** unchecked. Choose **None** for `.gitignore` and license. Those files already exist locally, and the repository must start empty. [GitHub's guidance for existing local code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github) recommends avoiding those initialization options.
6. Click **Create repository**.
7. Send the resulting repository URL back. Stop here: do not clone it, create a second project folder, connect a remote, or push yet.

The owner authorized the repository recreation and the new empty repository was created. The CLI alternative and publication runbook are retained in [PUBLISHING.md](PUBLISHING.md) for reference; do not repeat repository creation or initialize a different local project.

## Recommended settings after the URL handoff

- Default branch: `main`. Enable Issues; the issue forms are ready. Keep the Wiki disabled because documentation lives with the source.
- Enable [private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository) before announcing the project, so SECURITY.md has a working private channel.
- Keep Actions workflow permissions read-only and require approval for untrusted contributor workflows. The included workflows use pinned official Actions and do not request repository write permission. See [GitHub Actions repository settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).
- Enable dependency alerts and secret scanning/push protection where available.
- After the first actual CI run succeeds, require its relevant checks for merges to `main`; do not mark nonexistent checks as required before they have run.
- Prefer squash merges and automatic branch deletion. Leave deployments and Pages disabled unless a later task explicitly requests them.
- Upload `assets/social-preview.png` as the repository social preview. Set the description/topics above and use the prepared release/launch copy.
- Build source assets from the reviewed commit, verify SHA256SUMS, then publish only when authorized. No automatic public release workflow is installed.

## Applied metadata

The supplied public repository uses `main`, the description and 12 topics above, the MIT license, private vulnerability reporting, and read-only workflow permissions. The social preview PNG is prepared locally for optional manual upload; repository protection/merge policies remain maintainer choices.
