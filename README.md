# 🌱 NarraSeed: Temporal Narrative Intelligence

> **Transform time-series data into dramatized, interactive stories powered by AI.**  
> Built for the **Agents League Creative Apps Track — AI Skills Fest 2026**

---

## What It Does

**NarraSeed** turns flat, hard-to-parse numerical columns into engaging, accessible, and structured stories. By analyzing raw time-series data, it detects critical transitions, maps the overall pattern to human storytelling structures (narrative arcs), grounds itself in verified narrative templates via **Azure AI Search (Foundry IQ)**, and uses a local **Mistral-7B LLM (Ollama)** to draft an interactive narrative. The results are rendered in a warm, responsive dashboard with a custom D3.js timeline and synchronized text-to-speech voice narration.

---

## Features

1. **Intelligent CSV Ingestion & Preprocessing**
   - **Multi-column Auto-detection**: Automatically finds suitable numeric columns for value target (Y-axis) and sequential/time columns (X-axis).
   - **Chronological Sorting**: Parses and sorts datasets containing out-of-order date strings (e.g., `steps_tracker_dataset.csv`).
   - **Categorical Entity Filtering**: Automatically identifies entity columns (like `Entity` in `population-with-un-projections.csv`), filters by the most active entity (e.g. `Afghanistan`), and focuses the narrative.
   - **Data Interpolation**: Handles missing data points gracefully using linear interpolation.

2. **Advanced Time-Series Analysis Pipeline**
   - **PELT Changepoint Detection**: Uses the ruptures library to segment data into distinct temporal regimes and pinpoint exact turning points.
   - **Dynamic Time Warping (DTW)**: Maps normalized segments against 6 narrative archetypes (steady growth, decline, cautionary rise & fall, resilience comeback, transformative crash-and-ascent, and discovery).

3. **Grounded AI Generation with Citations**
   - **Foundry IQ Grounding**: Connects to Azure AI Search to fetch verified narrative rules, preventing hallucination.
   - **Ollama Offline-First Core**: Communicates with a local Mistral-7B LLM. Uses a robust connection-timeout system (3.0s limit) to fallback gracefully to predefined templates if Ollama is offline.
   - **Grounded Citations**: Citations link back to specific CSV indices/values and the exact template document retrieved.

4. **Interactive Dashboard & Voice Sync**
   - **D3.js Visualization**: Interactive timeline featuring smooth monotone curves, custom date-string axes, hover tooltips with original values, and glowing turning-point indicators.
   - **Synchronized Web Speech Narration**: Reads the generated story while highlighting active words with a cozy warm-beige sweep animation.
   - **Gen-Z Warm Minimalist Design**: Cozy light mode in cream `#FBF8F4` and terracotta `#C67B5C`, focused on accessibility and distraction-free readability.

---

## Project Architecture & Data Flow

```
                     [ CSV Data / Git History ]
                                 │
                                 ▼
                     [ FastAPI Backend (8000) ]
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
[ Normalize & Parse ]                           [ PELT Detection ]
 - Entity Filtering                              - Regime Transitions
 - Chronological Sorting                         - Segment Arcs
         │                                               │
         └───────────────────────┬───────────────────────┘
                                 ▼
                         [ DTW Arc Matching ]
                          - Compare Archetypes
                                 │
                                 ▼
                  [ Foundry IQ Knowledge Retrieval ]
                   - Azure AI Search (2026-04-01)
                   - Fallback local templates
                                 │
                                 ▼
                    [ Ollama Mistral-7B LLM ]
                     - Grounded prompts
                     - 3-second connection fallback
                                 │
                                 ▼
                  [ D3.js timeline & Web Speech ]
```

---

## Tech Stack

| Layer | Component | Technology | Rationale |
|---|---|---|---|
| **Backend** | API | Python 3.11+, FastAPI | Asynchronous performance, automatic Swagger documentation. |
| **Backend** | Statistics | ruptures, fastdtw, pandas | Robust changepoint and curve-matching mathematics. |
| **Knowledge** | Grounding | Azure AI Search (Foundry IQ) | Microsoft-compliant agentic knowledge grounding with citations. |
| **LLM** | Local AI | Ollama (Mistral-7B) | Local execution with zero cost, high privacy, and infinite tokens. |
| **Frontend** | Interface | Vanilla HTML5, CSS3 Variables | Cozy Gen-Z minimalist look, fast rendering without build steps. |
| **Frontend** | Visuals | D3.js v7 | Industry-standard vector charting with custom interaction. |
| **Frontend** | Voice | Web Speech API | Native browser text-to-speech with word boundary tracking. |
| **Copilot** | MCP | FastMCP SDK | Plugs directly into VS Code Copilot Chat via Model Context Protocol. |

---

## Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running locally
- Azure subscription (free tier suffices) with Azure AI Search configured

### 1. Clone & Set Up Directory
```bash
git clone https://github.com/anggatamr/narraseed-agents-league.git
cd narraseed-agents-league
```

### 2. Configure Environment Variables
Create a `.env` file in the `backend/` directory:
```env
# ===== LOCAL LLM (Ollama) =====
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=30

# ===== AZURE AI FOUNDRY — FOUNDRY IQ =====
AZURE_SEARCH_ENDPOINT=https://<your-service-name>.search.windows.net
AZURE_SEARCH_KEY=<your-primary-admin-key>
AZURE_SEARCH_INDEX=narrative-templates
AZURE_KNOWLEDGE_BASE_NAME=narraseed-kb

# ===== DEV SETTINGS =====
DEBUG=True
PORT=8000
LOG_LEVEL=INFO
```

### 3. Initialize Python Virtual Environment & Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 4. Seed Foundry IQ templates (Azure Search)
Populate your Azure Search Index with the 6 narrative templates:
```bash
python backend/setup_foundry_iq.py
```

### 5. Start Backend Server
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 6. Serve Frontend Dashboard
In a new terminal window:
```bash
cd frontend
python -m http.server 3000
```
Open your browser to: **[http://localhost:3000](http://localhost:3000)**

---

## VS Code Copilot MCP Server Configuration

Integrating NarraSeed directly into VS Code Copilot Chat allows you to run data analysis using conversational prompts.

1. Open VS Code settings file or create `.vscode/settings.json`:
```json
{
  "github.copilot.chat.codeGeneration.useInstructionFiles": true
}
```
2. Create/Update `.vscode/mcp.json`:
```json
{
  "servers": {
    "narraseed": {
      "command": "python",
      "args": ["backend/mcp/mcp_server.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```
3. Ask Copilot Chat questions like:
   - `@narraseed Analyze backend/data/sample_gpa.csv with dramatic style`
   - `@narraseed Remix git history into a developer's journey`

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
