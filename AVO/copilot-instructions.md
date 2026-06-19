# Copilot Instructions for AVO-Python

## Repository Purpose

This repository is a temporary development location for reusable, generic Python utilities used by the AVO app.

Primary utility scope:
- Generate PNG exports of web maps
- Generate PNG chart images (pie, bar, and other chart types)
- Generate CSV exports of data

## Current Constraints

- Treat this repo as an evolving staging area until a final location is chosen.
- Keep implementations portable and avoid environment-specific assumptions.
- Prioritize clear function boundaries and backward-compatible changes where practical.

## Coding Expectations

- Write generic, reusable utilities rather than one-off workflow code.
- Prefer small, focused functions with explicit inputs/outputs.
- Use type hints for public functions.
- Include docstrings for public functions and non-obvious behavior.
- Raise clear, actionable exceptions.
- Avoid hardcoded paths, credentials, and machine-specific config.

## Python Style Requirements

- Follow PEP 8 for all Python code.
- Use 4 spaces per indentation level (no tabs).
- Keep lines within PEP 8 limits (generally 79 chars for code, 72 for docstrings where practical).
- Use `snake_case` for functions/variables, `PascalCase` for classes, and `UPPER_CASE` for constants.
- Group imports according to PEP 8: standard library, third-party, then local imports.
- Prefer one class/function per logical responsibility and avoid overly long functions.

## Docstring Requirements (Sphinx Style)

- Use Sphinx/reStructuredText style docstrings for public modules, classes, and functions.
- Start docstrings with a short imperative summary line.
- Document parameters with `:param <name>:` and optional types with `:type <name>:` when useful.
- Document return values with `:returns:` and `:rtype:`.
- Document raised exceptions with `:raises <ExceptionType>:`.

Example:

```python
def export_csv(rows: list[dict], output_path: str) -> str:
    """Write tabular data to a CSV file.

    :param rows: Row data to write.
    :type rows: list[dict]
    :param output_path: Destination CSV path.
    :type output_path: str
    :returns: Absolute path to the written CSV file.
    :rtype: str
    :raises ValueError: If rows is empty.
    """
```

## Export Function Behavior

For map/chart/CSV utilities:
- Accept plain Python structures (lists/dicts) and/or DataFrame-like inputs when appropriate.
- Allow explicit output file paths and deterministic naming.
- Return useful metadata where appropriate (for example output path, dimensions, row counts).
- Validate inputs early and fail with understandable messages.

## Suggested Module Responsibilities

If creating or updating modules, prefer this split:
- `maps.py`: web map to PNG helpers
- `charts.py`: chart image generation helpers
- `exports.py`: CSV export helpers
- `io.py`: shared file/path/output utilities

## Testing Expectations

- Add or update unit tests for any new behavior.
- Cover success and failure paths for export functions.
- Keep tests deterministic (no network dependence unless explicitly required and mocked).

## Documentation Expectations

- Keep `README.md` aligned with implementation status.
- When adding new utility capabilities, update README scope/examples accordingly.
- Use concise examples in docstrings or docs for public APIs.

## Change Priorities

When there are tradeoffs, prioritize in this order:
1. Correctness of generated outputs (PNG/CSV)
2. Reusability and API clarity
3. Testability and maintainability
4. Performance optimizations

## Non-Goals (Unless Explicitly Requested)

- Building app-specific UI workflows
- Embedding environment-locked deployment logic
- Introducing heavy framework dependencies without clear utility value
