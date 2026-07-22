from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

SUPPORTED_FLAGS = [
    "uses_react",
    "uses_typescript",
    "uses_esri_js_api",
    "has_custom_esri_webmap_widgets",
    "uses_css",
]


def ensure_data_store(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)


def _latest_pointer_path(data_dir: Path) -> Path:
    return data_dir / "latest_report.json"


def _sanitize_slug(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)
    return cleaned.strip("_") or "org"


def _build_report_filename(report: dict[str, Any]) -> str:
    org = _sanitize_slug(str(report.get("organization") or "org"))
    generated_at = str(report.get("generated_at") or "")

    try:
        parsed = dt.datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        stamp = parsed.strftime("%Y%m%d_%H%M%S")
    except ValueError:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")

    return f"report_{org}_{stamp}.json"


def index_report(report: dict[str, Any], data_dir: Path, report_path: Path | None = None) -> Path:
    ensure_data_store(data_dir)

    if report_path and report_path.exists():
        indexed_path = data_dir / report_path.name
        indexed_path.write_text(report_path.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        indexed_path = data_dir / _build_report_filename(report)
        indexed_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    pointer = {
        "report_file": indexed_path.name,
        "indexed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    _latest_pointer_path(data_dir).write_text(json.dumps(pointer, indent=2), encoding="utf-8")

    return indexed_path


def load_latest_report(data_dir: Path) -> dict[str, Any] | None:
    ensure_data_store(data_dir)
    pointer_path = _latest_pointer_path(data_dir)

    if pointer_path.exists():
        try:
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            report_file = pointer.get("report_file") if isinstance(pointer, dict) else None
            if isinstance(report_file, str):
                report_path = data_dir / report_file
                if report_path.exists():
                    payload = json.loads(report_path.read_text(encoding="utf-8"))
                    return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            return None

    report_files = sorted(data_dir.glob("report_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not report_files:
        return None

    try:
        payload = json.loads(report_files[0].read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        return None


def _iter_repo_records(report: dict[str, Any]) -> list[dict[str, Any]]:
    repos = report.get("repos", [])
    if not isinstance(repos, list):
        return []
    return [repo for repo in repos if isinstance(repo, dict)]


def get_repository_count(data_dir: Path) -> int:
    report = load_latest_report(data_dir)
    if not report:
        return 0
    return len(_iter_repo_records(report))


def get_repositories_for_flag(data_dir: Path, flag: str) -> list[str]:
    if flag not in SUPPORTED_FLAGS:
        return []

    report = load_latest_report(data_dir)
    if not report:
        return []

    matching: list[str] = []
    for repo_record in _iter_repo_records(report):
        repo = repo_record.get("repo", {})
        analysis = repo_record.get("analysis", {})
        technology = analysis.get("technology", {}) if isinstance(analysis, dict) else {}
        flags = technology.get("flags", {}) if isinstance(technology, dict) else {}

        if flags.get(flag):
            full_name = repo.get("full_name") or repo.get("name") or "<unknown>"
            matching.append(str(full_name))

    return sorted(matching)


def get_evidence_by_repo(data_dir: Path, flag: str, max_rows_per_repo: int = 5) -> dict[str, list[dict[str, Any]]]:
    report = load_latest_report(data_dir)
    if not report:
        return {}

    result: dict[str, list[dict[str, Any]]] = {}

    for repo_record in _iter_repo_records(report):
        repo = repo_record.get("repo", {})
        analysis = repo_record.get("analysis", {})
        technology = analysis.get("technology", {}) if isinstance(analysis, dict) else {}
        evidence = technology.get("evidence", {}) if isinstance(technology, dict) else {}
        entries = evidence.get(flag, []) if isinstance(evidence, dict) else []

        if not isinstance(entries, list) or not entries:
            continue

        full_name = repo.get("full_name") or repo.get("name") or "<unknown>"
        result[str(full_name)] = []
        for entry in entries[:max_rows_per_repo]:
            if not isinstance(entry, dict):
                continue
            result[str(full_name)].append(
                {
                    "rule_id": str(entry.get("rule_id") or ""),
                    "path": str(entry.get("path") or ""),
                    "reason": str(entry.get("reason") or ""),
                    "snippet": entry.get("snippet"),
                }
            )

    return result
