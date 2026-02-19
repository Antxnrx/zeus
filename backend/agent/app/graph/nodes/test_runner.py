"""
test_runner node — execute tests, capture output, determine exit code.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
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
    "npm-test": ["npm", "test", "--", "--no-coverage"],
}

# Frameworks that need `npm install` before running
_NODE_FRAMEWORKS = {"jest", "vitest", "mocha", "npm-test"}


async def _ensure_node_deps(repo_dir: str, run_id: str, step: int) -> None:
    """
    If the repo has a package.json, run `npm install` to ensure
    test dependencies (jest, vitest, etc.) are available.
    """
    pkg_json = Path(repo_dir) / "package.json"
    node_modules = Path(repo_dir) / "node_modules"

    if not pkg_json.exists():
        return

    if node_modules.exists():
        return  # already installed

    await emit_thought(run_id, "test_runner", "Installing Node.js dependencies…", step)

    try:
        proc = await asyncio.create_subprocess_exec(
            "npm", "install", "--no-audit", "--no-fund", "--prefer-offline",
            cwd=repo_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, "CI": "true", "NODE_ENV": "development"},
        )
        stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        output = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""

        if proc.returncode != 0:
            logger.warning(
                "npm install failed (exit=%d) for run %s: %s",
                proc.returncode, run_id, output[:500],
            )
            await emit_thought(
                run_id, "test_runner",
                f"npm install failed (exit={proc.returncode}) — tests may fail",
                step,
            )
        else:
            logger.info("npm install succeeded for run %s", run_id)
    except asyncio.TimeoutError:
        logger.warning("npm install timed out for run %s", run_id)
        await emit_thought(run_id, "test_runner", "npm install timed out (120s)", step)
    except FileNotFoundError:
        logger.warning("npm not found for run %s", run_id)


async def test_runner(state: AgentState) -> AgentState:
    """
    Run the test suite in the cloned repo and capture output.
    """
    run_id = state["run_id"]
    repo_dir = state["repo_dir"]
    framework = state.get("framework", "pytest")
    language = state.get("language", "python")
    iteration = state.get("iteration", 1)
    step = iteration * 10 + 3

    await emit_thought(run_id, "test_runner", f"Running tests (iteration {iteration})…", step)

    # For unknown JS/TS frameworks, try to resolve from package.json
    if framework == "unknown" and language in ("javascript", "typescript"):
        framework = _resolve_js_framework(repo_dir)
        logger.info("Resolved unknown JS framework to '%s' for run %s", framework, run_id)

    # Install Node.js deps if needed (jest/vitest/mocha/npm-test)
    if framework in _NODE_FRAMEWORKS:
        await _ensure_node_deps(repo_dir, run_id, step)

    cmd = _COMMANDS.get(framework, _COMMANDS["pytest"])

    test_output, exit_code = await _run_cmd(cmd, repo_dir)

    # If primary command failed with "no tests" (exit=5 for jest) or
    # command not found (127), try npm test as fallback for JS/TS repos
    if exit_code in (5, 127) and language in ("javascript", "typescript") and framework != "npm-test":
        logger.info(
            "Primary test command failed (exit=%d), trying npm test fallback for run %s",
            exit_code, run_id,
        )
        await emit_thought(
            run_id, "test_runner",
            f"{framework} returned exit={exit_code}, trying npm test fallback…",
            step,
        )
        fallback_output, fallback_code = await _run_cmd(["npm", "test"], repo_dir)
        # Use fallback if it produced more output (even if it also failed)
        if len(fallback_output) > len(test_output) or fallback_code == 0:
            test_output = fallback_output
            exit_code = fallback_code
            framework = "npm-test"

    # If still no useful test output for JS repos, try running with
    # npx to discover test files directly
    if exit_code in (5, 127) and len(test_output) < 100 and language in ("javascript", "typescript"):
        logger.info("Attempting direct pytest fallback for Python files in run %s", run_id)
        # Check if there are Python test files (mixed repo like test-vue-app)
        py_test_files = list(Path(repo_dir).rglob("test_*.py")) + list(Path(repo_dir).rglob("*_test.py"))
        if py_test_files:
            await emit_thought(
                run_id, "test_runner",
                f"No JS tests found — detected {len(py_test_files)} Python test file(s), running pytest…",
                step,
            )
            py_output, py_code = await _run_cmd(
                ["python", "-m", "pytest", "--tb=short", "-q", "--no-header"],
                repo_dir,
            )
            if len(py_output) > len(test_output):
                test_output = py_output
                exit_code = py_code
                framework = "pytest"

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


async def _run_cmd(cmd: list[str], cwd: str) -> tuple[str, int]:
    """Run a command and return (stdout, exit_code)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=_build_env(cwd),
        )
        stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        output = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        return output, proc.returncode or 0
    except asyncio.TimeoutError:
        return "ERROR: Test execution timed out after 120s", 1
    except FileNotFoundError:
        return f"ERROR: Test command not found — {cmd[0]}", 127


def _resolve_js_framework(repo_dir: str) -> str:
    """Try to figure out the right test framework from package.json."""
    pkg_path = Path(repo_dir) / "package.json"
    if not pkg_path.exists():
        return "npm-test"
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "npm-test"

    all_deps: dict[str, str] = {}
    for key in ("dependencies", "devDependencies"):
        all_deps.update(pkg.get(key, {}))

    if "vitest" in all_deps or "@vitest/runner" in all_deps:
        return "vitest"
    if "jest" in all_deps or "@jest/core" in all_deps or "react-scripts" in all_deps:
        return "jest"
    if "mocha" in all_deps:
        return "mocha"

    # Check test script content
    test_script = pkg.get("scripts", {}).get("test", "")
    if "vitest" in test_script:
        return "vitest"
    if "jest" in test_script:
        return "jest"
    if "mocha" in test_script:
        return "mocha"

    # Has a test script at all?
    if test_script.strip():
        return "npm-test"

    return "npm-test"


def _build_env(repo_dir: str) -> dict[str, str]:
    """Build an environment dict for the subprocess."""
    import os

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = repo_dir
    # Disable interactive prompts
    env["CI"] = "true"
    return env
