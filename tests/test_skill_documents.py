# Test assertions are the behavior under test, not production validation.
# ruff: noqa: S101

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILLS_ROOT = ROOT / "skills"
EXPECTED_SKILLS = {
    "article-audit",
    "competitive-intel",
    "deep-research",
    "fact-check",
    "news-monitor",
    "tech-advisor",
}
ROUTER_SKILLS = {"competitive-intel", "tech-advisor"}


def skill_files() -> dict[str, Path]:
    return {name: SKILLS_ROOT / name / "SKILL.md" for name in EXPECTED_SKILLS}


def frontmatter(path: Path) -> str:
    text = path.read_text()
    parts = text.split("---", 2)
    assert len(parts) == 3 and not parts[0].strip(), f"Invalid frontmatter in {path}"
    return parts[1]


def folded_description(metadata: str) -> str:
    match = re.search(r"(?m)^description:\s*>\s*\n((?: {2}.*(?:\n|$))+)", metadata)
    assert match, "description must use a folded YAML block"
    return " ".join(line.strip() for line in match.group(1).splitlines())


def test_expected_skills_are_present() -> None:
    actual = {path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")}
    assert actual == EXPECTED_SKILLS


def test_frontmatter_names_and_descriptions_are_tight() -> None:
    for expected_name, path in skill_files().items():
        metadata = frontmatter(path)
        assert re.search(rf"(?m)^name:\s*{re.escape(expected_name)}\s*$", metadata)

        description = folded_description(metadata)
        assert len(description) <= 320, f"Description is too long in {path}"
        assert not re.search(
            r"\bALWAYS\b|Trigger on:|Do NOT trigger|Don't trigger",
            description,
            re.IGNORECASE,
        )


def test_top_level_skills_stay_legible() -> None:
    for path in skill_files().values():
        assert len(path.read_text().splitlines()) <= 180, f"Disclose branches from {path}"


def test_relative_markdown_references_ship_with_each_skill() -> None:
    link_pattern = re.compile(r"\[[^]]+\]\(([^)#]+\.md)\)")

    for skill_name in EXPECTED_SKILLS:
        skill_dir = SKILLS_ROOT / skill_name
        for document in skill_dir.glob("*.md"):
            for target in link_pattern.findall(document.read_text()):
                resolved = (document.parent / target).resolve()
                assert resolved.is_relative_to(skill_dir.resolve())
                assert resolved.is_file(), f"Broken reference {target} in {document}"


def test_tool_guidance_uses_stable_names_without_automatic_installation() -> None:
    for skill_name, path in skill_files().items():
        text = path.read_text()
        assert "mcp__" not in text
        assert "pip install ddgs" not in text
        assert "web_fetch" in text
        assert "duckduckgo_search" in text
        assert "uvx" in text
        assert "uv run --no-project" in text
        if skill_name == "news-monitor":
            assert "duckduckgo_news_search" in text


def test_fast_moving_examples_use_dynamic_years() -> None:
    for skill_name in ("deep-research", "tech-advisor"):
        text = "\n".join(
            path.read_text() for path in (SKILLS_ROOT / skill_name).glob("*.md")
        )
        assert "[current year]" in text
        assert not re.search(r"\b20\d{2}\b", text)


def test_workflows_have_checkable_completion_criteria() -> None:
    workflow_documents = [
        SKILLS_ROOT / "article-audit" / "SKILL.md",
        SKILLS_ROOT / "deep-research" / "SKILL.md",
        SKILLS_ROOT / "fact-check" / "SKILL.md",
        SKILLS_ROOT / "news-monitor" / "SKILL.md",
        SKILLS_ROOT / "competitive-intel" / "market-landscape.md",
        SKILLS_ROOT / "competitive-intel" / "competitive-positioning.md",
        SKILLS_ROOT / "tech-advisor" / "maturity-assessment.md",
        SKILLS_ROOT / "tech-advisor" / "product-comparison.md",
    ]

    for path in workflow_documents:
        assert path.read_text().count("**Complete when:**") >= 4, path


def test_detailed_news_requires_read_sources() -> None:
    text = (SKILLS_ROOT / "news-monitor" / "SKILL.md").read_text()
    assert re.search(r"Search snippets may support\s+headline discovery only", text)
    assert re.search(r"every detailed event has at least one fetched\s+source", text)


def test_clear_fact_checks_do_not_pause_for_confirmation() -> None:
    text = (SKILLS_ROOT / "fact-check" / "SKILL.md").read_text()
    assert "Continue immediately when the claim is clear" in text
    assert re.search(
        r"ask for\s+confirmation only when two plausible interpretations",
        text,
    )


def test_article_audit_is_distinct_from_single_claim_fact_check() -> None:
    text = (SKILLS_ROOT / "article-audit" / "SKILL.md").read_text()
    assert "For one isolated claim, use `fact-check`" in text
    assert "counter-voices" in text
    assert "Check scale" in text


def test_article_audit_enforces_its_evidence_contract() -> None:
    text = (SKILLS_ROOT / "article-audit" / "SKILL.md").read_text()
    assert "Split compound statements" in text
    assert "Before searching, show a numbered audit scope" in text
    assert "Search snippets are discovery aids, not verdict evidence" in text
    assert "Use exactly one label, unchanged" in text
    assert "support, challenge, baseline, or context" in text


def test_router_skills_disclose_each_mode() -> None:
    for skill_name in ROUTER_SKILLS:
        skill_dir = SKILLS_ROOT / skill_name
        references = {
            target.name
            for target in skill_dir.glob("*.md")
            if target.name != "SKILL.md"
        }
        assert len(references) == 2


def test_direct_workflows_right_size_their_output() -> None:
    article_audit = (SKILLS_ROOT / "article-audit" / "SKILL.md").read_text()
    deep_research = (SKILLS_ROOT / "deep-research" / "SKILL.md").read_text()
    fact_check = (SKILLS_ROOT / "fact-check" / "SKILL.md").read_text()
    news_monitor = (SKILLS_ROOT / "news-monitor" / "SKILL.md").read_text()

    assert "The default full audit is long-form" in article_audit
    assert "The ledger is working state, not an output template" in article_audit
    assert "A standard report is the default" in deep_research
    assert re.search(
        r"Research\s+depth stays high across all three formats",
        deep_research,
    )
    assert "Default to a compact verdict for one claim" in fact_check
    assert re.search(r"source-by-source\s+account only when", fact_check)
    assert "default briefing uses a single event list" in news_monitor
    assert "expanded briefing" in news_monitor


def test_router_modes_keep_tables_as_the_output_source_of_truth() -> None:
    market_landscape = (
        SKILLS_ROOT / "competitive-intel" / "market-landscape.md"
    ).read_text()
    competitive_positioning = (
        SKILLS_ROOT / "competitive-intel" / "competitive-positioning.md"
    ).read_text()
    maturity_assessment = (
        SKILLS_ROOT / "tech-advisor" / "maturity-assessment.md"
    ).read_text()
    product_comparison = (
        SKILLS_ROOT / "tech-advisor" / "product-comparison.md"
    ).read_text()

    assert "Default to a long-form map" in market_landscape
    assert "player tables as the single source of truth" in market_landscape
    assert "Default to a long-form comparison" in competitive_positioning
    assert "competitive matrix as the single source of truth" in competitive_positioning
    assert "Default to a medium-length assessment" in maturity_assessment
    assert "scorecard as the single source of truth" in maturity_assessment
    assert "Default to a compact decision brief" in product_comparison
    assert re.search(
        r"comparison table as the single source of\s+truth",
        product_comparison,
    )
