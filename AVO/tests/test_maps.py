"""Tests for map export utilities."""

from pathlib import Path

import pytest


def test_generate_webmap_png_requires_template_path() -> None:
    """Map config must include a template path."""
    from avo_utils.maps import generate_webmap_png

    with pytest.raises(ValueError, match="template_path"):
        generate_webmap_png({})


def test_generate_webmap_png_requires_positive_dimensions() -> None:
    """Width and height must be positive values."""
    from avo_utils.maps import generate_webmap_png

    with pytest.raises(ValueError, match="positive"):
        generate_webmap_png({"template_path": "dummy.pagx"}, width=0, height=1080)


def test_generate_webmap_png_raises_import_error_without_arcpy(monkeypatch, tmp_path) -> None:
    """Function should raise a clear error when ArcPy is unavailable."""
    from avo_utils import maps

    original_import_module = maps.importlib.import_module

    def _fake_import_module(name: str):
        if name == "arcpy":
            raise ModuleNotFoundError("No module named 'arcpy'")
        return original_import_module(name)

    monkeypatch.setattr(maps.importlib, "import_module", _fake_import_module)
    template_path = tmp_path / "template.pagx"
    template_path.write_text("placeholder", encoding="utf-8")

    with pytest.raises(ImportError, match="arcpy is required"):
        maps.generate_webmap_png(
            {"template_path": str(template_path)},
            output_path=str(tmp_path / "map.png"),
        )


def test_generate_webmap_pdf_dispatches_to_pdf_export(monkeypatch, tmp_path) -> None:
    """PDF output paths should call ArcPy PDF export instead of PNG export."""
    from avo_utils import maps

    calls: list[tuple[str, str]] = []

    class FakeLayout:
        def listElements(self, element_type: str):
            return []

        def exportToPNG(self, output_path: str, **kwargs):
            calls.append(("png", output_path))
            Path(output_path).write_text("png", encoding="utf-8")

        def exportToPDF(self, output_path: str, **kwargs):
            calls.append(("pdf", output_path))
            Path(output_path).write_text("pdf", encoding="utf-8")

    class FakeArcPy:
        pass

    template_path = tmp_path / "template.pagx"
    template_path.write_text("placeholder", encoding="utf-8")

    monkeypatch.setattr(maps, "_get_arcpy_module", lambda: FakeArcPy())
    monkeypatch.setattr(maps, "_resolve_layout", lambda arcpy, map_config: FakeLayout())

    result = maps.generate_webmap_png(
        {"template_path": str(template_path)},
        output_path=str(tmp_path / "map.pdf"),
    )

    assert Path(result["output_path"]).is_file()
    assert result["output_path"].endswith(".pdf")
    assert result["export_format"] == "pdf"
    assert calls == [("pdf", str(tmp_path / "map.pdf"))]
