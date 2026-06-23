"""Table image export utilities for AVO."""

import importlib
from pathlib import Path
from typing import Any

from .configs import (
    DEFAULT_TABLE_DPI,
    DEFAULT_TABLE_EDGE_COLOR,
    DEFAULT_TABLE_FONT_SIZE,
    DEFAULT_TABLE_HEADER_BACKGROUND,
    DEFAULT_TABLE_LINE_WIDTH,
    DEFAULT_TABLE_SCALE_Y,
    DEFAULT_TABLE_SUMMARY_BACKGROUND,
    DEFAULT_TABLE_SUMMARY_TEXT_COLOR,
    DELIVERY_BY_AREA_TABLE_FIGURE_WIDTH,
    DELIVERY_BY_AREA_TABLE_FIRST_COLUMN_WIDTH,
    DELIVERY_BY_AREA_TABLE_REMAINING_WIDTH,
    DELIVERY_BY_AREA_TABLE_ROW_BACKGROUND_COLORS,
    DELIVERY_BY_AREA_TABLE_ROW_TEXT_COLORS,
    LARGE_LANDOWNER_TABLE_COLUMNS,
    LARGE_LANDOWNER_TABLE_COLUMN_WIDTHS,
    LARGE_LANDOWNER_TABLE_FIGURE_WIDTH,
    LARGE_LANDOWNER_TABLE_NUMERIC_COLUMNS,
    LARGE_LANDOWNER_TABLE_TITLE,
    MILL_CONSUMPTION_CHANGE_SUFFIXES,
    MILL_CONSUMPTION_ROW_STYLES,
    MILL_CONSUMPTION_TABLE_COLUMN_WIDTHS,
    MILL_CONSUMPTION_TABLE_COLUMN_WIDTHS_WITH_PREV,
    MILL_CONSUMPTION_TABLE_FIGURE_WIDTH,
    MILL_CONSUMPTION_YEAR_LABELS,
)
from .io import build_visual_output_path
from .io import DEFAULT_CHART_OUTPUT_DIR
from .io import DEFAULT_TABLE_OUTPUT_DIR
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


def _format_cell_value(value: Any, is_numeric: bool) -> str:
    """Format a value for table rendering."""
    if value is None:
        return ""

    if is_numeric:
        number = float(value)
        if number.is_integer():
            return f"{number:,.0f}"
        return f"{number:,.2f}"

    return str(value)


def build_group_sum_summary_rows(
    rows: list[dict[str, Any]],
    *,
    group_column: str,
    summary_groups: list[str],
    label_column: str,
    sum_columns: list[str],
    label_prefix: str = "Total ",
) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    """Build summary rows by summing numeric columns for target groups.

    :param rows: Source data rows.
    :type rows: list[dict[str, Any]]
    :param group_column: Column used to filter rows into groups.
    :type group_column: str
    :param summary_groups: Group names to aggregate.
    :type summary_groups: list[str]
    :param label_column: Column to place the summary label into.
    :type label_column: str
    :param sum_columns: Numeric columns to sum.
    :type sum_columns: list[str]
    :param label_prefix: Prefix for generated summary labels.
    :type label_prefix: str
    :returns: Tuple of summary rows and totals metadata.
    :rtype: tuple[list[dict[str, Any]], dict[str, dict[str, float]]]
    """
    summary_rows: list[dict[str, Any]] = []
    summary_totals: dict[str, dict[str, float]] = {}

    for group_name in summary_groups:
        matching_rows = [
            row
            for row in rows
            if str(row.get(group_column, "")).strip().lower()
            == group_name.strip().lower()
        ]

        totals = {
            column: sum(float(row.get(column, 0.0)) for row in matching_rows)
            for column in sum_columns
        }
        summary_totals[group_name] = totals

        summary_row: dict[str, Any] = {label_column: f"{label_prefix}{group_name}"}
        summary_row.update(totals)
        summary_rows.append(summary_row)

    return summary_rows, summary_totals


def build_cover_type_summary_rows(
    rows: list[dict[str, Any]],
    *,
    cover_type_column: str = "broad_cover_type",
    label_column: str = "business",
    total_stand_column: str = "total_stand_acres",
    net_productive_column: str = "net_productive_acres",
    harvestable_column: str = "harvestable_acres",
) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    """Build summary rows for the Doug Fir / White Wood edge case table.

    :param rows: Source data rows.
    :type rows: list[dict[str, Any]]
    :param cover_type_column: Cover type column name.
    :type cover_type_column: str
    :param label_column: Column to place summary labels into.
    :type label_column: str
    :param total_stand_column: Total stand acres column.
    :type total_stand_column: str
    :param net_productive_column: Net productive acres column.
    :type net_productive_column: str
    :param harvestable_column: Harvestable acres column.
    :type harvestable_column: str
    :returns: Tuple of summary rows and totals metadata.
    :rtype: tuple[list[dict[str, Any]], dict[str, dict[str, float]]]
    """
    return build_group_sum_summary_rows(
        rows,
        group_column=cover_type_column,
        summary_groups=["Doug Fir", "White Wood"],
        label_column=label_column,
        sum_columns=[
            total_stand_column,
            net_productive_column,
            harvestable_column,
        ],
        label_prefix="Total ",
    )


def build_grand_total_row(
    rows: list[dict[str, Any]],
    *,
    sum_columns: list[str],
    label_column: str,
    label: str = "Total",
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """Build a single grand-total summary row by summing all rows.

    :param rows: Source data rows.
    :type rows: list[dict[str, Any]]
    :param sum_columns: Numeric columns to sum across all rows.
    :type sum_columns: list[str]
    :param label_column: Column to place the total label into.
    :type label_column: str
    :param label: Text for the total row label.
    :type label: str
    :returns: Tuple of a single-item summary row list and totals metadata.
    :rtype: tuple[list[dict[str, Any]], dict[str, float]]
    """
    totals = {
        column: sum(float(row.get(column, 0.0)) for row in rows)
        for column in sum_columns
    }
    summary_row: dict[str, Any] = {label_column: label}
    summary_row.update(totals)
    return [summary_row], totals


def build_percent_acres_rows(
    rows: list[dict[str, Any]],
    *,
    region_column: str = "region",
    total_column: str = "total",
    counts_column: str = "counts",
    count_keys: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Flatten percent-acres rows that store counts as a list into per-column dicts.

    :param rows: Source rows with a ``counts`` list field.
    :type rows: list[dict[str, Any]]
    :param region_column: Column containing the region label.
    :type region_column: str
    :param total_column: Column containing the total acreage.
    :type total_column: str
    :param counts_column: Column whose value is a list of percentage strings.
    :type counts_column: str
    :param count_keys: Output column keys for each count element. Defaults to
        ``["count_1", "count_2", "count_3", "count_4", "count_5plus"]``.
    :type count_keys: list[str] | None
    :returns: Flattened rows suitable for ``generate_table_png``.
    :rtype: list[dict[str, Any]]
    """
    if count_keys is None:
        count_keys = ["count_1", "count_2", "count_3", "count_4", "count_5plus"]

    result: list[dict[str, Any]] = []
    for row in rows:
        flat: dict[str, Any] = {
            region_column: row[region_column],
            total_column: row[total_column],
        }
        counts = row.get(counts_column) or []
        for i, key in enumerate(count_keys):
            flat[key] = counts[i] if i < len(counts) else ""
        result.append(flat)
    return result


def build_mill_consumption_change_rows(
    rows: list[dict[str, Any]],
    *,
    from_column: str,
    to_column: str,
    name_column: str = "name",
    change_type_column: str = "type",
    product_column: str = "product",
    product_name: str | None = None,
    passthrough_columns: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Build mill-consumption change rows for a specific period.

    Rows are included only when both source and destination values are present.

    :param rows: Raw mill consumption change rows.
    :type rows: list[dict[str, Any]]
    :param from_column: Baseline numeric column key.
    :type from_column: str
    :param to_column: Destination numeric column key.
    :type to_column: str
    :param name_column: Mill name column key.
    :type name_column: str
    :param change_type_column: Change-type column key.
    :type change_type_column: str
    :param product_column: Product/species column key.
    :type product_column: str
    :param product_name: Optional product filter (for example Douglas Fir).
    :type product_name: str | None
    :param passthrough_columns: Optional extra columns to copy into output rows.
    :type passthrough_columns: list[str] | None
    :returns: Table-ready rows including a computed ``change`` field.
    :rtype: list[dict[str, Any]]
    :raises ValueError: If required columns are missing.
    """
    if not rows:
        raise ValueError("rows must contain at least one item")

    required_columns = [name_column, from_column, to_column]
    if product_name:
        required_columns.append(product_column)
    passthrough_columns = passthrough_columns or []
    for column in passthrough_columns:
        if column not in required_columns:
            required_columns.append(column)

    missing_columns: dict[str, list[int]] = {}
    for column in required_columns:
        missing_indexes = [i for i, row in enumerate(rows) if column not in row]
        if missing_indexes:
            missing_columns[column] = missing_indexes

    if missing_columns:
        raise ValueError(f"missing required columns in rows: {missing_columns}")

    table_rows: list[dict[str, Any]] = []
    for row in rows:
        if product_name and str(row.get(product_column, "")) != product_name:
            continue

        start_value = row.get(from_column)
        end_value = row.get(to_column)
        if start_value is None or end_value is None:
            continue

        start_number = float(start_value)
        end_number = float(end_value)
        output_row: dict[str, Any] = {
            "name": str(row[name_column]),
            from_column: start_number,
            to_column: end_number,
            "change": end_number - start_number,
            "type": str(row.get(change_type_column, "")),
            "product": str(row.get(product_column, "")),
        }
        for column in passthrough_columns:
            value = row.get(column)
            output_row[column] = float(value) if value is not None else None

        table_rows.append(output_row)

    return table_rows


def build_mill_consumption_change_total_row(
    rows: list[dict[str, Any]],
    *,
    label_column: str = "name",
    label: str = "Total Change",
    change_column: str = "change",
) -> tuple[list[dict[str, Any]], float]:
    """Build a single total row for mill-consumption change tables."""
    total_change = sum(float(row.get(change_column, 0.0)) for row in rows)
    return [{label_column: label, change_column: total_change}], total_change


def _mill_consumption_change_row_style(change_type: str) -> tuple[str, str]:
    """Return (background, text) colors for a mill-change row type."""
    key = str(change_type).strip().lower()
    return MILL_CONSUMPTION_ROW_STYLES.get(key, ("#ffffff", "#111111"))


def generate_mill_consumption_change_table_png(
    rows: list[dict[str, Any]],
    *,
    from_column: str,
    to_column: str,
    output_path: str,
    title: str,
    total_label: str = "Total Change",
    product_name: str | None = None,
    from_label: str | None = None,
    to_label: str | None = None,
    include_prev_column: bool = False,
    prev_column: str = "prev",
    prev_label: str = "2023",
) -> dict[str, Any]:
    """Generate a mill-consumption change table PNG for a selected period.

    :param rows: Raw mill consumption change rows.
    :type rows: list[dict[str, Any]]
    :param from_column: Baseline numeric column key.
    :type from_column: str
    :param to_column: Destination numeric column key.
    :type to_column: str
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param title: Table title.
    :type title: str
    :param total_label: Label text for the summary row.
    :type total_label: str
    :param product_name: Optional product filter.
    :type product_name: str | None
    :param from_label: Optional display label for the baseline column.
    :type from_label: str | None
    :param to_label: Optional display label for the destination column.
    :type to_label: str | None
    :param include_prev_column: Whether to show a previous-year display column.
    :type include_prev_column: bool
    :param prev_column: Previous-year column key.
    :type prev_column: str
    :param prev_label: Display label for previous-year column.
    :type prev_label: str
    :returns: Metadata about the generated table image.
    :rtype: dict[str, Any]
    :raises ValueError: If no rows remain after filtering.
    """
    if include_prev_column is False and from_column == "curr" and to_column == "future":
        include_prev_column = True

    resolved_from_label = from_label or MILL_CONSUMPTION_YEAR_LABELS.get(
        from_column, from_column.replace("_", " ").title()
    )
    resolved_to_label = to_label or MILL_CONSUMPTION_YEAR_LABELS.get(
        to_column, to_column.replace("_", " ").title()
    )
    resolved_prev_label = prev_label or MILL_CONSUMPTION_YEAR_LABELS.get(
        prev_column, prev_column.replace("_", " ").title()
    )

    table_rows = build_mill_consumption_change_rows(
        rows,
        from_column=from_column,
        to_column=to_column,
        product_name=product_name,
        passthrough_columns=[prev_column] if include_prev_column else None,
    )
    if not table_rows:
        raise ValueError("no mill consumption change rows available for the requested filter")

    summary_rows, total_change = build_mill_consumption_change_total_row(
        table_rows,
        label=total_label,
    )

    columns = [{"key": "name", "label": "Mill"}]
    if include_prev_column:
        columns.append({"key": prev_column, "label": resolved_prev_label})
    columns.extend([
        {"key": from_column, "label": resolved_from_label},
        {"key": to_column, "label": resolved_to_label},
        {"key": "change", "label": "Change"},
    ])

    numeric_columns = [from_column, to_column, "change"]
    if include_prev_column:
        numeric_columns = [prev_column] + numeric_columns

    column_widths = MILL_CONSUMPTION_TABLE_COLUMN_WIDTHS.copy()
    if include_prev_column:
        column_widths = MILL_CONSUMPTION_TABLE_COLUMN_WIDTHS_WITH_PREV.copy()

    row_background_colors: list[str] = []
    row_text_colors: list[str] = []
    for row in table_rows:
        bg, fg = _mill_consumption_change_row_style(str(row.get("type", "")))
        row_background_colors.append(bg)
        row_text_colors.append(fg)

    result = generate_table_png(
        rows=table_rows,
        output_path=output_path,
        columns=columns,
        numeric_columns=numeric_columns,
        summary_rows=summary_rows,
        summary_value_suffixes=MILL_CONSUMPTION_CHANGE_SUFFIXES,
        data_row_background_colors=row_background_colors,
        data_row_text_colors=row_text_colors,
        column_widths=column_widths,
        figure_width=MILL_CONSUMPTION_TABLE_FIGURE_WIDTH,
        title=title,
    )
    result["total_change"] = total_change
    result["column_keys"] = [column["key"] for column in columns]
    result["column_labels"] = [column["label"] for column in columns]
    return result


def build_delivery_by_area_table_rows(
    rows: list[dict[str, Any]],
    *,
    area_column: str = "area",
    export_column: str = "export",
    domestic_internal_column: str = "domestic_internal",
    domestic_third_party_column: str = "domestic_third_party",
) -> tuple[list[dict[str, Any]], list[str]]:
    """Pivot delivery-by-area rows into a series-by-area table shape."""
    if not rows:
        raise ValueError("rows must contain at least one item")

    required_columns = [
        area_column,
        export_column,
        domestic_internal_column,
        domestic_third_party_column,
    ]
    missing_columns: dict[str, list[int]] = {}
    for column in required_columns:
        missing_indexes = [i for i, row in enumerate(rows) if column not in row]
        if missing_indexes:
            missing_columns[column] = missing_indexes
    if missing_columns:
        raise ValueError(f"missing required columns in rows: {missing_columns}")

    area_names = [str(row[area_column]).strip() for row in rows]
    if any(not area for area in area_names):
        raise ValueError(f"area_column '{area_column}' contains an empty value")

    export_row: dict[str, Any] = {"series": "Export"}
    domestic_internal_row: dict[str, Any] = {"series": "Domestic Internal"}
    domestic_third_party_row: dict[str, Any] = {"series": "Domestic 3rd Party"}

    for row, area_name in zip(rows, area_names):
        export_row[area_name] = float(row[export_column])
        domestic_internal_row[area_name] = float(row[domestic_internal_column])
        domestic_third_party_row[area_name] = float(row[domestic_third_party_column])

    return [export_row, domestic_internal_row, domestic_third_party_row], area_names


def generate_delivery_by_area_table_png(
    rows: list[dict[str, Any]],
    output_path: str | None = None,
    *,
    title: str | None = None,
) -> dict[str, Any]:
    """Generate delivery-by-area matrix table PNG with series-colored rows."""
    table_rows, area_names = build_delivery_by_area_table_rows(rows)

    columns = [{"key": "series", "label": ""}] + [
        {"key": area_name, "label": area_name} for area_name in area_names
    ]

    first_column_width = DELIVERY_BY_AREA_TABLE_FIRST_COLUMN_WIDTH
    remaining_width = DELIVERY_BY_AREA_TABLE_REMAINING_WIDTH
    per_area_width = remaining_width / max(1, len(area_names))
    column_widths = [first_column_width] + [per_area_width] * len(area_names)

    return generate_table_png(
        rows=table_rows,
        output_path=output_path,
        columns=columns,
        analysis_component="delivery_by_area",
        visual_name="delivery_by_area",
        numeric_columns=area_names,
        summary_rows=None,
        data_row_background_colors=DELIVERY_BY_AREA_TABLE_ROW_BACKGROUND_COLORS,
        data_row_text_colors=DELIVERY_BY_AREA_TABLE_ROW_TEXT_COLORS,
        highlight_summary_rows=False,
        column_widths=column_widths,
        figure_width=DELIVERY_BY_AREA_TABLE_FIGURE_WIDTH,
        title=title,
    )


def build_large_landowner_table_rows(
    rows: list[dict[str, Any]],
    *,
    name_column: str = "name",
    total_column: str = "total_acres",
    woodbasket_column: str = "woodbasket_acres",
    mills_column: str = "mills",
    top_n: int = 10,
    woodbasket_name: str | None = None,
    include_mill_rows: bool = True,
) -> list[dict[str, Any]]:
    """Build flattened rows for the large-landowner table view.

    :param rows: Raw large landowner rows.
    :type rows: list[dict[str, Any]]
    :param name_column: Column containing owner display names.
    :type name_column: str
    :param total_column: Column containing owner total acres values.
    :type total_column: str
    :param woodbasket_column: Column containing per-woodbasket acre dict values.
    :type woodbasket_column: str
    :param mills_column: Column containing associated mill list values.
    :type mills_column: str
    :param top_n: Number of largest owners to include in the table.
    :type top_n: int
    :param woodbasket_name: Optional woodbasket key used for acres-within value.
    :type woodbasket_name: str | None
    :param include_mill_rows: Whether to append mill-detail rows under each owner.
    :type include_mill_rows: bool
    :returns: Flattened owner + mill table rows.
    :rtype: list[dict[str, Any]]
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

    table_rows: list[dict[str, Any]] = []
    for rank_index, owner in enumerate(top_rows, start=1):
        total_acres = float(owner[total_column])
        acres_within = total_acres

        if woodbasket_name:
            wb_values = owner.get(woodbasket_column, {})
            if not isinstance(wb_values, dict):
                raise ValueError(
                    f"woodbasket_column '{woodbasket_column}' must contain dict values"
                )
            acres_within = float(wb_values.get(woodbasket_name, 0.0))

        owner_row = {
            "rank": rank_index,
            "landowner_name": str(owner[name_column]),
            "total_acres_owned": total_acres,
            "acres_within_woodbasket": acres_within,
            "mill_name": "",
            "city": "",
            "state": "",
            "county": "",
            "ils_id": "",
            "forisk_id": "",
            "lims_destination_id": "",
        }
        table_rows.append(owner_row)

        if include_mill_rows:
            mills = owner.get(mills_column) or []
            for mill in mills:
                table_rows.append(
                    {
                        "rank": None,
                        "landowner_name": "",
                        "total_acres_owned": None,
                        "acres_within_woodbasket": None,
                        "mill_name": str(mill.get("mill_name", "")),
                        "city": str(mill.get("city", "")),
                        "state": str(mill.get("state", "")),
                        "county": str(mill.get("county", "")),
                        "ils_id": str(mill.get("ils_id", "")),
                        "forisk_id": str(mill.get("forisk_id", "")),
                        "lims_destination_id": str(mill.get("lims_destination_id", "")),
                    }
                )

    return table_rows


def generate_large_landowner_table_png(
    rows: list[dict[str, Any]],
    output_path: str | None = None,
    *,
    title: str = LARGE_LANDOWNER_TABLE_TITLE,
    top_n: int = 10,
    woodbasket_name: str | None = None,
) -> dict[str, Any]:
    """Generate a large-landowner table PNG with optional mill detail rows.

    :param rows: Raw large landowner rows.
    :type rows: list[dict[str, Any]]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param title: Table title.
    :type title: str
    :param top_n: Number of largest owners to include.
    :type top_n: int
    :param woodbasket_name: Optional woodbasket key for acres-within column.
    :type woodbasket_name: str | None
    :returns: Metadata about the generated table image.
    :rtype: dict[str, Any]
    """
    table_rows = build_large_landowner_table_rows(
        rows,
        top_n=top_n,
        woodbasket_name=woodbasket_name,
        include_mill_rows=True,
    )

    return generate_table_png(
        rows=table_rows,
        output_path=output_path,
        columns=LARGE_LANDOWNER_TABLE_COLUMNS,
        analysis_component="large_landowners",
        visual_name="largest_landowners",
        numeric_columns=LARGE_LANDOWNER_TABLE_NUMERIC_COLUMNS,
        summary_rows=None,
        highlight_summary_rows=False,
        column_widths=LARGE_LANDOWNER_TABLE_COLUMN_WIDTHS,
        figure_width=LARGE_LANDOWNER_TABLE_FIGURE_WIDTH,
        title=title,
    )


def generate_table_png(
    rows: list[dict[str, Any]],
    output_path: str | None = None,
    *,
    columns: list[dict[str, str]] | None = None,
    analysis_component: str | None = None,
    visual_name: str | None = None,
    export_format: str = "png",
    numeric_columns: list[str] | None = None,
    percent_columns: list[str] | None = None,
    summary_rows: list[dict[str, Any]] | None = None,
    summary_value_suffixes: dict[str, str] | None = None,
    data_row_background_colors: list[str] | None = None,
    data_row_text_colors: list[str] | None = None,
    highlight_summary_rows: bool = True,
    column_widths: list[float] | None = None,
    figure_width: float = 12.0,
    title: str | None = None,
) -> dict[str, Any]:
    """Generate a PNG export for generic table data.

    :param rows: SQL rows as a list of dicts, one dict per row.
    :type rows: list[dict[str, Any]]
    :param output_path: Destination path for the PNG file.
    :type output_path: str | None
    :param columns: Ordered column config items with `key` and optional `label`.
    :type columns: list[dict[str, str]] | None
    :param analysis_component: Optional component token used for default filename generation.
    :type analysis_component: str | None
    :param visual_name: Optional visual-name token used for default filename generation.
    :type visual_name: str | None
    :param export_format: Visual export format, currently ``png`` or ``pdf``.
    :type export_format: str
    :param numeric_columns: Column keys to format/align as numeric.
    :type numeric_columns: list[str] | None
    :param percent_columns: Column keys to format as integer percentages (e.g. ``"67%"``).
    :type percent_columns: list[str] | None
    :param summary_rows: Optional extra rows appended at the end.
    :type summary_rows: list[dict[str, Any]] | None
    :param summary_value_suffixes: Optional suffixes appended to summary values by key.
    :type summary_value_suffixes: dict[str, str] | None
    :param data_row_background_colors: Optional background colors for data rows.
    :type data_row_background_colors: list[str] | None
    :param data_row_text_colors: Optional text colors for data rows.
    :type data_row_text_colors: list[str] | None
    :param highlight_summary_rows: Whether to style summary rows.
    :type highlight_summary_rows: bool
    :param column_widths: Optional normalized width list for rendered columns.
    :type column_widths: list[float] | None
    :param figure_width: Figure width in inches used for table rendering.
    :type figure_width: float
    :param title: Optional chart title.
    :type title: str | None
    :returns: Metadata about the generated table image.
    :rtype: dict[str, Any]
    :raises ValueError: If inputs are invalid or configuration is inconsistent.
    :raises ImportError: If matplotlib is not installed.
    """
    if not rows:
        raise ValueError("rows must contain at least one item")

    if columns is None:
        inferred_keys = list(rows[0].keys())
        columns = [{"key": key, "label": key.replace("_", " ").title()} for key in inferred_keys]

    if not columns:
        raise ValueError("columns must contain at least one item")

    column_keys = [item["key"] for item in columns]
    column_labels = [item.get("label", item["key"]) for item in columns]
    numeric_key_set = set(numeric_columns or [])
    percent_key_set = set(percent_columns or [])
    right_align_key_set = numeric_key_set | percent_key_set

    if column_widths is not None and len(column_widths) != len(column_keys):
        raise ValueError("column_widths must have the same length as columns")

    if data_row_background_colors is not None and len(data_row_background_colors) != len(rows):
        raise ValueError("data_row_background_colors must have the same length as rows")

    if data_row_text_colors is not None and len(data_row_text_colors) != len(rows):
        raise ValueError("data_row_text_colors must have the same length as rows")

    missing_columns: dict[str, list[int]] = {}
    for column in column_keys:
        missing_indexes = [i for i, row in enumerate(rows) if column not in row]
        if missing_indexes:
            missing_columns[column] = missing_indexes

    if missing_columns:
        raise ValueError(f"missing required columns in rows: {missing_columns}")

    output, resolved_format = resolve_visual_output_path(
        output_path,
        default_output_dir=DEFAULT_TABLE_OUTPUT_DIR,
        default_filename_stem="table",
        analysis_component=analysis_component,
        visual_name=(visual_name or title) if analysis_component else None,
        visual_kind="table",
        export_format=export_format,
    )
    ensure_output_directory(str(output))

    summary_value_suffixes = summary_value_suffixes or {}

    def _render_cell(row: dict[str, Any], key: str, *, is_summary_row: bool = False) -> str:
        value = row.get(key)
        if is_summary_row and key in summary_value_suffixes and value is not None:
            formatted = _format_cell_value(value, key in numeric_key_set)
            return f"{formatted}{summary_value_suffixes[key]}"
        if key in percent_key_set:
            if value is None:
                return ""
            return f"{int(round(float(value)))}%"
        return _format_cell_value(value, key in numeric_key_set)

    rendered_rows: list[list[str]] = []
    for row in rows:
        rendered_rows.append([_render_cell(row, key) for key in column_keys])

    summary_rows = summary_rows or []
    for row in summary_rows:
        rendered_rows.append([
            _render_cell(row, key, is_summary_row=True) for key in column_keys
        ])

    plt = _get_pyplot_module()

    row_count = len(rendered_rows)
    figure_height = max(4.0, 1.6 + row_count * 0.42)
    figure, axis = plt.subplots(
        figsize=(figure_width, figure_height),
        dpi=DEFAULT_TABLE_DPI,
    )
    try:
        axis.axis("off")

        if title:
            axis.set_title(title, pad=8)

        table = axis.table(
            cellText=rendered_rows,
            colLabels=column_labels,
            colWidths=column_widths,
            cellLoc="right",
            colLoc="center",
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(DEFAULT_TABLE_FONT_SIZE)
        table.scale(1, DEFAULT_TABLE_SCALE_Y)

        for (row_index, column_index), cell in table.get_celld().items():
            cell.set_edgecolor(DEFAULT_TABLE_EDGE_COLOR)
            cell.set_linewidth(DEFAULT_TABLE_LINE_WIDTH)

            if row_index == 0:
                cell.set_text_props(weight="bold")
                cell.set_facecolor(DEFAULT_TABLE_HEADER_BACKGROUND)

            if row_index > 0:
                key = column_keys[column_index]
                if key in right_align_key_set:
                    cell.set_text_props(ha="right")
                else:
                    cell.set_text_props(ha="left")

                data_row_index = row_index - 1
                if data_row_index < len(rows):
                    if data_row_background_colors is not None:
                        cell.set_facecolor(data_row_background_colors[data_row_index])
                    if data_row_text_colors is not None:
                        cell.set_text_props(color=data_row_text_colors[data_row_index])

            if (
                highlight_summary_rows
                and summary_rows
                and row_index >= (len(rows) + 1)
                and row_index > 0
            ):
                cell.set_text_props(weight="bold", color=DEFAULT_TABLE_SUMMARY_TEXT_COLOR)
                cell.set_facecolor(DEFAULT_TABLE_SUMMARY_BACKGROUND)
            elif row_index > 0 and column_keys[column_index] in right_align_key_set:
                cell.set_text_props(ha="right")

        figure.tight_layout()
        figure.savefig(output, format=resolved_format, bbox_inches="tight")

        width_px = int(figure.get_size_inches()[0] * figure.dpi)
        height_px = int(figure.get_size_inches()[1] * figure.dpi)

        return {
            "output_path": str(output),
            "row_count": row_count,
            "data_row_count": len(rows),
            "summary_row_count": len(summary_rows),
            "width_px": width_px,
            "height_px": height_px,
            "title": title,
            "export_format": resolved_format,
        }
    finally:
        plt.close(figure)


def generate_portfolio_attributes_table_png(
    data: dict[str, Any],
    output_path: str | None = None,
    *,
    export_format: str = "png",
) -> dict[str, Any]:
    """Generate a PNG export for a sectioned portfolio attributes table.

    :param data: Portfolio data with ``title`` and ``sections`` list.
    :type data: dict[str, Any]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :returns: Metadata about the generated table image.
    :rtype: dict[str, Any]
    :raises ValueError: If ``sections`` is empty.
    :raises ImportError: If matplotlib is not installed.
    """
    title = str(data.get("title", ""))
    sections = data.get("sections", [])

    if not sections:
        raise ValueError("data must contain at least one section")

    column_labels = [
        "Attribute",
        "Existing Characteristics/Agreements",
        "Identified Potential Opportunities",
        "Total",
        "% of Total",
    ]
    column_widths = [0.22, 0.28, 0.24, 0.14, 0.09]

    def _fmt(value: Any) -> str:
        if value is None:
            return "-"
        try:
            n = float(value)
            return f"{n:,.0f}" if n.is_integer() else f"{n:,.2f}"
        except (TypeError, ValueError):
            return str(value)

    rendered_rows: list[list[str]] = []
    section_header_indices: set[int] = set()

    for section in sections:
        section_header_indices.add(len(rendered_rows))
        rendered_rows.append([str(section.get("label", "")), "", "", "", ""])
        for row in section.get("rows", []):
            rendered_rows.append([
                str(row.get("attribute", "")),
                _fmt(row.get("existing")),
                _fmt(row.get("potential")),
                _fmt(row.get("total")),
                str(row.get("percent", "")),
            ])

    output, resolved_format = resolve_visual_output_path(
        output_path,
        default_output_dir=DEFAULT_TABLE_OUTPUT_DIR,
        default_filename_stem="portfolio_attributes",
        analysis_component="portfolio_attributes",
        visual_name="portfolio_attributes",
        visual_kind="table",
        export_format=export_format,
    )
    ensure_output_directory(str(output))

    plt = _get_pyplot_module()

    row_count = len(rendered_rows)
    figure_height = max(6.0, 1.8 + row_count * 0.32)
    figure, axis = plt.subplots(figsize=(14, figure_height), dpi=150)
    try:
        axis.axis("off")

        if title:
            axis.set_title(title, loc="left", pad=10, fontweight="bold", fontsize=11)

        table = axis.table(
            cellText=rendered_rows,
            colLabels=column_labels,
            colWidths=column_widths,
            cellLoc="right",
            colLoc="right",
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.2)

        for (row_index, col_index), cell in table.get_celld().items():
            cell.set_edgecolor("#d0d0d0")
            cell.set_linewidth(0.5)

            if row_index == 0:
                cell.set_facecolor("#f3f6f7")
                if col_index == 0:
                    cell.set_text_props(weight="bold", ha="left")
                else:
                    cell.set_text_props(weight="bold", ha="right")
                continue

            data_row_index = row_index - 1

            if data_row_index in section_header_indices:
                cell.set_facecolor("#e8e8e8")
                cell.set_linewidth(0)
                if col_index == 0:
                    cell.set_text_props(weight="bold", ha="left")
                else:
                    cell.set_text_props(ha="left")
            else:
                cell.set_facecolor("white")
                if col_index == 0:
                    cell.set_text_props(ha="left")
                else:
                    cell.set_text_props(ha="right")

        figure.tight_layout()
        figure.savefig(output, format=resolved_format, bbox_inches="tight")

        width_px = int(figure.get_size_inches()[0] * figure.dpi)
        height_px = int(figure.get_size_inches()[1] * figure.dpi)

        return {
            "output_path": str(output),
            "row_count": row_count,
            "section_count": len(sections),
            "width_px": width_px,
            "height_px": height_px,
            "title": title,
            "export_format": resolved_format,
        }
    finally:
        plt.close(figure)
