#!/usr/bin/env python3
"""Web app entry point for Portfolio Insights."""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("web.portfolio_web.web_app:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
