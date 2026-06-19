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
		csv/
	src/
		avo_utils/
			__init__.py
			maps.py        # web map to PNG helpers
			charts.py      # pie/bar/other chart PNG helpers
			exports.py     # CSV export helpers
			io.py          # shared file/path/output helpers
	tests/
		test_maps.py
		test_charts.py
		test_exports.py
```

## Example Function Scope

- `generate_webmap_png(...)`
- `generate_pie_chart_png(...)`
- `generate_bar_chart_png(...)`
- `generate_chart_png(...)` (generic chart dispatcher)
- `export_csv(...)`

## Input/Output Expectations

Recommended behavior for utility functions:

- Accept plain Python data structures (lists/dicts) or data frames
- Support explicit output paths and file naming
- Return metadata where useful (for example, output path, width/height, row counts)
- Raise clear exceptions with actionable error messages

## Current Status

- Project status: active early development
- Location status: temporary
- API status: expected to evolve while requirements are refined
- Module scaffold status: created (`src/avo_utils` and `tests`)
- Function status: signatures and docstrings are in place; logic is intentionally not implemented yet (`pass` stubs)
- Local output folders: created under `output/` for webmaps, charts, and csv
- Default output paths: wired in stubs through shared constants in `src/avo_utils/io.py`

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
