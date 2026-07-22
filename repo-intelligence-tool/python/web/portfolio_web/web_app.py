from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from core.portfolio_core.auth import CredentialLookupError, read_windows_generic_credential
from core.portfolio_core.agent import answer_portfolio_question_with_agent, get_agent_status
from core.portfolio_core.constants import API_BASE
from core.portfolio_core.github_api import infer_org_from_api_base
from core.portfolio_core.service import build_default_output_path, load_report, run_inventory_scan
from core.portfolio_core.store import index_report, load_latest_report


class ScanRequest(BaseModel):
    org: str | None = None
    credential_target: str | None = None
    token_env: str = "GITHUB_TOKEN"
    clone_root: str = "./.cache/org-repo-clones"
    output_path: str | None = None
    clone_enabled: bool = False
    force_reclone: bool = False


class QuestionRequest(BaseModel):
    question: str
    report_path: str | None = None


app = FastAPI(title="Portfolio Insights", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CLONE_ROOT = PROJECT_ROOT / ".cache" / "org-repo-clones"
DATA_DIR = PROJECT_ROOT / ".cache" / "portfolio-insights" / "data"

# In-memory state for current app session.
LATEST_REPORT: dict[str, Any] | None = None
LATEST_REPORT_PATH: Path | None = None


def _resolve_token(token_env: str) -> str:
    token = os.getenv(token_env)
    if not token:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No token was provided. Set credential target in the UI "
                f"or set environment variable {token_env} in the server process."
            ),
        )
    return token


def _resolve_request_token(req: ScanRequest) -> str:
    if req.credential_target and req.credential_target.strip():
        try:
            return read_windows_generic_credential(req.credential_target.strip())
        except CredentialLookupError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _resolve_token(req.token_env)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> Any:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "default_org": infer_org_from_api_base(API_BASE) or "",
            "default_credential_target": "",
            "default_clone_root": str(DEFAULT_CLONE_ROOT),
        },
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/agent-status")
def agent_status() -> dict[str, Any]:
    status = get_agent_status(DATA_DIR)
    status["data_dir"] = str(DATA_DIR.resolve())
    return status


@app.post("/api/scan")
def run_scan(req: ScanRequest) -> dict[str, Any]:
    global LATEST_REPORT, LATEST_REPORT_PATH

    token = _resolve_request_token(req)

    try:
        clone_root = Path(req.clone_root) if req.clone_root else DEFAULT_CLONE_ROOT
        output_path = Path(req.output_path) if req.output_path else DATA_DIR / build_default_output_path(
            req.org or infer_org_from_api_base(API_BASE) or "org"
        ).name
        report, report_path = run_inventory_scan(
            org=req.org,
            token=token,
            clone_root=clone_root,
            do_clone=req.clone_enabled,
            force_reclone=req.force_reclone,
            output_path=output_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - runtime/system errors
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    LATEST_REPORT = report
    LATEST_REPORT_PATH = report_path
    index_report(report=report, data_dir=DATA_DIR, report_path=report_path)

    summary = report.get("summary", {}) if isinstance(report, dict) else {}

    return {
        "status": "ok",
        "report_path": str(report_path.resolve()),
        "organization": report.get("organization"),
        "repo_count": report.get("repo_count"),
        "summary": summary,
    }


@app.post("/api/question")
def ask_question(req: QuestionRequest) -> dict[str, Any]:
    global LATEST_REPORT, LATEST_REPORT_PATH

    if req.report_path:
        report_path = Path(req.report_path)
        report = load_report(report_path)
        index_report(report=report, data_dir=DATA_DIR, report_path=report_path)
        LATEST_REPORT = report
        LATEST_REPORT_PATH = report_path
    elif LATEST_REPORT:
        if LATEST_REPORT_PATH is not None:
            index_report(report=LATEST_REPORT, data_dir=DATA_DIR, report_path=LATEST_REPORT_PATH)
    else:
        stored_report = load_latest_report(DATA_DIR)
        if stored_report is None:
            raise HTTPException(
                status_code=400,
                detail="No indexed report data is available yet. Run a scan first or provide report_path.",
            )
        LATEST_REPORT = stored_report

    return answer_portfolio_question_with_agent(req.question, data_dir=DATA_DIR)


@app.get("/api/latest")
def latest() -> dict[str, Any]:
    report = LATEST_REPORT or load_latest_report(DATA_DIR)
    if not report:
        return {"status": "empty"}

    return {
        "status": "ok",
        "report_path": str(LATEST_REPORT_PATH.resolve()) if LATEST_REPORT_PATH else None,
        "organization": report.get("organization"),
        "repo_count": report.get("repo_count"),
        "summary": report.get("summary", {}),
    }
