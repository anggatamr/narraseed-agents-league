# NarraSeed Architecture

## System Overview

NarraSeed is a full-stack application that transforms time-series data into AI-generated narratives through a 6-stage statistical and AI pipeline.

## Data Flow Pipeline

1. Ingest & Normalize — CSV → Pandas DataFrame → Min-max normalize [0,1]
2. Turning Points (PELT) — Changepoint detection → segment data into arcs
3. Arc Matching (DTW) — Dynamic Time Warping → match to 6 narrative archetypes
4. Knowledge Retrieval (Foundry IQ) — Azure AI Search Knowledge Base → grounded narrative guidelines with citations
5. Narrative Generation (Ollama) — Local Mistral-7B LLM → generate story using grounded templates + data facts
6. Visualization & Delivery — D3.js timeline + Web Speech API synchronized narration

## Microsoft IQ Integration: Foundry IQ

NarraSeed uses Foundry IQ via Azure AI Search Knowledge Base for agentic knowledge retrieval. The Knowledge Base stores 6 narrative arc templates with tone guidelines, opening/climax/resolution templates, and keywords.

When the pipeline determines a data pattern's narrative arc, it queries the Knowledge Base for arc-specific guidance. The Foundry IQ retrieval engine returns grounded, cited guidelines that the LLM uses to generate narratives that are template-consistent and factually anchored.

This ensures narratives are not hallucinated — every story element traces back to either (a) actual data values or (b) Foundry IQ knowledge base documents.

## GitHub Copilot Integration

NarraSeed exposes an MCP (Model Context Protocol) server with 2 tools:
- analyze_timeseries: Full pipeline from CSV to narrative
- remix_git_history: Transform git commits into developer journey stories

Accessible via @narraseed in VS Code Copilot Chat.
