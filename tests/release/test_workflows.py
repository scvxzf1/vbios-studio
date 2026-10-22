"""Release-pipeline contract tests.

These tests run without network access and are intentionally cheap: they check
the workflow definitions and the local build script against the amended t5
acceptance criteria (explicit PyPI index, system PyGObject, artifact names,
SHA256SUMS).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
EXPECTED = {"ci.yml", "build.yml", "release.yml", "upstream-sync.yml"}


def load(name: str) -> dict:
    data = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_all_workflows_parse() -> None:
    assert {path.name for path in WORKFLOWS.glob("*.yml")} == EXPECTED
    for name in EXPECTED:
        load(name)


def upload_step(job: dict) -> dict:
    steps = [
        step
        for step in job["steps"]
        if str(step.get("uses", "")).startswith("actions/upload-artifact")
    ]
    assert steps, "job must upload an artifact"
    return steps[0]


def test_build_windows_runner_and_artifact_name() -> None:
    data = load("build.yml")
    windows = data["jobs"]["windows"]
    assert windows["runs-on"] == "windows-latest"
    assert "vbios-studio-*-windows-x86_64.exe" in upload_step(windows)["with"]["path"]


def test_build_linux_artifact_name() -> None:
    data = load("build.yml")
    upload = upload_step(data["jobs"]["linux"])
    assert "vbios-studio-*-linux-x86_64.tar.gz" in upload["with"]["path"]


def test_release_uploads_both_platforms_and_checksums() -> None:
    text = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
    assert "SHA256SUMS" in text
    assert "gh release create" in text
    assert "linux-x86_64.tar.gz" in text
    assert "windows-x86_64.exe" in text
    data = load("release.yml")
    assert "build" in data["jobs"] and "publish" in data["jobs"]


def test_every_pip_install_uses_explicit_index() -> None:
    """Every 'pip install' line must carry --index-url or the PIP_INDEX_URL env."""
    files = [*list(WORKFLOWS.glob("*.yml")), ROOT / "tools" / "build_local.sh"]
    offenders: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        has_env_default = "PIP_INDEX_URL" in text
        for number, line in enumerate(text.splitlines(), 1):
            if "pip install" not in line:
                continue
            if "--index-url" in line or "PIP_INDEX_URL" in line:
                continue
            # The flag may be on the continuation line of a multi-line command.
            window = "\n".join(text.splitlines()[number - 3 : number + 2])
            if "--index-url" not in window and not has_env_default:
                offenders.append(f"{path.name}:{number}: {line.strip()}")
    assert not offenders, "\n".join(offenders)


def test_build_local_uses_system_site_packages_and_not_pygobject() -> None:
    text = (ROOT / "tools" / "build_local.sh").read_text(encoding="utf-8")
    assert "venv --system-site-packages" in text
    assert "PyGObject" in text  # documented as intentionally absent
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    assert not re.search(r"pip install[^\n]*PyGObject", code, re.I)
    assert not re.search(r"pip install[^\n]*(gtk|adwaita)", code, re.I)


def test_build_local_is_valid_shell() -> None:
    import subprocess

    result = subprocess.run(["bash", "-n", str(ROOT / "tools" / "build_local.sh")], check=False)
    assert result.returncode == 0
