import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from aegishealth.api.schema import PatientInput
from aegishealth.api.service import LocalAgents
from aegishealth.api.synthesis import CloudSynthesizer


def create_app(agents=None, synthesizer=None):
    @asynccontextmanager
    async def lifespan(app):
        load_dotenv()
        app.state.agents = agents or await run_in_threadpool(
            LocalAgents, os.getenv("AEGIS_OFFLINE", "true").lower() == "true"
        )
        app.state.synthesizer = synthesizer or CloudSynthesizer()
        app.state.local_slot = asyncio.Semaphore(1)
        yield
        await app.state.synthesizer.close()

    app = FastAPI(title="AegisHealth", version="0.3.0", lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Don't echo patient values in errors or logs.
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
                    for error in exc.errors()
                ]
            },
        )

    @app.get("/health")
    async def health():
        return {
            "status": "ready",
            "cloud_configured": bool(app.state.synthesizer.key),
            "provider": app.state.synthesizer.provider,
            "model": app.state.synthesizer.model,
        }

    @app.post("/analyze")
    async def analyze(patient: PatientInput):
        start = perf_counter()
        try:
            await asyncio.wait_for(app.state.local_slot.acquire(), timeout=0.1)
        except TimeoutError as error:
            raise HTTPException(429, "Analysis is busy. Retry shortly.") from error
        try:
            result = await run_in_threadpool(app.state.agents.analyze, patient)
        finally:
            app.state.local_slot.release()
        llm_start = perf_counter()
        synthesis = await app.state.synthesizer.summarize(
            patient.model_dump(), result["prediction"], result["evidence"]
        )
        result["timings_ms"].update(
            synthesis=(perf_counter() - llm_start) * 1000, total=(perf_counter() - start) * 1000
        )
        return {
            "analysis_id": str(uuid.uuid4()),
            "status": "complete" if synthesis["status"] == "complete" else "partial",
            **result,
            "synthesis": synthesis,
            "limitations": [
                "Research use only; existing disease presence is not ten-year ASCVD risk.",
                "Two retrieved passages may omit contraindications and do not establish treatment eligibility.",
            ],
        }

    frontend = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="dashboard")
    return app


app = create_app()
