"""Utilities for querying model output arrays from a local Zarr folder.

The main entry point is `query_zarr_array`, which resolves row and column indexes
from business parameters and returns a tidy pandas DataFrame.

Example:
	df = query_zarr_array(
		zarr_path="mihms_output.zarr",
		group_name="hydromt_nhdflowlines",
		data_array_name="ef1ddb79-76c6-4e19-947d-786d0e6c4bf4",
		hydrologic_sequence_values=["1001", "1002"],
		start_datetime="2024-01-01",
		end_datetime="2024-12-31",
	)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import zarr


RESULT_COLUMNS = ["time", "HydrologicSequence", "value"]


@dataclass(frozen=True)
class QueryContext:
	"""Resolved resources and indexes used to execute a Zarr query."""

	array_path: str
	row_indexes: np.ndarray
	column_indexes: np.ndarray
	row_time_values: np.ndarray
	column_feature_values: np.ndarray


def _empty_result() -> pd.DataFrame:
	return pd.DataFrame(columns=RESULT_COLUMNS)


def _as_string_array(values: np.ndarray) -> np.ndarray:
	return np.asarray([str(v) for v in values], dtype=object)


def _normalize_array_path(group_name: str, data_array_name: str) -> str:
	group = group_name.strip("/")
	array_name = data_array_name.strip("/")
	if array_name.startswith(group + "/"):
		return array_name
	return f"{group}/{array_name}"


def _coerce_timestamp(value: str | pd.Timestamp) -> pd.Timestamp:
	return pd.Timestamp(value)


def _resolve_time_indexes(
	time_values: np.ndarray,
	start_datetime: str | pd.Timestamp,
	end_datetime: str | pd.Timestamp,
) -> tuple[np.ndarray, np.ndarray]:
	start_ts = _coerce_timestamp(start_datetime)
	end_ts = _coerce_timestamp(end_datetime)

	if start_ts > end_ts:
		return np.array([], dtype=np.int64), np.array([], dtype="datetime64[ns]")

	as_ts = pd.to_datetime(np.asarray(time_values), utc=False)
	mask = (as_ts >= start_ts) & (as_ts <= end_ts)
	indexes = np.where(mask)[0].astype(np.int64)
	return indexes, as_ts[mask].to_numpy()


def _resolve_feature_indexes(
	feature_values: np.ndarray,
	requested_features: Sequence[str],
) -> tuple[np.ndarray, np.ndarray]:
	if not requested_features:
		return np.array([], dtype=np.int64), np.array([], dtype=object)

	feature_strings = _as_string_array(feature_values)
	lookup = {value: idx for idx, value in enumerate(feature_strings.tolist())}

	indexes: list[int] = []
	resolved_values: list[str] = []
	for requested in requested_features:
		key = str(requested)
		idx = lookup.get(key)
		if idx is None:
			# Missing features should return an empty DataFrame by caller policy.
			return np.array([], dtype=np.int64), np.array([], dtype=object)
		indexes.append(idx)
		resolved_values.append(feature_strings[idx])

	return np.asarray(indexes, dtype=np.int64), np.asarray(resolved_values, dtype=object)


def _read_array_if_exists(root: zarr.Group, path: str) -> np.ndarray | None:
	try:
		return np.asarray(root[path][:])
	except Exception:
		return None


def _resolve_query_context(
	root: zarr.Group,
	group_name: str,
	data_array_name: str,
	hydrologic_sequence_values: Sequence[str],
	start_datetime: str | pd.Timestamp,
	end_datetime: str | pd.Timestamp,
	row_indexes: Sequence[int] | None,
	column_indexes: Sequence[int] | None,
) -> QueryContext | None:
	group_path = group_name.strip("/")
	array_path = _normalize_array_path(group_path, data_array_name)

	try:
		_ = root[group_path]
		array = root[array_path]
	except Exception:
		return None

	if getattr(array, "ndim", None) != 2:
		return None

	time_path = f"{group_path}/time"
	feature_path = f"{group_path}/HydrologicSequence"

	time_values = _read_array_if_exists(root, time_path)
	feature_values = _read_array_if_exists(root, feature_path)
	if time_values is None or feature_values is None:
		return None

	if row_indexes is not None:
		resolved_row_indexes = np.asarray(list(row_indexes), dtype=np.int64)
		if resolved_row_indexes.size == 0:
			return None
		valid_rows = (resolved_row_indexes >= 0) & (resolved_row_indexes < array.shape[0])
		resolved_row_indexes = resolved_row_indexes[valid_rows]
		if resolved_row_indexes.size == 0:
			return None
		row_time_values = pd.to_datetime(np.asarray(time_values)[resolved_row_indexes]).to_numpy()
	else:
		resolved_row_indexes, row_time_values = _resolve_time_indexes(
			time_values=time_values,
			start_datetime=start_datetime,
			end_datetime=end_datetime,
		)
		if resolved_row_indexes.size == 0:
			return None

	if column_indexes is not None:
		resolved_column_indexes = np.asarray(list(column_indexes), dtype=np.int64)
		if resolved_column_indexes.size == 0:
			return None
		valid_cols = (resolved_column_indexes >= 0) & (resolved_column_indexes < array.shape[1])
		resolved_column_indexes = resolved_column_indexes[valid_cols]
		if resolved_column_indexes.size == 0:
			return None
		column_feature_values = _as_string_array(np.asarray(feature_values)[resolved_column_indexes])
	else:
		resolved_column_indexes, column_feature_values = _resolve_feature_indexes(
			feature_values=feature_values,
			requested_features=hydrologic_sequence_values,
		)
		if resolved_column_indexes.size == 0:
			return None

	return QueryContext(
		array_path=array_path,
		row_indexes=resolved_row_indexes,
		column_indexes=resolved_column_indexes,
		row_time_values=np.asarray(row_time_values),
		column_feature_values=np.asarray(column_feature_values),
	)


def query_zarr_array(
	zarr_path: str | Path,
	group_name: str,
	data_array_name: str,
	hydrologic_sequence_values: Sequence[str],
	start_datetime: str | pd.Timestamp,
	end_datetime: str | pd.Timestamp,
	row_indexes: Sequence[int] | None = None,
	column_indexes: Sequence[int] | None = None,
) -> pd.DataFrame:
	"""Query a 2D Zarr array and return a tidy DataFrame.

	Args:
		zarr_path: Filesystem path to the Zarr root folder.
		group_name: Zarr group containing coordinate arrays and target data array.
		data_array_name: Array name inside the group, or full path including group.
		hydrologic_sequence_values: List of feature ids to query. Used when
			`column_indexes` is not provided.
		start_datetime: Inclusive lower bound for time filtering.
		end_datetime: Inclusive upper bound for time filtering.
		row_indexes: Optional explicit row indexes. If provided, time bounds are
			ignored for index selection.
		column_indexes: Optional explicit column indexes. If provided, feature list
			is ignored for index selection.

	Returns:
		A pandas DataFrame with columns: time, HydrologicSequence, value.
		Returns an empty DataFrame when group/array/features/time selection does
		not resolve to queryable indexes.
	"""

	if not isinstance(hydrologic_sequence_values, Iterable):
		return _empty_result()

	try:
		root = zarr.open_group(str(Path(zarr_path)), mode="r")
	except Exception:
		return _empty_result()

	context = _resolve_query_context(
		root=root,
		group_name=group_name,
		data_array_name=data_array_name,
		hydrologic_sequence_values=list(hydrologic_sequence_values),
		start_datetime=start_datetime,
		end_datetime=end_datetime,
		row_indexes=row_indexes,
		column_indexes=column_indexes,
	)
	if context is None:
		return _empty_result()

	try:
		array = root[context.array_path]
		values = np.asarray(array.oindex[context.row_indexes, context.column_indexes])
	except Exception:
		return _empty_result()

	if values.ndim != 2:
		return _empty_result()

	time_rep = np.repeat(pd.to_datetime(context.row_time_values).to_numpy(), values.shape[1])
	feature_rep = np.tile(_as_string_array(context.column_feature_values), values.shape[0])

	return pd.DataFrame(
		{
			"time": time_rep,
			"HydrologicSequence": feature_rep,
			"value": values.reshape(-1),
		}
	)


if __name__ == "__main__":
	demo_path = Path("mihms_output.zarr")
	demo_group = "hydromt_nhdflowlines"
	demo_array = "ef1ddb79-76c6-4e19-947d-786d0e6c4bf4"

	root = zarr.open_group(str(demo_path), mode="r")
	time_values = pd.to_datetime(np.asarray(root[f"{demo_group}/time"][:]))
	features = [str(v) for v in np.asarray(root[f"{demo_group}/HydrologicSequence"][:]).tolist()]

	if len(features) == 0 or len(time_values) == 0:
		print("No features or time values found for demo query.")
	else:
		df = query_zarr_array(
			zarr_path=demo_path,
			group_name=demo_group,
			data_array_name=demo_array,
			hydrologic_sequence_values=features,
			start_datetime=time_values.min(),
			end_datetime=time_values.max(),
		)
		print(df.head())
		print(f"Rows returned: {len(df)}")
