"""Shared file and path helpers for AVO export utilities."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
DEFAULT_WEBMAP_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "webmaps"
DEFAULT_CHART_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "charts"
DEFAULT_PIE_CHART_OUTPUT_DIR = DEFAULT_CHART_OUTPUT_DIR / "pie"
DEFAULT_BAR_CHART_OUTPUT_DIR = DEFAULT_CHART_OUTPUT_DIR / "bar"
DEFAULT_CSV_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "csv"


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
