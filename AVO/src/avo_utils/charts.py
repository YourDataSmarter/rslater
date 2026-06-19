"""Chart image export utilities for AVO."""

from typing import Any

from .io import (
    DEFAULT_BAR_CHART_OUTPUT_DIR,
    DEFAULT_CHART_OUTPUT_DIR,
    DEFAULT_PIE_CHART_OUTPUT_DIR,
)


def generate_pie_chart_png(
    values: list[float],
    labels: list[str],
    output_path: str = str(DEFAULT_PIE_CHART_OUTPUT_DIR / "pie_chart.png"),
    *,
    title: str | None = None,
) -> dict[str, Any]:
    """Generate a PNG export for a pie chart.

    :param values: Numeric values for chart slices.
    :type values: list[float]
    :param labels: Labels mapped to values.
    :type labels: list[str]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param title: Optional chart title.
    :type title: str | None
    :returns: Metadata about the generated image.
    :rtype: dict[str, Any]
    :raises ValueError: If inputs are invalid.
    """
    pass


def generate_bar_chart_png(
    categories: list[str],
    values: list[float],
    output_path: str = str(DEFAULT_BAR_CHART_OUTPUT_DIR / "bar_chart.png"),
    *,
    title: str | None = None,
) -> dict[str, Any]:
    """Generate a PNG export for a bar chart.

    :param categories: Category labels for the x-axis.
    :type categories: list[str]
    :param values: Numeric values for each category.
    :type values: list[float]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param title: Optional chart title.
    :type title: str | None
    :returns: Metadata about the generated image.
    :rtype: dict[str, Any]
    :raises ValueError: If inputs are invalid.
    """
    pass


def generate_chart_png(
    chart_type: str,
    data: dict[str, Any],
    output_path: str = str(DEFAULT_CHART_OUTPUT_DIR / "chart.png"),
    *,
    title: str | None = None,
) -> dict[str, Any]:
    """Generate a PNG export for a supported chart type.

    :param chart_type: Chart type identifier (for example pie or bar).
    :type chart_type: str
    :param data: Chart payload used by the selected chart type.
    :type data: dict[str, Any]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param title: Optional chart title.
    :type title: str | None
    :returns: Metadata about the generated image.
    :rtype: dict[str, Any]
    :raises ValueError: If chart type or inputs are invalid.
    """
    pass
