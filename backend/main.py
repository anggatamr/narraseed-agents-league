from __future__ import annotations

import io
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# Load .env BEFORE importing backend modules that read os.getenv() at import time
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.arc_matcher import match_arc
from backend.changepoint import detect_turning_points
from backend.foundry_iq import get_narrative_template
from backend.narrative import check_ollama_status, generate_narrative
from backend.preprocessor import normalize_timeseries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Starting NarraSeed backend...")
    yield


app = FastAPI(title="NarraSeed Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


class HealthResponse(BaseModel):
    status: str
    ollama: str
    azure_search: str


class SampleItem(BaseModel):
    name: str
    filename: str


class AnalyzeResponse(BaseModel):
    story: str
    arc: str
    style: str
    citations: list[dict[str, Any]]
    turning_points: list[dict[str, Any]]
    segments: list[dict[str, Any]]
    grounding: dict[str, Any]
    x_labels: list[str] | None = None
    metadata: dict[str, Any] | None = None


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    # Real Ollama check
    try:
        ollama_info = check_ollama_status()
        ollama_status = "connected" if ollama_info["available"] else "disconnected"
    except Exception:
        ollama_status = "disconnected"
    # Real Azure config check
    azure_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    azure_key = os.getenv("AZURE_SEARCH_KEY", "")
    azure_status = "configured" if azure_endpoint and azure_key and "<your-" not in azure_key else "not_configured"
    overall = "ok" if ollama_status == "connected" else "degraded"
    return HealthResponse(status=overall, ollama=ollama_status, azure_search=azure_status)


@app.get("/api/samples", response_model=list[SampleItem])
async def samples() -> list[SampleItem]:
    items: list[SampleItem] = []
    for file_path in sorted(DATA_DIR.glob("*.csv")):
        items.append(SampleItem(name=file_path.stem.replace("sample_", "").replace("_", " ").title(), filename=file_path.name))
    return items


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...), style: str = Form("dramatic")) -> AnalyzeResponse:
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
        normalized = normalize_timeseries(df)
    except Exception as exc:
        logger.error("CSV processing failed: %s", exc)
        raise HTTPException(status_code=400, detail=f"Invalid CSV format or parsing failed: {str(exc)}")

    x_original = normalized["x_original"]
    y_original = normalized["y_original"]
    data = list(zip(x_original, y_original))
    
    values = np.asarray(normalized["y_normalized"], dtype=float)
    turning_points = detect_turning_points(values)
    arc_result = match_arc(normalized["y_normalized"])
    foundry = get_narrative_template(arc_result["arc_name"])
    
    narrative = generate_narrative(
        arc_result["arc_name"],
        data,
        turning_points,
        foundry,
        style,
        metadata=normalized.get("metadata"),
        x_labels=normalized.get("x_labels"),
    )
    
    # Inject arc confidence into grounding dict
    narrative["grounding"]["confidence"] = arc_result["confidence"]
    
    # Add labels and metadata to response
    narrative["x_labels"] = normalized.get("x_labels")
    narrative["metadata"] = normalized.get("metadata")

    return AnalyzeResponse(**narrative)


@app.get("/api/llm-status")
async def llm_status() -> JSONResponse:
    status = check_ollama_status()
    return JSONResponse({
        "status": "ok" if status["available"] else "warning",
        "message": "Ollama endpoint is reachable." if status["available"] else "Configured model is not visible to Ollama.",
        "model": status["model"],
        "available": status["available"],
        "models": status["models"],
    })
