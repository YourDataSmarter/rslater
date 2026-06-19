"""Chart compatibility exports for AVO.

New chart implementations live in `pies.py` and `bars.py`.
This module keeps stable imports for existing call sites.
"""

from typing import Any

from .bars import generate_bar_chart_png
from .io import DEFAULT_CHART_OUTPUT_DIR
from .pies import generate_pie_chart_png


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
    chart_type_key = chart_type.strip().lower()

    if chart_type_key == "pie":
        return generate_pie_chart_png(
            rows=data["rows"],
            label_column=data["label_column"],
            value_column=data["value_column"],
            output_path=output_path,
            title=title,
        )

    if chart_type_key == "bar":
        return generate_bar_chart_png(
            rows=data["rows"],
            category_column=data["category_column"],
            series_columns=data["series_columns"],
            output_path=output_path,
            title=title,
            y_label=data.get("y_label"),
            series_labels=data.get("series_labels"),
        )

    raise ValueError(f"unsupported chart_type: {chart_type}")
