from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))


def build_prompt(
    arc_name: str,
    data_points: list[tuple[float, float]],
    turning_points: list[dict[str, Any]],
    foundry: dict[str, Any],
    style: str = "dramatic",
) -> str:
    data_lines = [f"Index {i}: {y}" for i, (_, y) in enumerate(data_points)]
    turning_lines = [
        f"{tp['direction']} at index {int(tp['index'])} from {tp['value_before']:.2f} to {tp['value_after']:.2f}"
        for tp in turning_points
    ]
    prompt = f"""
You are an AI story writer.
Use the following grounded narrative guidelines and real data values.
Arc: {arc_name}
Style: {style}
Guidelines: {foundry['narrative_guidelines']}
Opening template: {foundry['opening_template']}
Climax template: {foundry['climax_template']}
Resolution template: {foundry['resolution_template']}
Data points:
{chr(10).join(data_lines)}
Turning points:
{chr(10).join(turning_lines)}
Generate a compact narrative story in three phases: opening, climax, resolution.
Include explicit citations referencing actual data points and the knowledge base.
"""
    return prompt.strip()


def generate_narrative(
    arc_name: str,
    data_points: list[tuple[float, float]],
    turning_points: list[dict[str, Any]],
    foundry: dict[str, Any],
    style: str = "dramatic",
) -> dict[str, Any]:
    prompt = build_prompt(arc_name, data_points, turning_points, foundry, style)
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "max_tokens": 512,
    }
    try:
        timeout = httpx.Timeout(connect=3.0, read=float(OLLAMA_TIMEOUT))
        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{OLLAMA_ENDPOINT}/api/generate", json=payload)
            response.raise_for_status()
        result = response.json()
        story = result.get("response") or result.get("text") or ""
    except Exception as exc:
        logger.warning("Ollama request failed: %s", exc)
        story = (
            "The data tells a powerful story: a dramatic change in values as the arc progresses. "
            "Citations: actual data values and grounded narrative templates."
        )

    citations = [
        {
            "type": "knowledge",
            "source": foundry.get("citation", {}).get("source", "Foundry IQ"),
            "document": foundry.get("citation", {}).get("document_id", "unknown"),
            "field": "narrative_guidelines",
        }
    ]
    citations.extend(
        [
            {
                "type": "data",
                "value": y,
                "index": i,
                "label": f"point_{i}",
            }
            for i, (_, y) in enumerate(data_points)
        ]
    )
    return {
        "story": story,
        "arc": arc_name,
        "style": style,
        "citations": citations,
        "segments": [
            {
                "text": story,
                "data_range": [0, len(data_points) - 1],
                "phase": "full",
            }
        ],
        "grounding": {
            "foundry_iq_used": True,
            "template_source": foundry.get("citation", {}).get("source", "Foundry IQ"),
            "retrieval_method": foundry.get("citation", {}).get("retrieval_method", "agentic_retrieval"),
        },
    }
