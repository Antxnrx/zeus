"""
test_runner node — execute tests, capture output, determine exit code.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from ...db import insert_trace
from ...events import emit_thought
from ..state import AgentState

logger = logging.getLogger("rift.node.test_runner")

# Framework → command template
_COMMANDS: dict[str, list[str]] = {
    "pytest": ["python", "-m", "pytest", "--tb=short", "-q", "--no-header"],
    "jest": ["npx", "jest", "--no-coverage", "--verbose"],
    "vitest": ["npx", "vitest", "run", "--reporter=verbose"],
    "mocha": ["npx", "mocha", "--recursive"],
}


async def test_runner(state: AgentState) -> AgentState:
    """
    Run the test suite in the cloned repo and capture output.
    """
    run_id = state["run_id"]
    repo_dir = state["repo_dir"]
    framework = state.get("framework", "pytest")
    iteration = state.get("iteration", 1)
    step = iteration * 10 + 3

    await emit_thought(run_id, "test_runner", f"Running tests (iteration {iteration})…", step)

    cmd = _COMMANDS.get(framework, _COMMANDS["pytest"])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=_build_env(repo_dir),
        )
        stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        test_output = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        exit_code = proc.returncode or 0
    except asyncio.TimeoutError:
        test_output = "ERROR: Test execution timed out after 120s"
        exit_code = 1
    except FileNotFoundError:
        test_output = f"ERROR: Test command not found — {cmd[0]}"
        exit_code = 127

    await emit_thought(
        run_id,
        "test_runner",
        f"Tests {'PASSED' if exit_code == 0 else 'FAILED'} (exit={exit_code}, {len(test_output)} chars output)",
        step + 1,
    )

    await insert_trace(
        run_id,
        step_index=step,
        agent_node="test_runner",
        action_type="test_execution",
        action_label=f"Ran {framework} — exit {exit_code}",
        payload={
            "framework": framework,
            "exit_code": exit_code,
            "output_length": len(test_output),
        },
        thought_text=test_output[:2000],
    )

    return {
        "test_output": test_output,
        "test_exit_code": exit_code,
        "current_node": "test_runner",
    }


def _build_env(repo_dir: str) -> dict[str, str]:
    """Build an environment dict for the subprocess."""
    import os

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = repo_dir
    # Disable interactive prompts
    env["CI"] = "true"
    return env
