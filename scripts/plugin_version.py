"""Bump the shared plugin version or check a change against its base revision."""

import argparse
import json
import re
import subprocess
from pathlib import Path

MANIFEST = Path(".claude-plugin/plugin.json")
MARKETPLACE = Path(".claude-plugin/marketplace.json")


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value
    ):
        raise ValueError(f"Expected a major.minor.patch version, got {value!r}")
    return tuple(map(int, value.split(".")))


def plugin_entry(marketplace):
    return next(p for p in marketplace["plugins"] if p["name"] == "forager-skills")


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def check(root, base=None):
    manifest = json.loads((root / MANIFEST).read_text())
    marketplace = json.loads((root / MARKETPLACE).read_text())
    current = manifest["version"]
    current_tuple = version_tuple(current)
    if (
        current != marketplace["metadata"]["version"]
        or current != plugin_entry(marketplace)["version"]
    ):
        raise ValueError("Plugin and marketplace versions differ; use the bump command")
    if base:
        # Older revisions kept the release version only in the marketplace.
        previous = json.loads(git(root, "show", f"{base}:{MARKETPLACE.as_posix()}"))
        previous_tuple = version_tuple(plugin_entry(previous)["version"])
        changed = git(
            root, "diff", "--name-only", base, "--", "skills", ".claude-plugin"
        )
        if changed and current_tuple <= previous_tuple:
            raise ValueError(
                "Skill/plugin changes require a version greater than the base"
            )
    return current


def bump(root, version):
    new_tuple = version_tuple(version)
    current = check(root)
    if new_tuple <= version_tuple(current):
        raise ValueError(f"New version must be greater than {current}")
    manifest = json.loads((root / MANIFEST).read_text())
    marketplace = json.loads((root / MARKETPLACE).read_text())
    manifest["version"] = version
    marketplace["metadata"]["version"] = version
    plugin_entry(marketplace)["version"] = version
    for path, value in ((MANIFEST, manifest), (MARKETPLACE, marketplace)):
        (root / path).write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check").add_argument("--base")
    commands.add_parser("bump").add_argument("version")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.command == "bump":
            bump(root, args.version)
        print(check(root, getattr(args, "base", None)))
    except (
        ValueError,
        KeyError,
        StopIteration,
        subprocess.CalledProcessError,
    ) as error:
        parser.exit(1, f"Version check failed: {error}\n")


if __name__ == "__main__":
    main()
