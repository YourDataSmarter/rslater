"""Pie chart image export utilities for AVO."""

import importlib
import math
from pathlib import Path
from typing import Any

from .configs import (
    GOV_TRIBAL_COLOR,
    NON_TOP10_COLOR,
    PRIVATE_PALETTE,
    WEYERHAEUSER_COLOR,
)
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
    label_colors: dict[str, str] | None = None,
    show_slice_labels: bool = True,
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
    :param label_colors: Optional mapping of label to hex color.
    :type label_colors: dict[str, str] | None
    :param show_slice_labels: Whether to render around-the-pie callout labels.
    :type show_slice_labels: bool
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

    pie_colors: list[str] | None = None
    if label_colors and all(label in label_colors for label in labels):
        pie_colors = [label_colors[label] for label in labels]

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
            colors=pie_colors,
        )

        if show_slice_labels:
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
            "labels": labels,
            "width_px": width_px,
            "height_px": height_px,
            "title": title,
        }
    finally:
        plt.close(figure)


def build_large_landowner_pie_rows(
    rows: list[dict[str, Any]],
    *,
    name_column: str = "name",
    type_column: str = "type",
    total_column: str = "total_acres",
    top_n: int = 10,
    other_label: str = "Other",
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Build top-N plus Other rows and color mapping for landowner pie charts.

    :param rows: Raw landowner rows.
    :type rows: list[dict[str, Any]]
    :param name_column: Column containing owner display names.
    :type name_column: str
    :param type_column: Column containing owner type values.
    :type type_column: str
    :param total_column: Column containing total acres values.
    :type total_column: str
    :param top_n: Number of largest owners to show before grouping remainder.
    :type top_n: int
    :param other_label: Label for grouped non-top owners.
    :type other_label: str
    :returns: Tuple of pie rows and label-to-color mapping.
    :rtype: tuple[list[dict[str, Any]], dict[str, str]]
    """
    if not rows:
        raise ValueError("rows must contain at least one item")

    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    missing_name = [i for i, row in enumerate(rows) if name_column not in row]
    if missing_name:
        raise ValueError(
            f"name_column '{name_column}' missing in rows at index: {missing_name}"
        )

    missing_total = [i for i, row in enumerate(rows) if total_column not in row]
    if missing_total:
        raise ValueError(
            f"total_column '{total_column}' missing in rows at index: {missing_total}"
        )

    sorted_rows = sorted(rows, key=lambda row: float(row[total_column]), reverse=True)
    top_rows = sorted_rows[:top_n]
    remainder_rows = sorted_rows[top_n:]

    pie_rows = [
        {name_column: str(row[name_column]), total_column: float(row[total_column])}
        for row in top_rows
    ]

    remainder_total = sum(float(row[total_column]) for row in remainder_rows)
    if remainder_total > 0:
        pie_rows.append({name_column: other_label, total_column: remainder_total})

    label_colors: dict[str, str] = {}
    private_palette_index = 0
    for row in top_rows:
        owner_name = str(row[name_column])
        owner_type = str(row.get(type_column, "")).strip()

        if owner_type == "WY":
            label_colors[owner_name] = WEYERHAEUSER_COLOR
        elif owner_type == "Gov/Tribal":
            label_colors[owner_name] = GOV_TRIBAL_COLOR
        else:
            color = PRIVATE_PALETTE[private_palette_index % len(PRIVATE_PALETTE)]
            label_colors[owner_name] = color
            private_palette_index += 1

    if remainder_total > 0:
        label_colors[other_label] = NON_TOP10_COLOR

    return pie_rows, label_colors


def generate_large_landowner_pie_chart_png(
    rows: list[dict[str, Any]],
    output_path: str = str(DEFAULT_PIE_CHART_OUTPUT_DIR / "large_landowners_pie_chart.png"),
    *,
    title: str = "Largest Landowners (ac.)",
    name_column: str = "name",
    type_column: str = "type",
    total_column: str = "total_acres",
    top_n: int = 10,
    other_label: str = "Other",
) -> dict[str, Any]:
    """Generate large-landowner pie chart PNG with top-N and color mapping.

    :param rows: Raw landowner rows.
    :type rows: list[dict[str, Any]]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param title: Chart title text.
    :type title: str
    :param name_column: Column containing owner display names.
    :type name_column: str
    :param type_column: Column containing owner type values.
    :type type_column: str
    :param total_column: Column containing total acres values.
    :type total_column: str
    :param top_n: Number of largest owners to show before grouping remainder.
    :type top_n: int
    :param other_label: Label for grouped non-top owners.
    :type other_label: str
    :returns: Metadata about the generated pie chart.
    :rtype: dict[str, Any]
    """
    pie_rows, label_colors = build_large_landowner_pie_rows(
        rows,
        name_column=name_column,
        type_column=type_column,
        total_column=total_column,
        top_n=top_n,
        other_label=other_label,
    )

    return generate_pie_chart_png(
        rows=pie_rows,
        label_column=name_column,
        value_column=total_column,
        output_path=output_path,
        title=title,
        label_colors=label_colors,
        show_slice_labels=False,
    )
