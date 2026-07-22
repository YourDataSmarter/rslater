from __future__ import annotations

import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from .analysis import analyze_repo_tree, init_technology_detection


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
            "technology": init_technology_detection(),
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


def build_portfolio_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    flags = [
        "uses_react",
        "uses_typescript",
        "uses_esri_js_api",
        "has_custom_esri_webmap_widgets",
        "uses_css",
    ]

    flag_counts = {flag: 0 for flag in flags}
    repos_by_flag: dict[str, list[str]] = {flag: [] for flag in flags}
    dependency_counts: Counter[str] = Counter()

    for record in records:
        repo_name = record.get("repo", {}).get("full_name") or record.get("repo", {}).get("name", "<unknown>")
        analysis = record.get("analysis", {})
        technology = analysis.get("technology", {})
        repo_flags = technology.get("flags", {})

        for flag in flags:
            if repo_flags.get(flag):
                flag_counts[flag] += 1
                repos_by_flag[flag].append(repo_name)

        for config in analysis.get("config_files", []):
            if config.get("name") != "package.json":
                continue
            dep_names = set(config.get("dependency_names", [])) | set(config.get("dev_dependency_names", []))
            for dep in dep_names:
                dependency_counts[dep] += 1

    top_dependencies = [{"name": name, "repo_count": count} for name, count in dependency_counts.most_common(25)]

    return {
        "flag_counts": flag_counts,
        "repos_by_flag": repos_by_flag,
        "top_dependencies": top_dependencies,
    }
