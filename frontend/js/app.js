const apiBase = "http://localhost:8000/api";
const state = {
  currentStyle: "dramatic",
  isNarrating: false,
  currentData: null,
};

const storyText = document.getElementById("story-text");
const citationsList = document.getElementById("citations-list");
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
      uploadLabel.style.color = "var(--accent-terracotta)";
    }
  });
}

// Pipeline progress bar animator
function animatePipeline(onComplete) {
  const progressContainer = document.getElementById("pipeline-progress");
  if (!progressContainer) {
    onComplete();
    return;
  }
  
  progressContainer.style.display = "flex";
  
  const stages = document.querySelectorAll(".pipeline-stage");
  const lines = document.querySelectorAll(".pipeline-line");
  
  let currentStage = 0;
  
  function tick() {
    stages.forEach((stage, idx) => {
      stage.classList.remove("active", "complete");
      if (idx < currentStage) {
        stage.classList.add("complete");
      } else if (idx === currentStage) {
        stage.classList.add("active");
      }
    });
    
    lines.forEach((line, idx) => {
      line.classList.remove("active");
      if (idx < currentStage) {
        line.classList.add("active");
      }
    });
    
    if (currentStage < 5) {
      currentStage++;
      setTimeout(tick, 300);
    } else {
      // Complete all
      stages.forEach(stage => {
        stage.classList.remove("active");
        stage.classList.add("complete");
      });
      lines.forEach(line => line.classList.add("active"));
      setTimeout(onComplete, 200);
    }
  }
  
  tick();
}

// Add voice control UI
function addVoiceControls() {
  const storyPanel = document.getElementById("story-panel");
  if (storyPanel.querySelector(".voice-controls")) {
    return;
  }

  const voiceControlsHTML = `
    <div class="voice-controls">
      <button id="play-narration" class="voice-btn play">
        🔊 Narrate Story
      </button>
      <button id="pause-narration" class="voice-btn pause" style="display: none;">
        ⏸ Pause
      </button>
      <button id="stop-narration" class="voice-btn stop">
        ⏹ Stop
      </button>
    </div>
  `;

  storyPanel.insertAdjacentHTML("afterbegin", voiceControlsHTML);

  // Attach event listeners
  document.getElementById("play-narration").addEventListener("click", () => {
    if (storyText.textContent && !storyText.textContent.includes("Select a dataset")) {
      startNarration(storyText.innerText);
      state.isNarrating = true;
      document.getElementById("play-narration").style.display = "none";
      document.getElementById("pause-narration").style.display = "inline-block";
    }
  });

  document.getElementById("pause-narration").addEventListener("click", () => {
    pauseNarration();
    state.isNarrating = false;
    document.getElementById("play-narration").style.display = "inline-block";
    document.getElementById("pause-narration").style.display = "none";
  });

  document.getElementById("stop-narration").addEventListener("click", () => {
    stopNarration();
    state.isNarrating = false;
    document.getElementById("play-narration").style.display = "inline-block";
    document.getElementById("pause-narration").style.display = "none";
  });
}

async function analyzeFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("style", state.currentStyle);

  storyText.textContent = "🔄 Analyzing data and connecting with Foundry IQ...";
  citationsList.innerHTML = "";
  
  const progressContainer = document.getElementById("pipeline-progress");
  if (progressContainer) progressContainer.style.display = "flex";

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
      // Update story panel
      storyText.innerHTML = `
        <div style="line-height: 1.8; color: #5C5750; font-size: 15px; margin-top: var(--space-4);">
          ${data.story.split('\n').filter(l => l.trim()).map(line => `<p style="margin-bottom: 12px;">${line.trim()}</p>`).join('')}
        </div>
      `;

      // Add voice controls
      addVoiceControls();

      // Update citations
      if (data.citations && data.citations.length > 0) {
        const knowledgeCitations = data.citations.filter((c) => c.type === "knowledge");
        const dataCitations = data.citations.filter((c) => c.type === "data").slice(0, 8);
        
        let citationsHTML = '';
        
        knowledgeCitations.forEach(c => {
          citationsHTML += `
            <div style="background-color: #FAF5EE; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #C67B5C;">
              <strong style="color: #2D2A26; font-size: 13px;">🧠 Foundry IQ Grounding Template</strong><br>
              <small style="color: #5C5750; display: block; margin-top: 4px;">Arc matched: <strong>${data.arc}</strong></small>
              <small style="color: #9C9689; display: block; margin-top: 2px;">Source: ${c.source} / doc: ${c.document}</small>
            </div>
          `;
        });
        
        dataCitations.forEach(c => {
          const xLabel = data.x_labels && data.x_labels[c.index] ? data.x_labels[c.index] : `Index ${c.index}`;
          citationsHTML += `
            <div style="background-color: #FAF5EE; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #8FAE7E;">
              <strong style="color: #2D2A26; font-size: 13px;">📊 Fact Citation: ${xLabel}</strong><br>
              <small style="color: #5C5750; display: block; margin-top: 4px;">Factual Value: <strong>${c.value.toLocaleString(undefined, {maximumFractionDigits: 3})}</strong></small>
            </div>
          `;
        });
        
        citationsList.innerHTML = citationsHTML;
      }

      // Render timeline chart
      renderTimeline("timeline", data);
    });

  } catch (error) {
    storyText.textContent = `❌ Error: ${error.message}`;
    citationsList.innerHTML = `<p style="color: #E07B5C;">${error.message}</p>`;
    
    // Hide progress bar on error
    if (progressContainer) progressContainer.style.display = "none";
  }
}

analyzeButton.addEventListener("click", () => {
  const file = csvUpload.files[0];
  if (!file) {
    storyText.textContent = "📁 Please choose or drag a CSV file first.";
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
      uploadLabel.style.color = "var(--accent-sage)";
    }
    const response = await fetch(`http://localhost:8000/data/${filename}`);
    const text = await response.text();
    const blob = new Blob([text], { type: "text/csv" });
    analyzeFile(new File([blob], filename, { type: "text/csv" }));
  } catch (error) {
    storyText.textContent = `❌ Failed to load sample: ${error.message}`;
  }
}
