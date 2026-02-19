"""
ast_analyzer node — parse test output and classify failures into the
six canonical bug types required by the hackathon scoring rubric.

Strategy (per SOURCE_OF_TRUTH §7):
  1. Rule-based parser/classifier first.
  2. LLM fallback only when rule path cannot resolve.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from ...config import OPENAI_API_KEY, OPENAI_MODEL
from ...db import insert_trace
from ...events import emit_thought
from ...llm import get_llm, has_llm_keys
from ..state import AgentState, BugType, TestFailure

logger = logging.getLogger("rift.node.ast_analyzer")

# ── Rule-based classifiers ──────────────────────────────────

_PYTEST_FAILURE_RE = re.compile(
    r"^(?:FAILED|ERROR)\s+([\w/\\.]+)::(\w+)"
    r"(?:\s*-\s*(.+))?$",
    re.MULTILINE,
)

_FILE_LINE_RE = re.compile(
    r'File "([^"]+)", line (\d+)',
)

_JEST_FAILURE_RE = re.compile(
    r"●\s+([\w\s]+)\s+›\s+([\w\s]+)\n\n\s+(.+)",
    re.MULTILINE,
)

# Error message patterns → bug type
_BUG_PATTERNS: list[tuple[re.Pattern[str], BugType]] = [
    (re.compile(r"SyntaxError|IndentationError|TabError", re.I), "SYNTAX"),
    (re.compile(r"IndentationError|unexpected indent|expected an indented block", re.I), "INDENTATION"),
    (re.compile(r"ImportError|ModuleNotFoundError|No module named", re.I), "IMPORT"),
    (re.compile(r"TypeError|type.?error|expected.*got|incompatible type", re.I), "TYPE_ERROR"),
    (re.compile(r"flake8|pylint|eslint|E\d{3}|W\d{3}|trailing whitespace|line too long", re.I), "LINTING"),
    (re.compile(r"AssertionError|assert\s|Expected.*received|to equal|toBe|not equal", re.I), "LOGIC"),
]


def _classify_bug_type(error_msg: str) -> BugType:
    """Match error message against known patterns."""
    for pattern, bug_type in _BUG_PATTERNS:
        if pattern.search(error_msg):
            return bug_type
    return "LOGIC"  # default fallback


def _parse_pytest_output(output: str, repo_dir: str) -> list[TestFailure]:
    """Extract failures from pytest output."""
    failures: list[TestFailure] = []

    # Split output into sections per failure
    sections = re.split(r"_{10,}\s+", output)

    for section in sections:
        # Try to find FAILED lines
        m = _PYTEST_FAILURE_RE.search(section)
        if not m:
            continue

        file_path = m.group(1)
        test_name = m.group(2)
        error_msg = m.group(3) or section[:500]

        # Try to extract line number
        line_match = _FILE_LINE_RE.search(section)
        line_number = int(line_match.group(2)) if line_match else 1

        bug_type = _classify_bug_type(error_msg)

        failures.append(
            TestFailure(
                file_path=file_path,
                test_name=test_name,
                line_number=line_number,
                error_message=error_msg.strip()[:500],
                bug_type=bug_type,
                raw_output=section[:1000],
            )
        )

    # If regex didn't catch structured failures, try line-by-line FAILED pattern
    if not failures:
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.startswith("FAILED ") or stripped.startswith("ERROR "):
                parts = stripped.split(" ", 1)
                if len(parts) > 1:
                    loc = parts[1].split("::")
                    file_path = loc[0] if loc else "unknown"
                    test_name = loc[1] if len(loc) > 1 else "unknown"
                    error_msg = " ".join(loc[2:]) if len(loc) > 2 else stripped
                    failures.append(
                        TestFailure(
                            file_path=file_path,
                            test_name=test_name,
                            line_number=1,
                            error_message=error_msg[:500],
                            bug_type=_classify_bug_type(error_msg),
                            raw_output=stripped,
                        )
                    )

    return failures


def _parse_jest_output(output: str, repo_dir: str) -> list[TestFailure]:
    """Extract failures from Jest/Vitest output."""
    failures: list[TestFailure] = []

    # Look for "● suite › test" pattern
    blocks = re.split(r"●\s+", output)
    for block in blocks[1:]:  # skip first empty part
        lines = block.strip().splitlines()
        if not lines:
            continue

        header = lines[0]
        error_msg = "\n".join(lines[1:])[:500]

        # Try to find file reference
        file_match = re.search(r"at.*?[( ]([\w./\\]+):(\d+):\d+", block)
        file_path = file_match.group(1) if file_match else "unknown"
        line_number = int(file_match.group(2)) if file_match else 1

        parts = header.split(" › ")
        test_name = parts[-1].strip() if parts else header

        failures.append(
            TestFailure(
                file_path=file_path,
                test_name=test_name,
                line_number=line_number,
                error_message=error_msg.strip()[:500],
                bug_type=_classify_bug_type(error_msg),
                raw_output=block[:1000],
            )
        )

    return failures


async def _llm_classify_failures(output: str) -> list[TestFailure]:
    """Use LLM as fallback to extract and classify failures."""
    if not has_llm_keys():
        logger.warning("No Groq API keys — cannot use LLM fallback")
        return []

    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(temperature=0.0)

    prompt = f"""Analyze this test output and extract each failure as JSON.
For each failure return:
- file_path: string
- test_name: string
- line_number: int
- error_message: string (brief)
- bug_type: one of LINTING, SYNTAX, LOGIC, TYPE_ERROR, IMPORT, INDENTATION

Return ONLY a JSON array. No markdown, no explanation.

Test output:
```
{output[:4000]}
```"""

    resp = await llm.ainvoke([
        SystemMessage(content="You are a test output parser. Return valid JSON only."),
        HumanMessage(content=prompt),
    ])

    import json
    try:
        items = json.loads(resp.content)  # type: ignore[arg-type]
        return [
            TestFailure(
                file_path=item.get("file_path", "unknown"),
                test_name=item.get("test_name", "unknown"),
                line_number=item.get("line_number", 1),
                error_message=item.get("error_message", ""),
                bug_type=item.get("bug_type", "LOGIC"),
                raw_output="",
            )
            for item in items
        ]
    except (json.JSONDecodeError, TypeError):
        logger.error("LLM returned invalid JSON for failure classification")
        return []


async def ast_analyzer(state: AgentState) -> AgentState:
    """
    Parse test output and classify each failure.
    Rule-based first, LLM fallback if empty.
    """
    run_id = state["run_id"]
    test_output = state.get("test_output", "")
    test_exit_code = state.get("test_exit_code", 0)
    framework = state.get("framework", "pytest")
    repo_dir = state.get("repo_dir", "")
    iteration = state.get("iteration", 1)
    step = iteration * 10 + 4

    await emit_thought(run_id, "ast_analyzer", "Analyzing test failures…", step)

    # If tests passed, no failures to analyze
    if test_exit_code == 0:
        await emit_thought(run_id, "ast_analyzer", "All tests passed ✓", step + 1)
        return {
            "failures": [],
            "current_node": "ast_analyzer",
        }

    # Rule-based parsing
    if framework in ("jest", "vitest"):
        failures = _parse_jest_output(test_output, repo_dir)
    else:
        failures = _parse_pytest_output(test_output, repo_dir)

    # LLM fallback if rule-based found nothing
    if not failures and test_exit_code != 0:
        await emit_thought(
            run_id, "ast_analyzer",
            "Rule-based parsing found no structured failures — trying LLM fallback…",
            step + 1,
        )
        failures = await _llm_classify_failures(test_output)

    # Ensure we cover all 6 required bug types for demo if we have failures
    seen_types = {f.bug_type for f in failures}
    logger.info(
        "ast_analyzer run=%s found %d failures, types=%s",
        run_id, len(failures), seen_types,
    )

    await emit_thought(
        run_id,
        "ast_analyzer",
        f"Found {len(failures)} failure(s): {', '.join(seen_types) if seen_types else 'none'}",
        step + 2,
    )

    await insert_trace(
        run_id,
        step_index=step,
        agent_node="ast_analyzer",
        action_type="analysis",
        action_label=f"Classified {len(failures)} failures",
        payload={
            "failure_count": len(failures),
            "bug_types": list(seen_types),
        },
    )

    return {
        "failures": failures,
        "current_node": "ast_analyzer",
    }
