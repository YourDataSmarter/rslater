from __future__ import annotations

import re

API_BASE = "https://api.github.com/orgs/YourDataSmarter/repos"

# Ignore heavy/generated paths when scanning source trees.
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    "vendor",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".styl",
    ".java",
    ".cs",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".swift",
    ".kt",
    ".scala",
    ".m",
    ".mm",
}

CONFIG_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "tsconfig.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".github/workflows",
}

REACT_DEPENDENCIES = {"react", "react-dom"}
ESRI_DEPENDENCIES = {"@arcgis/core", "esri-loader", "arcgis-js-api"}
TYPESCRIPT_DEPENDENCIES = {"typescript"}
JS_TS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}
STYLE_EXTENSIONS = {".css", ".scss", ".sass", ".less", ".styl"}
WIDGET_PATH_HINTS = (
    "widgets/",
    "widget/",
    "components/map",
    "map/widgets",
    "webmap",
)

REACT_IMPORT_PATTERN = re.compile(r"(?:from\s+['\"]react['\"]|require\(['\"]react['\"]\))")
CSS_IMPORT_PATTERN = re.compile(
    r"(?:from\s+['\"][^'\"]+\.(?:css|scss|sass|less|styl)['\"]|import\s+['\"][^'\"]+\.(?:css|scss|sass|less|styl)['\"])",
    flags=re.IGNORECASE,
)
ESRI_IMPORT_PATTERN = re.compile(
    r"(?:from\s+['\"]@arcgis/core|from\s+['\"]esri/|require\(['\"]@arcgis/core|require\(['\"]esri/|arcgis/core|esri/)",
    flags=re.IGNORECASE,
)
WIDGET_NAME_PATTERN = re.compile(
    r"\b(widget|mapwidget|layercontrol|basemaptoggle|toolpanel|legend|popup)\b",
    flags=re.IGNORECASE,
)
MAP_UI_WIRING_PATTERN = re.compile(
    r"(?:view\.ui\.add|new\s+MapView|new\s+WebMap|container\s*:|new\s+WebScene)",
    flags=re.IGNORECASE,
)
