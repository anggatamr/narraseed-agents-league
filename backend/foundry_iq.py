from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType

logger = logging.getLogger(__name__)

LOCAL_TEMPLATES = {
    "Rags to Riches": {
        "narrative_guidelines": "Frame the narrative as a progressive journey of improvement.",
        "tone": "Inspirational, warm, progressive",
        "opening_template": "It began with humble numbers — modest, unassuming, yet carrying the quiet promise of potential.",
        "climax_template": "And then, the momentum became undeniable — each milestone building upon the last.",
        "resolution_template": "What started as a whisper of ambition has become a resounding chorus of achievement.",
        "document_id": "rags-to-riches",
    },
    "Tragedy": {
        "narrative_guidelines": "Frame the narrative as an irreversible decline, emphasizing the weight of each loss.",
        "tone": "Somber, reflective, elegiac",
        "opening_template": "The numbers began strong — confident, even — as if the trajectory could only continue upward.",
        "climax_template": "But the descent was relentless, each data point marking another step into uncertain territory.",
        "resolution_template": "What remains is a cautionary record of what was lost and the patterns that went unnoticed.",
        "document_id": "tragedy",
    },
    "Icarus": {
        "narrative_guidelines": "Frame the narrative as a rise that overextended, followed by a dramatic fall.",
        "tone": "Dramatic, cautionary, bittersweet",
        "opening_template": "The ascent was intoxicating — each new high watermark fueling the belief that the climb would never end.",
        "climax_template": "At the peak, the numbers told a story of triumph — but the warning signs were already written in the margins.",
        "resolution_template": "The fall came swiftly, proving that even the most spectacular rises are subject to gravity.",
        "document_id": "icarus",
    },
    "Man in a Hole": {
        "narrative_guidelines": "Frame the narrative as a setback followed by recovery, emphasizing resilience.",
        "tone": "Resilient, hopeful, grounded",
        "opening_template": "Things were stable before the drop — the numbers tracking along a comfortable, predictable path.",
        "climax_template": "Then came the valley — a period where every metric seemed to conspire against recovery.",
        "resolution_template": "Yet from that low point emerged a comeback, steady and deliberate, rebuilding what was lost.",
        "document_id": "man-in-a-hole",
    },
    "Phoenix": {
        "narrative_guidelines": "The crash should be visceral and significant, and the rebirth should be extraordinary.",
        "tone": "Powerful, transformative, awe-inspiring",
        "opening_template": "Before the fire, there were ashes. Before the ashes, there was a world that crumbled.",
        "climax_template": "From the lowest point emerged something entirely new — not a return to the old, but a leap beyond it.",
        "resolution_template": "Like the phoenix, this journey proves that sometimes destruction is the prerequisite for transcendence.",
        "document_id": "phoenix",
    },
    "Oedipus": {
        "narrative_guidelines": "Frame the narrative as a fall from grace that eventually finds redemption through a second rise.",
        "tone": "Complex, redemptive, hard-won",
        "opening_template": "The beginning carried the weight of high expectations — strong numbers that seemed destined to continue.",
        "climax_template": "The collapse was both sudden and revealing, exposing the fragility beneath the surface.",
        "resolution_template": "What followed was not a quick fix but a patient, earned recovery — a second chance built on lessons learned.",
        "document_id": "oedipus",
    },
}


def _load_env() -> dict[str, str]:
    return {
        "endpoint": os.getenv("AZURE_SEARCH_ENDPOINT", ""),
        "key": os.getenv("AZURE_SEARCH_KEY", ""),
        "index": os.getenv("AZURE_SEARCH_INDEX", "narrative-templates"),
    }


def get_narrative_template(arc_name: str) -> dict[str, Any]:
    env = _load_env()
    if not env["endpoint"] or not env["key"]:
        logger.warning("Azure Search configuration missing. Using local fallback.")
        return _fallback_response(arc_name)

    try:
        client = SearchClient(endpoint=env["endpoint"], index_name=env["index"], credential=AzureKeyCredential(env["key"]))
        query = f"arc_name:\"{arc_name}\""
        results = client.search(query, query_type=QueryType.FULL)
        result = next(iter(results), None)
        if result:
            logger.debug("Foundry IQ returned document for arc_name=%s", arc_name)
            return {
                "narrative_guidelines": result.get("narrative_guidelines", ""),
                "tone": result.get("tone", ""),
                "opening_template": result.get("opening_template", ""),
                "climax_template": result.get("climax_template", ""),
                "resolution_template": result.get("resolution_template", ""),
                "citation": {
                    "source": "Foundry IQ Knowledge Base",
                    "index": env["index"],
                    "document_id": result.get("id", "unknown"),
                    "retrieval_method": "agentic_retrieval",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                },
            }
    except Exception as exc:
        logger.warning("Azure Search query failed: %s", exc)

    return _fallback_response(arc_name)


def _fallback_response(arc_name: str) -> dict[str, Any]:
    env = _load_env()
    template = LOCAL_TEMPLATES.get(arc_name, LOCAL_TEMPLATES.get("Rags to Riches"))
    return {
        "narrative_guidelines": template["narrative_guidelines"],
        "tone": template["tone"],
        "opening_template": template["opening_template"],
        "climax_template": template["climax_template"],
        "resolution_template": template["resolution_template"],
        "citation": {
            "source": "Local fallback knowledge base",
            "index": env["index"],
            "document_id": template["document_id"],
            "retrieval_method": "fallback",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
    }
