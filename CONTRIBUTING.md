# Contributing to TabTelly

The most useful contributions are focused bug reports, real-hardware compatibility observations, documentation corrections, and small changes that preserve the local-only design.

## Before opening a change

- Read [Architecture](docs/ARCHITECTURE.md) and [Compatibility](docs/COMPATIBILITY.md).
- Search existing issues first and discuss large architectural changes in an issue.
- Keep device names, IP and MAC addresses, pairing codes, peer IDs, and runtime secrets out of issues and fixtures.

## Local setup

The runtime needs Python 3.10 or later and has no pip dependencies. Development checks also need Node.js matching the `engines` field in package.json. Web checks use the repository lockfile; Ruff is pinned in requirements-dev.txt.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
npm ci
npx playwright install chromium
./tabtelly doctor
./tabtelly start --no-open
```

On Windows, create the environment with `python -m venv .venv`, activate it with `.venv\Scripts\Activate.ps1`, and use `python tabtelly` instead of `./tabtelly`.

## Validation

Run the checks relevant to your change. Before proposing a release, run the complete suite:

```bash
python -m ruff check .
python -m unittest discover -s tests -v
npm ci
npx playwright install chromium
npm run check
npm run test:web
npm run test:e2e
python scripts/audit_release.py
python scripts/build_release.py
```

The browser suite uses `@playwright/test`. On Linux, use `npx playwright install --with-deps chromium` when system browser dependencies are not already installed.

Automated browser and command tests do not prove that a television works. Describe hardware tests separately, including TV model, firmware, browser user agent, computer OS, Chrome version, and result. Do not turn one successful device test into a general claim.

## Pull requests

Keep each pull request focused. Explain the problem, resulting behavior, and validation. Update documentation when commands, configuration, UI, compatibility, or security behavior changes. Add user-visible changes under **Unreleased** in [CHANGELOG.md](CHANGELOG.md).

By submitting a contribution, you agree that it is licensed under the [MIT License](LICENSE). Report vulnerabilities through [SECURITY.md](SECURITY.md), not a public issue.
