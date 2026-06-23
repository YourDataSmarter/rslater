"""Shared file and path helpers for AVO export utilities."""

from datetime import date
from datetime import datetime
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_WEBMAP_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "webmaps"
DEFAULT_CHART_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "charts"
DEFAULT_PDF_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "pdf"
DEFAULT_PIE_CHART_OUTPUT_DIR = DEFAULT_CHART_OUTPUT_DIR / "pie"
DEFAULT_BAR_CHART_OUTPUT_DIR = DEFAULT_CHART_OUTPUT_DIR / "bar"
DEFAULT_TABLE_OUTPUT_DIR = DEFAULT_CHART_OUTPUT_DIR / "tables"
DEFAULT_PDF_PIE_OUTPUT_DIR = DEFAULT_PDF_OUTPUT_DIR / "pie"
DEFAULT_PDF_BAR_OUTPUT_DIR = DEFAULT_PDF_OUTPUT_DIR / "bar"
DEFAULT_PDF_TABLE_OUTPUT_DIR = DEFAULT_PDF_OUTPUT_DIR / "tables"
DEFAULT_CSV_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "csv"
SUPPORTED_VISUAL_EXPORT_FORMATS = {"png", "pdf"}

_NON_ALNUM_PATTERN = re.compile(r"[^A-Za-z0-9]+")


def normalize_filename_token(value: str, *, fallback: str = "untitled") -> str:
    """Convert freeform text into a stable snake_case filename token."""
    token = _NON_ALNUM_PATTERN.sub("_", str(value or "").strip()).strip("_").lower()
    return token or fallback


def build_visual_output_path(
    analysis_component: str,
    title: str,
    visual_kind: str,
    *,
    output_dir: str | Path,
    suffix: str,
) -> Path:
    """Build a convention-based output path for a map, graph, or table visual."""
    normalized_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    component_token = normalize_filename_token(analysis_component, fallback="analysis")
    kind_token = normalize_filename_token(visual_kind, fallback="visual")
    filename = f"{component_token}_woodbasket-title_{kind_token}{normalized_suffix}"
    return Path(output_dir).expanduser().resolve() / filename


def build_data_export_output_path(
    component_name: str,
    visual_name: str,
    exported_by: str,
    *,
    export_date: date | datetime | str | None = None,
    output_dir: str | Path,
    suffix: str = ".csv",
) -> Path:
    """Build a convention-based output path for a per-visual data export file."""
    normalized_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    component_token = normalize_filename_token(component_name, fallback="component")
    visual_token = normalize_filename_token(visual_name)
    user_token = normalize_filename_token(exported_by, fallback="user")

    if export_date is None:
        date_token = datetime.now().strftime("%Y%m%d")
    elif isinstance(export_date, datetime):
        date_token = export_date.strftime("%Y%m%d")
    elif isinstance(export_date, date):
        date_token = export_date.strftime("%Y%m%d")
    else:
        raw_date = str(export_date).strip()
        if not raw_date:
            raise ValueError("export_date must be a non-empty string when provided")
        date_token = normalize_filename_token(raw_date, fallback="date")

    filename = (
        f"{component_token}_{visual_token}_{user_token}_{date_token}{normalized_suffix}"
    )
    return Path(output_dir).expanduser().resolve() / filename


def ensure_output_directory(output_path: str) -> Path:
    """Ensure the output directory exists for a target file path.

    :param output_path: Target output file path.
    :type output_path: str
    :returns: Directory path that contains the output file.
    :rtype: Path
    :raises ValueError: If output path is invalid.
    """
    output = normalize_output_path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output.parent


def normalize_visual_export_format(export_format: str | None = None) -> str:
    """Normalize a visual export format and validate it is supported."""
    normalized = str(export_format or "png").strip().lower().lstrip(".")
    if normalized not in SUPPORTED_VISUAL_EXPORT_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_VISUAL_EXPORT_FORMATS))
        raise ValueError(f"unsupported visual export format '{normalized}'; expected one of: {supported}")
    return normalized


def resolve_visual_output_path(
    output_path: str | None,
    *,
    default_output_dir: str | Path,
    default_filename_stem: str,
    analysis_component: str | None = None,
    visual_name: str | None = None,
    visual_kind: str,
    export_format: str | None = None,
) -> tuple[Path, str]:
    """Resolve a visual output path and its export format from args and suffix."""
    requested_format = normalize_visual_export_format(export_format)

    if output_path is None:
        if analysis_component and visual_name:
            output = build_visual_output_path(
                analysis_component,
                visual_name,
                visual_kind,
                output_dir=default_output_dir,
                suffix=f".{requested_format}",
            )
        else:
            output = normalize_output_path(
                str(Path(default_output_dir).expanduser().resolve() / f"{default_filename_stem}.{requested_format}"),
                suffix=f".{requested_format}",
            )
        return output, requested_format

    candidate = normalize_output_path(output_path)
    suffix = candidate.suffix.lower().lstrip(".")
    if suffix:
        resolved_format = normalize_visual_export_format(suffix)
        return candidate, resolved_format

    output = normalize_output_path(str(candidate), suffix=f".{requested_format}")
    return output, requested_format


def normalize_output_path(output_path: str, *, suffix: str | None = None) -> Path:
    """Normalize and optionally enforce an output file suffix.

    :param output_path: Raw output file path.
    :type output_path: str
    :param suffix: Optional file suffix (for example .png or .csv).
    :type suffix: str | None
    :returns: Normalized output file path.
    :rtype: Path
    :raises ValueError: If output path is invalid.
    """
    candidate = (output_path or "").strip()
    if not candidate:
        raise ValueError("output_path must be a non-empty string")

    output = Path(candidate).expanduser().resolve()
    if output.exists() and output.is_dir():
        raise ValueError("output_path must point to a file, not a directory")

    if suffix:
        normalized_suffix = suffix if suffix.startswith(".") else f".{suffix}"
        if output.suffix.lower() != normalized_suffix.lower():
            output = output.with_suffix(normalized_suffix)

    return output
