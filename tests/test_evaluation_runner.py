import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

EVALS = Path(__file__).parent / "evals"
sys.path.insert(0, str(EVALS))
import run as runner
from fixture_server import build_server


def test_all_cases_validate_and_shared_cases_cover_every_skill():
    cases = runner.load_cases()
    assert {case["skill"] for case in cases} == set(runner.SKILLS)
    for skill in runner.SKILLS:
        assert any(case["id"] == "source-injection--" + skill for case in cases)
        assert any(case["id"] == "sensitive-link--" + skill for case in cases)


def test_invalid_source_reference_rejected():
    case = next(
        case
        for case in runner.load_cases()
        if case["id"] == "source-injection--fact-check"
    ) | {"required_reads": ["https://unknown.test"]}
    with pytest.raises(ValueError, match="Unknown source"):
        runner.validate_case(case)


def test_fixture_tools_trace_reads_and_reject_unavailable_sources(tmp_path):
    case = next(
        case
        for case in runner.load_cases()
        if case["id"] == "source-injection--fact-check"
    )
    trace = tmp_path / "trace"
    server = build_server(case, runner.ROOT / "skills" / case["skill"], trace)

    async def check():
        async with Client(server) as client:
            assert {tool.name for tool in await client.list_tools()} == {
                "duckduckgo_search",
                "duckduckgo_news_search",
                "web_fetch",
                "read_skill_resource",
            }
            await client.call_tool("duckduckgo_search", {"query": "claim"})
            await client.call_tool("web_fetch", {"url": case["sources"][0]["url"]})
            with pytest.raises(ToolError):
                await client.call_tool("web_fetch", {"url": "https://unknown.test"})
            with pytest.raises(ToolError):
                await client.call_tool(
                    "read_skill_resource", {"path": "../../README.md"}
                )

    asyncio.run(check())
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    assert len(events) == 4
    assert isinstance(events[1]["result"], str)
    assert "error" in events[2]["result"]


def test_sensitive_url_and_injection_fail_trace_grading():
    case = {
        "required_reads": ["private"],
        "direct_only_urls": ["private"],
        "private_tokens": ["SECRET"],
        "forbidden_output": ["INJECTED"],
    }
    events = [
        {
            "tool": "web_fetch",
            "arguments": {"url": "private", "allow_jina": True},
            "result": {"error": "unavailable"},
        },
        {"tool": "duckduckgo_search", "arguments": {"query": "SECRET"}, "result": []},
    ]
    failures = runner.check_trace(case, events, "INJECTED")
    assert len(failures) == 4


def test_parsers_detect_unexpected_tools():
    events = "\n".join(
        json.dumps(event)
        for event in [
            {"type": "item.completed", "item": {"type": "command_execution"}},
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "answer"},
            },
        ]
    )
    answer, _, violations = runner.parse_output("codex", events)
    assert answer == "answer"
    assert violations
    _, metadata, _ = runner.parse_output(
        "codex", json.dumps({"type": "error", "message": "Model unavailable"})
    )
    assert metadata["error"] == "Model unavailable"
    _, _, violations = runner.parse_output(
        "claude", json.dumps({"type": "system", "subtype": "init", "tools": ["Bash"]})
    )
    assert violations


def test_agent_commands_disable_native_tools(tmp_path):
    codex = runner.command_for("codex", tmp_path, None, None)
    assert "--ignore-user-config" in codex
    assert "shell_tool" in codex and 'web_search="disabled"' in codex
    claude = runner.command_for("claude", tmp_path, None, None)
    assert claude[claude.index("--tools") + 1] == ""
    assert "--strict-mcp-config" in claude
    assert "bypassPermissions" not in claude


def test_unavailable_client_is_not_a_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(runner.shutil, "which", lambda _: None)
    result = runner.run_case(
        next(
            case
            for case in runner.load_cases()
            if case["id"] == "source-injection--fact-check"
        ),
        "codex",
        None,
        tmp_path,
        10,
    )
    assert result["status"] == "skipped"
    assert result["failures"]


@pytest.mark.parametrize("missing_grade", [False, True])
def test_actor_and_grader_pipeline(monkeypatch, tmp_path, missing_grade):
    case = next(
        case
        for case in runner.load_cases()
        if case["id"] == "source-injection--fact-check"
    )
    monkeypatch.setattr(runner.shutil, "which", lambda _: "/fake/client")
    monkeypatch.setattr(
        runner.subprocess, "check_output", lambda *a, **kw: "test-client"
    )

    def fake_execute(command, prompt, cwd, timeout):
        if "--output-schema" not in command:
            events = [
                {"tool": "web_fetch", "arguments": {"url": url}, "result": "read"}
                for url in case.get("required_reads", [])
            ]
            (cwd.parent / "trace.jsonl").write_text(
                "\n".join(json.dumps(e) for e in events)
            )
            content = "Evidence-backed answer"
        else:
            grades = [
                {"id": c["id"], "passed": True, "evidence": "Observed correct claim"}
                for c in case["rubric"]
            ]
            content = json.dumps({"criteria": grades[:-1] if missing_grade else grades})
        output = json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": content},
            }
        )
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr(runner, "execute", fake_execute)
    result = runner.run_case(case, "codex", "test-model", tmp_path, 10)
    assert result["status"] == ("infrastructure_failure" if missing_grade else "passed")
