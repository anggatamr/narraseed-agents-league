from __future__ import annotations

import logging
import os
from typing import Any

import re

import httpx

logger = logging.getLogger(__name__)


def _get_ollama_config() -> dict[str, Any]:
    """Read Ollama config lazily so dotenv has time to load."""
    return {
        "endpoint": os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434"),
        "model": os.getenv("OLLAMA_MODEL", "").strip() or "qwen2.5:1.5b",
        "timeout": int(os.getenv("OLLAMA_TIMEOUT", "300")),
    }


def check_ollama_status() -> dict[str, Any]:
    cfg = _get_ollama_config()
    try:
        timeout = httpx.Timeout(float(cfg["timeout"]), connect=3.0)
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{cfg['endpoint']}/api/tags")
            response.raise_for_status()
        payload = response.json()
        models = payload.get("models", [])
        available = any(model.get("name") == cfg["model"] for model in models)
        return {
            "available": available,
            "endpoint": cfg["endpoint"],
            "model": cfg["model"],
            "models": [model.get("name") for model in models if model.get("name")],
        }
    except Exception as exc:
        logger.warning("Ollama status check failed: %s", exc)
        return {
            "available": False,
            "endpoint": cfg["endpoint"],
            "model": cfg["model"],
            "models": [],
        }


# Common English words that start with a capital letter in stories — not invented names
_COMMON_CAPITALIZED = frozenset({
    "the", "this", "that", "then", "but", "and", "from", "what", "when",
    "where", "which", "while", "with", "each", "every", "like", "just",
    "some", "many", "most", "such", "only", "even", "also", "here",
    "there", "their", "these", "those", "after", "before", "between",
    "through", "during", "without", "within", "along", "across",
    "it", "its", "they", "them", "she", "her", "his", "him", "our",
    "your", "who", "how", "why", "all", "any", "both",
    "things", "thing", "one", "new", "old", "first", "last", "next",
    "opening", "climax", "resolution", "chapter", "act",
    # Common story nouns
    "journey", "story", "tale", "path", "road", "world", "time",
    "beginning", "middle", "end", "moment", "day", "night",
    "morning", "evening", "spring", "summer", "autumn", "winter",
    "data", "dataset", "series", "trend", "pattern", "value",
    "growth", "decline", "recovery", "peak", "valley", "dip",
    "numbers", "figures", "metrics", "results", "records",
    # Common analytical subjects
    "steps", "measurements", "observations", "readings", "scores",
    "performance", "progress", "activity", "output", "levels",
})


def build_prompt(
    arc_name: str,
    data_points: list[tuple[float, float]],
    turning_points: list[dict[str, Any]],
    foundry: dict[str, Any],
    style: str = "dramatic",
    metadata: dict[str, Any] | None = None,
    x_labels: list[str] | None = None,
) -> str:
    meta = metadata or {}
    y_col = meta.get("y_column", "Value")
    x_col = meta.get("x_column", "Index")
    entity_info = ""
    if meta.get("entity_value"):
        entity_info = f"Entity: {meta['entity_value']}\n"

    # Downsample points for prompt size optimization (Ollama CPU speedup)
    max_pts = 12
    n_points = len(data_points)
    if n_points <= max_pts:
        sampled_points = [(i, y) for i, (_, y) in enumerate(data_points)]
    else:
        # Guarantee start, end, turning points, and evenly spaced indices
        idx_set = {0, n_points - 1}
        for tp in turning_points:
            idx_set.add(int(tp["index"]))
        # Add evenly spaced indices
        for i in range(1, max_pts - 1):
            idx_set.add(int(i * (n_points - 1) / (max_pts - 1)))

        sorted_indices = sorted(list(idx_set))
        sampled_points = [(idx, data_points[idx][1]) for idx in sorted_indices]

    # Build data lines with real X labels when available
    if x_labels:
        data_lines = [
            f"{x_col}={x_labels[idx] if idx < len(x_labels) else idx}: {y_col}={y:.2f}"
            for idx, y in sampled_points
        ]
    else:
        data_lines = [f"{x_col}={idx}: {y_col}={y:.2f}" for idx, y in sampled_points]

    # Build turning point lines with ORIGINAL-SCALE values (not normalized)
    turning_lines = []
    for tp in turning_points:
        tp_idx = int(tp["index"])
        tp_label = x_labels[tp_idx] if x_labels and tp_idx < len(x_labels) else f"index {tp_idx}"
        # Look up original values when possible
        if 0 < tp_idx < len(data_points):
            orig_before = data_points[tp_idx - 1][1]
            orig_after = data_points[tp_idx][1]
        else:
            orig_before = tp["value_before"]
            orig_after = tp["value_after"]
        turning_lines.append(
            f"{tp['direction']} at {x_col}={tp_label} "
            f"({y_col}: {orig_before:,.2f} → {orig_after:,.2f})"
        )

    domain_context = (
        f"Dataset domain: The Y-axis measures \"{y_col}\" and the X-axis represents \"{x_col}\".\n"
        f"{entity_info}"
        f"Write about {y_col.lower()} in the context of {x_col.lower()}. "
        f"Do NOT reinterpret the numbers as earnings, revenue, stock prices, or any other domain. "
        f"The data is about {y_col.lower()}, not financial metrics."
    )

    # Build multi-column context section
    multi_col_section = ""
    numeric_summaries = meta.get("numeric_summaries", {})
    categorical_summaries = meta.get("categorical_summaries", {})
    total_rows = meta.get("total_rows", len(data_points))
    other_cols = meta.get("other_numeric_columns", [])

    if len(numeric_summaries) > 1 or categorical_summaries:
        multi_col_lines = [f"\nDataset: {total_rows} records across multiple columns."]
        # Summarize other numeric columns
        for col in other_cols[:5]:
            if col in numeric_summaries:
                s = numeric_summaries[col]
                multi_col_lines.append(f"  - {col}: avg {s['mean']:,.1f}, range {s['min']:,.1f}–{s['max']:,.1f}")
        # Summarize categorical columns
        for col, vals in categorical_summaries.items():
            multi_col_lines.append(f"  - {col}: values include {', '.join(vals[:4])}")
        multi_col_lines.append(f"Weave these contextual columns into the narrative where relevant.")
        multi_col_section = chr(10).join(multi_col_lines)

    prompt = f"""
You are an AI story writer.
Use the following grounded narrative guidelines and real data values.
{domain_context}{multi_col_section}
Arc: {arc_name}
Style: {style}
Guidelines: {foundry['narrative_guidelines']}
Opening template: {foundry['opening_template']}
Climax template: {foundry['climax_template']}
Resolution template: {foundry['resolution_template']}
Data points (subset of {total_rows} total):
{chr(10).join(data_lines)}
Turning points:
{chr(10).join(turning_lines)}
Generate a compact narrative story in three phases: opening, climax, resolution. Keep it brief (under 3 paragraphs).
Rules:
- Do not invent names, people, or personas. Do not create invented person names. Write about the pattern, trend, or system directly — never personify the data.
- The data measures "{y_col}" across "{x_col}". Always reference the data by its actual domain ({y_col.lower()}), never as earnings, revenue, market index, stock price, or any unrelated concept.
- Keep the story data-grounded and avoid fictional character names or invented person names.
- Reference actual data points and the knowledge base rather than creating a narrative around an invented person.
- Include explicit citations referencing actual data points and the knowledge base.
"""
    return prompt.strip()


def _story_has_invented_names(story: str) -> bool:
    """Detect if the story contains invented person/entity names.

    Primary heuristic: possessive proper nouns (e.g. "Mania's earnings").
    Secondary: capitalised words used as subjects that are NOT
    common English words and NOT at sentence start.
    """
    # Strong signal: capitalised word in possessive form — very likely a name
    possessive_names = re.findall(r"\b([A-Z][a-z]{2,})['\u2019]s\b", story)
    for name in possessive_names:
        if name.lower() not in _COMMON_CAPITALIZED:
            return True

    # Secondary: capitalised word + personal verb, but skip sentence starters
    sentences = re.split(r'[.!?]\s+', story)
    for sentence in sentences:
        words = sentence.split()
        if len(words) < 2:
            continue
        # Skip the first word — it's always capitalised as a sentence starter
        first_word = words[0]
        remaining = " ".join(words[1:])
        match = re.match(
            r"\b([A-Z][a-z]{2,})\s+"
            r"(?:was|were|faced|discovered|learned|adapted|realized|analyzed|decided|believed|struggled)\b",
            remaining,
        )
        if match:
            name = match.group(1)
            if name.lower() not in _COMMON_CAPITALIZED:
                return True

    return False


def _looks_like_fictional_story(story: str) -> bool:
    lower_story = story.lower()
    # Only flag genuinely fictional markers — common analytical terms are allowed
    fictional_markers = [
        "city",
        "skyline",
        "ghost town",
        "streets",
        "abandoned",
        "bustle",
        "hustle",
        "infrastructure",
    ]
    return any(marker in lower_story for marker in fictional_markers)


def _extract_numbers_from_text(text: str) -> list[float]:
    """Extract numeric values from text, including million/billion/trillion abbreviations."""
    numbers = []
    # Match numbers with magnitude suffixes (e.g., "7.78 million", "40.3 billion")
    for match in re.finditer(
        r"(\d[\d,]*\.?\d*)\s*(million|billion|trillion)", text, re.IGNORECASE
    ):
        try:
            val = float(match.group(1).replace(",", ""))
            multiplier = {
                "million": 1e6,
                "billion": 1e9,
                "trillion": 1e12,
            }[match.group(2).lower()]
            numbers.append(val * multiplier)
        except ValueError:
            pass
    # Match plain numbers (integers and decimals, with optional commas) that are NOT followed by a magnitude suffix
    for match in re.finditer(
        r"(?<!\w)(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.\d+)(?!\s*(?:million|billion|trillion))",
        text,
        re.IGNORECASE,
    ):
        try:
            numbers.append(float(match.group(1).replace(",", "")))
        except ValueError:
            pass
    return numbers


def _story_contains_data_values(story: str, data_points: list[tuple[float, float]]) -> bool:
    """Check if the story references data values in any reasonable format.

    Handles exact values, rounded values, comma-formatted numbers, and
    million/billion/trillion abbreviations so that population-scale data
    (e.g. 7,776,180 rendered as "7.78 million") is accepted.
    """
    if not data_points:
        return True

    values = [p[1] for p in data_points]
    landmarks = {values[0], values[-1], min(values), max(values)}
    n = len(values)
    for i in range(1, min(4, n - 1)):
        landmarks.add(values[i * (n - 1) // 4])

    # Phase 1: exact / formatted string matching (fast path)
    for val in landmarks:
        formats = [
            f"{val:.2f}", f"{val:.1f}", f"{val:.0f}",
            f"{val:,.0f}", f"{val:,.1f}", f"{val:,.2f}",
            str(int(val)) if val == int(val) else None,
        ]
        for fmt in formats:
            if fmt and fmt in story:
                return True

    # Phase 2: extract numbers from story and check for approximate matches
    story_numbers = _extract_numbers_from_text(story)
    for val in landmarks:
        if val == 0:
            if any(abs(sn) < 1 for sn in story_numbers):
                return True
            continue
        for sn in story_numbers:
            if sn == 0:
                continue
            if abs(sn - val) / abs(val) < 0.05:  # within 5%
                return True

    return False


def _build_data_summary_story(
    arc_name: str,
    data_points: list[tuple[float, float]],
    turning_points: list[dict[str, Any]],
    style: str,
    foundry: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    x_labels: list[str] | None = None,
) -> str:
    """Build a rich, data-grounded fallback story using Foundry IQ templates and full dataset stats."""
    import numpy as _np

    meta = metadata or {}
    y_col = meta.get("y_column", "the measured value")
    x_col = meta.get("x_column", "time")
    total_rows = meta.get("total_rows", len(data_points))

    if not data_points:
        return "No data available to generate a narrative."

    values = [p[1] for p in data_points]
    start_value = values[0]
    end_value = values[-1]
    min_value = min(values)
    max_value = max(values)
    mean_value = sum(values) / len(values)
    change = end_value - start_value
    direction = "increased" if change > 0 else "decreased" if change < 0 else "stayed stable"

    # Date range from x_labels
    if x_labels and len(x_labels) >= 2:
        date_range = f"from {x_labels[0]} to {x_labels[-1]}"
    else:
        date_range = f"across {total_rows} data points"

    # Use foundry templates if available
    opening_tpl = ""
    climax_tpl = ""
    resolution_tpl = ""
    if foundry:
        opening_tpl = foundry.get("opening_template", "")
        climax_tpl = foundry.get("climax_template", "")
        resolution_tpl = foundry.get("resolution_template", "")

    # ── OPENING ──
    opening_parts = []
    if opening_tpl:
        opening_parts.append(opening_tpl)
    opening_parts.append(
        f"Across {total_rows} records spanning {date_range}, "
        f"{y_col.lower()} {direction} from {start_value:,.2f} to {end_value:,.2f}."
    )
    opening_parts.append(
        f"The overall range was {min_value:,.2f} to {max_value:,.2f}, "
        f"with an average of {mean_value:,.2f}."
    )
    opening_section = " ".join(opening_parts)

    # ── CLIMAX: All turning points with real date labels ──
    climax_parts = []
    if climax_tpl:
        climax_parts.append(climax_tpl)

    if turning_points:
        # Show up to 5 turning points with real date labels and original-scale values
        shown_tps = []
        for tp in turning_points:
            tp_idx = int(tp["index"])
            if tp_idx < 1 or tp_idx >= len(data_points):
                continue  # skip meaningless edge indices
            orig_before = data_points[tp_idx - 1][1]
            orig_after = data_points[tp_idx][1]
            if abs(orig_before - orig_after) < 1e-6:
                continue  # skip zero-change turning points
            shown_tps.append((tp, orig_before, orig_after))
            if len(shown_tps) >= 5:
                break

        for tp, orig_before, orig_after in shown_tps:
            tp_idx = int(tp["index"])
            tp_label = x_labels[tp_idx] if x_labels and tp_idx < len(x_labels) else f"point {tp_idx}"
            dir_word = "rose" if orig_after > orig_before else "dropped"
            climax_parts.append(
                f"At {tp_label}, {y_col.lower()} {dir_word} "
                f"from {orig_before:,.2f} to {orig_after:,.2f}."
            )
        if len(turning_points) > 5:
            climax_parts.append(
                f"In total, {len(turning_points)} turning points were detected across the dataset."
            )
    else:
        climax_parts.append(
            f"No major turning points were detected — the {y_col.lower()} trend remained relatively steady."
        )
    climax_section = " ".join(climax_parts)

    # ── MULTI-COLUMN CONTEXT ──
    multi_col_section = ""
    other_cols = meta.get("other_numeric_columns", [])
    numeric_summaries = meta.get("numeric_summaries", {})
    categorical_summaries = meta.get("categorical_summaries", {})

    context_parts = []
    if other_cols and numeric_summaries:
        for col in other_cols[:3]:
            if col in numeric_summaries:
                s = numeric_summaries[col]
                context_parts.append(
                    f"{col} averaged {s['mean']:,.1f} (range: {s['min']:,.1f}–{s['max']:,.1f})"
                )
        if context_parts:
            multi_col_section = "Beyond the primary metric, " + "; ".join(context_parts) + "."

    if categorical_summaries:
        for col, vals in categorical_summaries.items():
            multi_col_section += f" The {col.lower()} column showed values like {', '.join(vals[:3])}."

    # ── RESOLUTION ──
    resolution_parts = []
    if resolution_tpl:
        resolution_parts.append(resolution_tpl)
    resolution_parts.append(
        f"The data follows a {arc_name} narrative arc, "
        f"capturing the overall shape of {y_col.lower()} across the observed period."
    )
    resolution_section = " ".join(resolution_parts)

    # Assemble final story
    sections = [opening_section, climax_section]
    if multi_col_section:
        sections.append(multi_col_section)
    sections.append(resolution_section)
    return "\n\n".join(sections)


def generate_narrative(
    arc_name: str,
    data_points: list[tuple[float, float]],
    turning_points: list[dict[str, Any]],
    foundry: dict[str, Any],
    style: str = "dramatic",
    metadata: dict[str, Any] | None = None,
    x_labels: list[str] | None = None,
) -> dict[str, Any]:
    cfg = _get_ollama_config()
    prompt = build_prompt(arc_name, data_points, turning_points, foundry, style, metadata=metadata, x_labels=x_labels)
    payload = {
        "model": cfg["model"],
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 1024,
            "temperature": 0.7,
        }
    }
    try:
        timeout = httpx.Timeout(float(cfg["timeout"]), connect=3.0)
        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{cfg['endpoint']}/api/generate", json=payload)
            response.raise_for_status()
        result = response.json()
        story = result.get("response") or result.get("text") or ""
    except Exception as exc:
        logger.warning("Ollama request failed: %s", exc)
        story = _build_data_summary_story(arc_name, data_points, turning_points, style, foundry, metadata=metadata, x_labels=x_labels)

    normalized_story = story.strip()
    if (
        not normalized_story
        or len(normalized_story) < 40
        or normalized_story.lower() in {
            "the data tells a powerful story of change and growth.",
            "the data tells a powerful story: a dramatic change in values as the arc progresses. citations: actual data values and grounded narrative templates.",
        }
        or not _story_contains_data_values(normalized_story, data_points)
        or _looks_like_fictional_story(normalized_story)
        or _story_has_invented_names(normalized_story)
    ):
        story = _build_data_summary_story(arc_name, data_points, turning_points, style, foundry, metadata=metadata, x_labels=x_labels)

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
        "turning_points": turning_points,
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
