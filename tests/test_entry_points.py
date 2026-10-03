import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# The console script installed beside the interpreter, and the module entry point.
CONSOLE = shutil.which("web-forager", path=str(Path(sys.executable).parent))
ENTRY_POINTS = [[CONSOLE], [sys.executable, "-m", "web_forager"]]


def run(entry_point, *args):
    assert entry_point[0], "web-forager console script is not installed"
    return subprocess.run(
        [*entry_point, *args], capture_output=True, text=True, timeout=60
    )


@pytest.mark.parametrize("entry_point", ENTRY_POINTS, ids=["console", "module"])
def test_success_exits_zero(entry_point):
    result = run(entry_point, "version")
    assert result.returncode == 0
    assert result.stdout.startswith("Web Forager v")


@pytest.mark.parametrize("entry_point", ENTRY_POINTS, ids=["console", "module"])
def test_handled_failure_exits_one(entry_point):
    result = run(entry_point, "fetch", "not-a-url", "--direct-only")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "A valid HTTP/HTTPS URL is required" in result.stderr


@pytest.mark.parametrize("entry_point", ENTRY_POINTS, ids=["console", "module"])
def test_parser_failure_exits_two(entry_point):
    result = run(entry_point, "fetch")
    assert result.returncode == 2
    assert "the following arguments are required: url" in result.stderr
