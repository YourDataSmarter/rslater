"""Bar chart image export utilities for AVO."""

import importlib
from pathlib import Path
from typing import Any

from .configs import (
    GOV_TRIBAL_COLOR,
    NON_TOP10_COLOR,
    PRIVATE_PALETTE,
    WEYERHAEUSER_COLOR,
)
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
    stacked: bool = False,
    series_colors: list[str] | None = None,
    y_divisor: float = 1.0,
) -> dict[str, Any]:
    """Generate a grouped or stacked bar chart PNG from row data.

    :param rows: Source rows for the chart.
    :type rows: list[dict[str, Any]]
    :param category_column: Column used for x-axis categories.
    :type category_column: str
    :param series_columns: Numeric columns to plot as bars.
    :type series_columns: list[str]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param title: Optional chart title.
    :type title: str | None
    :param y_label: Optional y-axis label.
    :type y_label: str | None
    :param series_labels: Optional display-name mapping for series keys.
    :type series_labels: dict[str, str] | None
    :param stacked: Render as stacked bars rather than grouped.
    :type stacked: bool
    :param series_colors: Optional hex color strings per series in order.
    :type series_colors: list[str] | None
    :param y_divisor: Divide all values by this factor before plotting.
    :type y_divisor: float
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

        if stacked:
            bottoms = [0.0] * len(categories)
            for index, series_key in enumerate(series_columns):
                display_name = (
                    series_labels.get(series_key, series_key.replace("_", " ").title())
                    if series_labels
                    else series_key.replace("_", " ").title()
                )
                display_values = [v / y_divisor for v in series_values[series_key]]
                color = (
                    series_colors[index]
                    if series_colors and index < len(series_colors)
                    else None
                )
                bar_kwargs: dict[str, Any] = {
                    "width": 0.6,
                    "label": display_name,
                    "bottom": bottoms,
                }
                if color:
                    bar_kwargs["color"] = color
                axis.bar(x_positions, display_values, **bar_kwargs)
                bottoms = [b + v for b, v in zip(bottoms, display_values)]
        else:
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
                display_values = [v / y_divisor for v in series_values[series_key]]
                color = (
                    series_colors[index]
                    if series_colors and index < len(series_colors)
                    else None
                )
                bar_kwargs = {"width": per_bar_width * 0.95, "label": display_name}
                if color:
                    bar_kwargs["color"] = color
                axis.bar(bar_positions, display_values, **bar_kwargs)

        axis.set_xticks(x_positions)
        axis.set_xticklabels(categories, rotation=0, ha="center")
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


def _build_large_landowner_global_color_map(
    rows: list[dict[str, Any]],
    *,
    name_column: str,
    type_column: str,
    total_column: str,
    top_n: int = 10,
) -> dict[str, str]:
    """Build owner-to-color mapping using the same top-10 rules as the pie chart."""
    sorted_rows = sorted(rows, key=lambda row: float(row[total_column]), reverse=True)
    top_rows = sorted_rows[:top_n]

    color_map: dict[str, str] = {}
    private_palette_index = 0
    for row in top_rows:
        owner_name = str(row[name_column])
        owner_type = str(row.get(type_column, "")).strip()

        if owner_type == "WY":
            color_map[owner_name] = WEYERHAEUSER_COLOR
        elif owner_type == "Gov/Tribal":
            color_map[owner_name] = GOV_TRIBAL_COLOR
        else:
            color = PRIVATE_PALETTE[private_palette_index % len(PRIVATE_PALETTE)]
            color_map[owner_name] = color
            private_palette_index += 1

    return color_map


def build_large_landowner_bar_data(
    rows: list[dict[str, Any]],
    *,
    name_column: str = "name",
    type_column: str = "type",
    total_column: str = "total_acres",
    woodbasket_column: str = "woodbasket_acres",
    category_column: str = "woodbasket",
    top_private_per_woodbasket: int = 5,
    include_weyerhaeuser: bool = True,
    include_gov_tribal: bool = False,
) -> tuple[list[dict[str, Any]], list[str], dict[str, str], list[str]]:
    """Build grouped-bar payload for large landowners by woodbasket.

    :param rows: Raw landowner rows with nested ``woodbasket_acres`` values.
    :type rows: list[dict[str, Any]]
    :param name_column: Owner name column.
    :type name_column: str
    :param type_column: Owner type column.
    :type type_column: str
    :param total_column: Owner total acres column.
    :type total_column: str
    :param woodbasket_column: Column containing per-woodbasket acre dict.
    :type woodbasket_column: str
    :param category_column: Output category column name.
    :type category_column: str
    :param top_private_per_woodbasket: Number of private owners to keep per woodbasket.
    :type top_private_per_woodbasket: int
    :param include_weyerhaeuser: Whether to include WY series.
    :type include_weyerhaeuser: bool
    :param include_gov_tribal: Whether to include Gov/Tribal series.
    :type include_gov_tribal: bool
    :returns: Tuple of row payload, series keys, labels mapping, and series colors.
    :rtype: tuple[list[dict[str, Any]], list[str], dict[str, str], list[str]]
    """
    if not rows:
        raise ValueError("rows must contain at least one item")

    if top_private_per_woodbasket < 1:
        raise ValueError("top_private_per_woodbasket must be at least 1")

    missing_names = [i for i, row in enumerate(rows) if name_column not in row]
    if missing_names:
        raise ValueError(
            f"name_column '{name_column}' missing in rows at index: {missing_names}"
        )

    missing_totals = [i for i, row in enumerate(rows) if total_column not in row]
    if missing_totals:
        raise ValueError(
            f"total_column '{total_column}' missing in rows at index: {missing_totals}"
        )

    missing_woodbaskets = [i for i, row in enumerate(rows) if woodbasket_column not in row]
    if missing_woodbaskets:
        raise ValueError(
            f"woodbasket_column '{woodbasket_column}' missing in rows at index: {missing_woodbaskets}"
        )

    owner_rows: dict[str, dict[str, Any]] = {str(row[name_column]): row for row in rows}
    first_woodbasket_dict = rows[0][woodbasket_column]
    if not isinstance(first_woodbasket_dict, dict):
        raise ValueError(f"woodbasket_column '{woodbasket_column}' must contain dict values")

    woodbasket_names = list(first_woodbasket_dict.keys())

    selected_private_names: list[str] = []
    for woodbasket_name in woodbasket_names:
        private_candidates: list[tuple[str, float]] = []
        for row in rows:
            owner_name = str(row[name_column])
            owner_type = str(row.get(type_column, "")).strip()
            if owner_type in {"WY", "Gov/Tribal"}:
                continue

            wb_values = row.get(woodbasket_column, {})
            if not isinstance(wb_values, dict):
                continue
            acres = float(wb_values.get(woodbasket_name, 0.0))
            if acres > 0:
                private_candidates.append((owner_name, acres))

        private_candidates.sort(key=lambda item: item[1], reverse=True)
        for owner_name, _ in private_candidates[:top_private_per_woodbasket]:
            if owner_name not in selected_private_names:
                selected_private_names.append(owner_name)

    series_names: list[str] = []
    if include_weyerhaeuser:
        wy_name = next(
            (str(row[name_column]) for row in rows if str(row.get(type_column, "")).strip() == "WY"),
            None,
        )
        if wy_name:
            series_names.append(wy_name)

    if include_gov_tribal:
        gov_name = next(
            (
                str(row[name_column])
                for row in rows
                if str(row.get(type_column, "")).strip() == "Gov/Tribal"
            ),
            None,
        )
        if gov_name:
            series_names.append(gov_name)

    series_names.extend(selected_private_names)

    chart_rows: list[dict[str, Any]] = []
    for woodbasket_name in woodbasket_names:
        chart_row: dict[str, Any] = {category_column: woodbasket_name}
        for owner_name in series_names:
            owner_row = owner_rows[owner_name]
            wb_values = owner_row.get(woodbasket_column, {})
            chart_row[owner_name] = float(wb_values.get(woodbasket_name, 0.0))
        chart_rows.append(chart_row)

    series_labels = {name: name for name in series_names}

    global_color_map = _build_large_landowner_global_color_map(
        rows,
        name_column=name_column,
        type_column=type_column,
        total_column=total_column,
    )
    series_colors = [global_color_map.get(name, NON_TOP10_COLOR) for name in series_names]

    return chart_rows, series_names, series_labels, series_colors


def generate_large_landowner_bar_chart_png(
    rows: list[dict[str, Any]],
    output_path: str = str(DEFAULT_BAR_CHART_OUTPUT_DIR / "large_landowners_bar_chart.png"),
    *,
    title: str = "Top Five Private Landowners per Woodbasket",
    top_private_per_woodbasket: int = 5,
    include_weyerhaeuser: bool = True,
    include_gov_tribal: bool = False,
) -> dict[str, Any]:
    """Generate grouped large-landowner bar chart PNG with pie-consistent colors."""
    chart_rows, series_columns, series_labels, series_colors = build_large_landowner_bar_data(
        rows,
        top_private_per_woodbasket=top_private_per_woodbasket,
        include_weyerhaeuser=include_weyerhaeuser,
        include_gov_tribal=include_gov_tribal,
    )

    return generate_bar_chart_png(
        rows=chart_rows,
        category_column="woodbasket",
        series_columns=series_columns,
        output_path=output_path,
        title=title,
        y_label="Thousands of Acres",
        series_labels=series_labels,
        stacked=False,
        series_colors=series_colors,
        y_divisor=1000,
    )
