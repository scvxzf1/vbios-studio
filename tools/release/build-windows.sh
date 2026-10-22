#!/usr/bin/env bash
# Build the single-file Windows executable.
#
# Runs inside an MSYS2 UCRT64 shell (GitHub Actions windows-latest job or a local
# MSYS2 installation).  GTK 4 and PyGObject come from MSYS2 packages; Nuitka
# compiles our Python code and embeds the GTK runtime as a onefile payload that
# is unpacked to %LOCALAPPDATA%\VBIOS Studio\<version>\gtk on first start.
#
# This is the Windows half of the upstream nvidia-vbios-vix-editor release
# tooling (GPL-3.0-or-later), adapted for the VBIOS Studio entry point.
set -euo pipefail

root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"

version_pattern='^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z]+([.-][0-9A-Za-z]+)*)?(\+[0-9A-Za-z]+([.-][0-9A-Za-z]+)*)?$'
if [ -z "${VERSION:-}" ]; then
    VERSION=$(python - <<'PY'
import pathlib, re
text = pathlib.Path('src/vbios_studio/__init__.py').read_text(encoding='utf-8')
match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.M)
print(match.group(1) if match else '')
PY
)
    VERSION=$(printf '%s' "$VERSION" | tr -d '\r')
fi
[[ ${VERSION:-} =~ $version_pattern ]] || { echo "invalid or missing VERSION: ${VERSION:-}" >&2; exit 2; }

work="$root/build-windows"
out="$root/dist-windows"
rm -rf "$work" "$out"
mkdir -p "$work" "$out"
cp -a "$root/src" "$work/src"
src="$work/src"
export PYTHONPATH="$src"

metadata=(
    --company-name="VBIOS Studio contributors"
    --product-name="VBIOS Studio"
    --file-version="${VERSION%%[-+]*}"
    --product-version="${VERSION%%[-+]*}"
    --copyright="Copyright (C) 2026 VBIOS Studio contributors"
)
export LDFLAGS="-march=x86_64"
nuitka=(env -u MSYSTEM python -m nuitka --assume-yes-for-downloads --zig
        --python-flag=no_docstrings --python-flag=no_asserts --python-flag=no_site --python-flag=isolated
        --nofollow-import-to=tests --nofollow-import-to=unittest --nofollow-import-to=pydoc
        --remove-output "${metadata[@]}")

# PyGObject ships unmodified next to the compiled program (LGPL): only its
# compiled extension modules are copied; the Python sources stay replaceable.
gi_src=$(python -c 'import gi, os; print(os.path.dirname(gi.__file__))')
gi_stdlib=$(python - "$gi_src" <<'PY'
import ast, pathlib, sys
names = set()
for path in pathlib.Path(sys.argv[1]).rglob('*.py'):
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
import importlib.util
tops = sorted({n.split('.')[0] for n in names} & set(sys.stdlib_module_names) - {'__future__', 'sys'})
specs = {t: importlib.util.find_spec(t) for t in tops}
print(' '.join(('--include-package=' if spec.submodule_search_locations else '--include-module=') + t
               for t, spec in specs.items() if spec is not None))
PY
)
read -r -a gi_args <<< "$gi_stdlib"

runtime="$work/gtk"
mkdir -p "$runtime/girepository"
cp -a "$gi_src" "$runtime/gi"
find "$runtime/gi" -name __pycache__ -type d -prune -exec rm -rf {} +
prefix=/ucrt64
# Only the typelibs GTK actually loads (namespaces and their dependencies).
for typelib in $(python - <<'PY' | tr -d '\r'
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: F401
repo = gi.Repository.get_default()
names = {f'{ns}-{repo.get_version(ns)}' for ns in repo.get_loaded_namespaces()}
for ns in repo.get_loaded_namespaces():
    names.update(repo.get_dependencies(ns))
print(' '.join(sorted(names)))
PY
); do
    cp "$prefix/lib/girepository-1.0/$typelib.typelib" "$runtime/girepository/"
done
mkdir -p "$runtime/share/glib-2.0/schemas" "$runtime/share/icons"
cp "$prefix/share/glib-2.0/schemas/gschemas.compiled" "$runtime/share/glib-2.0/schemas/"
cp -a "$prefix/share/icons/hicolor" "$runtime/share/icons/" 2>/dev/null || true

# DLL closure: GTK plus everything GObject loads by name.
roots=("$runtime"/gi/_gi*.pyd "$prefix/bin/libgtk-4-1.dll")
for typelib in "$runtime"/girepository/*.typelib; do
    while IFS= read -r library; do
        [ -f "$prefix/bin/$library" ] && roots+=("$prefix/bin/$library")
    done < <(strings "$typelib" | grep -oE 'lib[A-Za-z0-9_.+-]*-[0-9]+\.dll' | sort -u)
done
for dll in $(ntldd -R "${roots[@]}" 2>/dev/null | grep -oiE '[A-Z]:\\[^ ]*\\ucrt64\\bin\\[^ ]*\.dll' | sort -u); do
    cp -n "$(cygpath -u "$dll")" "$runtime/"
done
for library in "${roots[@]}"; do
    case "$library" in "$prefix"/bin/*) cp -n "$library" "$runtime/" ;; esac
done

"${nuitka[@]}" --onefile --onefile-tempdir-spec="{CACHE_DIR}/VBIOS Studio/${VERSION}" \
    --windows-console-mode=attach --output-dir="$(cygpath -w "$work/gui")" \
    --output-filename=vbios-studio.exe --file-description="VBIOS Studio" \
    --no-deployment-flag=excluded-module-usage \
    --include-raw-dir="$(cygpath -w "$runtime")=gtk" \
    --include-package=vbios_studio --include-package=nvidia_vbios \
    --nofollow-import-to=gi --include-package=importlib "${gi_args[@]}" \
    "$root/tools/entry_gui.py"

exe="$out/vbios-studio-$VERSION-windows-x86_64.exe"
cp "$work/gui/vbios-studio.exe" "$exe"
cp "$root/LICENSE" "$out/LICENSE" 2>/dev/null || true
cp "$root/NOTICE.md" "$out/NOTICE.md" 2>/dev/null || true
(cd "$out" && sha256sum "vbios-studio-$VERSION-windows-x86_64.exe" > SHA256SUMS-windows)
cat "$out/SHA256SUMS-windows"
