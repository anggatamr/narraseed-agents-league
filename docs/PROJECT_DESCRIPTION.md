# NarraSeed: Temporal Narrative Intelligence Platform

NarraSeed transforms raw time-series data into dramatized, interactive narratives using statistical analysis and AI. Users upload CSV data → the system detects turning points using PELT changepoint detection → matches data patterns to 6 narrative archetypes via Dynamic Time Warping → queries Azure AI Foundry IQ Knowledge Base for grounded narrative templates → generates a compelling story using a local Mistral-7B LLM → renders everything as an interactive D3.js timeline with synchronized voice narration.

Key innovations: (1) A rigorous statistical pipeline ensures narratives are data-grounded, not hallucinated. (2) Foundry IQ provides cited knowledge retrieval so every narrative claim traces back to source data and templates. (3) The local-first architecture (Ollama) means zero quota limits and full offline capability. (4) GitHub Copilot MCP integration enables developers to generate data narratives directly in VS Code.

Built for accessibility — the warm, minimalist interface makes complex data understandable for everyone from students to business analysts.

Technologies: Python/FastAPI, Ollama/Mistral-7B, Azure AI Search (Foundry IQ), D3.js, Web Speech API, GitHub Copilot MCP.
