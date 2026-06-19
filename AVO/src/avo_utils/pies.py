"""Pie chart image export utilities for AVO."""

import importlib
import math
from pathlib import Path
from typing import Any

from .io import DEFAULT_PIE_CHART_OUTPUT_DIR


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


def generate_pie_chart_png(
    rows: list[dict[str, Any]],
    label_column: str,
    value_column: str,
    output_path: str = str(DEFAULT_PIE_CHART_OUTPUT_DIR / "pie_chart.png"),
    *,
    title: str | None = None,
) -> dict[str, Any]:
    """Generate a PNG export for a pie chart from SQL row data.

    Rows with the same label are aggregated by summing their values.

    :param rows: SQL rows as a list of dicts, one dict per row.
    :type rows: list[dict[str, Any]]
    :param label_column: Column name to use as pie slice labels.
    :type label_column: str
    :param value_column: Column name to use as pie slice values.
    :type value_column: str
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param title: Optional chart title.
    :type title: str | None
    :returns: Metadata about the generated image.
    :rtype: dict[str, Any]
    :raises ValueError: If inputs are invalid or columns are missing.
    :raises ImportError: If matplotlib is not installed.
    """
    if not rows:
        raise ValueError("rows must contain at least one item")

    missing_label = [i for i, row in enumerate(rows) if label_column not in row]
    if missing_label:
        raise ValueError(
            f"label_column '{label_column}' missing in rows at index: {missing_label}"
        )

    missing_value = [i for i, row in enumerate(rows) if value_column not in row]
    if missing_value:
        raise ValueError(
            f"value_column '{value_column}' missing in rows at index: {missing_value}"
        )

    aggregated: dict[str, float] = {}
    for row in rows:
        label = str(row[label_column]).strip()
        if not label:
            raise ValueError(f"label_column '{label_column}' contains an empty value")
        value = float(row[value_column])
        if value < 0:
            raise ValueError(
                f"value_column '{value_column}' contains a negative value: {value}"
            )
        aggregated[label] = aggregated.get(label, 0.0) + value

    total = sum(aggregated.values())
    if total <= 0:
        raise ValueError("sum of values must be greater than zero")

    labels = list(aggregated.keys())
    numeric_values = list(aggregated.values())

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    plt = _get_pyplot_module()

    figure, axis = plt.subplots(figsize=(8, 8), dpi=150)
    try:
        wedges, _ = axis.pie(
            numeric_values,
            labels=None,
            startangle=90,
            counterclock=False,
        )

        for wedge, label, value in zip(wedges, labels, numeric_values):
            percentage = (value / total) * 100.0
            value_text = f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
            angle = (wedge.theta1 + wedge.theta2) / 2.0
            angle_rad = math.radians(angle)

            x = math.cos(angle_rad)
            y = math.sin(angle_rad)
            text_x = 1.22 * (1 if x >= 0 else -1)
            text_y = 1.08 * y
            horizontal_alignment = "left" if x >= 0 else "right"

            axis.annotate(
                f"{label}: {value_text} ({percentage:.1f}%)",
                xy=(1.02 * x, 1.02 * y),
                xytext=(text_x, text_y),
                ha=horizontal_alignment,
                va="center",
                zorder=3,
                arrowprops={
                    "arrowstyle": "-",
                    "color": "black",
                    "linewidth": 1.0,
                    "connectionstyle": "angle,angleA=0,angleB=90,rad=0",
                    "shrinkA": 0,
                    "shrinkB": 0,
                    "zorder": 1,
                },
            )

        axis.legend(
            wedges,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.02),
            ncol=max(1, min(3, len(labels))),
            frameon=False,
        )

        axis.axis("equal")

        if title:
            axis.set_title(title, pad=2, y=0.97)

        figure.tight_layout()
        figure.savefig(output, format="png", bbox_inches="tight")

        width_px = int(figure.get_size_inches()[0] * figure.dpi)
        height_px = int(figure.get_size_inches()[1] * figure.dpi)

        return {
            "output_path": str(output),
            "label_count": len(labels),
            "value_total": total,
            "width_px": width_px,
            "height_px": height_px,
            "title": title,
        }
    finally:
        plt.close(figure)
