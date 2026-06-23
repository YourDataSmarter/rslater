"""Tests for shared output naming helpers."""

from datetime import date


def test_build_visual_output_path_uses_component_title_and_kind() -> None:
    """Visual output paths should follow the shared component-title-kind convention."""
    from avo_utils.io import build_visual_output_path

    output = build_visual_output_path(
        "Delivery By Area",
        "Mill Mix",
        "graph",
        output_dir="output/charts/bar",
        suffix=".png",
    )

    assert output.name == "delivery_by_area_woodbasket-title_graph.png"


def test_build_data_export_output_path_uses_component_visual_user_and_date() -> None:
    """Data export paths should follow the shared component-visual-user-date convention."""
    from avo_utils.io import build_data_export_output_path

    output = build_data_export_output_path(
        "Delivery By Area",
        "Mill Mix",
        "Riley Slater",
        export_date=date(2026, 6, 23),
        output_dir="output/csv",
    )

    assert output.name == "delivery_by_area_mill_mix_riley_slater_20260623.csv"