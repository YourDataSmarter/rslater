"""Shared layout and display configuration for AVO tables."""

DEFAULT_TABLE_DPI: int = 150
DEFAULT_TABLE_EDGE_COLOR: str = "#c8cdd0"
DEFAULT_TABLE_HEADER_BACKGROUND: str = "#f3f6f7"
DEFAULT_TABLE_SUMMARY_BACKGROUND: str = "#eef2f1"
DEFAULT_TABLE_SUMMARY_TEXT_COLOR: str = "#0b3d4a"
DEFAULT_TABLE_LINE_WIDTH: float = 0.5
DEFAULT_TABLE_FONT_SIZE: int = 10
DEFAULT_TABLE_SCALE_Y: float = 1.2

MILL_CONSUMPTION_YEAR_LABELS: dict[str, str] = {
    "prev": "2023",
    "curr": "2024",
    "future": "2029",
}
MILL_CONSUMPTION_ROW_STYLES: dict[str, tuple[str, str]] = {
    "increase": ("#86d98b", "#111111"),
    "new": ("#86d98b", "#111111"),
    "decrease": ("#e7e2bc", "#111111"),
    "at-risk": ("#f9ad00", "#111111"),
    "closure": ("#ff6448", "#ffffff"),
}
MILL_CONSUMPTION_CHANGE_SUFFIXES: dict[str, str] = {"change": " MMBF"}
MILL_CONSUMPTION_TABLE_COLUMN_WIDTHS: list[float] = [0.46, 0.14, 0.14, 0.14]
MILL_CONSUMPTION_TABLE_COLUMN_WIDTHS_WITH_PREV: list[float] = [0.39, 0.12, 0.12, 0.12, 0.12]
MILL_CONSUMPTION_TABLE_FIGURE_WIDTH: float = 10.0

DELIVERY_BY_AREA_TABLE_ROW_BACKGROUND_COLORS: list[str] = ["#58a8db", "#b8d871", "#efd35e"]
DELIVERY_BY_AREA_TABLE_ROW_TEXT_COLORS: list[str] = ["#ffffff", "#1a1a1a", "#1a1a1a"]
DELIVERY_BY_AREA_TABLE_FIRST_COLUMN_WIDTH: float = 0.16
DELIVERY_BY_AREA_TABLE_REMAINING_WIDTH: float = 0.84
DELIVERY_BY_AREA_TABLE_FIGURE_WIDTH: float = 14.0

LARGE_LANDOWNER_TABLE_COLUMNS: list[dict[str, str]] = [
    {"key": "rank", "label": "Rank"},
    {"key": "landowner_name", "label": "Landowner Name"},
    {"key": "total_acres_owned", "label": "Total Acres Owned"},
    {"key": "acres_within_woodbasket", "label": "Acres Within Woodbasket"},
    {"key": "mill_name", "label": "Mill Name"},
    {"key": "city", "label": "City"},
    {"key": "state", "label": "State"},
    {"key": "county", "label": "County"},
    {"key": "ils_id", "label": "ILS_ID"},
    {"key": "forisk_id", "label": "Forisk_ID"},
    {"key": "lims_destination_id", "label": "LIMS_Destination_ID"},
]
LARGE_LANDOWNER_TABLE_NUMERIC_COLUMNS: list[str] = [
    "rank",
    "total_acres_owned",
    "acres_within_woodbasket",
]
LARGE_LANDOWNER_TABLE_COLUMN_WIDTHS: list[float] = [
    0.05,
    0.17,
    0.11,
    0.12,
    0.12,
    0.075,
    0.05,
    0.08,
    0.07,
    0.07,
    0.135,
]
LARGE_LANDOWNER_TABLE_FIGURE_WIDTH: float = 15.5
LARGE_LANDOWNER_TABLE_TITLE: str = "Landowner Level Data"