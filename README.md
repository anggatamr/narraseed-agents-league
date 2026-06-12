# 🌱 NarraSeed: Temporal Narrative Intelligence

> Transform time-series data into dramatized, interactive stories powered by AI.

**Agents League Creative Apps Track — AI Skills Fest 2026**

## What It Does

NarraSeed turns time-series data into compelling narratives. Upload any time-series CSV → the system analyzes turning points, matches narrative arcs, queries Foundry IQ for grounded templates → generates an AI story → renders an interactive timeline with synchronized voice narration.

## Quick Start

### Prerequisites
- Python 3.11+
- Ollama installed and running
- Azure AI Search configured

### Installation

```bash
cd hackathon/narraseed-agents-league
python -m venv venv
venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Run Backend

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### Run Frontend

```bash
cd frontend
python -m http.server 3000
```

Open: http://localhost:3000
