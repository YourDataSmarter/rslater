# AVO Python Utilities (Temporary Dev Location)

This folder contains reusable, generic Python functions for the AVO app.

It is currently a temporary development location while the long-term repository/package location is being finalized.

## Purpose

The goal of this project is to provide common utility functions that can be shared across AVO features and services, especially for report/export generation.

## Planned Capabilities

The utilities in this folder are intended to generate:

- PNG exports of web maps
- PNG chart images, including:
	- pie charts
	- bar charts
	- additional chart types as needed
- CSV exports of tabular/report data

## Design Intent

These utilities should be:

- Generic: independent of one specific workflow whenever possible
- Reusable: easy to call from multiple AVO code paths
- Consistent: predictable inputs, outputs, and error handling
- Testable: functions should be straightforward to unit test

## Project Structure

As this grows, keep functions grouped by responsibility:

```text
AVO/
	README.md
	copilot-instructions.md
	output/
		webmaps/
		charts/
			pie/
			bar/
			tables/
		csv/
	src/
		avo_utils/
			__init__.py
			configs/
				color_config.py
				pies_config.py
				bars_config.py
				tables_config.py
			maps.py        # web map to PNG helpers
			pies.py        # pie chart PNG helpers
			bars.py        # bar chart PNG helpers
			tables.py      # table PNG helpers
			csv.py         # CSV export helpers
			io.py          # shared file/path/output helpers
	tests/
		mock_data/
			cover_type_rows.json
		test_maps.py
		test_charts.py
		test_exports.py
```

## Example Function Scope

- `generate_webmap_png(...)`
- `generate_pie_chart_png(...)`
- `generate_table_png(...)`
- `build_cover_type_summary_rows(...)` (optional edge-case helper for this specific table)
- `generate_bar_chart_png(...)`
- `export_csv(...)`

## Input/Output Expectations

Recommended behavior for utility functions:

- Accept plain Python data structures (lists/dicts) or data frames
- Support explicit output paths and file naming
- PDF and PNG visual exports are supported; format can be inferred from the output file suffix or requested via `export_format`
- Default visual filenames follow `[analysis component]_woodbasket-title_{map|graph|table}.[format]` when convention metadata is supplied or specialized helpers are used
- Per-visual CSV exports default to separate files named `[Component]_[VisualName]_[User]_[Date].csv` when `component_name`, `visual_name`, and `exported_by` are provided to `export_csv(...)`
- Return metadata where useful (for example, output path, width/height, row counts)
- Raise clear exceptions with actionable error messages

## Current Status

- Project status: active early development
- Location status: temporary
- API status: expected to evolve while requirements are refined
- Module scaffold status: created (`src/avo_utils` and `tests`)
- Function status: `generate_webmap_png`, `generate_pie_chart_png`, `generate_bar_chart_png`, `generate_table_png`, and `export_csv` are implemented; chart, table, and webmap visual exports support PNG and PDF output, and table logic supports optional summary rows and edge-case helper totals in `src/avo_utils/tables.py`
- Map template status: `generate_webmap_png` supports template-driven ArcPy PNG/PDF export from PAGX/APRX configs, but template-backed behavioral testing is still pending until real templates are available.
- Test data status: chart mock rows moved to external JSON under `tests/mock_data/`
- Pie and table chart tests: implemented and passing against file-based mock data
- Local output folders: created under `output/` for webmaps, charts, pdf, and csv
- Default output paths: wired through shared constants in `src/avo_utils/io.py`; path normalization, naming-convention builders, and output-directory helpers are implemented

## README Maintenance

To keep this README aligned with active development:

- Update this file in the same change whenever function signatures are added/removed/renamed.
- Update folder structure docs whenever files or directories are added, moved, or deleted.
- Update Current Status whenever implementation milestones change (for example, stubs to working logic).
- Keep examples synchronized with real public function names in `src/avo_utils/`.
- Keep output path conventions synchronized with constants defined in `src/avo_utils/io.py`.

Quick checklist for each meaningful code change:

1. Does the documented project structure still match the repository?
2. Do documented function names and responsibilities match actual modules?
3. Do output folder/path docs still match defaults used by code?
4. Does Current Status still describe what is actually implemented?
5. If behavior changed, is there a short note in this README about it?

## Contribution Notes

While this remains in a temporary location:

- Keep functions narrowly scoped and well documented
- Avoid hardcoding environment-specific paths/config
- Prefer backward-compatible changes when possible
- Add or update tests with any new utility behavior

## Next Steps

1. Confirm final package/repository location.
2. Implement function logic for map/chart/CSV exports.
3. Replace placeholder tests with behavioral unit tests.
4. Add sample usage scripts for common export workflows.
5. Add dependency and environment setup instructions.
