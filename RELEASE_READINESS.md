# TabTelly 0.1.0 — release readiness

Review updated: **2026-10-20**. Scope: the existing project directory. The owner authorized recreating the empty public repository [jckceo/tabtelly](https://github.com/jckceo/tabtelly) after deleting the original repository. Final publication checks use this same local directory and its already-sanitized history.

## Release disposition

**Sanitized source and history ready for an experimental release draft.** The original repository was deleted by the owner, after which all 15 checked original commit/LICENSE/README URLs returned 404. The owner then authorized a new public repository, which was created with a different repository ID. Copyright notices and author/committer identities use the approved public identity; source and history safeguards are active. Revalidate the old URLs, published source, release assets and fresh CI before any public release. A 404 access check does not establish global erasure of retained data or external copies. No hosted site, public release, or launch announcement has been published. See [Privacy](docs/PRIVACY.md).

The intended release is **experimental 0.1.0**, under the MIT license. It is a usable LAN casting utility with explicit device and network limits, not a promise of universal TV support.

## Implemented

- Product name and positioning: **TabTelly**, a Chrome-tab-with-audio caster to a compatible TV browser using direct LAN WebRTC. Dated competitor and naming research is in [RESEARCH.md](docs/RESEARCH.md).
- Portable Python command interface: `start`, `stop`, `restart`, `status`, `log`, `doctor`, help/version, `--no-open`, and the old `tabcast` compatibility wrapper. Runtime uses the same Python interpreter, no curl/lsof, no hardcoded application runtime path, private per-port state, and explicit environment overrides.
- Loopback-only sender; rate-limited six-digit receiver pairing; random per-start role credentials; current-peer ownership checks; Host/Origin protections; private atomic session files; bounded request bodies, message queues, signaling rates, connections, and socket timeouts.
- Authenticated server self-shutdown and verified instance identity. Managed stop never sends an OS signal to a stored PID.
- Sender and receiver onboarding, keyboard pairing, focus states, responsive controls, live diagnostic statistics, and actionable failures. Receiver script remains ES5-compatible by syntax checks.
- Capture switching and stop lifecycle repairs, queued ICE handling, receiver reload/reconnect, browser-default congestion control, explicit experimental loss mode and optional keepalive tone.
- Versioned source ZIP and tar.gz packaging, SHA-256 checksums, deterministic metadata, strict publication allowlist, archive-content verification, and a heuristic credential/machine-path audit.
- Pinned developer tools and lockfiles; read-only CI and a manual workflow for building unsigned source artifacts. These workflows do not create GitHub releases.
- README, MIT license, contribution/security/changelog files, user tutorials, compatibility matrix, FAQ, troubleshooting, architecture and security-review notes, authentic founder story, issue/PR templates, launch copy for GitHub/HN/Reddit/X, original icon/social graphics, and redacted app screenshots.

## Review findings and fixes

The prototype contained private device/network details, unauthenticated signaling/control endpoints, insufficient request validation, unbounded relay state, a machine-specific shell launcher, and an experimental congestion workaround enabled by default. These were removed or addressed as described above and in [SECURITY_REVIEW.md](docs/SECURITY_REVIEW.md).

Independent review also identified missing sender-stop/resource-control tests, publicly exposed health identity metadata, and Host normalization edge cases. Tests were added, health identity became loopback-only, and authorities now normalize case/default HTTP ports without relaxing origin boundaries. Frontend review repaired capture cancellation races, pre-offer ICE loss, and authenticated latency synchronization. The first GitHub run exposed a pip-cache path configuration error, which was corrected. The Python matrix also revealed that decoder recursion thresholds differ across interpreter versions; the server now enforces its own 32-container JSON nesting limit and rejects numeric overflow, with independently reproduced regression cases. Hosted macOS runs also exposed the standard HTTP server's blocking hostname lookup before listening; the relay and HTTP test fixtures now bind numeric addresses without that lookup, and local test health probes explicitly bypass proxies. Both dependencies have regression tests. The [GitHub runner issue](https://github.com/actions/runner-images/issues/14409) documents the macOS startup behavior.

Runtime dependencies are Python's standard library and the browsers already used to send/receive. npm packages and Ruff are development-only, version-pinned. There is no pip install step for using the application.

## Validation evidence

Local validation ran on **macOS arm64, Python 3.11.9, Node.js 26.5.0, Ruff 0.17.1, Playwright 1.64.0, and Chromium 156.0.8078.4**. Historical prototype measurements are not counted as current-release tests.

| Check | Actual result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | **56 passed** after local privacy changes: 14 launcher, 28 server/boundary, 5 release/audit, 9 privacy tests |
| `npm test` | **Passed**: module and inline ESLint, script parsing, and **11 frontend unit tests** |
| Receiver compatibility syntax | Acorn ECMAScript 5 parse and lint passed; this checks syntax, not every old-TV API/CSS behavior |
| `npm run test:e2e` | **4 passed** using Chromium: wrong/right keyboard pairing; actual WebRTC generated video/audio; switch/reload/busy sender/stop; narrow sender and 720p receiver layout; unsupported WebRTC receiver |
| `python -m ruff check .` | Passed with the pinned project-local Ruff installation |
| Clean dependency installation | `NPM_CONFIG_USERCONFIG=/dev/null npm ci --ignore-scripts --cache .run/npm-cache` passed using the lockfile, without personal npm settings |
| `npm audit --audit-level=high` | **0 vulnerabilities reported** for the locked development dependency tree at review time |
| `python3 scripts/audit_release.py` | No high-confidence credential or machine-path findings in publishable files; manual private-identifier review also found no old hotel/device identifiers |
| Privacy safeguards and history | Current source/effective maintainer identity passed; 9 privacy regressions passed, including staged-vs-working-copy content, unstaged policy bypass, alternate branches, deleted historical content, author environment overrides and annotated taggers. The owner-approved rewrite sanitized all 5 original commits, preserving all other original source bytes; rewritten public trees and raw identities were independently verified. After owner deletion, all 15 original commit/LICENSE/README URL checks returned 404. Repeat those checks on the recreated repository before releasing |
| `python3 scripts/build_release.py` | ZIP, tar.gz, SHA256SUMS built; exact allowlisted source bytes verified; independent unchanged-source rebuilds matched |
| Extracted source smoke check | ZIP extracted only into a temporary fixture inside this workspace; `--version`, `doctor`, `start --no-open`, `status`, `stop`, and source audit passed with a minimal environment and no node_modules/venv/user configuration |
| Default port startup | Verified and retired the old prototype process from this workspace, then upgraded launcher start/status/stop on port 8090 passed with loopback binding; app left stopped |
| Documentation/assets | Local Markdown/image links checked; sender/receiver/social PNGs visually inspected; pairing code/address redacted from sender screenshot |
| CI and repository files | Pre-remediation implementation CI passed **all 11 jobs**: nine Python OS/version jobs, JavaScript/release checks, and Chromium integration; pinned official Actions and read-only permissions verified. This does not validate the new privacy changes remotely |
| Git/publication boundary | The original folder is connected to `https://github.com/jckceo/tabtelly.git`; 53 allowlisted source files were committed and pushed under the owner identity. Runtime secrets, logs, dependencies, OS metadata, and archives remain ignored. Public source ZIP contents were compared with the local commit |

The browser download was stored under `.run/browsers`, and local developer environments/caches remain ignored. Runtime session files and logs are also ignored; neither the source archive nor future Git staging should contain them. The immutable source archive excludes all of those directories. SHA256SUMS lives beside the archives and is regenerated whenever included source/documentation changes.

The local test run and hosted CI prove only the exercised command/protocol/synthetic-media behavior. Native capture picker permissions, physical TV playback, and sustained hotel Wi-Fi performance were not tested. Windows skips the POSIX-only symlink cases.

## Known limitations and unsupported scenarios

- The automated WebRTC test uses generated moving canvas video and oscillator audio in Chromium. It proves browser signaling/media flow, not native OS capture permissions, a real screen picker, speaker output, lip sync, hardware decoding, or physical TV compatibility.
- The original prototype worked on one legacy Chromium-based Hisense VIDAA TV. The release candidate has **not** been retested on that TV. Other TV brands, firmware versions, and browsers are unverified.
- macOS is the locally exercised OS. Hosted command CI passed on Linux, macOS, and Windows; browser media CI ran on Linux. Do not infer native desktop capture or TV validation from an OS matrix.
- One sender and one receiver only. The newest paired receiver can replace the previous receiver. Restart rotates all credentials; reload the sender and re-pair the TV.
- A compatible WebRTC receiver, shared codec, and direct IPv4 LAN reachability are required. No automatic discovery, IPv6-only operation, STUN/TURN, cloud relay, NAT traversal, or guest/client-isolation bypass.
- Hotel/public networks may be isolated or hostile. Pairing is over HTTP and does not protect against a network operator or on-path attacker. Use a trusted LAN; never port-forward the server.
- Native AirPlay/Google Cast/Miracast/DLNA protocols, multiple viewers, native installers, code signing, and a hosted service are outside this release.
- Chrome/OS determine tab-audio availability and local-audio suppression. Window/system audio is not promised. Protected/DRM media may be black or silent; capture restrictions are not bypassed.
- Quality presets are targets, not guarantees. PiP availability, background throttling, autoplay, fullscreen, decoder performance, long sessions, Wi-Fi drops, and TV standby require real-device checks. Experimental options have no guaranteed benefit.
- Resource bounds reduce accidental/excessive use; the standard-library HTTP server is not an internet-facing service or a complete denial-of-service defense.
- Source archives are unsigned. SHA256SUMS detects corruption when obtained through a trusted channel; it is not an independent signature or attestation.

## Publication checklist

- [x] Owner approved the reviewed history remediation; updated only `main` with an exact lease, validated sanitized public history, and replaced/retargeted the existing release draft assets.
- [x] Owner deleted the original repository; all 15 checked original commit/LICENSE/README URLs returned 404. Owner authorized a new public repository, which was created with a different ID.
- [ ] Before publishing a release, verify the recreated repository, fresh CI, downloaded draft assets and all original SHA URLs again. Seek GitHub Support review if any affected view becomes accessible; do not claim global erasure.

- [x] Complete final local validation and record exact outcomes above.
- [x] Owner creates an **empty** public `tabtelly` repository, without generated README/license/gitignore, and supplies its URL.
- [x] After the URL is supplied, re-review the source, Git state/remotes, ignored files, and secret scan before making the first commits.
- [x] Insert the real repository URL in launch drafts, revalidate links/metadata, and rebuild archives from the reviewed source.
- [x] Stage/review only intended files; author commits solely as the owner with no AI attribution/trailers.
- [x] Connect this same folder, push, and run configured GitHub Actions; resolve actual platform/runner failures before preparing release assets.
- [x] Verify description, 12 topics, `main`, private vulnerability reporting, and read-only workflow permissions.
- [ ] Optional: upload the prepared social preview PNG through repository settings.
- [x] Prepare the `v0.1.0` notes and verified source archives/checksums for the release draft.
- [ ] Publish the experimental pre-release only when explicitly authorized.
- [ ] Replace launch links and check current community rules before any announcement is posted.

Repository name, description, topics, settings, and exact empty-repository creation steps are ready in [REPOSITORY_METADATA.md](docs/REPOSITORY_METADATA.md).

## Recommended next improvements

1. Run a recorded physical-TV matrix with model/firmware/browser versions, including a long session, standby, Wi-Fi interruption, audio, fullscreen, and visual lip-sync checks.
2. Exercise native Chrome capture pickers and permissions on current macOS, Windows, and Linux desktops.
3. Evaluate a practical trusted HTTPS onboarding path before supporting untrusted networks; do not market pairing as transport security.
4. Add an explicit per-receiver approval/revocation model if multiple devices become a product requirement.
5. Consider native packaging and signed releases only after the compatibility surface is better measured.
