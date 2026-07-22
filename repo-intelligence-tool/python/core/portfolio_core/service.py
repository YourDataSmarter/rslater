from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Callable

from .constants import API_BASE
from .github_api import build_headers, get_org_repos, infer_org_from_api_base
from .scanner import build_portfolio_summary, build_repo_record

ProgressCallback = Callable[[str], None]

FLAG_LABELS = {
    "uses_react": "projects using React",
    "uses_typescript": "projects using TypeScript",
    "uses_esri_js_api": "projects using Esri JS API",
    "has_custom_esri_webmap_widgets": "projects with custom Esri WebMap widgets",
    "uses_css": "projects using CSS",
}


def build_default_output_path(org: str) -> Path:
    return Path(f"org_repo_inventory_{org}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")


def run_inventory_scan(
    org: str | None,
    token: str,
    clone_root: Path,
    do_clone: bool,
    force_reclone: bool,
    output_path: Path | None = None,
    progress_callback: ProgressCallback | None = None,
) -> tuple[dict[str, Any], Path]:
    resolved_org = org or infer_org_from_api_base(API_BASE)
    if not resolved_org:
        raise ValueError("Missing organization. Provide org or include /orgs/<org>/repos in API base.")
    if not token:
        raise ValueError("Missing GitHub token.")

    report_path = output_path or build_default_output_path(resolved_org)

    if progress_callback:
        progress_callback(f"[1/3] Fetching repositories for organization: {resolved_org}")

    headers = build_headers(token)
    repos = get_org_repos(resolved_org, headers)

    if progress_callback:
        progress_callback(f"Found {len(repos)} repositories")

    records: list[dict[str, Any]] = []
    total = len(repos)
    for idx, repo in enumerate(repos, start=1):
        full_name = repo.get("full_name", repo.get("name", "<unknown>"))
        if progress_callback:
            progress_callback(f"[2/3] Processing {idx}/{total}: {full_name}")

        record = build_repo_record(
            org=resolved_org,
            repo=repo,
            clone_root=clone_root,
            do_clone=do_clone,
            force_reclone=force_reclone,
        )
        records.append(record)

    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "organization": resolved_org,
        "repo_count": len(records),
        "options": {
            "clone_enabled": do_clone,
            "clone_root": str(clone_root.resolve()) if do_clone else None,
            "force_reclone": bool(force_reclone),
        },
        "repos": records,
        "summary": build_portfolio_summary(records),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if progress_callback:
        progress_callback(f"[3/3] Wrote inventory JSON: {report_path.resolve()}")

    return report, report_path


def load_report(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Report JSON root must be an object.")
    return payload


def infer_question_flag(question: str) -> str | None:
    q = question.lower()
    if "custom" in q and "widget" in q and "esri" in q:
        return "has_custom_esri_webmap_widgets"
    if "css" in q or "stylesheet" in q or "style" in q:
        return "uses_css"
    if "react" in q:
        return "uses_react"
    if "typescript" in q or "ts " in q:
        return "uses_typescript"
    if "esri" in q or "webmap" in q or "arcgis" in q:
        return "uses_esri_js_api"
    return None


def answer_portfolio_question(report: dict[str, Any], question: str) -> dict[str, Any]:
    flag = infer_question_flag(question)
    if not flag:
        return {
            "question": question,
            "status": "unknown",
            "message": "I could not map that question to a known detector yet.",
        }

    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    repos_by_flag = summary.get("repos_by_flag", {})
    if not isinstance(repos_by_flag, dict):
        repos_by_flag = {}

    matching_repos = repos_by_flag.get(flag, [])
    if not isinstance(matching_repos, list):
        matching_repos = []

    evidence_by_repo: dict[str, list[dict[str, Any]]] = {}
    for repo_record in report.get("repos", []):
        if not isinstance(repo_record, dict):
            continue

        repo = repo_record.get("repo", {})
        analysis = repo_record.get("analysis", {})
        technology = analysis.get("technology", {}) if isinstance(analysis, dict) else {}
        evidence = technology.get("evidence", {}) if isinstance(technology, dict) else {}
        entries = evidence.get(flag, []) if isinstance(evidence, dict) else []

        full_name = repo.get("full_name") or repo.get("name") or "<unknown>"
        if entries:
            evidence_by_repo[str(full_name)] = entries[:5]

    return {
        "question": question,
        "status": "ok",
        "flag": flag,
        "label": FLAG_LABELS.get(flag, flag),
        "count": len(matching_repos),
        "matching_repositories": matching_repos,
        "evidence_by_repository": evidence_by_repo,
    }
