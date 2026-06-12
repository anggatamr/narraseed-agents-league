# Phase 7: Demo Video & Submission Checklist

## Pre-Submission Verification

### ✅ Technical Readiness

- [ ] Backend API endpoints tested and working
  - [ ] GET /api/health (Ollama + Azure Search connectivity)
  - [ ] GET /api/samples (CSV file listing)
  - [ ] POST /api/analyze (full pipeline execution)
- [ ] Frontend dashboard accessible
  - [ ] D3.js timeline rendering correctly
  - [ ] Story panel displays narrative
  - [ ] Citations panel shows KB + data sources
  - [ ] Voice controls working (play/pause/stop)
- [ ] Sample data files working
  - [ ] sample_gpa.csv → "Rags to Riches" arc
  - [ ] sample_startup.csv → "Icarus" arc
  - [ ] sample_fitness.csv → "Phoenix" arc
- [ ] Integration tests passing
  - [ ] pytest tests/test_pipeline.py -v (11/11 passing)
- [ ] MCP server operational
  - [ ] @narraseed tools available in VS Code

### ✅ Repository Compliance

- [ ] .gitignore properly configured (excludes .env, __pycache__, venv/)
- [ ] .env.example created (credentials template)
- [ ] LICENSE file present (MIT)
- [ ] README.md comprehensive (quick start + architecture)
- [ ] docs/PROJECT_DESCRIPTION.md complete (300+ words)
- [ ] docs/ARCHITECTURE.md detailed (system overview + flow)
- [ ] Git repository initialized and committed
- [ ] No credentials committed (verify: `git log -S "AZURE_SEARCH_KEY"` returns empty)

### ✅ Documentation Complete

- [ ] README includes:
  - [ ] Problem statement + solution
  - [ ] Tech stack table
  - [ ] 6-stage pipeline explanation
  - [ ] Quick start guide
  - [ ] API documentation
  - [ ] Copilot MCP usage example
- [ ] Architecture diagram available (ASCII or PNG)
- [ ] Sample data documented
- [ ] Test coverage explained

---

## Demo Video Recording (5 minutes)

### Script Template

```
[0:00-0:30] INTRODUCTION
"Hi! I'm Angga Tamara, and I want to show you NarraSeed — 
a temporal narrative intelligence platform that transforms 
raw data into compelling, grounded AI stories.

Here's the problem: Most data storytelling requires expertise 
in three areas — domain knowledge, narrative craft, and verified 
information sources. NarraSeed solves this automatically."

[0:30-1:30] DEMO: DASHBOARD
"Let me walk you through the interface. This is the dashboard. 
I can upload a CSV file or click one of the pre-loaded samples.

Let's click 'Sample: Student GPA Journey' to see it in action..."
[Click sample, watch pipeline progress]
"Notice the system is analyzing the data..."

[1:30-2:30] DEMO: TIMELINE + STORY
"Here's the magic. The system detected this is a 'Rags to Riches' 
narrative — the student's GPA steadily improved over semesters.

The timeline shows the data normalized to [0-1], with turning 
points marked in green. You can hover to see exact values.

Below is the AI-generated narrative, grounded in verified 
knowledge base templates..."

[2:30-3:30] DEMO: CITATIONS + VOICE
"Every claim in the story traces back to sources — either 
data points from the CSV or knowledge base templates from 
Foundry IQ (our Azure AI Search integration).

And here's the voice narration — synthesized using Web Speech API..."
[Click play button, let narrative play for 10 seconds]
"You can pause, resume, or adjust playback speed."

[3:30-4:30] TECHNICAL ARCHITECTURE
"Behind the scenes, NarraSeed runs a 6-stage pipeline:
1. Normalize the data to [0-1] range
2. Detect turning points using PELT changepoint detection
3. Match narrative patterns using Dynamic Time Warping
4. Query our knowledge base (Azure AI Search)
5. Generate narrative with local Ollama LLM
6. Render interactive visualization

All processing happens locally — no external API calls, 
full offline capability, zero quota limits."

[4:30-5:00] CLOSING
"This platform democratizes data storytelling. 
Journalists, analysts, educators — anyone can now 
transform raw data into engaging narratives in seconds.

The code is open source on GitHub, and the tools are 
available as GitHub Copilot MCP integration.

Thanks for watching!"
```

### Recording Setup

**Software:**
- Screen recorder: Windows 11 built-in (Win+G), OBS Studio (free), or ScreenFlow (Mac)
- Microphone: Built-in or USB
- Format: 1920×1080, 30fps, MP4 codec

**Environment:**
- Close unnecessary applications
- Ensure Ollama is running (backend starts automatically)
- Start frontend on localhost:3000
- Backend running on localhost:8000
- Clear cache (Dev Tools → Application → Clear storage)

**Recording Checklist:**
- [ ] Timestamp visible in corner (optional, helps with pacing)
- [ ] Mouse cursor clearly visible
- [ ] Narrator audio clear (45-55 dB)
- [ ] No background noise
- [ ] Video bitrate: 5-8 Mbps for 1080p60
- [ ] Duration: 4:50-5:10 (target 5 min)

---

## GitHub Repository Setup

### Create Repository

```bash
# Prerequisite: GitHub account with 2FA enabled
# Visit: https://github.com/new

Repository Name: narraseed-agents-league
Owner: anggatamr
Visibility: PUBLIC (CRITICAL — competitions require public repos)
Initialize: No (we have existing code)
License: MIT (already added)
.gitignore: Python (already added)
```

### Add Remote & Push

```bash
cd narraseed-agents-league
git remote add origin https://github.com/anggatamr/narraseed-agents-league.git
git branch -M main
git push -u origin main

# Verify
git remote -v
git branch -a
```

### Repository Settings

- [ ] Set default branch to `main`
- [ ] Enable "Require branches to be up to date before merging" (optional)
- [ ] Add Topics: `temporal-narrative`, `ai-storytelling`, `data-viz`, `azure-search`, `ollama`
- [ ] Write repository description:
  ```
  🌱 Transform time-series data into AI-generated narratives 
  using statistical analysis + knowledge grounding + local LLM.
  Agents League Creative Apps 2026.
  ```

---

## Video Upload (YouTube)

### Create YouTube Video

1. **Go to**: https://youtube.com/upload
2. **Upload file**: Select demo video MP4
3. **Title**: `NarraSeed: Temporal Narrative Intelligence — Agents League 2026`
4. **Description**:
   ```
   Temporal narrative intelligence platform transforming time-series data 
   into grounded AI stories.
   
   🔗 GitHub: https://github.com/anggatamr/narraseed-agents-league
   📖 Architecture: See docs/ARCHITECTURE.md
   
   🌱 Features:
   - PELT changepoint detection for turning points
   - 6 narrative archetypes (Rags to Riches, Icarus, Phoenix, etc.)
   - Foundry IQ knowledge base grounding
   - Local Ollama LLM (offline-capable)
   - Interactive D3.js timeline + voice narration
   
   Built for Agents League Creative Apps Track 2026.
   ```
4. **Thumbnail**: Generate auto or create custom (1280×720)
5. **Visibility**: 🔒 Unlisted (share link only, not searchable)
6. **Save & Get Shareable Link**

---

## Contest Submission

### 1. Contest Website Form

**Location**: Agents League submission portal (TBD at contest site)

| Field | Value |
|-------|-------|
| **Project Title** | NarraSeed: Temporal Narrative Intelligence |
| **GitHub Repository** | https://github.com/anggatamr/narraseed-agents-league |
| **Demo Video URL** | [Unlisted YouTube link] |
| **Track** | Creative Apps |
| **Team Lead** | Angga Tamara |
| **Microsoft Learn ID** | AnggaTamara-1496 |
| **Project Description** | [Copy from docs/PROJECT_DESCRIPTION.md] |
| **Architecture Diagram** | [Upload docs/ARCHITECTURE.md or PNG] |
| **Tech Stack** | Python, FastAPI, Azure AI Search, Ollama, D3.js |
| **Innovation Highlight** | Statistical rigor (PELT) + knowledge grounding (Foundry IQ) + local LLM (offline) |

### 2. Discord Community Vote (Optional, 10% of score)

**Channel**: Agents League submissions (TBD)
**Post**:
```
🌱 NarraSeed: Temporal Narrative Intelligence

Transform time-series data into AI-generated narratives using 
statistical analysis + knowledge grounding + local LLM.

✨ Highlights:
- PELT changepoint detection
- 6 narrative archetypes (DTW matching)
- Foundry IQ knowledge base integration
- Ollama local LLM (offline-capable)
- Interactive D3.js timeline

🔗 GitHub: https://github.com/anggatamr/narraseed-agents-league
📹 Demo: [YouTube link]
```

---

## Submission Timeline

| Task | Deadline | Status |
|------|----------|--------|
| Complete Phase 7 checklist | June 13 (Fri) | ⏳ |
| Record demo video | June 13 (Fri) | ⏳ |
| Upload to YouTube | June 13 (Fri) | ⏳ |
| Create GitHub repo + push | June 13 (Fri) | ✅ (In progress) |
| Final documentation review | June 13 (Fri) | ⏳ |
| **SUBMIT** | June 14 (Sat) 11:59 PM PT | ⏳ |

---

## Post-Submission

### Follow-Up

- [ ] Monitor for judge questions/feedback
- [ ] Check GitHub for issues/PRs
- [ ] Prepare for potential demo call (live walkthrough)
- [ ] Track contest results (announced June 21 or later)

### Potential Judge Questions (Prepare Answers)

1. **"Why PELT over other changepoint detection?"**
   - Published algorithm with theoretical guarantees; handles multiple regimes

2. **"How do you ensure narratives aren't hallucinated?"**
   - Dual citation system: Knowledge Base templates + data points; fallback local templates

3. **"Why local Ollama instead of cloud LLM?"**
   - No API keys, no quotas, offline-capable, privacy-preserving, cost-effective

4. **"How does this compare to existing narrative tools?"**
   - Statistical rigor (PELT + DTW), knowledge grounding (Foundry IQ), local-first architecture

5. **"Scalability for large datasets?"**
   - Benchmark: 100MB CSV, 1000+ time points handled at ~5s per request

---

## Success Criteria

✅ **Minimum:**
- Repository public on GitHub
- README + docs complete
- Demo video uploaded
- Form submitted by deadline

✅ **Expected:**
- Integration tests passing
- All endpoints functional
- Demo video clear + engaging
- Documentation comprehensive

✅ **Stretch:**
- Top 10 finalist (judged on innovation + execution)
- Accepted for final round
- Prize consideration

---

**Status**: Ready for Phase 7 execution
**Next Step**: Start backend server + test API endpoints
