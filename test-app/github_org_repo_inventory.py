#!/usr/bin/env python3
"""
Inventory all repositories in a GitHub organization and export metadata to JSON.

Features:
- Authenticates to GitHub API with a personal access token.
- Lists all repositories in an organization (handles pagination).
- Optionally shallow clones each repository.
- Walks repository trees to gather file-level stats.
- Parses common config files and basic source metrics.

Usage example:
    python github_org_repo_inventory.py --org my-org --token-env GITHUB_TOKEN
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib import error, parse, request

API_BASE = "https://api.github.com/orgs/YourDataSmarter/repos"


def infer_org_from_api_base(api_base: str) -> str | None:
    match = re.search(r"/orgs/([^/]+)/repos/?$", api_base)
    if match:
        return match.group(1)
    return None

# Ignore heavy/generated paths when scanning source trees.
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    "vendor",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".swift",
    ".kt",
    ".scala",
    ".m",
    ".mm",
}

CONFIG_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "tsconfig.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".github/workflows",
}


def build_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-org-repo-inventory-script",
    }


def github_get_json(url: str, headers: dict[str, str]) -> Any:
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed: {exc.code} {exc.reason}. Body: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error calling GitHub API: {exc}") from exc


def get_org_repos(org: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    page = 1
    per_page = 100

    api_base_org = infer_org_from_api_base(API_BASE)
    if api_base_org:
        base_url = API_BASE.rstrip("/")
    else:
        base_url = f"{API_BASE.rstrip('/')}/orgs/{org}/repos"

    while True:
        query = parse.urlencode({"per_page": per_page, "page": page, "type": "all"})
        url = f"{base_url}?{query}"
        batch = github_get_json(url, headers)
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected API response while listing org repos: {batch}")
        if not batch:
            break
        repos.extend(batch)
        page += 1

    return repos


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def shallow_clone_repo(clone_url: str, destination: Path) -> dict[str, Any]:
    if shutil.which("git") is None:
        return {"success": False, "error": "git executable not found on PATH"}

    if destination.exists():
        return {"success": True, "already_present": True, "path": str(destination)}

    destination.parent.mkdir(parents=True, exist_ok=True)
    code, _, stderr = run_command(["git", "clone", "--depth", "1", clone_url, str(destination)])
    if code != 0:
        return {
            "success": False,
            "error": stderr.strip() or "unknown git clone failure",
            "path": str(destination),
        }
    return {"success": True, "already_present": False, "path": str(destination)}


def safe_read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        data = path.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8", errors="ignore")
    except OSError:
        return ""


def parse_config_file(path: Path) -> dict[str, Any]:
    name = path.name
    rel = path.as_posix()
    parsed: dict[str, Any] = {"path": rel, "name": name}

    if name == "package.json":
        text = safe_read_text(path)
        try:
            content = json.loads(text)
            parsed["type"] = "node"
            parsed["package_name"] = content.get("name")
            parsed["version"] = content.get("version")
            parsed["has_scripts"] = bool(content.get("scripts"))
            parsed["dependencies_count"] = len(content.get("dependencies", {}))
            parsed["dev_dependencies_count"] = len(content.get("devDependencies", {}))
        except json.JSONDecodeError:
            parsed["type"] = "node"
            parsed["parse_error"] = "invalid JSON"
        return parsed

    if name == "pyproject.toml":
        text = safe_read_text(path)
        parsed["type"] = "python"
        parsed["mentions_poetry"] = "[tool.poetry]" in text
        parsed["mentions_setuptools"] = "setuptools" in text
        parsed["mentions_hatch"] = "[tool.hatch" in text
        requires_python = re.search(r"requires-python\s*=\s*['\"]([^'\"]+)['\"]", text)
        if requires_python:
            parsed["requires_python"] = requires_python.group(1)
        return parsed

    if name == "requirements.txt":
        text = safe_read_text(path)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        parsed["type"] = "python"
        parsed["requirements_count"] = len(lines)
        parsed["sample_requirements"] = lines[:20]
        return parsed

    if name == "tsconfig.json":
        text = safe_read_text(path)
        try:
            content = json.loads(text)
            compiler_opts = content.get("compilerOptions", {}) if isinstance(content, dict) else {}
            parsed["type"] = "typescript"
            parsed["target"] = compiler_opts.get("target")
            parsed["module"] = compiler_opts.get("module")
            parsed["strict"] = compiler_opts.get("strict")
        except json.JSONDecodeError:
            parsed["type"] = "typescript"
            parsed["parse_error"] = "invalid JSON"
        return parsed

    if name == "go.mod":
        text = safe_read_text(path)
        module_match = re.search(r"^module\s+(.+)$", text, flags=re.MULTILINE)
        parsed["type"] = "go"
        if module_match:
            parsed["module"] = module_match.group(1).strip()
        return parsed

    if name == "Cargo.toml":
        text = safe_read_text(path)
        parsed["type"] = "rust"
        pkg_name = re.search(r"^name\s*=\s*['\"]([^'\"]+)['\"]", text, flags=re.MULTILINE)
        pkg_ver = re.search(r"^version\s*=\s*['\"]([^'\"]+)['\"]", text, flags=re.MULTILINE)
        if pkg_name:
            parsed["package_name"] = pkg_name.group(1)
        if pkg_ver:
            parsed["version"] = pkg_ver.group(1)
        return parsed

    parsed["type"] = "generic"
    return parsed


def source_metrics_for_file(path: Path, rel_path: str) -> dict[str, Any]:
    text = safe_read_text(path)
    lines = text.splitlines()
    ext = path.suffix.lower()

    metrics: dict[str, Any] = {
        "path": rel_path,
        "ext": ext,
        "line_count": len(lines),
        "non_empty_line_count": sum(1 for ln in lines if ln.strip()),
    }

    if ext == ".py":
        metrics["function_count"] = len(re.findall(r"^\s*def\s+\w+\s*\(", text, flags=re.MULTILINE))
        metrics["class_count"] = len(re.findall(r"^\s*class\s+\w+\s*[:\(]", text, flags=re.MULTILINE))
        metrics["import_count"] = len(re.findall(r"^\s*(import|from)\s+", text, flags=re.MULTILINE))
    elif ext in {".js", ".jsx", ".ts", ".tsx"}:
        metrics["function_count"] = len(
            re.findall(r"\bfunction\s+\w+\s*\(|\b\w+\s*=\s*\([^)]*\)\s*=>", text)
        )
        metrics["class_count"] = len(re.findall(r"\bclass\s+\w+", text))
        metrics["import_count"] = len(re.findall(r"^\s*import\s+", text, flags=re.MULTILINE))
    elif ext in {".go"}:
        metrics["function_count"] = len(re.findall(r"^\s*func\s+\w+\s*\(", text, flags=re.MULTILINE))
        metrics["import_count"] = len(re.findall(r"^\s*import\s+", text, flags=re.MULTILINE))
    elif ext in {".java", ".cs"}:
        metrics["class_count"] = len(re.findall(r"\bclass\s+\w+", text))
        metrics["method_like_count"] = len(re.findall(r"\b\w+\s+\w+\s*\([^)]*\)\s*\{", text))

    return metrics


def analyze_repo_tree(local_repo_path: Path) -> dict[str, Any]:
    total_files = 0
    ext_counts: dict[str, int] = {}
    config_summaries: list[dict[str, Any]] = []
    source_file_metrics: list[dict[str, Any]] = []

    for root, dirs, files in os.walk(local_repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        root_path = Path(root)

        for filename in files:
            total_files += 1
            file_path = root_path / filename
            rel_path = str(file_path.relative_to(local_repo_path)).replace("\\", "/")

            ext = file_path.suffix.lower() or "<no_ext>"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

            if filename in CONFIG_FILES or rel_path == ".github/workflows":
                config_summaries.append(parse_config_file(file_path))

            if file_path.suffix.lower() in SOURCE_EXTENSIONS:
                source_file_metrics.append(source_metrics_for_file(file_path, rel_path))

    source_totals = {
        "source_file_count": len(source_file_metrics),
        "total_source_lines": sum(item.get("line_count", 0) for item in source_file_metrics),
        "total_non_empty_source_lines": sum(
            item.get("non_empty_line_count", 0) for item in source_file_metrics
        ),
    }

    # Keep payload manageable by capping per-file metrics in output.
    source_file_metrics = sorted(source_file_metrics, key=lambda x: x.get("line_count", 0), reverse=True)[:500]

    return {
        "tree_stats": {
            "total_files": total_files,
            "extension_counts": dict(sorted(ext_counts.items(), key=lambda kv: kv[1], reverse=True)),
        },
        "config_files": config_summaries,
        "source_totals": source_totals,
        "source_file_metrics": source_file_metrics,
    }


def build_repo_record(
    org: str,
    repo: dict[str, Any],
    clone_root: Path,
    do_clone: bool,
    force_reclone: bool,
) -> dict[str, Any]:
    name = repo.get("name", "")
    full_name = repo.get("full_name", f"{org}/{name}")
    default_branch = repo.get("default_branch")

    record: dict[str, Any] = {
        "repo": {
            "name": name,
            "full_name": full_name,
            "id": repo.get("id"),
            "private": repo.get("private"),
            "archived": repo.get("archived"),
            "disabled": repo.get("disabled"),
            "fork": repo.get("fork"),
            "default_branch": default_branch,
            "language": repo.get("language"),
            "size_kb": repo.get("size"),
            "topics": repo.get("topics", []),
            "visibility": repo.get("visibility"),
            "created_at": repo.get("created_at"),
            "updated_at": repo.get("updated_at"),
            "pushed_at": repo.get("pushed_at"),
            "html_url": repo.get("html_url"),
            "clone_url": repo.get("clone_url"),
            "ssh_url": repo.get("ssh_url"),
        },
        "analysis": {
            "clone_attempted": do_clone,
            "clone": None,
            "tree_stats": None,
            "config_files": [],
            "source_totals": None,
            "source_file_metrics": [],
        },
    }

    if not do_clone:
        return record

    clone_url = repo.get("clone_url")
    if not clone_url:
        record["analysis"]["clone"] = {"success": False, "error": "missing clone_url from GitHub API"}
        return record

    local_path = clone_root / name

    if force_reclone and local_path.exists():
        shutil.rmtree(local_path, ignore_errors=True)

    clone_result = shallow_clone_repo(clone_url, local_path)
    record["analysis"]["clone"] = clone_result

    if not clone_result.get("success"):
        return record

    tree_analysis = analyze_repo_tree(local_path)
    record["analysis"].update(tree_analysis)
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory GitHub organization repositories into JSON")
    parser.add_argument(
        "--org",
        required=False,
        help="GitHub organization login name. Optional if API_BASE already includes /orgs/<org>/repos",
    )
    parser.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="Environment variable name that stores a GitHub token (default: GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to output JSON file. Default: ./org_repo_inventory_<org>_<timestamp>.json",
    )
    parser.add_argument(
        "--clone-root",
        default="./.cache/org-repo-clones",
        help="Directory where repositories are shallow-cloned for analysis",
    )
    parser.add_argument(
        "--no-clone",
        action="store_true",
        help="Skip cloning and only capture API metadata",
    )
    parser.add_argument(
        "--force-reclone",
        action="store_true",
        help="Delete and re-clone existing local repo folders",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    org = args.org or infer_org_from_api_base(API_BASE)

    if not org:
        print(
            "Missing organization. Pass --org or set API_BASE to include /orgs/<org>/repos.",
            file=sys.stderr,
        )
        return 1

    token = os.getenv(args.token_env)

    if not token:
        print(
            f"Missing token. Set env var {args.token_env} with a GitHub token that can read org repositories.",
            file=sys.stderr,
        )
        return 1

    output_path = Path(args.output) if args.output else Path(
        f"org_repo_inventory_{org}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    clone_root = Path(args.clone_root)
    do_clone = not args.no_clone

    headers = build_headers(token)

    print(f"[1/3] Fetching repositories for organization: {org}")
    repos = get_org_repos(org, headers)
    print(f"Found {len(repos)} repositories")

    records: list[dict[str, Any]] = []
    for idx, repo in enumerate(repos, start=1):
        full_name = repo.get("full_name", repo.get("name", "<unknown>"))
        print(f"[2/3] Processing {idx}/{len(repos)}: {full_name}")
        record = build_repo_record(
            org=org,
            repo=repo,
            clone_root=clone_root,
            do_clone=do_clone,
            force_reclone=args.force_reclone,
        )
        records.append(record)

    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "organization": org,
        "repo_count": len(records),
        "options": {
            "clone_enabled": do_clone,
            "clone_root": str(clone_root.resolve()) if do_clone else None,
            "force_reclone": bool(args.force_reclone),
        },
        "repos": records,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[3/3] Wrote inventory JSON: {output_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
