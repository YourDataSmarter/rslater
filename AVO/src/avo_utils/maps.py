"""Map image export utilities for AVO."""

from typing import Any

from .io import DEFAULT_WEBMAP_OUTPUT_DIR


def generate_webmap_png(
    map_config: dict[str, Any],
    output_path: str = str(DEFAULT_WEBMAP_OUTPUT_DIR / "webmap.png"),
    *,
    width: int = 1920,
    height: int = 1080,
) -> dict[str, Any]:
    """Generate a PNG export from a web map definition.

    :param map_config: Serialized map configuration data.
    :type map_config: dict[str, Any]
    :param output_path: Destination path for the PNG file.
    :type output_path: str
    :param width: Desired image width in pixels.
    :type width: int
    :param height: Desired image height in pixels.
    :type height: int
    :returns: Metadata about the generated image.
    :rtype: dict[str, Any]
    :raises ValueError: If inputs are invalid.
    """
    pass
