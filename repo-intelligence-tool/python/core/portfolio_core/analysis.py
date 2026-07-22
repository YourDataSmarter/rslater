from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .constants import (
    CSS_IMPORT_PATTERN,
    CONFIG_FILES,
    IGNORE_DIRS,
    JS_TS_EXTENSIONS,
    MAP_UI_WIRING_PATTERN,
    REACT_DEPENDENCIES,
    REACT_IMPORT_PATTERN,
    ESRI_DEPENDENCIES,
    ESRI_IMPORT_PATTERN,
    SOURCE_EXTENSIONS,
    STYLE_EXTENSIONS,
    TYPESCRIPT_DEPENDENCIES,
    WIDGET_NAME_PATTERN,
    WIDGET_PATH_HINTS,
)


def safe_read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        data = path.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8", errors="ignore")
    except OSError:
        return ""


def init_technology_detection() -> dict[str, Any]:
    return {
        "flags": {
            "uses_react": False,
            "uses_typescript": False,
            "uses_esri_js_api": False,
            "has_custom_esri_webmap_widgets": False,
            "uses_css": False,
        },
        "evidence": {
            "uses_react": [],
            "uses_typescript": [],
            "uses_esri_js_api": [],
            "has_custom_esri_webmap_widgets": [],
            "uses_css": [],
        },
        "confidence": "low",
    }


def first_matching_line(text: str, pattern: re.Pattern[str]) -> str | None:
    for line in text.splitlines():
        if pattern.search(line):
            return line.strip()[:200]
    return None


def add_tech_evidence(
    technology: dict[str, Any],
    flag: str,
    rule_id: str,
    file_path: str,
    reason: str,
    snippet: str | None = None,
) -> None:
    if len(technology["evidence"][flag]) >= 100:
        return

    entry: dict[str, Any] = {
        "rule_id": rule_id,
        "path": file_path,
        "reason": reason,
    }
    if snippet:
        entry["snippet"] = snippet

    technology["flags"][flag] = True
    technology["evidence"][flag].append(entry)


def detect_package_json_signals(rel_path: str, text: str, technology: dict[str, Any]) -> None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return

    if not isinstance(payload, dict):
        return

    dependencies = payload.get("dependencies", {})
    dev_dependencies = payload.get("devDependencies", {})
    dep_keys = set()

    if isinstance(dependencies, dict):
        dep_keys.update(k.lower() for k in dependencies.keys())
    if isinstance(dev_dependencies, dict):
        dep_keys.update(k.lower() for k in dev_dependencies.keys())

    for dep in sorted(dep_keys):
        if dep in REACT_DEPENDENCIES:
            add_tech_evidence(
                technology,
                "uses_react",
                "react.pkg.dependency",
                rel_path,
                f"package.json declares dependency {dep}",
                snippet=f"dependency: {dep}",
            )
        if dep in ESRI_DEPENDENCIES:
            add_tech_evidence(
                technology,
                "uses_esri_js_api",
                "esri.pkg.dependency",
                rel_path,
                f"package.json declares dependency {dep}",
                snippet=f"dependency: {dep}",
            )
        if dep in TYPESCRIPT_DEPENDENCIES:
            add_tech_evidence(
                technology,
                "uses_typescript",
                "typescript.pkg.dependency",
                rel_path,
                f"package.json declares dependency {dep}",
                snippet=f"dependency: {dep}",
            )


def detect_source_signals(
    rel_path: str,
    file_path: Path,
    text: str,
    technology: dict[str, Any],
    widget_candidates: list[dict[str, Any]],
) -> None:
    ext = file_path.suffix.lower()
    rel_lower = rel_path.lower()

    if ext in STYLE_EXTENSIONS:
        add_tech_evidence(
            technology,
            "uses_css",
            "css.file.extension",
            rel_path,
            f"Stylesheet file extension detected ({ext})",
        )

    if ext in {".ts", ".tsx"}:
        add_tech_evidence(
            technology,
            "uses_typescript",
            "typescript.file.extension",
            rel_path,
            f"TypeScript source file extension detected ({ext})",
        )

    if ext in JS_TS_EXTENSIONS:
        css_import_line = first_matching_line(text, CSS_IMPORT_PATTERN)
        if css_import_line:
            add_tech_evidence(
                technology,
                "uses_css",
                "css.import",
                rel_path,
                "Stylesheet import detected in source",
                snippet=css_import_line,
            )

        react_line = first_matching_line(text, REACT_IMPORT_PATTERN)
        if react_line:
            add_tech_evidence(
                technology,
                "uses_react",
                "react.import",
                rel_path,
                "React import detected in source",
                snippet=react_line,
            )

        esri_line = first_matching_line(text, ESRI_IMPORT_PATTERN)
        if esri_line:
            add_tech_evidence(
                technology,
                "uses_esri_js_api",
                "esri.import",
                rel_path,
                "Esri import/reference detected in source",
                snippet=esri_line,
            )

        has_widget_path_hint = any(hint in rel_lower for hint in WIDGET_PATH_HINTS)
        has_widget_name_hint = bool(WIDGET_NAME_PATTERN.search(rel_lower) or WIDGET_NAME_PATTERN.search(text))
        has_map_ui_wiring = bool(MAP_UI_WIRING_PATTERN.search(text))

        if (has_widget_path_hint or has_widget_name_hint) and has_map_ui_wiring:
            widget_line = first_matching_line(text, MAP_UI_WIRING_PATTERN)
            widget_candidates.append(
                {
                    "rule_id": "esri.widget.custom.candidate",
                    "path": rel_path,
                    "reason": "Map UI wiring with custom widget/component naming or path hints",
                    "snippet": widget_line,
                }
            )


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
            dependencies = content.get("dependencies", {}) if isinstance(content, dict) else {}
            dev_dependencies = content.get("devDependencies", {}) if isinstance(content, dict) else {}
            parsed["dependencies_count"] = len(dependencies) if isinstance(dependencies, dict) else 0
            parsed["dev_dependencies_count"] = len(dev_dependencies) if isinstance(dev_dependencies, dict) else 0
            parsed["dependency_names"] = sorted(dependencies.keys()) if isinstance(dependencies, dict) else []
            parsed["dev_dependency_names"] = (
                sorted(dev_dependencies.keys()) if isinstance(dev_dependencies, dict) else []
            )
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
    elif ext == ".go":
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
    technology = init_technology_detection()
    widget_candidates: list[dict[str, Any]] = []

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
                parsed_config = parse_config_file(file_path)
                config_summaries.append(parsed_config)

                if filename == "package.json":
                    detect_package_json_signals(rel_path, safe_read_text(file_path), technology)
                elif filename == "tsconfig.json":
                    add_tech_evidence(
                        technology,
                        "uses_typescript",
                        "typescript.config.tsconfig",
                        rel_path,
                        "tsconfig.json detected",
                    )

            if file_path.suffix.lower() in SOURCE_EXTENSIONS:
                text = safe_read_text(file_path)
                source_file_metrics.append(source_metrics_for_file(file_path, rel_path))
                detect_source_signals(
                    rel_path=rel_path,
                    file_path=file_path,
                    text=text,
                    technology=technology,
                    widget_candidates=widget_candidates,
                )

    if technology["flags"]["uses_esri_js_api"]:
        for candidate in widget_candidates:
            add_tech_evidence(
                technology,
                "has_custom_esri_webmap_widgets",
                candidate["rule_id"],
                candidate["path"],
                candidate["reason"],
                candidate.get("snippet"),
            )

    if source_file_metrics:
        technology["confidence"] = "high"
    elif config_summaries:
        technology["confidence"] = "medium"

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
        "technology": technology,
    }
