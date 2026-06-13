// Backend runs on port 8000, frontend on port 3000 during hackathon demo
const BACKEND_ORIGIN = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8000"
  : window.location.origin;
const apiBase = `${BACKEND_ORIGIN}/api`;
const state = {
  currentStyle: "dramatic",
  isNarrating: false,
  currentData: null,
};

function parseMarkdown(text) {
  return text
    .replace(/^### (.+)$/gm, '<h4 class="story-heading">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="story-heading">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 class="story-heading">$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[h|p])(.+)$/gm, '<p>$1</p>');
}

const storyText = document.getElementById("story-text");
const citationsTopList = document.getElementById("citations-top-list");
const citationsBottomList = document.getElementById("citations-bottom-list");
const analyzeButton = document.getElementById("analyze-button");
const csvUpload = document.getElementById("csv-upload");
const uploadLabel = document.getElementById("upload-label");
const styleSelect = document.getElementById("style-select");

const sampleGpa = document.getElementById("sample-gpa");
const sampleStartup = document.getElementById("sample-startup");
const sampleFitness = document.getElementById("sample-fitness");

// Update style selector
if (styleSelect) {
  styleSelect.addEventListener("change", (e) => {
    state.currentStyle = e.target.value;
  });
}

// Show selected filename in dropzone
if (csvUpload && uploadLabel) {
  csvUpload.addEventListener("change", () => {
    const file = csvUpload.files[0];
    if (file) {
      uploadLabel.textContent = file.name;
      uploadLabel.style.color = "var(--coral)";
    }
  });
}

// Drag-and-drop file upload handlers
const fileUploadWrapper = document.querySelector(".file-upload-wrapper");
if (fileUploadWrapper) {
  fileUploadWrapper.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.stopPropagation();
    fileUploadWrapper.classList.add("drag-over");
  });
  fileUploadWrapper.addEventListener("dragleave", (e) => {
    e.preventDefault();
    e.stopPropagation();
    fileUploadWrapper.classList.remove("drag-over");
  });
  fileUploadWrapper.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    fileUploadWrapper.classList.remove("drag-over");
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.type === "text/csv" || droppedFile.name.endsWith(".csv"))) {
      const dt = new DataTransfer();
      dt.items.add(droppedFile);
      csvUpload.files = dt.files;
      if (uploadLabel) {
        uploadLabel.textContent = droppedFile.name;
        uploadLabel.style.color = "var(--coral)";
      }
    } else {
      if (uploadLabel) {
        uploadLabel.textContent = "Please drop a CSV file";
        uploadLabel.style.color = "var(--error)";
      }
    }
  });
}

// ══════════════════════════════════════════════════════════════
// PIPELINE STEPPER (dark card context)
// ══════════════════════════════════════════════════════════════

function initPipeline() {
  const progressContainer = document.getElementById("pipeline-progress");
  if (!progressContainer) return;

  const stages = [
    { label: "Preprocess", icon: "database",    color: "#4B5FD4" },
    { label: "Detect",     icon: "activity",    color: "#D9A000" },
    { label: "Match",      icon: "share-2",     color: "#D4614A" },
    { label: "Ground",     icon: "lightbulb",   color: "#7B4FB5" },
    { label: "Narrate",    icon: "book-open",   color: "#3D7A5F" },
    { label: "Polish",     icon: "sparkles",    color: "#1C7CC0" },
  ];

  progressContainer.innerHTML = stages
    .map((stage, idx) => {
      return `
        <div class="pipeline-stage pending" data-index="${idx}" data-color="${stage.color}" data-icon="${stage.icon}">
          <div class="stage-dot">
            <i data-lucide="${stage.icon}" style="width: 11px; height: 11px; color: inherit;"></i>
          </div>
          <div class="stage-label">${stage.label}</div>
        </div>
        ${idx < stages.length - 1 ? '<div class="pipeline-line"></div>' : ''}
      `;
    })
    .join("");

  lucide.createIcons();
}

function hexToRgba(hex, alpha) {
  const normalized = hex.replace("#", "");
  const parsed = normalized.length === 3
    ? normalized.split("").map((char) => char + char).join("")
    : normalized;
  const intValue = parseInt(parsed, 16);
  const r = (intValue >> 16) & 255;
  const g = (intValue >> 8) & 255;
  const b = intValue & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function applyPipelineState(stage, stateName, accentColor, iconName) {
  const dot = stage.querySelector(".stage-dot");
  stage.classList.remove("pending", "active", "complete");
  stage.classList.add(stateName);

  if (stateName === "active") {
    stage.style.background = accentColor;
    stage.style.borderColor = accentColor;
    stage.style.color = "#FFFFFF";
    stage.style.boxShadow = `0 0 8px ${hexToRgba(accentColor, 0.3)}`;
    dot.style.color = "#FFFFFF";
  } else if (stateName === "complete") {
    stage.style.background = "#F0FDF4";
    stage.style.borderColor = "#86EFAC";
    stage.style.color = "#16A34A";
    stage.style.boxShadow = "none";
    dot.style.color = "#16A34A";
  } else {
    stage.style.background = "#FFFFFF";
    stage.style.borderColor = "#E7E5E4";
    stage.style.color = "#78716C";
    stage.style.boxShadow = "none";
    dot.style.color = "#78716C";
  }

  // Completed steps show a check icon instead of the step icon
  const resolvedIcon = stateName === "complete" ? "check" : iconName;
  dot.innerHTML = `<i data-lucide="${resolvedIcon}" style="width: 11px; height: 11px; color: inherit;"></i>`;
  lucide.createIcons();
}

// Pipeline progress bar animator
function animatePipeline(onComplete) {
  const progressContainer = document.getElementById("pipeline-progress");
  if (!progressContainer) {
    onComplete();
    return;
  }

  const stages = document.querySelectorAll(".pipeline-stage");
  const lines = document.querySelectorAll(".pipeline-line");

  let currentStage = 0;

  function tick() {
    stages.forEach((stage, idx) => {
      const accentColor = stage.getAttribute("data-color") || "#D4614A";
      const iconName = stage.getAttribute("data-icon") || "sparkles";
      if (idx < currentStage) {
        applyPipelineState(stage, "complete", accentColor, iconName);
      } else if (idx === currentStage) {
        applyPipelineState(stage, "active", accentColor, iconName);
      } else {
        applyPipelineState(stage, "pending", accentColor, iconName);
      }
    });

    lines.forEach((line, idx) => {
      line.style.background = idx < currentStage ? "#86EFAC" : "#E7E5E4";
    });

    if (currentStage < stages.length - 1) {
      currentStage++;
      setTimeout(tick, 300);
    } else {
      stages.forEach((stage) => {
        const accentColor = stage.getAttribute("data-color") || "#D4614A";
        applyPipelineState(stage, "complete", accentColor, "check");
      });
      lines.forEach((line) => {
        line.style.background = "#86EFAC";
      });
      setTimeout(onComplete, 200);
    }
  }

  tick();
}

// Initialize pipeline on page load
initPipeline();

// ══════════════════════════════════════════════════════════════
// VOICE NARRATION
// ══════════════════════════════════════════════════════════════

function setupVoiceControls() {
  const narrateBtn = document.getElementById("narrate-btn");
  const stopBtn = document.getElementById("stop-btn");

  if (narrateBtn) {
    narrateBtn.addEventListener("click", () => {
      if (storyText.textContent && !storyText.textContent.includes("Select a dataset")) {
        const textContent = storyText.innerText;
        startNarration(textContent);
        state.isNarrating = true;
        narrateBtn.style.display = "none";
        stopBtn.style.display = "flex";
      }
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", () => {
      stopNarration();
      state.isNarrating = false;
      narrateBtn.style.display = "flex";
      stopBtn.style.display = "none";
    });
  }
}

// ══════════════════════════════════════════════════════════════
// ANALYSIS
// ══════════════════════════════════════════════════════════════

async function analyzeFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("style", state.currentStyle);

  // Disable analyze button during processing
  if (analyzeButton) {
    analyzeButton.disabled = true;
    analyzeButton.classList.add("loading");
    analyzeButton.innerHTML = '<i data-lucide="loader-2" style="width: 15px; height: 15px;"></i> Analyzing...';
    lucide.createIcons();
  }

  initPipeline();
  storyText.innerHTML = '<div style="display:flex;align-items:center;gap:8px;color:#716A62;"><i data-lucide="loader-2" style="width:20px;height:20px;animation:spin 1s linear infinite;"></i> Analyzing data...</div>';
  if (citationsTopList) citationsTopList.innerHTML = "";
  if (citationsBottomList) citationsBottomList.innerHTML = "";

  // Reset arc/confidence cells
  const arcValue = document.getElementById("arc-value");
  const confidenceValue = document.getElementById("confidence-value");
  if (arcValue) arcValue.textContent = "—";
  if (confidenceValue) confidenceValue.textContent = "—";

  try {
    const response = await fetch(`${apiBase}/analyze`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Analysis failed.");
    }

    state.currentData = data;

    // Run the visual progress animation before rendering results
    animatePipeline(() => {
      // ── Update story panel ──
      storyText.innerHTML = parseMarkdown(data.story);

      // ── Setup voice controls ──
      setupVoiceControls();

      // ── Populate arc stat cell ──
      if (arcValue) {
        arcValue.textContent = data.arc || "Unknown Arc";
      }

      // ── Populate confidence stat cell ──
      if (confidenceValue) {
        const conf = ((data.grounding?.confidence || 0.85) * 100).toFixed(0);
        confidenceValue.textContent = conf + "%";
      }

      // ── Update citations ──
      if (data.citations && data.citations.length > 0) {
        const knowledgeCitations = data.citations.filter((c) => c.type === "knowledge");
        const dataCitations = data.citations.filter((c) => c.type === "data").slice(0, 8);

        if (citationsTopList) {
          let knowledgeHTML = '';
          knowledgeCitations.forEach(c => {
            knowledgeHTML += `
              <div class="citation-item foundry">
                <div class="citation-icon-chip"><i data-lucide="lightbulb"></i></div>
                <div class="citation-content">
                  <div class="citation-tag">Foundry IQ</div>
                  <div class="citation-label">Arc matched: <strong>${data.arc}</strong></div>
                  <div class="citation-source">Source: ${c.source} / doc: ${c.document}</div>
                </div>
              </div>
            `;
          });
          citationsTopList.innerHTML = knowledgeHTML || `
            <div class="citations-empty">
              <i data-lucide="lightbulb"></i>
              <div class="citations-empty-text">No grounding templates matched.</div>
            </div>
          `;
        }

        if (citationsBottomList) {
          let dataHTML = '';
          dataCitations.forEach(c => {
            const xLabel = data.x_labels && data.x_labels[c.index] ? data.x_labels[c.index] : `Index ${c.index}`;
            dataHTML += `
              <div class="citation-item datapoint">
                <div class="citation-icon-chip"><i data-lucide="database"></i></div>
                <div class="citation-content">
                  <div class="citation-tag">Data Point</div>
                  <div class="citation-label">Fact Citation: <strong>${xLabel}</strong></div>
                  <div class="citation-value">${c.value.toLocaleString(undefined, {maximumFractionDigits: 3})}</div>
                </div>
              </div>
            `;
          });
          citationsBottomList.innerHTML = dataHTML || `
            <div class="citations-empty">
              <i data-lucide="database-zap"></i>
              <div class="citations-empty-text">No data facts cited.</div>
            </div>
          `;
        }
        lucide.createIcons();
      }

      // ── Render timeline chart ──
      renderTimeline("timeline", data);
      window.dispatchEvent(new Event("resize"));
    });

  } catch (error) {
    storyText.innerHTML = `<div style="color:#D4614A;display:flex;gap:8px;align-items:center;"><i data-lucide="alert-circle"></i> Error: ${error.message}</div>`;
    if (citationsTopList) citationsTopList.innerHTML = "";
    if (citationsBottomList) citationsBottomList.innerHTML = "";
    lucide.createIcons();
  } finally {
    // Re-enable analyze button
    if (analyzeButton) {
      analyzeButton.disabled = false;
      analyzeButton.classList.remove("loading");
      analyzeButton.innerHTML = '<i data-lucide="sparkles"></i> Analyze Data';
      lucide.createIcons();
    }
  }
}

analyzeButton.addEventListener("click", () => {
  const file = csvUpload.files[0];
  if (!file) {
    storyText.innerHTML = '<div style="display:flex;gap:8px;align-items:center;color:#D4614A;"><i data-lucide="inbox"></i> Please choose or drag a CSV file first.</div>';
    lucide.createIcons();
    return;
  }
  analyzeFile(file);
});

sampleGpa.addEventListener("click", async () => {
  await loadSample("sample_gpa.csv");
});

sampleStartup.addEventListener("click", async () => {
  await loadSample("sample_startup.csv");
});

sampleFitness.addEventListener("click", async () => {
  await loadSample("sample_fitness.csv");
});

async function loadSample(filename) {
  try {
    if (uploadLabel) {
      uploadLabel.textContent = filename.replace("sample_", "").replace("_", " ").replace(".csv", "").toUpperCase();
      uploadLabel.style.color = "var(--sage)";
    }
    const response = await fetch(`${BACKEND_ORIGIN}/data/${filename}`);
    const text = await response.text();
    const blob = new Blob([text], { type: "text/csv" });
    analyzeFile(new File([blob], filename, { type: "text/csv" }));
  } catch (error) {
    storyText.innerHTML = `<div style="display:flex;gap:8px;align-items:center;color:#D4614A;"><i data-lucide="alert-circle"></i> Failed to load sample: ${error.message}</div>`;
    lucide.createIcons();
  }
}
