"""Regressions for release drift and the user-visible package version."""

import json
import runpy
import subprocess
from argparse import Namespace
from importlib.metadata import version
from pathlib import Path

import pytest

from web_forager import cli

HELPERS = runpy.run_path(str(Path(__file__).parents[1] / "scripts/plugin_version.py"))


@pytest.fixture
def repository(tmp_path):
    folder = tmp_path / ".claude-plugin"
    folder.mkdir()
    (folder / "plugin.json").write_text(json.dumps({"version": "1.1.3"}))
    (folder / "marketplace.json").write_text(
        json.dumps(
            {
                "metadata": {"version": "1.1.3"},
                "plugins": [{"name": "forager-skills", "version": "1.1.3"}],
            }
        )
    )
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills/example.md").write_text("original")
    for args in (
        ["init"],
        ["add", "."],
        [
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "base",
        ],
    ):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def test_plugin_change_requires_bump(repository):
    (repository / "skills/example.md").write_text("updated")
    with pytest.raises(ValueError, match="greater than the base"):
        HELPERS["check"](repository, "HEAD")
    HELPERS["bump"](repository, "1.1.4")
    assert HELPERS["check"](repository, "HEAD") == "1.1.4"


def test_unrelated_change_needs_no_plugin_bump(repository):
    (repository / "README.md").write_text("documentation")
    assert HELPERS["check"](repository, "HEAD") == "1.1.3"


@pytest.mark.parametrize("value", ["1.1.3", "1.0.0", "01.2.3", "banana"])
def test_invalid_or_non_increasing_bump_is_rejected(repository, value):
    with pytest.raises(ValueError):
        HELPERS["bump"](repository, value)
    assert HELPERS["check"](repository) == "1.1.3"


def test_manifest_drift_is_rejected(repository):
    (repository / ".claude-plugin/plugin.json").write_text('{"version": "1.1.4"}')
    with pytest.raises(ValueError, match="versions differ"):
        HELPERS["check"](repository)


def test_cli_reports_installed_package_version(capsys):
    assert cli._handle_version(Namespace(debug=False)) == 0
    assert capsys.readouterr().out.strip() == f"Web Forager v{version('web-forager')}"
