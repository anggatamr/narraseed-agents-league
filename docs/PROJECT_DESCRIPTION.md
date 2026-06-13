# NarraSeed: Temporal Narrative Intelligence Platform

**NarraSeed** transforms raw time-series data into dramatized, interactive narratives using statistical analysis and AI. Users upload CSV data → the system detects turning points using PELT changepoint detection → matches data patterns to 6 narrative archetypes via Dynamic Time Warping → queries Azure AI Foundry IQ Knowledge Base for grounded narrative templates → generates a compelling story using a local Qwen2.5-1.5B LLM → renders everything as an interactive D3.js timeline with synchronized voice narration.

### Key Innovations
1. **Statistical Rigor**: A rigorous mathematical pipeline (PELT + DTW) ensures narratives are data-grounded and structured, not hallucinated.
2. **Foundry IQ Grounding**: Azure AI Search acts as a Knowledge Base for narrative patterns, returning cited templates so every story element traces back to source data and verified guidelines.
3. **Local-First Core**: The local LLM architecture (Ollama) means zero billing, infinite token quotas, and full offline capability.
4. **GitHub Copilot Integration**: An MCP server exposes custom tools enabling developers to query datasets and compile git commit metrics into narratives directly within VS Code Copilot Chat.

Built with accessibility in mind, the warm Gen-Z minimalist interface makes complex data understandable and engaging for everyone from students to business analysts.

**Technologies**: Python/FastAPI, Ollama/Qwen2.5-1.5B, Azure AI Search (Foundry IQ), D3.js, Web Speech API, GitHub Copilot MCP.
