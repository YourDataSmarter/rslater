"""Shared layout and display configuration for AVO bar charts."""

BAR_FIGURE_SIZE: tuple[float, float] = (11.0, 6.0)
BAR_DPI: int = 150
BAR_STACKED_WIDTH: float = 0.6
BAR_GROUP_WIDTH: float = 0.8
BAR_GROUP_WIDTH_SCALE: float = 0.95
BAR_VALUE_LABEL_FONT_SIZE: int = 8
BAR_VALUE_LABEL_COLOR: str = "#4a4a4a"
BAR_GRID_LINESTYLE: str = "--"
BAR_GRID_ALPHA: float = 0.35

LARGE_LANDOWNER_BAR_TITLE: str = "Top Five Private Landowners per Woodbasket"
LARGE_LANDOWNER_BAR_Y_LABEL: str = "Thousands of Acres"
LARGE_LANDOWNER_BAR_Y_DIVISOR: float = 1000.0

MILL_CONSUMPTION_BAR_SERIES_LABELS: dict[str, str] = {
    "prev": "2023",
    "curr": "2024",
    "future": "2028/2029 ESH/WHITE",
}
MILL_CONSUMPTION_BAR_SERIES_COLORS: list[str] = ["#b0c4de", "#6495ed", "#4682b4"]
MILL_CONSUMPTION_BAR_TITLE: str = "Expected Log Consumption Changes 2023 - 2028/2029 (MMBF)"
MILL_CONSUMPTION_BAR_Y_LABEL: str = "MMBF"

DELIVERY_BY_AREA_BAR_SERIES_LABELS: dict[str, str] = {
    "export": "Export",
    "domestic_internal": "Domestic Internal",
    "domestic_third_party": "Domestic 3rd Party",
}
DELIVERY_BY_AREA_BAR_SERIES_COLORS: list[str] = ["#58a8db", "#b8d871", "#efd35e"]
DELIVERY_BY_AREA_BAR_TITLE: str = "2023 Combined DF/WW Deliveries by Area"
DELIVERY_BY_AREA_BAR_Y_LABEL: str = "MMBF"