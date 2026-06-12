const narrationState = {
  utterance: null,
};

function startNarration(text, onProgress) {
  if (!window.speechSynthesis) {
    console.warn("SpeechSynthesis not supported.");
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.onboundary = () => {
    if (typeof onProgress === "function") {
      onProgress();
    }
  };
  window.speechSynthesis.speak(utterance);
  narrationState.utterance = utterance;
}

function pauseNarration() {
  window.speechSynthesis?.pause();
}

function resumeNarration() {
  window.speechSynthesis?.resume();
}

function stopNarration() {
  window.speechSynthesis?.cancel();
}
