"""
repo_scanner node — clone the repo, detect language / framework, list test files.
"""
from __future__ import annotations

import asyncio
import json
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
        ("**/*.test.jsx", "jest"),
        ("**/test/**/*.js", "mocha"),
        ("**/__tests__/**/*.js", "jest"),
    ],
    "typescript": [
        ("**/*.test.ts", "jest"),
        ("**/*.spec.ts", "jest"),
        ("**/*.test.tsx", "jest"),
        ("**/*.spec.tsx", "jest"),
        ("**/test/**/*.ts", "vitest"),
        ("**/__tests__/**/*.ts", "jest"),
    ],
    "csharp": [
        ("**/*Tests.cs", "dotnet-test"),
        ("**/*Test.cs", "dotnet-test"),
        ("**/*Tests/*.cs", "dotnet-test"),
        ("**/Tests/**/*.cs", "dotnet-test"),
        ("**/*.Tests/**/*.cs", "dotnet-test"),
    ],
    "fsharp": [
        ("**/*Tests.fs", "dotnet-test"),
        ("**/*Test.fs", "dotnet-test"),
    ],
    "java": [
        ("**/src/test/**/*.java", "maven"),
        ("**/*Test.java", "maven"),
        ("**/*Tests.java", "maven"),
    ],
    "go": [
        ("**/*_test.go", "go-test"),
    ],
    "ruby": [
        ("**/test/**/*_test.rb", "ruby-test"),
        ("**/spec/**/*_spec.rb", "rspec"),
    ],
}

# File extension → language
_EXT_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mjs": "javascript",
    ".vue": "javascript",
    ".cs": "csharp",
    ".fs": "fsharp",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".rs": "rust",
}

# Known test-related npm packages → framework
_NPM_FRAMEWORK_MAP: dict[str, str] = {
    "jest": "jest",
    "@jest/core": "jest",
    "react-scripts": "jest",          # CRA bundles jest
    "vitest": "vitest",
    "mocha": "mocha",
    "@vue/test-utils": "vitest",
    "@testing-library/jest-dom": "jest",
    "@testing-library/react": "jest",
    "@testing-library/vue": "vitest",
}


def _detect_language(repo_path: Path) -> str:
    """Heuristic: count file extensions in the repo, skip node_modules."""
    counts: dict[str, int] = {}
    for f in repo_path.rglob("*"):
        if f.is_file() and "node_modules" not in f.parts and f.suffix in _EXT_MAP:
            lang = _EXT_MAP[f.suffix]
            counts[lang] = counts.get(lang, 0) + 1
    if counts:
        return max(counts, key=counts.get)  # type: ignore[arg-type]

    # Fallback: check for project/build files that indicate language
    if list(repo_path.glob("**/*.sln")) or list(repo_path.glob("**/*.csproj")):
        return "csharp"
    if list(repo_path.glob("**/*.fsproj")):
        return "fsharp"
    if (repo_path / "pom.xml").exists() or (repo_path / "build.gradle").exists():
        return "java"
    if (repo_path / "go.mod").exists():
        return "go"
    if (repo_path / "Cargo.toml").exists():
        return "rust"
    if (repo_path / "Gemfile").exists():
        return "ruby"
    if (repo_path / "package.json").exists():
        return "javascript"

    return "python"  # ultimate fallback


def _read_package_json(repo_path: Path) -> dict:
    """Safely read and parse package.json if it exists."""
    pkg_path = repo_path / "package.json"
    if not pkg_path.exists():
        return {}
    try:
        return json.loads(pkg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _detect_framework_from_pkg(pkg: dict) -> str | None:
    """Detect test framework from package.json deps and scripts."""
    all_deps: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        all_deps.update(pkg.get(key, {}))

    # Check deps for known test packages
    for dep_name, framework in _NPM_FRAMEWORK_MAP.items():
        if dep_name in all_deps:
            return framework

    # Check scripts for test runner hints
    scripts = pkg.get("scripts", {})
    test_script = scripts.get("test", "")
    if "vitest" in test_script:
        return "vitest"
    if "jest" in test_script:
        return "jest"
    if "mocha" in test_script:
        return "mocha"
    if "pytest" in test_script:
        return "pytest"

    return None


def _detect_framework(repo_path: Path, language: str) -> tuple[str, list[str]]:
    """Return (framework_name, list_of_test_files)."""
    # 1. Check glob patterns for test files
    patterns = _DETECTION_MAP.get(language, [])
    for glob_pattern, framework in patterns:
        matches = sorted(
            str(p.relative_to(repo_path))
            for p in repo_path.glob(glob_pattern)
            if "node_modules" not in p.parts
        )
        if matches:
            return framework, matches

    # 2. Check config files
    if (repo_path / "pytest.ini").exists() or (repo_path / "setup.cfg").exists():
        return "pytest", []
    if (repo_path / "jest.config.js").exists() or (repo_path / "jest.config.ts").exists():
        return "jest", []
    if (repo_path / "jest.config.mjs").exists() or (repo_path / "jest.config.cjs").exists():
        return "jest", []
    if (repo_path / "vitest.config.ts").exists() or (repo_path / "vitest.config.js").exists():
        return "vitest", []
    if (repo_path / ".mocharc.yml").exists() or (repo_path / ".mocharc.json").exists():
        return "mocha", []

    # 2b. .NET project files (.sln, .csproj, .fsproj)
    if list(repo_path.glob("**/*.sln")) or list(repo_path.glob("**/*.csproj")):
        # Look for test project references
        test_csprojs = [
            str(p.relative_to(repo_path))
            for p in repo_path.rglob("*.csproj")
            if "test" in p.stem.lower() or "test" in str(p.parent).lower()
        ]
        return "dotnet-test", test_csprojs

    if list(repo_path.glob("**/*.fsproj")):
        return "dotnet-test", []

    # 2c. Java build files
    if (repo_path / "pom.xml").exists():
        return "maven", []
    if (repo_path / "build.gradle").exists() or (repo_path / "build.gradle.kts").exists():
        return "gradle", []

    # 2d. Go module
    if (repo_path / "go.mod").exists():
        return "go-test", []

    # 2e. Ruby
    if (repo_path / "Gemfile").exists():
        if (repo_path / ".rspec").exists() or list(repo_path.glob("**/spec/**/*_spec.rb")):
            return "rspec", []
        return "ruby-test", []

    # 2f. Rust
    if (repo_path / "Cargo.toml").exists():
        return "cargo-test", []

    # 3. Check package.json for deps/scripts
    pkg = _read_package_json(repo_path)
    if pkg:
        fw = _detect_framework_from_pkg(pkg)
        if fw:
            return fw, []

        # 4. If there's a "test" script in package.json, use npm-test as runner
        scripts = pkg.get("scripts", {})
        if "test" in scripts and scripts["test"].strip():
            return "npm-test", []

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
