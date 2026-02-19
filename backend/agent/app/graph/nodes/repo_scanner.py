"""
repo_scanner node — clone the repo, detect language / framework, list test files.
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
from pathlib import Path

from git import Repo as GitRepo  # type: ignore[import-untyped]

from ...config import REPOS_DIR
from ...db import insert_trace
from ...events import emit_thought
from ..state import AgentState

logger = logging.getLogger("rift.node.repo_scanner")

# Language → (test glob patterns, framework name)
_DETECTION_MAP: dict[str, list[tuple[str, str]]] = {
    "python": [
        ("**/test_*.py", "pytest"),
        ("**/tests.py", "pytest"),
        ("**/*_test.py", "pytest"),
    ],
    "javascript": [
        ("**/*.test.js", "jest"),
        ("**/*.spec.js", "jest"),
        ("**/*.test.mjs", "jest"),
        ("**/test/**/*.js", "mocha"),
    ],
    "typescript": [
        ("**/*.test.ts", "jest"),
        ("**/*.spec.ts", "jest"),
        ("**/*.test.tsx", "jest"),
        ("**/test/**/*.ts", "vitest"),
    ],
}

# File extension → language
_EXT_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mjs": "javascript",
}


def _detect_language(repo_path: Path) -> str:
    """Heuristic: count file extensions in the repo."""
    counts: dict[str, int] = {}
    for f in repo_path.rglob("*"):
        if f.is_file() and f.suffix in _EXT_MAP:
            lang = _EXT_MAP[f.suffix]
            counts[lang] = counts.get(lang, 0) + 1
    if not counts:
        return "python"  # safe fallback
    return max(counts, key=counts.get)  # type: ignore[arg-type]


def _detect_framework(repo_path: Path, language: str) -> tuple[str, list[str]]:
    """Return (framework_name, list_of_test_files)."""
    patterns = _DETECTION_MAP.get(language, [])
    for glob_pattern, framework in patterns:
        matches = sorted(str(p.relative_to(repo_path)) for p in repo_path.glob(glob_pattern))
        if matches:
            return framework, matches

    # Fallback: look for common config files
    if (repo_path / "pytest.ini").exists() or (repo_path / "setup.cfg").exists():
        return "pytest", []
    if (repo_path / "jest.config.js").exists() or (repo_path / "jest.config.ts").exists():
        return "jest", []
    if (repo_path / "vitest.config.ts").exists():
        return "vitest", []

    return "unknown", []


async def repo_scanner(state: AgentState) -> AgentState:
    """
    Clone the repository, detect language/framework, list test files.
    """
    run_id = state["run_id"]
    repo_url = state["repo_url"]
    branch_name = state["branch_name"]
    step = state.get("iteration", 0) * 10 + 1

    await emit_thought(run_id, "repo_scanner", f"Cloning {repo_url}…", step)

    repo_dir = REPOS_DIR / run_id
    if repo_dir.exists():
        shutil.rmtree(repo_dir, ignore_errors=True)
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Clone in a thread to avoid blocking the event loop
    def _clone() -> GitRepo:
        repo = GitRepo.clone_from(repo_url, str(repo_dir), depth=1)
        # Create and checkout the healing branch
        if branch_name not in [h.name for h in repo.heads]:
            repo.create_head(branch_name)
        repo.heads[branch_name].checkout()  # type: ignore[union-attr]
        return repo

    await asyncio.to_thread(_clone)

    language = _detect_language(repo_dir)
    framework, test_files = _detect_framework(repo_dir, language)

    await emit_thought(
        run_id,
        "repo_scanner",
        f"Detected {language}/{framework} — {len(test_files)} test file(s)",
        step + 1,
    )

    await insert_trace(
        run_id,
        step_index=step,
        agent_node="repo_scanner",
        action_type="clone",
        action_label=f"Cloned {repo_url}, detected {language}/{framework}",
        payload={
            "language": language,
            "framework": framework,
            "test_file_count": len(test_files),
        },
    )

    return {
        "repo_dir": str(repo_dir),
        "language": language,
        "framework": framework,
        "test_files": test_files,
        "current_node": "repo_scanner",
    }
