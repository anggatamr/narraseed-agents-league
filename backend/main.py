from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Any

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
from backend.narrative import generate_narrative
from backend.preprocessor import normalize_timeseries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = FastAPI(title="NarraSeed Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
    segments: list[dict[str, Any]]
    grounding: dict[str, Any]
    x_labels: list[str] | None = None
    metadata: dict[str, Any] | None = None


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    ollama_status = "connected"
    azure_status = "connected"
    return HealthResponse(status="ok", ollama=ollama_status, azure_search=azure_status)


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
    
    narrative = generate_narrative(arc_result["arc_name"], data, turning_points, foundry, style)
    
    # Add labels and metadata to response
    narrative["x_labels"] = normalized.get("x_labels")
    narrative["metadata"] = normalized.get("metadata")

    return AnalyzeResponse(**narrative)


@app.get("/api/llm-status")
async def llm_status() -> JSONResponse:
    return JSONResponse({"status": "ok", "message": "Ollama endpoint is assumed available."})


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting NarraSeed backend...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
