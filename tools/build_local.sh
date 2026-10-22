#!/usr/bin/env bash
# Local equivalent of the GitHub Actions pipelines.
#
#   tools/build_local.sh --check   create .venv, install dev dependencies, run all gates
#   tools/build_local.sh --dist    build dist/vbios-studio-<ver>-linux-x86_64.tar.gz
#   tools/build_local.sh --clean   remove .venv and build outputs
#
# PyGObject is deliberately NOT installed from PyPI: it needs GTK development
# headers (gtk4.pc, libadwaita-1.pc) that this machine does not have.  The venv
# is created with --system-site-packages so the distribution's python3-gi is
# used instead.  All pip invocations explicitly target pypi.org because the
# system-wide pip configuration on this machine points at a mirror whose TLS
# endpoint is unreachable.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

PYTHON=${PYTHON:-python3}
VENV=${VENV:-.venv}
PIP_INDEX_URL=${PIP_INDEX_URL:-https://pypi.org/simple}
export PIP_INDEX_URL

MODE=${1:---check}
if [ "$#" -gt 1 ]; then
    echo "usage: tools/build_local.sh [--check|--dist|--clean]" >&2
    exit 2
fi

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

venv_python() { printf '%s/bin/python' "$VENV"; }

ensure_venv() {
    if [ ! -x "$VENV/bin/python" ]; then
        log "creating $VENV with --system-site-packages (PyGObject comes from the OS)"
        "$PYTHON" -m venv --system-site-packages "$VENV"
    fi
    if ! grep -q '^include-system-site-packages = true' "$VENV/pyvenv.cfg"; then
        die "$VENV is not a --system-site-packages venv; remove it and rerun"
    fi
    # pip itself is upgraded from pypi.org, never from the broken system mirror.
    "$VENV/bin/python" -m pip install --index-url "$PIP_INDEX_URL" --upgrade pip
}

install_deps() {
    log "installing dev dependencies from $PIP_INDEX_URL"
    "$(venv_python)" -m pip install --index-url "$PIP_INDEX_URL" \
        -r tools/requirements-dev.txt
    # The project itself is installed editable.  PyGObject must not be a hard
    # dependency of the project (enforced by t2); if it were, this step would
    # try to compile it and fail without gtk4.pc.
    "$(venv_python)" -m pip install --index-url "$PIP_INDEX_URL" -e .
}

check_gtk() {
    log "checking system PyGObject / GTK 4 runtime (pkg-config is not required)"
    "$(venv_python)" - <<'PY'
import gi

try:
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk  # noqa: F401
except (ValueError, ImportError) as exc:  # pragma: no cover - host dependent
    raise SystemExit(
        "PyGObject with the GTK 4 typelib is required. Install it with the OS "
        "package manager, for example:\n"
        "  sudo apt-get install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1\n"
        "Do not install PyGObject with pip on a machine without gtk4.pc.\n"
        f"original error: {exc}"
    )
print(f"GTK {Gtk.get_major_version()}.{Gtk.get_minor_version()} available")
PY
}

run_checks() {
    check_gtk
    log "ruff check"
    "$(venv_python)" -m ruff check src tests
    log "ruff format --check"
    "$(venv_python)" -m ruff format --check src tests
    log "mypy --strict"
    "$(venv_python)" -m mypy src/vbios_studio
    log "import-linter"
    "$VENV/bin/lint-imports"
    log "pytest"
    "$(venv_python)" -m pytest -q
    log "entry point"
    "$(venv_python)" -m vbios_studio --version
}

build_dist() {
    log "building Linux distribution"
    "$(venv_python)" tools/build_release.py --target linux "$@"
}

clean() {
    log "removing build outputs"
    rm -rf "$VENV" build dist dist-linux dist-windows
}

case "$MODE" in
    --check)
        ensure_venv
        install_deps
        run_checks
        log "all checks passed"
        ;;
    --dist)
        ensure_venv
        install_deps
        check_gtk
        shift || true
        build_dist "$@"
        ;;
    --clean)
        clean
        ;;
    --help|-h)
        sed -n '2,12p' "$0"
        ;;
    *)
        echo "unknown option: $MODE (expected --check, --dist or --clean)" >&2
        exit 2
        ;;
esac
