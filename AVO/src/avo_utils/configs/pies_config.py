"""Shared layout and rendering configuration for AVO pie charts."""

# Figure dimensions
PIE_FIGURE_SIZE: tuple[float, float] = (8.0, 8.0)
PIE_DPI: int = 150

# Default pie radius and legend position for standard pies.
# legend_bbox_y is in axes coordinates; tight_layout() + bbox_inches="tight"
# in savefig includes the legend in the saved image without clipping.
PIE_DEFAULT_RADIUS: float = 1.0
PIE_DEFAULT_LEGEND_Y: float = -0.02
PIE_DEFAULT_LEGEND_NCOL_MAX: int = 3

# Layout overrides for the top-destination / top-customer 11-item pies.
# ncol=4 → 3 legend rows so the legend stays compact and clear of the pie.
TOP_PIE_RADIUS: float = 0.74
TOP_PIE_LEGEND_Y: float = -0.02
TOP_PIE_LEGEND_NCOL: int = 4
TOP_CUSTOMER_PIE_RADIUS: float = 0.74
TOP_CUSTOMER_PIE_LEGEND_Y: float = -0.02

# Large landowner: 11 items, 4 cols = 3 legend rows.
LARGE_LANDOWNER_PIE_LEGEND_NCOL: int = 4
