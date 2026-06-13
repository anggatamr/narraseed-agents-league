from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from fastmcp import FastMCP
from pydantic import BaseModel, Field, ValidationError

from backend.arc_matcher import match_arc
from backend.changepoint import detect_turning_points
from backend.foundry_iq import get_narrative_template
from backend.narrative import generate_narrative
from backend.preprocessor import normalize_timeseries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyzeTimeseriesInput(BaseModel):
    file_path: str = Field(..., description="Path to the CSV file to analyze.")
    style: str = Field("dramatic", description="Narrative style to use.")


class RemixGitHistoryInput(BaseModel):
    repo_path: str = Field(".", description="Path to the git repository.")


class NarraSeedMCP:
    def __init__(self) -> None:
        self.name = "narraseed"
        self.mcp = FastMCP(name=self.name)
        self._register_tools()

    def _register_tools(self) -> None:
        @self.mcp.tool(
            name="analyze_timeseries",
            description="Analyze a CSV time-series file and generate an AI-powered narrative story with data citations and Foundry IQ grounding.",
        )
        def analyze_timeseries(input_data: AnalyzeTimeseriesInput) -> dict[str, Any]:
            file_path = input_data.file_path
            if not Path(file_path).exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")
            normalized = normalize_timeseries(file_path)
            turning_points = detect_turning_points(np.asarray(normalized["y_normalized"], dtype=float))
            arc_result = match_arc(normalized["y_normalized"])
            foundry = get_narrative_template(arc_result["arc_name"])
            data = list(zip(normalized["x_original"], normalized["y_original"]))
            narrative = generate_narrative(arc_result["arc_name"], data, turning_points, foundry, input_data.style)
            return narrative

        @self.mcp.tool(
            name="remix_git_history",
            description="Transform a git repository's commit history into a dramatized Developer's Journey narrative.",
        )
        def remix_git_history(input_data: RemixGitHistoryInput) -> dict[str, Any]:
            repo_path = Path(input_data.repo_path)
            if not repo_path.exists():
                raise FileNotFoundError(f"Repository path not found: {repo_path}")
            result = subprocess.run(
                ["git", "-C", str(repo_path), "log", "--since=1 year ago", "--pretty=format:%ad", "--date=short"],
                capture_output=True, text=True, timeout=30
            )
            git_log = result.stdout.strip().splitlines()
            commit_dates = [line.strip() for line in git_log if line.strip()]
            if not commit_dates:
                raise ValueError("No git history available.")
            counts: dict[str, int] = {}
            for date in commit_dates:
                counts[date] = counts.get(date, 0) + 1
            sorted_dates = sorted(counts.items())
            x = list(range(1, len(sorted_dates) + 1))
            y = [count for _, count in sorted_dates]
            data = list(zip(x, y))
            normalized = normalize_timeseries(data)
            turning_points = detect_turning_points(np.asarray(normalized["y_normalized"], dtype=float))
            arc_result = match_arc(normalized["y_normalized"])
            foundry = get_narrative_template(arc_result["arc_name"])
            narrative = generate_narrative(arc_result["arc_name"], data, turning_points, foundry, "dramatic")
            return narrative

    def run(self) -> None:
        logger.info("Starting MCP server %s", self.name)
        self.mcp.start()


if __name__ == "__main__":
    NarraSeedMCP().run()
