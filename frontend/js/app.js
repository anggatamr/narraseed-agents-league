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
const sampleGpa = document.getElementById("sample-gpa");
const sampleStartup = document.getElementById("sample-startup");
const sampleFitness = document.getElementById("sample-fitness");

// Add voice control UI
function addVoiceControls() {
  const storyPanel = document.getElementById("story-panel");
  if (storyPanel.querySelector(".voice-controls")) {
    return;
  }

  const voiceControlsHTML = `
    <div class="voice-controls" style="display: flex; gap: 8px; margin-bottom: 16px; align-items: center; flex-wrap: wrap;">
      <button id="play-narration" class="voice-btn" style="padding: 8px 16px; background-color: #8FAE7E; color: white; border: none; border-radius: 20px; cursor: pointer; font-weight: 600; font-size: 12px;">
        🔊 Narrate
      </button>
      <button id="pause-narration" class="voice-btn" style="padding: 8px 16px; background-color: #D4A574; color: white; border: none; border-radius: 20px; cursor: pointer; font-weight: 600; font-size: 12px; display: none;">
        ⏸ Pause
      </button>
      <button id="stop-narration" class="voice-btn" style="padding: 8px 16px; background-color: #E07B5C; color: white; border: none; border-radius: 20px; cursor: pointer; font-weight: 600; font-size: 12px;">
        ⏹ Stop
      </button>
    </div>
  `;

  storyPanel.insertAdjacentHTML("afterbegin", voiceControlsHTML);

  // Attach event listeners
  document.getElementById("play-narration").addEventListener("click", () => {
    if (storyText.textContent && storyText.textContent !== "Upload a CSV or choose a sample to generate a narrative.") {
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

  storyText.textContent = "🔄 Analyzing your data...";
  citationsList.innerHTML = "";

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

    // Update story with better formatting
    storyText.innerHTML = `
      <div style="line-height: 1.8; color: #5C5750; font-size: 15px;">
        ${data.story.split('\n').filter(l => l.trim()).map(line => `<p style="margin-bottom: 12px;">${line.trim()}</p>`).join('')}
      </div>
    `;

    // Add voice controls
    addVoiceControls();

    // Update citations with better UI
    if (data.citations && data.citations.length > 0) {
      const knowledgeCitations = data.citations.filter((c) => c.type === "knowledge");
      const dataCitations = data.citations.filter((c) => c.type === "data").slice(0, 5);
      
      let citationsHTML = '';
      
      knowledgeCitations.forEach(c => {
        citationsHTML += `
          <div style="background-color: #FAF5EE; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #C67B5C;">
            <strong style="color: #2D2A26;">📚 Knowledge Base</strong><br>
            <small style="color: #9C9689;">Source: ${c.source}</small>
          </div>
        `;
      });
      
      dataCitations.forEach(c => {
        citationsHTML += `
          <div style="background-color: #FAF5EE; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #8FAE7E;">
            <strong style="color: #2D2A26;">📊 Data Point ${c.index}</strong><br>
            <small style="color: #9C9689;">Value: ${c.value.toFixed(3)}</small>
          </div>
        `;
      });
      
      citationsList.innerHTML = citationsHTML;
    }

    renderTimeline("timeline", data);
  } catch (error) {
    storyText.textContent = `❌ Error: ${error.message}`;
    citationsList.innerHTML = `<p style="color: #E07B5C;">${error.message}</p>`;
  }
}

function renderTimeline(containerId, data) {
  const container = document.getElementById(containerId);
  container.innerHTML = "<p>Timeline rendered.</p>";
}

analyzeButton.addEventListener("click", () => {
  const file = csvUpload.files[0];
  if (!file) {
    storyText.textContent = "📁 Please choose a CSV file first.";
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
    const response = await fetch(`http://localhost:8000/data/${filename}`);
    const text = await response.text();
    const blob = new Blob([text], { type: "text/csv" });
    analyzeFile(new File([blob], filename, { type: "text/csv" }));
  } catch (error) {
    storyText.textContent = `❌ Failed to load sample: ${error.message}`;
  }
}
