"""Table image export utilities for AVO."""

import importlib
from pathlib import Path
from typing import Any

from .io import DEFAULT_CHART_OUTPUT_DIR


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


def generate_table_png(
    rows: list[dict[str, Any]],
    output_path: str = str(DEFAULT_CHART_OUTPUT_DIR / "tables" / "table.png"),
    *,
    columns: list[dict[str, str]] | None = None,
    numeric_columns: list[str] | None = None,
    summary_rows: list[dict[str, Any]] | None = None,
    highlight_summary_rows: bool = True,
    column_widths: list[float] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Generate a PNG export for generic table data.

    :param rows: SQL rows as a list of dicts, one dict per row.
    :type rows: list[dict[str, Any]]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param columns: Ordered column config items with `key` and optional `label`.
    :type columns: list[dict[str, str]] | None
    :param numeric_columns: Column keys to format/align as numeric.
    :type numeric_columns: list[str] | None
    :param summary_rows: Optional extra rows appended at the end.
    :type summary_rows: list[dict[str, Any]] | None
    :param highlight_summary_rows: Whether to style summary rows.
    :type highlight_summary_rows: bool
    :param column_widths: Optional normalized width list for rendered columns.
    :type column_widths: list[float] | None
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

    if column_widths is not None and len(column_widths) != len(column_keys):
        raise ValueError("column_widths must have the same length as columns")

    missing_columns: dict[str, list[int]] = {}
    for column in column_keys:
        missing_indexes = [i for i, row in enumerate(rows) if column not in row]
        if missing_indexes:
            missing_columns[column] = missing_indexes

    if missing_columns:
        raise ValueError(f"missing required columns in rows: {missing_columns}")

    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    rendered_rows: list[list[str]] = []
    for row in rows:
        rendered_rows.append(
            [
                _format_cell_value(row.get(key), key in numeric_key_set)
                for key in column_keys
            ]
        )

    summary_rows = summary_rows or []
    for row in summary_rows:
        rendered_rows.append(
            [
                _format_cell_value(row.get(key), key in numeric_key_set)
                for key in column_keys
            ]
        )

    plt = _get_pyplot_module()

    row_count = len(rendered_rows)
    figure_height = max(4.0, 1.6 + row_count * 0.42)
    figure, axis = plt.subplots(figsize=(12, figure_height), dpi=150)
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
        table.set_fontsize(10)
        table.scale(1, 1.2)

        for (row_index, column_index), cell in table.get_celld().items():
            cell.set_edgecolor("#c8cdd0")
            cell.set_linewidth(0.5)

            if row_index == 0:
                cell.set_text_props(weight="bold")
                cell.set_facecolor("#f3f6f7")

            if row_index > 0:
                key = column_keys[column_index]
                if key in numeric_key_set:
                    cell.set_text_props(ha="right")
                else:
                    cell.set_text_props(ha="left")

            if (
                highlight_summary_rows
                and summary_rows
                and row_index >= (len(rows) + 1)
                and row_index > 0
            ):
                cell.set_text_props(weight="bold", color="#0b3d4a")
                cell.set_facecolor("#eef2f1")
            elif row_index > 0 and column_keys[column_index] in numeric_key_set:
                cell.set_text_props(ha="right")

        figure.tight_layout()
        figure.savefig(output, format="png", bbox_inches="tight")

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
        }
    finally:
        plt.close(figure)
