#!/usr/bin/env python3
"""Build the distributable Linux archive for VBIOS Studio.

The Linux package is intentionally a source package: it ships our Python code
plus a launcher that uses the distribution's python3-gi / GTK 4 runtime.  GTK
is a system library on Linux (as it is for every GTK application packaged by a
distribution); compiling PyGObject here would require gtk4.pc and libadwaita-1.pc
and is explicitly out of scope for this project.

Usage:
    python tools/build_release.py --target linux [--version X.Y.Z] [--output dist]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import re
import shutil
import stat
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "dist"
LAUNCHER_HEAD = """#!/bin/sh
# VBIOS Studio launcher.  Uses the system Python so that the distribution's
# PyGObject/GTK 4 installation is available (the package does not bundle GTK).
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python=${VBIOS_STUDIO_PYTHON:-/usr/bin/python3}
PYTHONPATH="$here/lib${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPATH
"""
CLI_LAUNCHER = LAUNCHER_HEAD + 'exec "$python" -m vbios_studio "$@"\n'
GUI_LAUNCHER = LAUNCHER_HEAD + """if ! "$python" -c 'import gi; gi.require_version("Gtk", "4.0")' >/dev/null 2>&1; then
    echo "VBIOS Studio: PyGObject with GTK 4 is missing." >&2
    echo "Install it with: sudo apt-get install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1" >&2
    exit 1
fi
exec "$python" -m vbios_studio.ui "$@"
"""


def read_version(explicit: str | None) -> str:
    if explicit:
        return explicit
    if os.environ.get("VERSION"):
        return os.environ["VERSION"]
    init = ROOT / "src" / "vbios_studio" / "__init__.py"
    if init.is_file():
        match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init.read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    pyproject = ROOT / "pyproject.toml"
    if pyproject.is_file():
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', pyproject.read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    raise SystemExit("cannot determine version; pass --version or set VERSION")


def copy_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise SystemExit(f"missing source package: {source}")
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".mypy_cache", ".ruff_cache"),
    )


def build_linux(version: str, output: Path) -> Path:
    name = f"vbios-studio-{version}-linux-x86_64"
    staging = ROOT / "build" / "linux" / name
    if staging.exists():
        shutil.rmtree(staging)
    (staging / "lib").mkdir(parents=True)
    (staging / "bin").mkdir()
    copy_tree(ROOT / "src" / "vbios_studio", staging / "lib" / "vbios_studio")
    upstream = ROOT / "src" / "nvidia_vbios"
    if upstream.is_dir():
        copy_tree(upstream, staging / "lib" / "nvidia_vbios")
    launchers = (("vbios-studio", CLI_LAUNCHER), ("vbios-studio-gui", GUI_LAUNCHER))
    for launcher_name, content in launchers:
        launcher = staging / "bin" / launcher_name
        launcher.write_text(content, encoding="utf-8")
        launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    for filename in ("README.md", "LICENSE", "NOTICE.md", "THIRD_PARTY_NOTICES.md"):
        candidate = ROOT / filename
        if candidate.is_file():
            shutil.copy2(candidate, staging / filename)
    # A desktop entry makes the archive usable from a file manager.
    applications = staging / "share" / "applications"
    applications.mkdir(parents=True)
    (applications / "vbios-studio.desktop").write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=VBIOS Studio\n"
        "Comment=Inspect and edit NVIDIA VBIOS images\n"
        "Exec=vbios-studio\n"
        "Terminal=false\n"
        "Categories=Utility;System;\n",
        encoding="utf-8",
    )

    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{name}.tar.gz"
    if archive.exists():
        archive.unlink()
    write_deterministic_tar(staging, archive, arcname=name)
    write_checksums(output)
    print(f"built {archive}")
    return archive


def write_deterministic_tar(staging: Path, archive: Path, arcname: str) -> None:
    entries = sorted(staging.rglob("*"), key=lambda path: path.relative_to(staging).as_posix())
    with archive.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as tar:
                for path in [staging, *entries]:
                    info = tar.gettarinfo(
                        str(path),
                        arcname=arcname if path == staging else f"{arcname}/{path.relative_to(staging).as_posix()}",
                    )
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mtime = 0
                    if info.isreg():
                        with path.open("rb") as handle:
                            tar.addfile(info, handle)
                    else:
                        tar.addfile(info)


def write_checksums(output: Path) -> None:
    lines = []
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.name}")
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=["linux"], default="linux")
    parser.add_argument("--version", default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    version = read_version(args.version)
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
        raise SystemExit(f"invalid version: {version}")
    build_linux(version, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
