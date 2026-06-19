"""Tests for chart export utilities."""

import json
from pathlib import Path

import pytest

MOCK_DATA_DIR = Path(__file__).parent / "mock_data"

TABLE_COLUMNS = [
    {"key": "business", "label": "Business"},
    {"key": "region", "label": "Region"},
    {"key": "area", "label": "Area"},
    {"key": "broad_cover_type", "label": "Broad Cover Type"},
    {"key": "total_stand_acres", "label": "Total Stand Acres"},
    {"key": "net_productive_acres", "label": "Net Productive Acres"},
    {"key": "harvestable_acres", "label": "Harvestable Acres"},
]

TABLE_NUMERIC_COLUMNS = [
    "total_stand_acres",
    "net_productive_acres",
    "harvestable_acres",
]

TABLE_WIDTHS = [0.13, 0.13, 0.09, 0.13, 0.13, 0.145, 0.145]

OWNERSHIP_TABLE_COLUMNS = [
    {"key": "business", "label": "Business"},
    {"key": "region", "label": "Region"},
    {"key": "area", "label": "Area"},
    {"key": "ownership_type", "label": "Ownership Type"},
    {"key": "total_stand_acres", "label": "Total Stand Acres"},
    {"key": "net_productive_acres", "label": "Net Productive Acres"},
    {"key": "harvestable_acres", "label": "Harvestable Acres"},
]

OWNERSHIP_TABLE_WIDTHS = [0.13, 0.09, 0.11, 0.13, 0.13, 0.145, 0.145]

COUNTY_SUMMARY_TABLE_COLUMNS = [
    {"key": "woodbasket", "label": "Woodbasket"},
    {"key": "business", "label": "Business"},
    {"key": "region", "label": "Region"},
    {"key": "state", "label": "State"},
    {"key": "county", "label": "County"},
    {"key": "state_county_fip", "label": "State County FIP"},
    {"key": "acres_within_woodbasket", "label": "Acres Within Woodbasket"},
    {"key": "wy_ownership_acres", "label": "WY Ownership Acres"},
]

COUNTY_SUMMARY_NUMERIC_COLUMNS = [
    "acres_within_woodbasket",
    "wy_ownership_acres",
]

COUNTY_SUMMARY_TABLE_WIDTHS = [0.14, 0.08, 0.07, 0.06, 0.08, 0.13, 0.18, 0.13]

PINE_AGE_CLASS_TABLE_COLUMNS = [
    {"key": "age_class", "label": "Age Class"},
    {"key": "wy", "label": "WY"},
    {"key": "other_private", "label": "Other Private"},
]

PINE_AGE_CLASS_NUMERIC_COLUMNS = ["wy", "other_private"]
PINE_AGE_CLASS_TABLE_WIDTHS = [0.2, 0.2, 0.2]


def load_mock_cover_type_rows() -> list[dict[str, object]]:
    """Load cover type SQL-like mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "cover_type_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def load_mock_ownership_type_rows() -> list[dict[str, object]]:
    """Load ownership type SQL-like mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "ownership_type_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def load_mock_county_summary_rows() -> list[dict[str, object]]:
    """Load county summary SQL-like mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "county_summary_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def load_mock_pine_age_class_rows() -> list[dict[str, object]]:
    """Load pine acres by age class SQL-like mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "pine_acres_by_age_class_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def test_generate_pie_chart_png_aggregates_labels(tmp_path) -> None:
    """Rows with the same label should be summed into one slice."""
    from avo_utils.charts import generate_pie_chart_png

    output = str(tmp_path / "test_pie.png")
    rows = load_mock_cover_type_rows()
    result = generate_pie_chart_png(
        rows,
        label_column="broad_cover_type",
        value_column="total_stand_acres",
        output_path=output,
        title="Acres & Volume by Broad Cover Type",
    )

    # Doug Fir: 42959 + 10195 = 53154
    # White Wood: 12000 + 9000 = 21000
    # Other: 4000 + 3742 = 7742
    assert result["label_count"] == 3
    assert result["value_total"] == pytest.approx(81896.0)
    assert result["output_path"] == output
    assert result["title"] == "Acres & Volume by Broad Cover Type"


def test_generate_pie_chart_png_creates_file(tmp_path) -> None:
    """Output PNG file should exist after a successful call."""
    from avo_utils.charts import generate_pie_chart_png

    output = str(tmp_path / "test_pie.png")
    rows = load_mock_cover_type_rows()
    generate_pie_chart_png(
        rows,
        label_column="broad_cover_type",
        value_column="total_stand_acres",
        output_path=output,
    )

    import os
    assert os.path.isfile(output)


def test_generate_pie_chart_png_empty_rows_raises() -> None:
    """Empty rows should raise ValueError."""
    from avo_utils.charts import generate_pie_chart_png

    with pytest.raises(ValueError, match="rows"):
        generate_pie_chart_png([], "broad_cover_type", "harvestable_acres")


def test_generate_pie_chart_png_missing_column_raises() -> None:
    """Missing column name should raise ValueError."""
    from avo_utils.charts import generate_pie_chart_png

    rows = load_mock_cover_type_rows()
    with pytest.raises(ValueError, match="label_column"):
        generate_pie_chart_png(rows, "non_existent", "harvestable_acres")


def test_generate_bar_chart_png_for_pine_age_class(tmp_path) -> None:
    """Generic grouped bar chart should render pine age class series."""
    from avo_utils.bars import generate_bar_chart_png

    output = str(tmp_path / "pine_age_class_bar.png")
    rows = load_mock_pine_age_class_rows()
    result = generate_bar_chart_png(
        rows=rows,
        category_column="age_class",
        series_columns=["wy", "other_private"],
        output_path=output,
        title="Pine Acres by Age Class",
        y_label="Acres",
        series_labels={"wy": "WY", "other_private": "Other Private"},
    )

    import os

    assert os.path.isfile(output)
    assert result["category_count"] == 9
    assert result["series_count"] == 2
    assert result["series_totals"]["wy"] == pytest.approx(3300000.0)
    assert result["series_totals"]["other_private"] == pytest.approx(2850000.0)


def test_generate_table_png_creates_file(tmp_path) -> None:
    """Table PNG output file should exist after a successful call."""
    from avo_utils.tables import build_cover_type_summary_rows, generate_table_png

    output = str(tmp_path / "test_table.png")
    rows = load_mock_cover_type_rows()
    summary_rows, _ = build_cover_type_summary_rows(rows)
    generate_table_png(
        rows=rows,
        output_path=output,
        columns=TABLE_COLUMNS,
        numeric_columns=TABLE_NUMERIC_COLUMNS,
        summary_rows=summary_rows,
        column_widths=TABLE_WIDTHS,
        title="Cover Type Table",
    )

    import os

    assert os.path.isfile(output)


def test_generate_table_png_includes_summary_totals(tmp_path) -> None:
    """Summary totals should include Doug Fir and White Wood sums."""
    from avo_utils.tables import build_cover_type_summary_rows, generate_table_png

    output = str(tmp_path / "test_table.png")
    rows = load_mock_cover_type_rows()
    summary_rows, summary_totals = build_cover_type_summary_rows(rows)
    result = generate_table_png(
        rows=rows,
        output_path=output,
        columns=TABLE_COLUMNS,
        numeric_columns=TABLE_NUMERIC_COLUMNS,
        summary_rows=summary_rows,
        column_widths=TABLE_WIDTHS,
    )

    assert result["row_count"] == 8
    assert result["summary_row_count"] == 2
    assert summary_totals["Doug Fir"]["total_stand_acres"] == pytest.approx(
        53154.0
    )
    assert summary_totals["Doug Fir"]["net_productive_acres"] == pytest.approx(
        50500.0
    )
    assert summary_totals["Doug Fir"]["harvestable_acres"] == pytest.approx(
        34620.0
    )
    assert summary_totals["White Wood"]["total_stand_acres"] == pytest.approx(
        21000.0
    )
    assert summary_totals["White Wood"]["net_productive_acres"] == pytest.approx(
        19500.0
    )
    assert summary_totals["White Wood"]["harvestable_acres"] == pytest.approx(
        15000.0
    )


def test_generate_chart_png_placeholder() -> None:
    """Placeholder test for generic chart PNG export."""
    pass


def test_generate_ownership_type_pie_chart_png_aggregates_labels(tmp_path) -> None:
    """Ownership type pie slices should be aggregated by ownership_type."""
    from avo_utils.charts import generate_pie_chart_png

    output = str(tmp_path / "ownership_pie.png")
    rows = load_mock_ownership_type_rows()
    result = generate_pie_chart_png(
        rows,
        label_column="ownership_type",
        value_column="total_stand_acres",
        output_path=output,
        title="Acres & Volume by Ownership Type",
    )

    # Fee: 553611 + 10000 + 25000 + 12000 + 6000 + 4000 = 610611
    # Lease: 46469 + 8000 + 18000 + 7000 + 5000 = 84469
    # Timber Res: 7742 + 9000 = 16742
    assert result["label_count"] == 3
    assert result["value_total"] == pytest.approx(711822.0)
    assert result["output_path"] == output
    assert result["title"] == "Acres & Volume by Ownership Type"


def test_generate_ownership_type_table_png_creates_file(tmp_path) -> None:
    """Ownership type table PNG file should exist after a successful call."""
    from avo_utils.tables import build_grand_total_row, generate_table_png

    output = str(tmp_path / "ownership_table.png")
    rows = load_mock_ownership_type_rows()
    summary_rows, _ = build_grand_total_row(
        rows,
        sum_columns=["total_stand_acres", "net_productive_acres", "harvestable_acres"],
        label_column="business",
        label="Total",
    )
    generate_table_png(
        rows=rows,
        output_path=output,
        columns=OWNERSHIP_TABLE_COLUMNS,
        numeric_columns=TABLE_NUMERIC_COLUMNS,
        summary_rows=summary_rows,
        column_widths=OWNERSHIP_TABLE_WIDTHS,
        title="Ownership Type Table",
    )

    import os

    assert os.path.isfile(output)


def test_generate_ownership_type_table_grand_total(tmp_path) -> None:
    """Grand total row should sum all rows across all ownership types."""
    from avo_utils.tables import build_grand_total_row, generate_table_png

    output = str(tmp_path / "ownership_table.png")
    rows = load_mock_ownership_type_rows()
    summary_rows, totals = build_grand_total_row(
        rows,
        sum_columns=["total_stand_acres", "net_productive_acres", "harvestable_acres"],
        label_column="business",
        label="Total",
    )
    result = generate_table_png(
        rows=rows,
        output_path=output,
        columns=OWNERSHIP_TABLE_COLUMNS,
        numeric_columns=TABLE_NUMERIC_COLUMNS,
        summary_rows=summary_rows,
        column_widths=OWNERSHIP_TABLE_WIDTHS,
    )

    assert result["summary_row_count"] == 1
    assert totals["total_stand_acres"] == pytest.approx(711822.0)
    assert totals["net_productive_acres"] == pytest.approx(659987.0)
    assert totals["harvestable_acres"] == pytest.approx(603816.0)


def test_generate_county_summary_table_png_creates_file(tmp_path) -> None:
    """County summary table PNG should be created with a total row."""
    from avo_utils.tables import build_grand_total_row, generate_table_png

    output = str(tmp_path / "county_summary_table.png")
    rows = load_mock_county_summary_rows()
    summary_rows, _ = build_grand_total_row(
        rows,
        sum_columns=["acres_within_woodbasket", "wy_ownership_acres"],
        label_column="woodbasket",
        label="Total",
    )
    generate_table_png(
        rows=rows,
        output_path=output,
        columns=COUNTY_SUMMARY_TABLE_COLUMNS,
        numeric_columns=COUNTY_SUMMARY_NUMERIC_COLUMNS,
        summary_rows=summary_rows,
        column_widths=COUNTY_SUMMARY_TABLE_WIDTHS,
        title="County Summary Table",
    )

    import os

    assert os.path.isfile(output)


def test_generate_county_summary_table_grand_total(tmp_path) -> None:
    """County summary total row should sum the two acreage columns."""
    from avo_utils.tables import build_grand_total_row, generate_table_png

    output = str(tmp_path / "county_summary_table.png")
    rows = load_mock_county_summary_rows()
    summary_rows, totals = build_grand_total_row(
        rows,
        sum_columns=["acres_within_woodbasket", "wy_ownership_acres"],
        label_column="woodbasket",
        label="Total",
    )
    result = generate_table_png(
        rows=rows,
        output_path=output,
        columns=COUNTY_SUMMARY_TABLE_COLUMNS,
        numeric_columns=COUNTY_SUMMARY_NUMERIC_COLUMNS,
        summary_rows=summary_rows,
        column_widths=COUNTY_SUMMARY_TABLE_WIDTHS,
    )

    assert result["summary_row_count"] == 1
    assert totals["acres_within_woodbasket"] == pytest.approx(60000.0)
    assert totals["wy_ownership_acres"] == pytest.approx(21000.0)


def test_generate_pine_age_class_table_with_total(tmp_path) -> None:
    """Pine age class table should include a grand total row for WY and Other Private."""
    from avo_utils.tables import build_grand_total_row, generate_table_png

    output = str(tmp_path / "pine_age_class_table.png")
    rows = load_mock_pine_age_class_rows()
    summary_rows, totals = build_grand_total_row(
        rows,
        sum_columns=["wy", "other_private"],
        label_column="age_class",
        label="Total",
    )

    result = generate_table_png(
        rows=rows,
        output_path=output,
        columns=PINE_AGE_CLASS_TABLE_COLUMNS,
        numeric_columns=PINE_AGE_CLASS_NUMERIC_COLUMNS,
        summary_rows=summary_rows,
        column_widths=PINE_AGE_CLASS_TABLE_WIDTHS,
        title="Pine Acres by Age Class",
    )

    import os

    assert os.path.isfile(output)
    assert result["summary_row_count"] == 1
    assert totals["wy"] == pytest.approx(3300000.0)
    assert totals["other_private"] == pytest.approx(2850000.0)
