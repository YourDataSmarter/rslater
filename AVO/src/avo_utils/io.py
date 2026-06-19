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
    pass


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
    pass
