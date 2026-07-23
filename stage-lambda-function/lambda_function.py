"""AWS Lambda entry point for querying model output arrays from a local Zarr folder.

Expected event payload (or API Gateway JSON body):
{
  "zarr_path": "/mnt/data/mihms_output.zarr",
  "group_name": "hydromt_nhdflowlines",
  "data_array_name": "ef1ddb79-76c6-4e19-947d-786d0e6c4bf4",
  "hydrologic_sequence_values": ["1001", "1002"],
  "start_datetime": "2024-01-01",
  "end_datetime": "2024-12-31",
  "row_indexes": [0, 1],
  "column_indexes": [0, 1],
  "max_records": 10000
}
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Any, Iterable

from stage_zarr_api import query_zarr_array_from_path


def _response(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload, default=str),
    }


def _parse_event_payload(event: dict[str, Any] | None) -> dict[str, Any]:
    if event is None:
        return {}

    if "body" in event:
        body = event.get("body")
        if body is None:
            return {}
        if isinstance(body, str):
            return json.loads(body) if body.strip() else {}
        if isinstance(body, dict):
            return body
        raise ValueError("event.body must be a JSON string or object")

    return event


def _coerce_optional_index_list(values: Any) -> list[int] | None:
    if values is None:
        return None
    if isinstance(values, (str, bytes)):
        raise ValueError("index lists must be arrays of integers")
    try:
        return [int(v) for v in values]
    except Exception as exc:
        raise ValueError("index lists must be arrays of integers") from exc


def _to_json_safe_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


def _format_records(df: Any) -> list[dict[str, Any]]:
    if df.empty:
        return []

    records = df.to_dict(orient="records")
    return [{key: _to_json_safe_value(value) for key, value in row.items()} for row in records]


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda handler for Zarr array query requests."""

    try:
        payload = _parse_event_payload(event)
    except Exception as exc:
        return _response(400, {"error": f"Invalid request payload: {exc}"})

    if not isinstance(payload, dict):
        return _response(400, {"error": "Payload must be a JSON object"})

    zarr_path = payload.get("zarr_path") or os.environ.get("ZARR_PATH")
    group_name = payload.get("group_name")
    data_array_name = payload.get("data_array_name")
    hydrologic_sequence_values = payload.get("hydrologic_sequence_values")
    start_datetime = payload.get("start_datetime")
    end_datetime = payload.get("end_datetime")

    required_missing = [
        name
        for name, value in [
            ("zarr_path", zarr_path),
            ("group_name", group_name),
            ("data_array_name", data_array_name),
            ("hydrologic_sequence_values", hydrologic_sequence_values),
            ("start_datetime", start_datetime),
            ("end_datetime", end_datetime),
        ]
        if value is None
    ]
    if required_missing:
        return _response(400, {"error": "Missing required fields", "fields": required_missing})

    if isinstance(hydrologic_sequence_values, (str, bytes)) or not isinstance(
        hydrologic_sequence_values, Iterable
    ):
        return _response(400, {"error": "hydrologic_sequence_values must be an array"})

    try:
        row_indexes = _coerce_optional_index_list(payload.get("row_indexes"))
        column_indexes = _coerce_optional_index_list(payload.get("column_indexes"))
        max_records = payload.get("max_records")
        if max_records is not None:
            max_records = int(max_records)
            if max_records <= 0:
                raise ValueError("max_records must be greater than zero")

        df = query_zarr_array_from_path(
            zarr_path=zarr_path,
            group_name=str(group_name),
            data_array_name=str(data_array_name),
            hydrologic_sequence_values=[str(v) for v in hydrologic_sequence_values],
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            row_indexes=row_indexes,
            column_indexes=column_indexes,
        )
    except Exception as exc:
        return _response(500, {"error": f"Query execution failed: {exc}"})

    total_count = len(df)
    truncated = False
    if max_records is not None and total_count > max_records:
        df = df.iloc[:max_records].copy()
        truncated = True

    return _response(
        200,
        {
            "row_count": len(df),
            "total_count": total_count,
            "truncated": truncated,
            "results": _format_records(df),
        },
    )

