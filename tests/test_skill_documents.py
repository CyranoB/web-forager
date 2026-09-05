"""Packaging checks only. Model behavior is exercised by tests/evals/run.py."""

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
SKILLS_ROOT = ROOT / "skills"
EXPECTED_SKILLS = {
    "article-audit",
    "competitive-intel",
    "deep-research",
    "fact-check",
    "geopolitical-analyst",
    "news-monitor",
    "tech-advisor",
}


def test_published_skills_match_manifest():
    actual = {path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")}
    manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    assert actual == EXPECTED_SKILLS
    assert {Path(path).name for path in manifest["skills"]} == actual


def test_frontmatter_and_entrypoints():
    for name in EXPECTED_SKILLS:
        path = SKILLS_ROOT / name / "SKILL.md"
        text = path.read_text()
        before, metadata, body = text.split("---", 2)
        assert not before.strip()
        data = yaml.safe_load(metadata)
        assert data["name"] == name
        assert isinstance(data["description"], str)
        assert 20 <= len(data["description"].strip()) <= 320
        assert body.strip()
        assert len(text.splitlines()) <= 180


def test_each_skill_is_self_contained_and_references_are_reachable():
    for name in EXPECTED_SKILLS:
        folder = (SKILLS_ROOT / name).resolve()
        pending = [folder / "SKILL.md"]
        reached = set()
        while pending:
            document = pending.pop()
            if document in reached:
                continue
            reached.add(document)
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", document.read_text()):
                if "://" in target or target.startswith("#"):
                    continue
                destination = (document.parent / target.split("#")[0]).resolve()
                assert destination.is_relative_to(folder), (document, target)
                assert destination.is_file(), (document, target)
                if destination.suffix == ".md":
                    pending.append(destination)
        assert reached == set(folder.rglob("*.md")), f"Orphaned reference in {name}"


def test_optional_ui_metadata_is_valid():
    for path in SKILLS_ROOT.glob("*/agents/openai.yaml"):
        data = yaml.safe_load(path.read_text())
        interface = data["interface"]
        assert interface["display_name"]
        assert interface["short_description"]
        assert "$" + path.parents[1].name in interface["default_prompt"]
