"""CSV export utilities for AVO."""

import csv
from datetime import date
from datetime import datetime
import json
from typing import Any

from .io import build_data_export_output_path
from .io import DEFAULT_CSV_OUTPUT_DIR
from .io import ensure_output_directory
from .io import normalize_output_path


def _serialize_csv_value(value: Any) -> Any:
    """Serialize nested values into CSV-safe scalar text."""
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, ensure_ascii=True)
    return value


def _coerce_rows(data: Any) -> list[dict[str, Any]]:
    """Coerce generic inputs into list-of-dict row data for CSV writing."""
    if isinstance(data, list):
        if not data:
            raise ValueError("data must contain at least one item")

        if all(isinstance(item, dict) for item in data):
            return [dict(item) for item in data]

        return [{"value": _serialize_csv_value(item)} for item in data]

    if isinstance(data, dict):
        if isinstance(data.get("rows"), list):
            row_items = data["rows"]
            if not row_items:
                raise ValueError("data['rows'] must contain at least one item")
            if all(isinstance(item, dict) for item in row_items):
                return [dict(item) for item in row_items]
            return [{"value": _serialize_csv_value(item)} for item in row_items]

        if isinstance(data.get("sections"), list):
            flattened_rows: list[dict[str, Any]] = []
            sections = data["sections"]
            for section in sections:
                if not isinstance(section, dict):
                    continue
                section_label = str(section.get("label", ""))
                section_rows = section.get("rows", [])
                if isinstance(section_rows, list):
                    for row in section_rows:
                        if isinstance(row, dict):
                            flattened_rows.append({"section": section_label, **row})

            if flattened_rows:
                return flattened_rows

        return [dict(data)]

    return [{"value": _serialize_csv_value(data)}]


def _normalize_row_keys_and_values(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize row keys to strings and serialize nested values."""
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized_row: dict[str, Any] = {}
        for key, value in row.items():
            normalized_row[str(key)] = _serialize_csv_value(value)
        normalized.append(normalized_row)
    return normalized


def export_csv(
    data: Any,
    output_path: str | None = None,
    *,
    fieldnames: list[str] | None = None,
    component_name: str | None = None,
    visual_name: str | None = None,
    exported_by: str | None = None,
    export_date: date | datetime | str | None = None,
) -> dict[str, Any]:
    """Export tabular data to a CSV file.

    :param data: Source payload to export (for example list of dict rows,
        dict with ``rows`` or ``sections``, plain dict, or scalar/list values).
    :type data: Any
    :param output_path: Destination path for the CSV file.
    :type output_path: str | None
    :param fieldnames: Optional explicit CSV column ordering.
    :type fieldnames: list[str] | None
    :param component_name: Optional analysis component name for convention-based file naming.
    :type component_name: str | None
    :param visual_name: Optional visual name for convention-based file naming.
    :type visual_name: str | None
    :param exported_by: Optional user name for convention-based file naming.
    :type exported_by: str | None
    :param export_date: Optional date token for convention-based file naming.
    :type export_date: date | datetime | str | None
    :returns: Metadata about the generated CSV.
    :rtype: dict[str, Any]
    :raises ValueError: If inputs are invalid.
    """
    rows = _normalize_row_keys_and_values(_coerce_rows(data))
    if not rows:
        raise ValueError("data must contain at least one row")

    if output_path is None:
        if component_name and visual_name and exported_by:
            resolved_output = build_data_export_output_path(
                component_name,
                visual_name,
                exported_by,
                export_date=export_date,
                output_dir=DEFAULT_CSV_OUTPUT_DIR,
                suffix=".csv",
            )
        else:
            resolved_output = normalize_output_path(
                str(DEFAULT_CSV_OUTPUT_DIR / "export.csv"),
                suffix=".csv",
            )
    else:
        resolved_output = normalize_output_path(output_path, suffix=".csv")
    ensure_output_directory(str(resolved_output))

    if fieldnames is None:
        seen: set[str] = set()
        inferred_fieldnames: list[str] = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("coerced rows must be dict items")
            for key in row.keys():
                key_text = str(key)
                if key_text not in seen:
                    seen.add(key_text)
                    inferred_fieldnames.append(key_text)
        if not inferred_fieldnames:
            raise ValueError("rows must contain at least one column")
        resolved_fieldnames = inferred_fieldnames
    else:
        if not fieldnames:
            raise ValueError("fieldnames must contain at least one column")
        resolved_fieldnames = [str(name) for name in fieldnames]

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("coerced rows must be dict items")
        unknown_columns = [str(key) for key in row.keys() if str(key) not in resolved_fieldnames]
        if unknown_columns:
            raise ValueError(
                f"row at index {index} contains columns not present in fieldnames: {unknown_columns}"
            )

    with resolved_output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=resolved_fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    return {
        "output_path": str(resolved_output),
        "row_count": len(rows),
        "column_count": len(resolved_fieldnames),
        "fieldnames": resolved_fieldnames,
    }