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
    {"key": "total", "label": "Total"},
    {"key": "pct_wy", "label": "% WY"},
]

PINE_AGE_CLASS_NUMERIC_COLUMNS = ["wy", "other_private", "total"]
PINE_AGE_CLASS_PERCENT_COLUMNS = ["pct_wy"]
PINE_AGE_CLASS_TABLE_WIDTHS = [0.14, 0.14, 0.16, 0.14, 0.10]

PINE_VOLUME_TABLE_COLUMNS = [
    {"key": "age_class", "label": "Age Class"},
    {"key": "wy", "label": "WY"},
    {"key": "other_private", "label": "Other Private"},
    {"key": "total", "label": "Total"},
    {"key": "pct_wy", "label": "% WY"},
]

PINE_VOLUME_NUMERIC_COLUMNS = ["wy", "other_private", "total"]
PINE_VOLUME_PERCENT_COLUMNS = ["pct_wy"]
PINE_VOLUME_TABLE_WIDTHS = [0.14, 0.14, 0.16, 0.14, 0.10]


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


def load_mock_pine_volume_rows() -> list[dict[str, object]]:
    """Load pine volume by age class SQL-like mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "pine_volume_by_age_class_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def load_mock_portfolio_attributes() -> dict[str, object]:
    """Load portfolio attributes mock data from JSON test data."""
    data_file = MOCK_DATA_DIR / "portfolio_attributes.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def test_generate_pie_chart_png_aggregates_labels(tmp_path) -> None:
    """Rows with the same label should be summed into one slice."""
    from avo_utils.pies import generate_pie_chart_png

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
    from avo_utils.pies import generate_pie_chart_png

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
    from avo_utils.pies import generate_pie_chart_png

    with pytest.raises(ValueError, match="rows"):
        generate_pie_chart_png([], "broad_cover_type", "harvestable_acres")


def test_generate_pie_chart_png_missing_column_raises() -> None:
    """Missing column name should raise ValueError."""
    from avo_utils.pies import generate_pie_chart_png

    rows = load_mock_cover_type_rows()
    with pytest.raises(ValueError, match="label_column"):
        generate_pie_chart_png(rows, "non_existent", "harvestable_acres")


def test_generate_bar_chart_png_for_pine_age_class(tmp_path) -> None:
    """Stacked bar chart should render pine age class series with colors."""
    from avo_utils.bars import generate_bar_chart_png

    output = str(tmp_path / "pine_age_class_bar.png")
    rows = load_mock_pine_age_class_rows()
    result = generate_bar_chart_png(
        rows=rows,
        category_column="age_class",
        series_columns=["wy", "other_private"],
        output_path=output,
        title="Private Pine Acres by Age Class",
        y_label="Thousands",
        series_labels={"wy": "WY", "other_private": "Other Private"},
        stacked=True,
        series_colors=["#1b5e35", "#78be43"],
        y_divisor=1000,
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


def test_generate_ownership_type_pie_chart_png_aggregates_labels(tmp_path) -> None:
    """Ownership type pie slices should be aggregated by ownership_type."""
    from avo_utils.pies import generate_pie_chart_png

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


def _enrich_pine_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Add computed total and pct_wy columns to pine age class rows."""
    enriched = []
    for row in rows:
        wy = float(row["wy"])
        other = float(row["other_private"])
        total = wy + other
        enriched.append(
            {**row, "total": total, "pct_wy": (wy / total * 100) if total else 0.0}
        )
    return enriched


def test_generate_pine_volume_bar_chart_png(tmp_path) -> None:
    """Stacked bar chart should render pine volume series with green colors."""
    from avo_utils.bars import generate_bar_chart_png

    output = str(tmp_path / "pine_volume_bar.png")
    rows = load_mock_pine_volume_rows()
    result = generate_bar_chart_png(
        rows=rows,
        category_column="age_class",
        series_columns=["wy", "other_private"],
        output_path=output,
        title="Private Pine Volume by Age Class",
        y_label="Thousands",
        series_labels={"wy": "WY", "other_private": "Other Private"},
        stacked=True,
        series_colors=["#1b5e35", "#78be43"],
        y_divisor=1000,
    )

    import os

    assert os.path.isfile(output)
    assert result["category_count"] == 9
    assert result["series_count"] == 2


def test_generate_pine_volume_table_png(tmp_path) -> None:
    """Pine volume table should include Total and % WY columns."""
    from avo_utils.tables import generate_table_png

    output = str(tmp_path / "pine_volume_table.png")
    rows = _enrich_pine_rows(load_mock_pine_volume_rows())

    result = generate_table_png(
        rows=rows,
        output_path=output,
        columns=PINE_VOLUME_TABLE_COLUMNS,
        numeric_columns=PINE_VOLUME_NUMERIC_COLUMNS,
        percent_columns=PINE_VOLUME_PERCENT_COLUMNS,
        column_widths=PINE_VOLUME_TABLE_WIDTHS,
        title="Private Pine Volume by Age Class",
    )

    import os

    assert os.path.isfile(output)
    assert result["summary_row_count"] == 0
    assert result["data_row_count"] == 9


def test_generate_portfolio_attributes_table_png_creates_file(tmp_path) -> None:
    """Portfolio attributes table PNG should be created with all sections."""
    from avo_utils.tables import generate_portfolio_attributes_table_png

    output = str(tmp_path / "portfolio_attributes_table.png")
    data = load_mock_portfolio_attributes()
    result = generate_portfolio_attributes_table_png(data=data, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["section_count"] == 4
    assert result["title"] == "Sample Woodbasket Name"


def test_generate_pine_age_class_table_with_total(tmp_path) -> None:
    """Pine table should include Total/% WY columns and a grand total row."""
    from avo_utils.tables import build_grand_total_row, generate_table_png

    output = str(tmp_path / "pine_age_class_table.png")
    rows = _enrich_pine_rows(load_mock_pine_age_class_rows())

    result = generate_table_png(
        rows=rows,
        output_path=output,
        columns=PINE_AGE_CLASS_TABLE_COLUMNS,
        numeric_columns=PINE_AGE_CLASS_NUMERIC_COLUMNS,
        percent_columns=PINE_AGE_CLASS_PERCENT_COLUMNS,
        column_widths=PINE_AGE_CLASS_TABLE_WIDTHS,
        title="Private Pine Acres by Age Class",
    )

    import os

    assert os.path.isfile(output)
    assert result["summary_row_count"] == 0
    assert result["data_row_count"] == 9


PERCENT_ACRES_TABLE_COLUMNS = [
    {"key": "region", "label": ""},
    {"key": "total", "label": "Total Stand Ac"},
    {"key": "count_1", "label": "1"},
    {"key": "count_2", "label": "2"},
    {"key": "count_3", "label": "3"},
    {"key": "count_4", "label": "4"},
    {"key": "count_5plus", "label": "5+"},
]

PERCENT_ACRES_NUMERIC_COLUMNS = ["total"]
PERCENT_ACRES_TABLE_WIDTHS = [0.10, 0.14, 0.10, 0.10, 0.10, 0.10, 0.10]


def load_mock_percent_acres_rows() -> list[dict[str, object]]:
    """Load percent acres mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "percent_acres_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def test_build_percent_acres_rows_flattens_counts() -> None:
    """build_percent_acres_rows should expand counts list into named columns."""
    from avo_utils.tables import build_percent_acres_rows

    raw_rows = load_mock_percent_acres_rows()
    rows = build_percent_acres_rows(raw_rows)

    assert len(rows) == 6
    first = rows[0]
    assert first["region"] == "AO"
    assert first["total"] == 1030646
    assert first["count_1"] == "21%"
    assert first["count_2"] == "6%"
    assert first["count_3"] == "1%"
    assert first["count_4"] == "0%"
    assert first["count_5plus"] == "0.1%"


def test_generate_percent_acres_table_png_creates_file(tmp_path) -> None:
    """Percent acres table PNG should be created with a Grand Total summary row."""
    from avo_utils.tables import build_grand_total_row, build_percent_acres_rows, generate_table_png

    output = str(tmp_path / "percent_acres_table.png")
    raw_rows = load_mock_percent_acres_rows()
    rows = build_percent_acres_rows(raw_rows)

    grand_total_rows, totals = build_grand_total_row(
        rows,
        sum_columns=["total"],
        label_column="region",
        label="Grand Total",
    )
    grand_total_rows[0].update({
        "count_1": "30%",
        "count_2": "13%",
        "count_3": "4%",
        "count_4": "1%",
        "count_5plus": "0%",
    })

    result = generate_table_png(
        rows=rows,
        output_path=output,
        columns=PERCENT_ACRES_TABLE_COLUMNS,
        numeric_columns=PERCENT_ACRES_NUMERIC_COLUMNS,
        summary_rows=grand_total_rows,
        column_widths=PERCENT_ACRES_TABLE_WIDTHS,
        title="% of Total Productive Acres with AVO Opportunities Defined",
    )

    import os

    assert os.path.isfile(output)
    assert result["data_row_count"] == 6
    assert result["summary_row_count"] == 1
    assert totals["total"] == pytest.approx(6658364.0)


def test_generate_percent_acres_table_png_to_output_dir() -> None:
    """Generate percent acres table PNG to the real output directory."""
    from avo_utils.io import DEFAULT_CHART_OUTPUT_DIR
    from avo_utils.tables import build_grand_total_row, build_percent_acres_rows, generate_table_png

    output = str(DEFAULT_CHART_OUTPUT_DIR / "tables" / "mock_percent_acres_table.png")
    raw_rows = load_mock_percent_acres_rows()
    rows = build_percent_acres_rows(raw_rows)

    grand_total_rows, _ = build_grand_total_row(
        rows,
        sum_columns=["total"],
        label_column="region",
        label="Grand Total",
    )
    grand_total_rows[0].update({
        "count_1": "30%",
        "count_2": "13%",
        "count_3": "4%",
        "count_4": "1%",
        "count_5plus": "0%",
    })

    result = generate_table_png(
        rows=rows,
        output_path=output,
        columns=PERCENT_ACRES_TABLE_COLUMNS,
        numeric_columns=PERCENT_ACRES_NUMERIC_COLUMNS,
        summary_rows=grand_total_rows,
        column_widths=PERCENT_ACRES_TABLE_WIDTHS,
        title="% of Total Productive Acres with AVO Opportunities Defined",
    )

    import os

    assert os.path.isfile(output)
    assert result["data_row_count"] == 6
    assert result["summary_row_count"] == 1


def load_mock_large_landowner_rows() -> list[dict[str, object]]:
    """Load large landowner mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "large_landowner_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def load_mock_mill_consumption_change_rows() -> list[dict[str, object]]:
    """Load mill consumption change mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "mill_consumption_change_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def load_mock_top_destination_rows() -> list[dict[str, object]]:
    """Load top destination mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "top_destination_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def load_mock_top_customer_rows() -> list[dict[str, object]]:
    """Load top customer mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "top_customer_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def load_mock_delivery_by_area_rows() -> list[dict[str, object]]:
    """Load delivery by area mock rows from JSON test data."""
    data_file = MOCK_DATA_DIR / "delivery_by_area_rows.json"
    return json.loads(data_file.read_text(encoding="utf-8"))


def test_build_large_landowner_pie_rows_top10_and_other() -> None:
    """Large landowner pie rows should include top 10 plus an Other row."""
    from avo_utils.pies import build_large_landowner_pie_rows

    rows = load_mock_large_landowner_rows()
    pie_rows, label_colors = build_large_landowner_pie_rows(rows)

    assert len(pie_rows) == 11
    assert pie_rows[0]["name"] == "Weyerhaeuser"
    assert pie_rows[1]["name"] == "Government/Tribal"
    assert pie_rows[-1]["name"] == "Other"
    assert pie_rows[-1]["total_acres"] == pytest.approx(287000.0)
    assert label_colors["Weyerhaeuser"] == "#016a3a"
    assert label_colors["Government/Tribal"] == "#efe8be"
    assert label_colors["Other"] == "#9e9e9e"


def test_generate_large_landowner_pie_chart_png_creates_file(tmp_path) -> None:
    """Large landowner pie chart should render top 10 plus Other."""
    from avo_utils.pies import generate_large_landowner_pie_chart_png

    output = str(tmp_path / "large_landowner_pie.png")
    rows = load_mock_large_landowner_rows()
    result = generate_large_landowner_pie_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["label_count"] == 11
    assert result["value_total"] == pytest.approx(6076400.0)
    assert result["title"] == "Largest Landowners (ac.)"


def test_generate_large_landowner_pie_chart_png_to_output_dir() -> None:
    """Generate large landowner pie chart PNG to the real output directory."""
    from avo_utils.io import DEFAULT_PIE_CHART_OUTPUT_DIR
    from avo_utils.pies import generate_large_landowner_pie_chart_png

    output = str(DEFAULT_PIE_CHART_OUTPUT_DIR / "mock_large_landowners_pie_chart.png")
    rows = load_mock_large_landowner_rows()
    result = generate_large_landowner_pie_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["label_count"] == 11


def test_generate_top_destination_pie_chart_png_creates_file(tmp_path) -> None:
    """Top destination pie chart should render from mock rows."""
    from avo_utils.pies import generate_top_destination_pie_chart_png

    output = str(tmp_path / "top_destination_pie.png")
    rows = load_mock_top_destination_rows()
    result = generate_top_destination_pie_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["label_count"] == 11
    assert result["value_total"] == pytest.approx(899.15)
    assert result["title"] == "MMBF"


def test_generate_top_customer_pie_chart_png_creates_file(tmp_path) -> None:
    """Top customer pie chart should render from mock rows."""
    from avo_utils.pies import generate_top_customer_pie_chart_png

    output = str(tmp_path / "top_customer_pie.png")
    rows = load_mock_top_customer_rows()
    result = generate_top_customer_pie_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["label_count"] == 11
    assert result["value_total"] == pytest.approx(828.25)
    assert result["title"] == "MMBF"


def test_generate_top_destination_pie_chart_png_to_output_dir() -> None:
    """Generate top destination pie chart PNG to the real output directory."""
    from avo_utils.io import DEFAULT_PIE_CHART_OUTPUT_DIR
    from avo_utils.pies import generate_top_destination_pie_chart_png

    output = str(DEFAULT_PIE_CHART_OUTPUT_DIR / "mock_top_destination_pie_chart.png")
    rows = load_mock_top_destination_rows()
    result = generate_top_destination_pie_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["label_count"] == 11


def test_generate_top_customer_pie_chart_png_to_output_dir() -> None:
    """Generate top customer pie chart PNG to the real output directory."""
    from avo_utils.io import DEFAULT_PIE_CHART_OUTPUT_DIR
    from avo_utils.pies import generate_top_customer_pie_chart_png

    output = str(DEFAULT_PIE_CHART_OUTPUT_DIR / "mock_top_customer_pie_chart.png")
    rows = load_mock_top_customer_rows()
    result = generate_top_customer_pie_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["label_count"] == 11


def test_build_large_landowner_bar_data_shapes_rows() -> None:
    """Large landowner bar data should shape 9 woodbasket rows and include WY series."""
    from avo_utils.bars import build_large_landowner_bar_data

    rows = load_mock_large_landowner_rows()
    chart_rows, series_columns, _, series_colors = build_large_landowner_bar_data(rows)

    assert len(chart_rows) == 9
    assert chart_rows[0]["woodbasket"] == "Longview"
    assert "Weyerhaeuser" in series_columns
    assert "Government/Tribal" not in series_columns
    assert len(series_columns) == len(series_colors)
    assert chart_rows[0]["Weyerhaeuser"] == pytest.approx(310000.0)


def test_generate_large_landowner_bar_chart_png_creates_file(tmp_path) -> None:
    """Large landowner grouped bar chart PNG should be created successfully."""
    from avo_utils.bars import generate_large_landowner_bar_chart_png

    output = str(tmp_path / "large_landowner_bar.png")
    rows = load_mock_large_landowner_rows()
    result = generate_large_landowner_bar_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["category_count"] == 9
    assert result["title"] == "Top Five Private Landowners per Woodbasket"


def test_generate_large_landowner_bar_chart_png_to_output_dir() -> None:
    """Generate large landowner grouped bar PNG to the real output directory."""
    from avo_utils.bars import generate_large_landowner_bar_chart_png
    from avo_utils.io import DEFAULT_BAR_CHART_OUTPUT_DIR

    output = str(DEFAULT_BAR_CHART_OUTPUT_DIR / "mock_large_landowners_bar_chart.png")
    rows = load_mock_large_landowner_rows()
    result = generate_large_landowner_bar_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["category_count"] == 9


def test_build_large_landowner_table_rows_shapes_owner_and_mill_rows() -> None:
    """Large landowner table rows should include top owners and nested mill rows."""
    from avo_utils.tables import build_large_landowner_table_rows

    rows = load_mock_large_landowner_rows()
    table_rows = build_large_landowner_table_rows(rows)

    assert len(table_rows) == 14
    assert table_rows[0]["rank"] == 1
    assert table_rows[0]["landowner_name"] == "Weyerhaeuser"
    assert table_rows[0]["total_acres_owned"] == pytest.approx(1882500.0)
    assert table_rows[1]["mill_name"] == "Mill A"
    assert table_rows[2]["mill_name"] == "Mill B"


def test_generate_large_landowner_table_png_creates_file(tmp_path) -> None:
    """Large landowner table PNG should be generated with top-10 owner rows."""
    from avo_utils.tables import generate_large_landowner_table_png

    output = str(tmp_path / "large_landowner_table.png")
    rows = load_mock_large_landowner_rows()
    result = generate_large_landowner_table_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["data_row_count"] == 14
    assert result["title"] == "Landowner Level Data"


def test_generate_large_landowner_table_png_to_output_dir() -> None:
    """Generate large landowner table PNG to the real output directory."""
    from avo_utils.io import DEFAULT_CHART_OUTPUT_DIR
    from avo_utils.tables import generate_large_landowner_table_png

    output = str(DEFAULT_CHART_OUTPUT_DIR / "tables" / "mock_large_landowners_table.png")
    rows = load_mock_large_landowner_rows()
    result = generate_large_landowner_table_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["data_row_count"] == 14


def test_build_mill_consumption_change_rows_recent_and_future() -> None:
    """Mill consumption table rows should match frontend-style period filters."""
    from avo_utils.tables import (
        build_mill_consumption_change_rows,
        build_mill_consumption_change_total_row,
    )

    rows = load_mock_mill_consumption_change_rows()

    recent_rows = build_mill_consumption_change_rows(
        rows,
        from_column="prev",
        to_column="curr",
    )
    future_rows = build_mill_consumption_change_rows(
        rows,
        from_column="curr",
        to_column="future",
    )
    df_recent_rows = build_mill_consumption_change_rows(
        rows,
        from_column="prev",
        to_column="curr",
        product_name="Douglas Fir",
    )

    _, recent_total = build_mill_consumption_change_total_row(recent_rows)
    _, future_total = build_mill_consumption_change_total_row(future_rows)

    assert len(recent_rows) == 7
    assert len(future_rows) == 7
    assert len(df_recent_rows) == 4
    assert recent_rows[0]["name"] == "Longview Sawmill"
    assert recent_rows[0]["change"] == pytest.approx(11.0)
    assert recent_total == pytest.approx(-22.0)
    assert future_total == pytest.approx(-170.0)


def test_generate_mill_consumption_change_table_png_creates_file(tmp_path) -> None:
    """Mill consumption table PNG should render recent-change rows and total."""
    from avo_utils.tables import generate_mill_consumption_change_table_png

    output = str(tmp_path / "mill_consumption_recent_table.png")
    rows = load_mock_mill_consumption_change_rows()
    result = generate_mill_consumption_change_table_png(
        rows,
        from_column="prev",
        to_column="curr",
        from_label="2023",
        to_label="2024",
        output_path=output,
        title="All Products - Recent Changes",
        total_label="Total Change",
    )

    import os

    assert os.path.isfile(output)
    assert result["data_row_count"] == 7
    assert result["summary_row_count"] == 1
    assert result["total_change"] == pytest.approx(-22.0)


def test_generate_mill_consumption_change_future_table_with_prev_column(tmp_path) -> None:
    """Future mill table should support showing 2023 while changing 2024 -> 2029."""
    from avo_utils.tables import generate_mill_consumption_change_table_png

    output = str(tmp_path / "mill_consumption_future_table_with_prev.png")
    rows = load_mock_mill_consumption_change_rows()
    result = generate_mill_consumption_change_table_png(
        rows,
        from_column="curr",
        to_column="future",
        from_label="2024",
        to_label="2029",
        include_prev_column=True,
        prev_column="prev",
        prev_label="2023",
        output_path=output,
        title="All Products - Future Changes",
        total_label="Total Change",
    )

    import os

    assert os.path.isfile(output)
    assert result["data_row_count"] == 7
    assert result["summary_row_count"] == 1
    assert result["total_change"] == pytest.approx(-170.0)


def test_generate_mill_consumption_change_table_defaults_recent_labels(tmp_path) -> None:
    """Recent table should default to Mill/2023/2024/Change labels."""
    from avo_utils.tables import generate_mill_consumption_change_table_png

    output = str(tmp_path / "mill_consumption_df_recent_default_labels.png")
    rows = load_mock_mill_consumption_change_rows()
    result = generate_mill_consumption_change_table_png(
        rows,
        from_column="prev",
        to_column="curr",
        product_name="Douglas Fir",
        output_path=output,
        title="Recent Changes",
        total_label="Total Change DF",
    )

    assert result["column_labels"] == ["Mill", "2023", "2024", "Change"]
    assert result["column_keys"] == ["name", "prev", "curr", "change"]
    assert result["total_change"] == pytest.approx(7.0)


def test_generate_mill_consumption_change_table_defaults_future_labels(tmp_path) -> None:
    """Future table should default to Mill/2023/2024/2029/Change labels."""
    from avo_utils.tables import generate_mill_consumption_change_table_png

    output = str(tmp_path / "mill_consumption_ww_future_default_labels.png")
    rows = load_mock_mill_consumption_change_rows()
    result = generate_mill_consumption_change_table_png(
        rows,
        from_column="curr",
        to_column="future",
        product_name="Whitewood",
        output_path=output,
        title="Future Changes",
        total_label="Total Change WW",
    )

    assert result["column_labels"] == ["Mill", "2023", "2024", "2029", "Change"]
    assert result["column_keys"] == ["name", "prev", "curr", "future", "change"]
    assert result["total_change"] == pytest.approx(-156.0)


def test_generate_mill_consumption_change_bar_chart_png_creates_file(tmp_path) -> None:
    """Mill consumption grouped bar PNG should render 2023/2024/future series."""
    from avo_utils.bars import generate_mill_consumption_change_bar_chart_png

    output = str(tmp_path / "mill_consumption_bar.png")
    rows = load_mock_mill_consumption_change_rows()
    result = generate_mill_consumption_change_bar_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["category_count"] == 9
    assert result["series_count"] == 3
    assert result["series_totals"]["prev"] == pytest.approx(625.0)
    assert result["series_totals"]["curr"] == pytest.approx(603.0)
    assert result["series_totals"]["future"] == pytest.approx(743.0)


def test_build_delivery_by_area_bar_data_shapes_rows() -> None:
    """Delivery-by-area bar data should preserve area order and series columns."""
    from avo_utils.bars import build_delivery_by_area_bar_data

    rows = load_mock_delivery_by_area_rows()
    chart_rows, series_columns, series_labels, series_colors = build_delivery_by_area_bar_data(rows)

    assert len(chart_rows) == 10
    assert chart_rows[0]["area"] == "Longview"
    assert chart_rows[0]["export"] == pytest.approx(60.0)
    assert series_columns == ["export", "domestic_internal", "domestic_third_party"]
    assert series_labels["domestic_third_party"] == "Domestic 3rd Party"
    assert len(series_colors) == 3


def test_generate_delivery_by_area_bar_chart_png_creates_file(tmp_path) -> None:
    """Delivery-by-area stacked bar PNG should render all areas and series totals."""
    from avo_utils.bars import generate_delivery_by_area_bar_chart_png

    output = str(tmp_path / "delivery_by_area_bar.png")
    rows = load_mock_delivery_by_area_rows()
    result = generate_delivery_by_area_bar_chart_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["category_count"] == 10
    assert result["series_count"] == 3
    assert result["series_totals"]["export"] == pytest.approx(242.0)
    assert result["series_totals"]["domestic_internal"] == pytest.approx(465.0)
    assert result["series_totals"]["domestic_third_party"] == pytest.approx(303.0)


def test_build_delivery_by_area_table_rows_pivots_series() -> None:
    """Delivery-by-area table rows should pivot to three series rows."""
    from avo_utils.tables import build_delivery_by_area_table_rows

    rows = load_mock_delivery_by_area_rows()
    table_rows, area_names = build_delivery_by_area_table_rows(rows)

    assert len(table_rows) == 3
    assert area_names[0] == "Longview"
    assert table_rows[0]["series"] == "Export"
    assert table_rows[0]["Longview"] == pytest.approx(60.0)
    assert table_rows[1]["series"] == "Domestic Internal"
    assert table_rows[2]["series"] == "Domestic 3rd Party"


def test_generate_delivery_by_area_table_png_creates_file(tmp_path) -> None:
    """Delivery-by-area table PNG should render a 3-row matrix table."""
    from avo_utils.tables import generate_delivery_by_area_table_png

    output = str(tmp_path / "delivery_by_area_table.png")
    rows = load_mock_delivery_by_area_rows()
    result = generate_delivery_by_area_table_png(rows=rows, output_path=output)

    import os

    assert os.path.isfile(output)
    assert result["data_row_count"] == 3


def test_generate_delivery_by_area_outputs_to_output_dir() -> None:
    """Generate delivery-by-area chart and table PNGs to real output directories."""
    from avo_utils.bars import generate_delivery_by_area_bar_chart_png
    from avo_utils.io import DEFAULT_BAR_CHART_OUTPUT_DIR, DEFAULT_CHART_OUTPUT_DIR
    from avo_utils.tables import generate_delivery_by_area_table_png

    rows = load_mock_delivery_by_area_rows()
    bar_output = str(DEFAULT_BAR_CHART_OUTPUT_DIR / "mock_delivery_by_area_bar_chart.png")
    table_output = str(DEFAULT_CHART_OUTPUT_DIR / "tables" / "mock_delivery_by_area_table.png")

    bar_result = generate_delivery_by_area_bar_chart_png(rows=rows, output_path=bar_output)
    table_result = generate_delivery_by_area_table_png(rows=rows, output_path=table_output)

    import os

    assert os.path.isfile(bar_output)
    assert os.path.isfile(table_output)
    assert bar_result["category_count"] == 10
    assert table_result["data_row_count"] == 3
