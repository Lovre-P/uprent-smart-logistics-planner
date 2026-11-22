"""HTTP sučelje planera i posluživanje izgrađene aplikacije."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from uprent.compare import ComparisonRow, Preset, compare
from uprent.domain import Scenario, ScenarioError, input_error
from uprent.plan import Plan
from uprent.result import SolveResult
from uprent.service import solve
from uprent.validator import ValidationReport, validate


class ScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Scenario


class SolveRequest(ScenarioRequest):
    detailed: bool = False


class ValidateRequest(ScenarioRequest):
    plan: Plan


class CompareRequest(ScenarioRequest):
    variants: list[Preset] | None = None


def create_app(static_dir: Path | None = Path("web/dist")) -> FastAPI:
    app = FastAPI(title="UP RENT – Smart Logistics Planner", version="0.1.0")
    origin = os.environ.get("UPRENT_CORS_ORIGIN", "").strip()
    if origin:
        app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_methods=["GET", "POST"],
                           allow_headers=["Content-Type"])

    # U kontejneru se podaci nalaze u radnom direktoriju /app. U lokalnom
    # razvoju CLI se može pokrenuti i iz podmape repozitorija.
    root = Path.cwd()
    if not (root / "data/default_scenario.json").is_file():
        root = Path(__file__).resolve().parents[2]

    @app.exception_handler(ScenarioError)
    async def scenario_error(_request: Request, exc: ScenarioError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def request_error(_request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": str(input_error(exc.errors()))})

    @app.get("/api/health", summary="Stanje aplikacije")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/scenario/default", response_model=Scenario, summary="Podaci iz zadatka")
    def default_scenario() -> FileResponse:
        return FileResponse(root / "data/default_scenario.json", media_type="application/json")

    @app.post("/api/solve", summary="Izračun plana")
    def solve_request(payload: SolveRequest) -> SolveResult:
        return solve(payload.scenario, detailed=payload.detailed)

    @app.post("/api/validate", summary="Neovisna provjera plana")
    def validate_request(payload: ValidateRequest) -> ValidationReport:
        return validate(payload.scenario, payload.plan)

    @app.post("/api/compare", summary="Usporedba tumačenja")
    def compare_request(payload: CompareRequest) -> list[ComparisonRow]:
        if payload.variants is None:
            return compare(payload.scenario)
        return compare(payload.scenario, payload.variants)

    folder = root / static_dir if static_dir is not None else None
    if folder is not None and (folder / "index.html").is_file():
        app.mount("/", StaticFiles(directory=folder, html=True), name="sučelje")
    else:
        @app.get("/", response_class=HTMLResponse, include_in_schema=False)
        def frontend_fallback():
            return ('<!doctype html><html lang="hr"><meta charset="utf-8"><title>UP RENT</title>'
                    '<p>Sučelje nije izgrađeno – pokreni <code>npm run build</code> u mapi web.</p></html>')

    return app
