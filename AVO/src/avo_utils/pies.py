"""Pie chart image export utilities for AVO."""

import importlib
import math
from pathlib import Path
from typing import Any

from .configs import (
    GOV_TRIBAL_COLOR,
    LARGE_LANDOWNER_PIE_LEGEND_NCOL,
    NON_TOP10_COLOR,
    OTHER_SLICE_COLOR,
    PIE_DEFAULT_LEGEND_NCOL_MAX,
    PIE_DEFAULT_LEGEND_Y,
    PIE_DEFAULT_RADIUS,
    PIE_DPI,
    PIE_FIGURE_SIZE,
    PRIVATE_PALETTE,
    TOP_CUSTOMER_PALETTE,
    TOP_CUSTOMER_PIE_LEGEND_Y,
    TOP_CUSTOMER_PIE_RADIUS,
    TOP_DESTINATION_PALETTE,
    TOP_PIE_LEGEND_NCOL,
    TOP_PIE_LEGEND_Y,
    TOP_PIE_RADIUS,
    WEYERHAEUSER_COLOR,
)
from .io import build_visual_output_path
from .io import DEFAULT_PIE_CHART_OUTPUT_DIR
from .io import ensure_output_directory
from .io import resolve_visual_output_path


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


def _build_ranked_label_colors(
    rows: list[dict[str, Any]],
    *,
    label_column: str,
    value_column: str,
    palette: list[str],
    other_label: str = "Other",
    other_color: str = OTHER_SLICE_COLOR,
) -> dict[str, str]:
    """Return deterministic label-color mapping ranked by descending values."""
    ranked_rows = sorted(rows, key=lambda row: float(row[value_column]), reverse=True)
    label_colors: dict[str, str] = {}
    color_index = 0

    for row in ranked_rows:
        label = str(row[label_column]).strip()
        if not label:
            continue
        if label in label_colors:
            continue

        if label.lower() == other_label.lower():
            label_colors[label] = other_color
            continue

        label_colors[label] = palette[color_index % len(palette)]
        color_index += 1

    return label_colors


def generate_pie_chart_png(
    rows: list[dict[str, Any]],
    label_column: str,
    value_column: str,
    output_path: str | None = None,
    *,
    title: str | None = None,
    analysis_component: str | None = None,
    visual_name: str | None = None,
    export_format: str = "png",
    label_colors: dict[str, str] | None = None,
    show_slice_labels: bool = True,
    pie_radius: float = PIE_DEFAULT_RADIUS,
    legend_bbox_y: float = PIE_DEFAULT_LEGEND_Y,
    legend_ncol: int | None = None,
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
    :type output_path: str | None
    :param title: Optional chart title.
    :type title: str | None
    :param analysis_component: Optional component token used for default filename generation.
    :type analysis_component: str | None
    :param visual_name: Optional visual-name token used for default filename generation.
    :type visual_name: str | None
    :param export_format: Visual export format, currently ``png`` or ``pdf``.
    :type export_format: str
    :param label_colors: Optional mapping of label to hex color.
    :type label_colors: dict[str, str] | None
    :param show_slice_labels: Whether to render around-the-pie callout labels.
    :type show_slice_labels: bool
    :param pie_radius: Radius used for pie rendering.
    :type pie_radius: float
    :param legend_bbox_y: Vertical legend anchor (negative values move legend down).
    :type legend_bbox_y: float
    :param legend_ncol: Optional fixed legend column count.
    :type legend_ncol: int | None
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

    output, resolved_format = resolve_visual_output_path(
        output_path,
        default_output_dir=DEFAULT_PIE_CHART_OUTPUT_DIR,
        default_filename_stem="pie_chart",
        analysis_component=analysis_component,
        visual_name=(visual_name or title) if analysis_component else None,
        visual_kind="graph",
        export_format=export_format,
    )
    ensure_output_directory(str(output))

    plt = _get_pyplot_module()

    figure, axis = plt.subplots(figsize=PIE_FIGURE_SIZE, dpi=PIE_DPI)
    try:
        wedges, _ = axis.pie(
            numeric_values,
            labels=None,
            startangle=90,
            counterclock=False,
            colors=pie_colors,
            radius=pie_radius,
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
            bbox_to_anchor=(0.5, legend_bbox_y),
            ncol=legend_ncol if legend_ncol is not None else max(1, min(PIE_DEFAULT_LEGEND_NCOL_MAX, len(labels))),
            frameon=False,
        )

        axis.axis("equal")

        if title:
            axis.set_title(title, pad=2, y=0.97)

        figure.tight_layout()
        figure.savefig(output, format=resolved_format, bbox_inches="tight")

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
            "export_format": resolved_format,
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
    output_path: str | None = None,
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
        analysis_component="large_landowners",
        visual_name="largest_landowners",
        label_colors=label_colors,
        show_slice_labels=False,
        legend_ncol=LARGE_LANDOWNER_PIE_LEGEND_NCOL,
    )


def generate_top_destination_pie_chart_png(
    rows: list[dict[str, Any]],
    output_path: str | None = None,
    *,
    title: str = "MMBF",
    label_column: str = "name",
    value_column: str = "volume",
) -> dict[str, Any]:
    """Generate pie chart PNG for top destination volume data."""
    label_colors = _build_ranked_label_colors(
        rows,
        label_column=label_column,
        value_column=value_column,
        palette=TOP_DESTINATION_PALETTE,
    )

    return generate_pie_chart_png(
        rows=rows,
        label_column=label_column,
        value_column=value_column,
        output_path=output_path,
        title=title,
        analysis_component="top_destination",
        visual_name="top_destination",
        label_colors=label_colors,
        show_slice_labels=False,
        pie_radius=TOP_PIE_RADIUS,
        legend_bbox_y=TOP_PIE_LEGEND_Y,
        legend_ncol=TOP_PIE_LEGEND_NCOL,
    )


def generate_top_customer_pie_chart_png(
    rows: list[dict[str, Any]],
    output_path: str | None = None,
    *,
    title: str = "MMBF",
    label_column: str = "name",
    value_column: str = "volume",
) -> dict[str, Any]:
    """Generate pie chart PNG for top customer volume data."""
    label_colors = _build_ranked_label_colors(
        rows,
        label_column=label_column,
        value_column=value_column,
        palette=TOP_CUSTOMER_PALETTE,
    )

    return generate_pie_chart_png(
        rows=rows,
        label_column=label_column,
        value_column=value_column,
        output_path=output_path,
        title=title,
        analysis_component="top_customer",
        visual_name="top_customer",
        label_colors=label_colors,
        show_slice_labels=False,
        pie_radius=TOP_CUSTOMER_PIE_RADIUS,
        legend_bbox_y=TOP_CUSTOMER_PIE_LEGEND_Y,
        legend_ncol=TOP_PIE_LEGEND_NCOL,
    )
