"""Map image export utilities for AVO."""

import importlib
from pathlib import Path
from typing import Any

from .io import DEFAULT_WEBMAP_OUTPUT_DIR
from .io import ensure_output_directory
from .io import normalize_output_path


def _get_arcpy_module() -> Any:
    """Return ArcPy module or raise a clear import error."""
    try:
        return importlib.import_module("arcpy")
    except ModuleNotFoundError as exc:
        raise ImportError(
            "arcpy is required to generate web map PNG files"
        ) from exc


def _resolve_layout(arcpy: Any, map_config: dict[str, Any]) -> Any:
    """Resolve a layout object from a PAGX or APRX template."""
    template_path = str(map_config.get("template_path", "")).strip()
    if not template_path:
        raise ValueError("map_config must include a non-empty 'template_path'")

    template = Path(template_path).expanduser().resolve()
    if not template.is_file():
        raise ValueError(f"template_path does not exist: {template}")

    template_type = str(map_config.get("template_type", "pagx")).strip().lower()
    if template_type == "pagx":
        return arcpy.mp.ConvertLayoutFileToLayout(str(template))

    if template_type == "aprx":
        project = arcpy.mp.ArcGISProject(str(template))
        layout_name = str(map_config.get("layout_name", "")).strip()
        if layout_name:
            layouts = project.listLayouts(layout_name)
        else:
            layouts = project.listLayouts()
        if not layouts:
            raise ValueError("no matching layouts found in APRX template")
        return layouts[0]

    raise ValueError("template_type must be either 'pagx' or 'aprx'")


def _apply_layer_queries(layout: Any, layer_queries: dict[str, str]) -> int:
    """Apply definition queries to named layers in the first map frame."""
    if not layer_queries:
        return 0

    map_frames = layout.listElements("MAPFRAME_ELEMENT")
    if not map_frames:
        raise ValueError("layout does not contain a map frame")

    target_map = map_frames[0].map
    layers = target_map.listLayers()
    applied = 0
    for layer in layers:
        if layer.name in layer_queries:
            layer.definitionQuery = str(layer_queries[layer.name])
            applied += 1
    return applied


def _apply_text_overrides(layout: Any, text_elements: dict[str, Any]) -> int:
    """Apply text substitutions to named text elements."""
    if not text_elements:
        return 0

    updated = 0
    for element in layout.listElements("TEXT_ELEMENT"):
        if element.name in text_elements:
            element.text = str(text_elements[element.name])
            updated += 1
    return updated


def _apply_zoom_to_layer(layout: Any, extent_layer_name: str | None) -> bool:
    """Pan/zoom the first map frame camera to a named layer extent."""
    if not extent_layer_name:
        return False

    map_frames = layout.listElements("MAPFRAME_ELEMENT")
    if not map_frames:
        raise ValueError("layout does not contain a map frame")

    map_frame = map_frames[0]
    target_layers = [
        layer for layer in map_frame.map.listLayers() if layer.name == extent_layer_name
    ]
    if not target_layers:
        raise ValueError(
            f"extent_layer '{extent_layer_name}' was not found in the map"
        )

    extent = map_frame.getLayerExtent(target_layers[0])
    map_frame.panToExtent(extent)
    return True


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
    if not isinstance(map_config, dict):
        raise ValueError("map_config must be a dict")

    if width < 1 or height < 1:
        raise ValueError("width and height must be positive integers")

    template_path = str(map_config.get("template_path", "")).strip()
    if not template_path:
        raise ValueError("map_config must include a non-empty 'template_path'")

    template = Path(template_path).expanduser().resolve()
    if not template.is_file():
        raise ValueError(f"template_path does not exist: {template}")

    resolved_output = normalize_output_path(output_path, suffix=".png")
    ensure_output_directory(str(resolved_output))

    arcpy = _get_arcpy_module()
    layout = _resolve_layout(arcpy, map_config)

    layer_queries = map_config.get("layer_queries", {})
    if layer_queries and not isinstance(layer_queries, dict):
        raise ValueError("map_config['layer_queries'] must be a dict[str, str]")

    text_elements = map_config.get("text_elements", {})
    if text_elements and not isinstance(text_elements, dict):
        raise ValueError("map_config['text_elements'] must be a dict[str, Any]")

    extent_layer = map_config.get("extent_layer")
    if extent_layer is not None and not isinstance(extent_layer, str):
        raise ValueError("map_config['extent_layer'] must be a string when provided")

    export_options = map_config.get("export_options", {})
    if export_options and not isinstance(export_options, dict):
        raise ValueError("map_config['export_options'] must be a dict[str, Any]")

    queries_applied = _apply_layer_queries(layout, layer_queries)
    text_overrides_applied = _apply_text_overrides(layout, text_elements)
    zoom_applied = _apply_zoom_to_layer(layout, extent_layer)

    try:
        layout.exportToPNG(str(resolved_output), **export_options)
    except TypeError as exc:
        raise ValueError(f"invalid export_options for ArcPy exportToPNG: {exc}") from exc

    return {
        "output_path": str(resolved_output),
        "width_px": width,
        "height_px": height,
        "queries_applied": queries_applied,
        "text_overrides_applied": text_overrides_applied,
        "zoom_applied": zoom_applied,
        "template_path": str(map_config.get("template_path", "")),
        "template_type": str(map_config.get("template_type", "pagx")).lower(),
    }
