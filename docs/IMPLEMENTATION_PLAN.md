# Local release plan — TabTelly 0.1.0

All work stays in the original working directory. No repository, remote, deployment, commit, or release is created during this preparation.

## Design decisions

Retain the small Python standard-library HTTP relay and existing browser WebRTC implementation. A native app or Electron shell would add packaging and dependency cost without improving the TV browser requirement; a cloud relay would change privacy and operating costs. Package the current architecture as an experimental, self-hosted LAN utility.

Use a loopback-only sender, random per-run sender/admin credentials, and rate-limited TV pairing. Host and Origin checks defend the local sender against cross-site requests and DNS rebinding. Pairing over plain HTTP assumes a trusted LAN and is not confidential. Encrypt media through WebRTC, with no cloud signaling, analytics, STUN, or TURN.

Keep sender capture permissions controlled by the browser. Preserve quality presets, tab switching, PiP controls, audio options, and diagnostic pages. Restore browser congestion control by default; experimental loss mode and keepalive tone are explicit opt-ins. Keep receiver syntax ES5 and detect missing WebRTC.

## File ownership and execution

1. Root: `server.py`, `tests/test_server.py`, browser integration tests, integration review, release readiness. Write failing boundary tests; implement authorization, parsing limits, ownership checks, private runtime identity; verify with real loopback requests. Audit final publishable source and extracted artifacts.
2. Launcher: `tabtelly`, legacy `tabcast`, `tests/test_cli.py`. Portable process control, doctor, private per-port runtime, health/instance identity checks; never signal unrelated PIDs. Verify temporary runtimes and occupied ports.
3. Browser: `web/*`, `tests/web-unit.mjs`. Pairing, capability/error states, asynchronous capture/session lifecycle repairs, accessible controls; test regressions and actual browser WebRTC frames with synthetic media.
4. Documentation: README, legal/contribution/security/changelog files, user and architecture guides, founder story and launch drafts. Match only actual features and label hardware validation limits.
5. Research: `docs/RESEARCH.md`. Check competing projects and candidate names using primary sources. Adopt TabTelly consistently.
6. Quality: pinned development tooling, syntax/lint checks, source archive builder/auditor, CI and manual artifact workflow, ignore rules. Tests verify deterministic packaging and exclusion of secrets/runtime artifacts.

## Release gates

- Python HTTP, CLI, and packaging regressions pass.
- Browser syntax/lint and frontend unit regressions pass.
- Chromium integration establishes WebRTC and receives frames/audio using test media; verifies stop and tab switching. This is not physical-TV validation.
- Source archives build deterministically, include documentation and license, exclude local runtime files, and run independently when extracted inside the workspace.
- Documentation and launch drafts have no private IPs, device identifiers, unverified performance promises, invented founder details, or premature repository links.
- Record concrete evidence and unresolved nonblocking hardware/platform limits in RELEASE_READINESS.md.
- Only then provide repository metadata and manual creation instructions; stop for the user's repository URL.
