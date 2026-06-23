"""Tests for CSV export utilities."""

import csv
from datetime import date
import json
from pathlib import Path

import pytest


MOCK_DATA_DIR = Path(__file__).parent / "mock_data"

LIST_BASED_MOCK_FILES = [
    "county_summary_rows.json",
    "cover_type_rows.json",
    "delivery_by_area_rows.json",
    "large_landowner_rows.json",
    "mill_consumption_change_rows.json",
    "ownership_type_rows.json",
    "percent_acres_rows.json",
    "pine_acres_by_age_class_rows.json",
    "pine_volume_by_age_class_rows.json",
    "top_customer_rows.json",
    "top_destination_rows.json",
    "woodbasket_rows.json",
]


def load_mock_percent_acres_rows() -> list[dict[str, object]]:
    """Load percent acres mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "percent_acres_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def _load_mock_json(file_name: str) -> object:
    """Load a JSON fixture from tests/mock_data."""
    data_file = MOCK_DATA_DIR / file_name
    return json.loads(data_file.read_text(encoding="utf-8"))


def test_export_csv_writes_file_with_inferred_columns(tmp_path) -> None:
    """CSV export should infer columns from rows and write a .csv file."""
    from avo_utils.csv import export_csv

    output = str(tmp_path / "cover_type_export")
    rows = [
        {"business": "NWS", "acres": 42, "region": "AO"},
        {"business": "SWS", "acres": 100, "region": "SO"},
    ]

    result = export_csv(rows, output_path=output)
    output_csv = Path(result["output_path"])

    assert output_csv.is_file()
    assert output_csv.suffix.lower() == ".csv"
    assert result["row_count"] == 2
    assert result["column_count"] == 3
    assert result["fieldnames"] == ["business", "acres", "region"]

    with output_csv.open("r", encoding="utf-8", newline="") as csv_file:
        parsed = list(csv.DictReader(csv_file))

    assert parsed[0]["business"] == "NWS"
    assert parsed[0]["acres"] == "42"
    assert parsed[1]["region"] == "SO"


def test_export_csv_uses_explicit_field_order(tmp_path) -> None:
    """Explicit fieldnames should control column order in output CSV."""
    from avo_utils.csv import export_csv

    output = str(tmp_path / "ordered.csv")
    rows = [
        {"region": "AO", "business": "NWS", "acres": 42},
    ]

    result = export_csv(
        rows,
        output_path=output,
        fieldnames=["business", "region", "acres"],
    )

    assert result["fieldnames"] == ["business", "region", "acres"]

    with Path(result["output_path"]).open("r", encoding="utf-8", newline="") as csv_file:
        header = csv_file.readline().strip()

    assert header == "business,region,acres"


def test_export_csv_rejects_row_columns_not_in_fieldnames(tmp_path) -> None:
    """Rows with columns missing from explicit fieldnames should raise."""
    from avo_utils.csv import export_csv

    output = str(tmp_path / "invalid.csv")
    rows = [{"region": "AO", "total": 100, "count_1": "10%"}]

    with pytest.raises(ValueError, match="not present in fieldnames"):
        export_csv(rows, output_path=output, fieldnames=["region", "total"])


def test_export_csv_for_percent_acres_table_rows(tmp_path) -> None:
    """Flattened percent acres rows should export to CSV for table pipelines."""
    from avo_utils.csv import export_csv
    from avo_utils.tables import build_percent_acres_rows

    raw_rows = load_mock_percent_acres_rows()
    rows = build_percent_acres_rows(raw_rows)
    output = str(tmp_path / "percent_acres_table_data.csv")

    result = export_csv(
        rows,
        output_path=output,
        fieldnames=["region", "total", "count_1", "count_2", "count_3", "count_4", "count_5plus"],
    )

    assert result["row_count"] == 6
    assert Path(result["output_path"]).is_file()

    with Path(result["output_path"]).open("r", encoding="utf-8", newline="") as csv_file:
        parsed = list(csv.DictReader(csv_file))

    assert parsed[0]["region"] == "AO"
    assert parsed[0]["count_5plus"] == "0.1%"


@pytest.mark.parametrize("mock_file", LIST_BASED_MOCK_FILES)
def test_export_csv_for_all_list_based_mock_files(tmp_path, mock_file: str) -> None:
    """Every list-based mock fixture should export to CSV successfully."""
    from avo_utils.csv import export_csv

    raw = _load_mock_json(mock_file)
    assert isinstance(raw, list)
    assert raw
    assert isinstance(raw[0], dict)

    output = str(tmp_path / mock_file.replace(".json", ".csv"))
    result = export_csv(raw, output_path=output)

    output_csv = Path(result["output_path"])
    assert output_csv.is_file()
    assert result["row_count"] == len(raw)
    assert result["column_count"] >= 1


def test_export_csv_for_portfolio_attributes_mock_data(tmp_path) -> None:
    """Portfolio attributes fixture should export from sectioned input directly."""
    from avo_utils.csv import export_csv

    raw = _load_mock_json("portfolio_attributes.json")
    assert isinstance(raw, dict)

    output = str(tmp_path / "portfolio_attributes_rows.csv")
    result = export_csv(raw, output_path=output)

    output_csv = Path(result["output_path"])
    assert output_csv.is_file()
    assert result["row_count"] == 23
    assert "section" in result["fieldnames"]
    assert "attribute" in result["fieldnames"]


def test_export_csv_supports_plain_dict_input(tmp_path) -> None:
    """Plain dict payloads should be exported as one-row CSV files."""
    from avo_utils.csv import export_csv

    payload = {"name": "sample", "count": 3}
    output = str(tmp_path / "single_dict.csv")
    result = export_csv(payload, output_path=output)

    assert result["row_count"] == 1
    assert Path(result["output_path"]).is_file()
    assert result["fieldnames"] == ["name", "count"]


def test_export_csv_supports_scalar_list_input(tmp_path) -> None:
    """List payloads with scalar items should export via a value column."""
    from avo_utils.csv import export_csv

    payload = ["AO", "SO", "NW"]
    output = str(tmp_path / "scalar_list.csv")
    result = export_csv(payload, output_path=output)

    assert result["row_count"] == 3
    assert result["fieldnames"] == ["value"]


def test_export_csv_builds_convention_named_file_when_metadata_is_supplied() -> None:
    """CSV export should support per-visual convention naming without an explicit path."""
    from avo_utils.csv import export_csv

    payload = [{"region": "AO", "total": 100}]
    result = export_csv(
        payload,
        component_name="Delivery By Area",
        visual_name="Summary Table",
        exported_by="Riley Slater",
        export_date=date(2026, 6, 23),
    )

    output_csv = Path(result["output_path"])
    assert output_csv.is_file()
    assert output_csv.name == "delivery_by_area_summary_table_riley_slater_20260623.csv"


def test_export_csv_all_mocks_to_output_csv_folder() -> None:
    """All mock fixtures should export to output/csv for manual inspection."""
    from avo_utils.csv import export_csv
    from avo_utils.io import DEFAULT_CSV_OUTPUT_DIR

    outputs: list[Path] = []
    for mock_file in LIST_BASED_MOCK_FILES:
        raw = _load_mock_json(mock_file)
        output = DEFAULT_CSV_OUTPUT_DIR / f"mock_{mock_file.replace('.json', '.csv')}"
        result = export_csv(raw, output_path=str(output))
        outputs.append(Path(result["output_path"]))

    portfolio_raw = _load_mock_json("portfolio_attributes.json")
    portfolio_result = export_csv(
        portfolio_raw,
        output_path=str(DEFAULT_CSV_OUTPUT_DIR / "mock_portfolio_attributes_rows.csv"),
    )
    outputs.append(Path(portfolio_result["output_path"]))

    for output in outputs:
        assert output.is_file()
