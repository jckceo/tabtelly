#!/usr/bin/env python3
"""Build reproducible TabTelly source archives from a strict allowlist."""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import io
import json
import re
import tarfile
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = (
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".privacy-policy.json",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "RELEASE_READINESS.md",
    "SECURITY.md",
    "eslint.config.mjs",
    "package-lock.json",
    "package.json",
    "playwright.config.mjs",
    "requirements-dev.txt",
    "ruff.toml",
    "server.py",
    "tabcast",
    "tabtelly",
)
ALLOWLIST = {
    ".githooks": {""},
    ".github": {".md", ".yml", ".yaml"},
    "assets": {".png", ".svg"},
    "docs": {".md"},
    "scripts": {".mjs", ".py"},
    "tests": {".mjs", ".py"},
    "web": {".html"},
}
REQUIRED_RUNTIME_FILES = (
    Path("LICENSE"),
    Path("README.md"),
    Path("RELEASE_READINESS.md"),
    Path("server.py"),
    Path("tabtelly"),
    Path("web/receiver.html"),
    Path("web/sender.html"),
)
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


def version_from_server(root: Path) -> str:
    """Read the canonical VERSION assignment without importing the server."""
    tree = ast.parse((root / "server.py").read_text(encoding="utf-8"), "server.py")
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets
        ):
            version = ast.literal_eval(node.value)
            if isinstance(version, str) and VERSION_PATTERN.fullmatch(version):
                return version
            break
    raise ValueError("server.py must define VERSION as an X.Y.Z string literal")


def release_files(root: Path) -> tuple[Path, ...]:
    """Return regular source files permitted in a public source archive."""
    root = root.resolve()
    result: set[Path] = set()
    for name in ROOT_FILES:
        path = root / name
        if path.is_file() and not path.is_symlink():
            result.add(Path(name))
    for directory, suffixes in ALLOWLIST.items():
        base = root / directory
        if not base.is_dir() or base.is_symlink():
            continue
        for path in base.rglob("*"):
            if path.is_file() and not path.is_symlink() and path.suffix.lower() in suffixes:
                result.add(path.relative_to(root))
    return tuple(sorted(result, key=lambda path: path.as_posix()))


def _mode(path: Path) -> int:
    return 0o755 if path.as_posix() in {"server.py", "tabcast", "tabtelly"} or path.parts[0] == ".githooks" else 0o644


def _write_zip(path: Path, root: Path, prefix: str, files: tuple[Path, ...]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for relative in files:
            info = zipfile.ZipInfo(f"{prefix}/{relative.as_posix()}", ZIP_DATE)
            info.create_system = 3
            info.external_attr = (_mode(relative) & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, (root / relative).read_bytes())


def _write_tar_gz(path: Path, root: Path, prefix: str, files: tuple[Path, ...]) -> None:
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for relative in files:
            data = (root / relative).read_bytes()
            info = tarfile.TarInfo(f"{prefix}/{relative.as_posix()}")
            info.size = len(data)
            info.mode = _mode(relative)
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    with path.open("wb") as destination:
        with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed:
            compressed.write(tar_buffer.getvalue())


def _expected_members(prefix: str, files: tuple[Path, ...]) -> set[str]:
    return {f"{prefix}/{relative.as_posix()}" for relative in files}


def verify_archive(path: Path, root: Path, prefix: str, files: tuple[Path, ...]) -> None:
    """Verify an archive expands to the exact allowlisted, byte-identical source tree."""
    expected = _expected_members(prefix, files)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if names != expected:
                raise ValueError(f"{path.name}: archive members differ from the release allowlist")
            for relative in files:
                if archive.read(f"{prefix}/{relative.as_posix()}") != (root / relative).read_bytes():
                    raise ValueError(f"{path.name}: content mismatch for {relative}")
        return
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        if any(not member.isfile() for member in members):
            raise ValueError(f"{path.name}: archive contains a non-regular entry")
        if {member.name for member in members} != expected:
            raise ValueError(f"{path.name}: archive members differ from the release allowlist")
        for relative in files:
            extracted = archive.extractfile(f"{prefix}/{relative.as_posix()}")
            if extracted is None or extracted.read() != (root / relative).read_bytes():
                raise ValueError(f"{path.name}: content mismatch for {relative}")


def build(root: Path = PROJECT_ROOT, output: Path | None = None) -> tuple[Path, ...]:
    root = root.resolve()
    output = (output or root / "dist").resolve()
    version = version_from_server(root)
    files = release_files(root)
    missing = [path.as_posix() for path in REQUIRED_RUNTIME_FILES if path not in files]
    if missing:
        raise ValueError("release is missing required files: " + ", ".join(missing))

    # Build-time checks also protect manual builds outside GitHub Actions.
    try:
        from scripts import audit_privacy, audit_release
    except ModuleNotFoundError:
        import audit_privacy
        import audit_release
    policy = json.loads((root / ".privacy-policy.json").read_text())
    if audit_privacy.audit_tree(root, policy, audit_privacy.private_terms(root)) or audit_release.audit(root):
        raise ValueError("release privacy/credential audit failed; run scripts/audit_privacy.py and scripts/audit_release.py")

    output.mkdir(parents=True, exist_ok=True)
    prefix = f"TabTelly-{version}"
    zip_path = output / f"{prefix}.zip"
    tar_path = output / f"{prefix}.tar.gz"
    sums_path = output / "SHA256SUMS"
    _write_zip(zip_path, root, prefix, files)
    _write_tar_gz(tar_path, root, prefix, files)
    verify_archive(zip_path, root, prefix, files)
    verify_archive(tar_path, root, prefix, files)

    archives = (tar_path, zip_path)
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in archives]
    sums_path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    return zip_path, tar_path, sums_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="project root (default: repository root)")
    parser.add_argument("--output", type=Path, help="artifact directory (default: ROOT/dist)")
    args = parser.parse_args()
    artifacts = build(args.root, args.output)
    for artifact in artifacts:
        print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
