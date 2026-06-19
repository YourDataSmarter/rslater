"""Bar chart image export utilities for AVO."""

import importlib
from pathlib import Path
from typing import Any

from .io import DEFAULT_BAR_CHART_OUTPUT_DIR


def _get_pyplot_module() -> Any:
    """Return matplotlib.pyplot configured for headless PNG rendering."""
    try:
        matplotlib = importlib.import_module("matplotlib")
    except ModuleNotFoundError as exc:
        raise ImportError(
            "matplotlib is required to generate chart PNG files"
        ) from exc

    backend_name = str(matplotlib.get_backend()).lower()
    if backend_name != "agg":
        matplotlib.use("Agg", force=True)

    try:
        return importlib.import_module("matplotlib.pyplot")
    except ModuleNotFoundError as exc:
        raise ImportError(
            "matplotlib is required to generate chart PNG files"
        ) from exc


def generate_bar_chart_png(
    rows: list[dict[str, Any]],
    category_column: str,
    series_columns: list[str],
    output_path: str = str(DEFAULT_BAR_CHART_OUTPUT_DIR / "bar_chart.png"),
    *,
    title: str | None = None,
    y_label: str | None = None,
    series_labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Generate a grouped bar chart PNG from row data.

    :param rows: Source rows for the chart.
    :type rows: list[dict[str, Any]]
    :param category_column: Column used for x-axis categories.
    :type category_column: str
    :param series_columns: Numeric columns to plot as grouped bars.
    :type series_columns: list[str]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param title: Optional chart title.
    :type title: str | None
    :param y_label: Optional y-axis label.
    :type y_label: str | None
    :param series_labels: Optional display-name mapping for series keys.
    :type series_labels: dict[str, str] | None
    :returns: Metadata about the generated image.
    :rtype: dict[str, Any]
    :raises ValueError: If inputs are invalid.
    :raises ImportError: If matplotlib is not installed.
    """
    if not rows:
        raise ValueError("rows must contain at least one item")

    if not series_columns:
        raise ValueError("series_columns must contain at least one column")

    missing_category = [i for i, row in enumerate(rows) if category_column not in row]
    if missing_category:
        raise ValueError(
            f"category_column '{category_column}' missing in rows at index: {missing_category}"
        )

    missing_series: dict[str, list[int]] = {}
    for series_key in series_columns:
        missing_indexes = [i for i, row in enumerate(rows) if series_key not in row]
        if missing_indexes:
            missing_series[series_key] = missing_indexes

    if missing_series:
        raise ValueError(f"series columns missing in rows: {missing_series}")

    categories: list[str] = []
    series_values: dict[str, list[float]] = {key: [] for key in series_columns}
    for row in rows:
        category = str(row[category_column]).strip()
        if not category:
            raise ValueError(
                f"category_column '{category_column}' contains an empty value"
            )
        categories.append(category)

        for series_key in series_columns:
            value = float(row[series_key])
            if value < 0:
                raise ValueError(
                    f"series column '{series_key}' contains a negative value: {value}"
                )
            series_values[series_key].append(value)

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    plt = _get_pyplot_module()

    figure, axis = plt.subplots(figsize=(11, 6), dpi=150)
    try:
        x_positions = list(range(len(categories)))
        bar_group_width = 0.8
        per_bar_width = bar_group_width / len(series_columns)

        for index, series_key in enumerate(series_columns):
            offset = (index - (len(series_columns) - 1) / 2) * per_bar_width
            bar_positions = [x + offset for x in x_positions]
            display_name = (
                series_labels.get(series_key, series_key.replace("_", " ").title())
                if series_labels
                else series_key.replace("_", " ").title()
            )
            axis.bar(
                bar_positions,
                series_values[series_key],
                width=per_bar_width * 0.95,
                label=display_name,
            )

        axis.set_xticks(x_positions)
        axis.set_xticklabels(categories, rotation=20, ha="right")
        axis.legend(loc="upper right")
        axis.grid(axis="y", linestyle="--", alpha=0.35)

        if title:
            axis.set_title(title)
        if y_label:
            axis.set_ylabel(y_label)

        figure.tight_layout()
        figure.savefig(output, format="png", bbox_inches="tight")

        width_px = int(figure.get_size_inches()[0] * figure.dpi)
        height_px = int(figure.get_size_inches()[1] * figure.dpi)
        series_totals = {
            key: sum(series_values[key]) for key in series_columns
        }

        return {
            "output_path": str(output),
            "category_count": len(categories),
            "series_count": len(series_columns),
            "series_totals": series_totals,
            "width_px": width_px,
            "height_px": height_px,
            "title": title,
        }
    finally:
        plt.close(figure)
