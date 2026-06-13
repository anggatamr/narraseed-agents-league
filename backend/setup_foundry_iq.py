"""
Setup Foundry IQ Knowledge Base with narrative templates.
Run this once before starting the backend.

Usage: python backend/setup_foundry_iq.py
"""

import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
)

load_dotenv("backend/.env")

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
key = os.getenv("AZURE_SEARCH_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX", "narrative-templates")

if not endpoint or not key:
    raise RuntimeError("AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_KEY must be configured in backend/.env")

credential = AzureKeyCredential(key)

index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="arc_name", type=SearchFieldDataType.String, filterable=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="narrative_guidelines", type=SearchFieldDataType.String),
    SearchableField(name="tone", type=SearchFieldDataType.String),
    SearchableField(name="opening_template", type=SearchFieldDataType.String),
    SearchableField(name="climax_template", type=SearchFieldDataType.String),
    SearchableField(name="resolution_template", type=SearchFieldDataType.String),
    SearchableField(name="keywords", type=SearchFieldDataType.String),
]

index = SearchIndex(name=index_name, fields=fields)
index_client.create_or_update_index(index)
print(f"[OK] Created index: {index_name}")

search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

narrative_templates = [
    {
        "id": "rags-to-riches",
        "arc_name": "Rags to Riches",
        "title": "The Ascent — Steady Upward Journey",
        "narrative_guidelines": "Frame the narrative as a progressive journey of improvement. Emphasize incremental gains, persistence, and the compounding effect of consistent effort. Use encouraging, aspirational language. Each data point should feel like a step on a staircase.",
        "tone": "Inspirational, warm, progressive",
        "opening_template": "It began with humble numbers — modest, unassuming, yet carrying the quiet promise of potential.",
        "climax_template": "And then, the momentum became undeniable — each milestone building upon the last.",
        "resolution_template": "What started as a whisper of ambition has become a resounding chorus of achievement.",
        "keywords": "growth progress improvement ascending upward climbing achievement",
    },
    {
        "id": "tragedy",
        "arc_name": "Tragedy",
        "title": "The Descent — A Story of Decline",
        "narrative_guidelines": "Approach with empathy and respect. Frame decline not as failure but as a chapter that deserves understanding. Use reflective, contemplative tone. Highlight what was lost to underscore its value. Avoid blame or judgment.",
        "tone": "Reflective, empathetic, contemplative",
        "opening_template": "There was a time when the numbers told a different story — one of abundance and stability.",
        "climax_template": "But somewhere along the way, the trajectory shifted, and the descent began.",
        "resolution_template": "This chapter, while difficult, carries lessons written in the language of experience.",
        "keywords": "decline loss falling diminishing reducing downward challenge",
    },
    {
        "id": "icarus",
        "arc_name": "Icarus",
        "title": "Rise and Fall — The Cautionary Arc",
        "narrative_guidelines": "Tell the story in two distinct acts: the exhilarating ascent and the sobering fall. Use contrast as the primary narrative device. The rise should feel exciting and earned; the fall should feel inevitable in hindsight. Draw lessons from overreach.",
        "tone": "Dramatic, cautionary, insightful",
        "opening_template": "The beginning was electric — a surge of progress that seemed to defy gravity itself.",
        "climax_template": "At the peak, everything seemed possible. But peaks, by their very nature, give way to descent.",
        "resolution_template": "Like Icarus, the story reminds us: the same ambition that lifts us can humble us.",
        "keywords": "rise fall peak crash overreach ambition hubris caution",
    },
    {
        "id": "man-in-a-hole",
        "arc_name": "Man in a Hole",
        "title": "Fall Then Recovery — The Resilience Arc",
        "narrative_guidelines": "Structure as a three-act story: stability, crisis, and recovery. The dip should feel real and consequential, but the recovery should feel earned and satisfying. Emphasize resilience, adaptation, and the strength found in adversity.",
        "tone": "Resilient, hopeful, triumphant",
        "opening_template": "The journey started on solid ground — comfortable, perhaps even routine.",
        "climax_template": "Then came the unexpected dip — a valley that tested every foundation.",
        "resolution_template": "But from that valley emerged something stronger — a recovery built on hard-won wisdom.",
        "keywords": "dip recovery bounce resilience adversity comeback strength",
    },
    {
        "id": "phoenix",
        "arc_name": "Phoenix",
        "title": "Crash Then Massive Ascent — The Transformation Arc",
        "narrative_guidelines": "This is the most dramatic arc. The crash should be visceral and significant. But the rebirth should be extraordinary — not just recovery, but transformation. Use vivid, powerful language. This is a story of reinvention, not just repair.",
        "tone": "Powerful, transformative, awe-inspiring",
        "opening_template": "Before the fire, there were ashes. Before the ashes, there was a world that crumbled.",
        "climax_template": "From the lowest point emerged something entirely new — not a return to the old, but a leap beyond it.",
        "resolution_template": "Like the phoenix, this journey proves that sometimes destruction is the prerequisite for transcendence.",
        "keywords": "crash rebirth transformation reinvention phoenix transcendence breakthrough",
    },
    {
        "id": "oedipus",
        "arc_name": "Oedipus",
        "title": "Down Then Up — The Discovery Arc",
        "narrative_guidelines": "Frame as a journey of discovery through struggle. The initial decline represents the shedding of illusions. The subsequent rise represents the gain of genuine understanding. The turning point is a moment of revelation, not just recovery.",
        "tone": "Philosophical, revelatory, deep",
        "opening_template": "The story begins with a descent — not of failure, but of necessary unlearning.",
        "climax_template": "In the depths, a revelation: what seemed like loss was actually the clearing of a path.",
        "resolution_template": "The ascent that followed wasn't just growth — it was the embrace of a deeper truth.",
        "keywords": "discovery revelation understanding struggle enlightenment wisdom depth",
    },
]

result = search_client.upload_documents(documents=narrative_templates)
print(f"[OK] Uploaded {len(narrative_templates)} narrative templates to Foundry IQ")
print(f"[OK] Knowledge Base ready at: {endpoint}/indexes/{index_name}")
