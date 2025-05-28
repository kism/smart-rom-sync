"""Test versioning."""

from pathlib import Path

import tomlkit

import smartromsync


def test_version_pyproject():
    """Verify version in pyproject.toml matches package version."""
    pyproject_path = Path("pyproject.toml")
    with pyproject_path.open("rb") as f:
        pyproject_toml = tomlkit.load(f)
    assert pyproject_toml["project"]["version"] == smartromsync.__version__


def test_version_lock():
    """Verify version in uv.lock matches package version."""
    lock_path = Path("uv.lock")
    with lock_path.open() as f:
        uv_lock = tomlkit.load(f)

    found_version = False
    for package in uv_lock["package"]:
        if package["name"] == "smartromsync":
            assert package["version"] == smartromsync.__version__
            found_version = True
            break

    assert found_version, "smartromsync not found in uv.lock"


def test_init_pyproject_fields():
    """Verify required fields in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    with pyproject_path.open("rb") as f:
        pyproject_toml = tomlkit.load(f)

    from smartromsync import DESCRIPTION, PROGRAM_NAME, URL

    assert pyproject_toml["project"]["description"] == DESCRIPTION

    assert PROGRAM_NAME in pyproject_toml["project"]["scripts"]

    assert pyproject_toml["project"]["urls"]["Homepage"] == URL
