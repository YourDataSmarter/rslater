from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from .llm import OllamaClient
from .store import get_evidence_by_repo, get_repositories_for_flag, get_repository_count, load_latest_report

FLAG_LABELS = {
    "uses_react": "projects using React",
    "uses_typescript": "projects using TypeScript",
    "uses_esri_js_api": "projects using Esri JS API",
    "has_custom_esri_webmap_widgets": "projects with custom Esri WebMap widgets",
    "uses_css": "projects using CSS",
}

SYSTEM_PROMPT = """You are an internal repository intelligence agent.
Answer only from the provided indexed repository evidence.
Do not invent repositories, files, frameworks, or counts.
If the evidence is incomplete, say so clearly.
Keep answers concise and evidence-first.
"""

CLASSIFIER_PROMPT = """Map the user's question to exactly one detector flag.
Allowed values:
- uses_react
- uses_typescript
- uses_esri_js_api
- has_custom_esri_webmap_widgets
- uses_css
- none

Reply with only the flag value.
"""

MULTI_CLASSIFIER_PROMPT = """Map the user's question to zero or more detector flags.
Allowed values:
- uses_react
- uses_typescript
- uses_esri_js_api
- has_custom_esri_webmap_widgets
- uses_css

Return either:
- none
or a comma-separated list of one or more allowed values.
Reply with only the values.
"""


def infer_question_flag(question: str) -> str | None:
    q = question.lower()
    if "custom" in q and "widget" in q and "esri" in q:
        return "has_custom_esri_webmap_widgets"
    if "css" in q or "stylesheet" in q or "style" in q:
        return "uses_css"
    if "react" in q:
        return "uses_react"
    if re.search(r"\btypescript\b|\bts\b", q):
        return "uses_typescript"
    if "esri" in q or "webmap" in q or "arcgis" in q:
        return "uses_esri_js_api"
    return None


def infer_question_flags(question: str) -> list[str]:
    q = question.lower()
    flags: list[str] = []

    if "css" in q or "stylesheet" in q or "style" in q:
        flags.append("uses_css")
    if "react" in q:
        flags.append("uses_react")
    if re.search(r"\btypescript\b|\bts\b", q):
        flags.append("uses_typescript")
    if "esri" in q or "webmap" in q or "arcgis" in q:
        flags.append("uses_esri_js_api")
    if "custom" in q and "widget" in q and ("esri" in q or "webmap" in q or "arcgis" in q):
        flags.append("has_custom_esri_webmap_widgets")

    seen: list[str] = []
    for flag in flags:
        if flag not in seen:
            seen.append(flag)
    return seen


def _build_fallback_summary(question: str, flag: str, total_indexed_repos: int, matching_repos: list[str]) -> str:
    label = FLAG_LABELS.get(flag, flag)
    if not matching_repos:
        return (
            f"From {total_indexed_repos} indexed repositories, I found no matches for {label} "
            f"for the question: {question}"
        )

    preview = ", ".join(matching_repos[:5])
    more = "" if len(matching_repos) <= 5 else f", plus {len(matching_repos) - 5} more"
    return (
        f"From {total_indexed_repos} indexed repositories, {len(matching_repos)} match {label}. "
        f"Examples: {preview}{more}."
    )


def _build_fallback_summary_multi(
    question: str,
    flags: list[str],
    total_indexed_repos: int,
    matching_repos: list[str],
) -> str:
    labels = [FLAG_LABELS.get(flag, flag) for flag in flags]
    label_text = " and ".join(labels)
    if not matching_repos:
        return (
            f"From {total_indexed_repos} indexed repositories, I found no matches for repositories that satisfy "
            f"{label_text} for the question: {question}"
        )

    preview = ", ".join(matching_repos[:5])
    more = "" if len(matching_repos) <= 5 else f", plus {len(matching_repos) - 5} more"
    return (
        f"From {total_indexed_repos} indexed repositories, {len(matching_repos)} satisfy {label_text}. "
        f"Examples: {preview}{more}."
    )


def _build_agent_context(
    question: str,
    flags: list[str],
    report: dict[str, Any],
    total_indexed_repos: int,
    matching_repos: list[str],
    evidence_by_repo: dict[str, list[dict[str, Any]]],
) -> str:
    summary = report.get("summary", {}) if isinstance(report, dict) else {}
    top_dependencies = summary.get("top_dependencies", []) if isinstance(summary, dict) else []

    lines = [
        f"Question: {question}",
        f"Detected intent flags: {', '.join(flags)}",
        f"Indexed repository count: {total_indexed_repos}",
        f"Matching repository count: {len(matching_repos)}",
        "Matching repositories:",
    ]

    for repo_name in matching_repos[:25]:
        lines.append(f"- {repo_name}")

    lines.append("Evidence by repository:")
    for repo_name, entries in evidence_by_repo.items():
        lines.append(f"- {repo_name}")
        for entry in entries[:3]:
            path = entry.get("path") or ""
            reason = entry.get("reason") or ""
            snippet = entry.get("snippet") or ""
            lines.append(f"  path={path}; reason={reason}; snippet={snippet}")

    if isinstance(top_dependencies, list) and top_dependencies:
        lines.append("Top dependencies in the indexed report:")
        for item in top_dependencies[:10]:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {item.get('name')}: {item.get('repo_count')}")

    lines.append(
        "Respond with a short direct answer, then list matching repositories, then mention 2-5 concrete evidence files if available."
    )
    return "\n".join(lines)


def _build_open_question_context(question: str, report: dict[str, Any], total_indexed_repos: int) -> str:
    summary = report.get("summary", {}) if isinstance(report, dict) else {}
    flag_counts = summary.get("flag_counts", {}) if isinstance(summary, dict) else {}
    repos_by_flag = summary.get("repos_by_flag", {}) if isinstance(summary, dict) else {}
    top_dependencies = summary.get("top_dependencies", []) if isinstance(summary, dict) else []

    lines = [
        f"Question: {question}",
        f"Indexed repository count: {total_indexed_repos}",
        "Known detector coverage:",
        "- uses_react",
        "- uses_typescript",
        "- uses_esri_js_api",
        "- has_custom_esri_webmap_widgets",
        "- uses_css",
    ]

    if isinstance(flag_counts, dict) and flag_counts:
        lines.append("Detector match counts:")
        for key in sorted(flag_counts.keys()):
            lines.append(f"- {key}: {flag_counts.get(key)}")

    if isinstance(top_dependencies, list) and top_dependencies:
        lines.append("Top dependencies in the indexed report:")
        for item in top_dependencies[:15]:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {item.get('name')}: {item.get('repo_count')}")

    if isinstance(repos_by_flag, dict) and repos_by_flag:
        lines.append("Sample repositories by detector (up to 3 per detector):")
        for key in sorted(repos_by_flag.keys()):
            raw_repos = repos_by_flag.get(key, [])
            if not isinstance(raw_repos, list) or not raw_repos:
                continue
            sample = ", ".join(str(repo) for repo in raw_repos[:3])
            lines.append(f"- {key}: {sample}")

    lines.append(
        "Answer from this indexed evidence only. If the question is outside available evidence, say what is missing and suggest the closest answerable query."
    )
    return "\n".join(lines)


def _build_local_llm_client() -> OllamaClient:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    return OllamaClient(base_url=base_url, model=model)


def _generate_llm_answer(prompt: str) -> dict[str, Any]:
    client = _build_local_llm_client()
    response = client.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.1)
    return {
        "enabled": True,
        "provider": response.provider,
        "model": response.model,
        "ok": response.ok,
        "error": response.error,
        "answer": response.content if response.ok else None,
    }


def _infer_flag_with_llm(question: str) -> str | None:
    client = _build_local_llm_client()
    response = client.generate(prompt=question, system_prompt=CLASSIFIER_PROMPT, temperature=0.0)
    if not response.ok:
        return None

    candidate = response.content.strip().splitlines()[0].strip().lower()
    allowed = {
        "uses_react",
        "uses_typescript",
        "uses_esri_js_api",
        "has_custom_esri_webmap_widgets",
        "uses_css",
        "none",
    }
    if candidate not in allowed or candidate == "none":
        return None
    return candidate


def _infer_flags_with_llm(question: str) -> list[str]:
    client = _build_local_llm_client()
    response = client.generate(prompt=question, system_prompt=MULTI_CLASSIFIER_PROMPT, temperature=0.0)
    if not response.ok:
        return []

    allowed = {
        "uses_react",
        "uses_typescript",
        "uses_esri_js_api",
        "has_custom_esri_webmap_widgets",
        "uses_css",
    }
    raw = response.content.strip().lower()
    if raw == "none":
        return []

    items = [item.strip() for item in raw.split(",")]
    flags: list[str] = []
    for item in items:
        if item in allowed and item not in flags:
            flags.append(item)
    return flags


def _get_matching_repositories(data_dir: Path, flags: list[str]) -> list[str]:
    if not flags:
        return []

    repo_sets = [set(get_repositories_for_flag(data_dir, flag)) for flag in flags]
    if not repo_sets:
        return []

    matching = set.intersection(*repo_sets)
    return sorted(matching)


def _get_evidence_for_repositories(
    data_dir: Path,
    flags: list[str],
    matching_repos: list[str],
    max_rows_per_repo: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, list[dict[str, Any]]] = {repo_name: [] for repo_name in matching_repos}
    for flag in flags:
        evidence_by_repo = get_evidence_by_repo(data_dir, flag, max_rows_per_repo=max_rows_per_repo)
        for repo_name in matching_repos:
            for entry in evidence_by_repo.get(repo_name, []):
                enriched = dict(entry)
                enriched["flag"] = flag
                merged[repo_name].append(enriched)

    for repo_name in list(merged.keys()):
        merged[repo_name] = merged[repo_name][:max_rows_per_repo]
    return merged


def get_agent_status(data_dir: Path) -> dict[str, Any]:
    client = _build_local_llm_client()
    llm_available, llm_error = client.is_available()
    report = load_latest_report(data_dir)

    return {
        "source": "backend-agent",
        "llm": {
            "provider": "ollama",
            "model": client.model,
            "base_url": client.base_url,
            "available": llm_available,
            "error": llm_error,
        },
        "indexed_report_available": report is not None,
        "indexed_repo_count": get_repository_count(data_dir),
    }


def answer_portfolio_question_with_agent(question: str, data_dir: Path) -> dict[str, Any]:
    flags = infer_question_flags(question)
    if not flags:
        fallback_flag = infer_question_flag(question)
        if fallback_flag:
            flags = [fallback_flag]

    report = load_latest_report(data_dir)
    if not report:
        return {
            "question": question,
            "status": "empty-index",
            "message": "No indexed repository data found. Run a scan first.",
            "source": "backend-agent",
        }

    total_indexed_repos = get_repository_count(data_dir)
    if total_indexed_repos == 0:
        return {
            "question": question,
            "status": "empty-index",
            "message": "No indexed repository data found. Run a scan first.",
            "source": "backend-agent",
        }

    if not flags:
        fallback_summary = (
            "I could not map that question to a specific detector flag, but I can still answer from indexed repository "
            "summary data only."
        )
        prompt = _build_open_question_context(
            question=question,
            report=report,
            total_indexed_repos=total_indexed_repos,
        )
        llm = _generate_llm_answer(prompt)
        final_answer = llm.get("answer") or fallback_summary
        llm["answer"] = final_answer

        return {
            "question": question,
            "status": "ok",
            "source": "backend-agent",
            "flags": [],
            "label": "open-ended portfolio question",
            "indexed_repo_count": total_indexed_repos,
            "count": None,
            "answer": final_answer,
            "matching_repositories": [],
            "evidence_by_repository": {},
            "llm": llm,
        }

    matching_repos = _get_matching_repositories(data_dir, flags)
    evidence_by_repo = _get_evidence_for_repositories(data_dir, flags, matching_repos, max_rows_per_repo=5)
    fallback_summary = _build_fallback_summary_multi(question, flags, total_indexed_repos, matching_repos)
    prompt = _build_agent_context(
        question=question,
        flags=flags,
        report=report,
        total_indexed_repos=total_indexed_repos,
        matching_repos=matching_repos,
        evidence_by_repo=evidence_by_repo,
    )
    llm = _generate_llm_answer(prompt)
    final_answer = llm.get("answer") or fallback_summary

    # When there are no matches, enforce deterministic output from indexed facts.
    if not matching_repos:
        final_answer = fallback_summary

    llm["answer"] = final_answer

    return {
        "question": question,
        "status": "ok",
        "source": "backend-agent",
        "flags": flags,
        "label": " and ".join(FLAG_LABELS.get(flag, flag) for flag in flags),
        "indexed_repo_count": total_indexed_repos,
        "count": len(matching_repos),
        "answer": final_answer,
        "matching_repositories": matching_repos,
        "evidence_by_repository": evidence_by_repo,
        "llm": llm,
    }
