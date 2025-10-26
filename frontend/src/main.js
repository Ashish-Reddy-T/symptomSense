import { processInput, transcribeAudio, synthesizeSpeech } from './api.js';
import { startRecording, stopRecording } from './recorder.js';

const form = document.getElementById('query-form');
const textQuery = document.getElementById('text_query');
const imageInput = document.getElementById('image_file');
const answerEl = document.getElementById('answer');
const citationsEl = document.getElementById('citations');
const warningsEl = document.getElementById('warnings');
const followUpEl = document.getElementById('follow-up');
const imageAnalysisEl = document.getElementById('image-analysis');
const transcriptEl = document.getElementById('transcript');
const recordBtn = document.getElementById('record-btn');

let isRecording = false;
let lastAnswer = '';

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  toggleBusy(true);
  try {
    const payload = await buildPayload();
    const result = await processInput(payload);
    renderAnswer(result);
  } catch (error) {
    renderError(error);
  } finally {
    toggleBusy(false);
  }
});

recordBtn.addEventListener('click', async () => {
  if (!isRecording) {
    try {
      await startRecording();
      recordBtn.textContent = '⏹ Stop';
      isRecording = true;
    } catch (error) {
      renderError(error);
    }
  } else {
    try {
      const blob = await stopRecording();
      recordBtn.textContent = '🎙 Record';
      isRecording = false;
      const file = new File([blob], 'input.webm', { type: 'audio/webm' });
      const transcription = await transcribeAudio(file);
      transcriptEl.textContent = `Transcript: ${transcription.text}`;
      textQuery.value = transcription.text;
    } catch (error) {
      renderError(error);
    }
  }
});

async function buildPayload() {
  const payload = { text_query: textQuery.value.trim() || null, image_base64: null };
  if (imageInput.files.length > 0) {
    const file = imageInput.files[0];
    payload.image_base64 = await fileToDataURL(file);
  }
  return payload;
}

async function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function renderAnswer(result) {
  lastAnswer = result.answer || '';
  answerEl.innerHTML = `<div class="answer-text">${lastAnswer}</div>`;
  
  // Show confidence profile if available
  if (result.confidence_profile) {
    renderConfidence(result.confidence_profile, result.hitl_flagged);
  }
  
  renderCitations(result.citations || []);
  renderWebSources(result.web_sources || []);
  renderWarnings(result.warnings || []);
  renderFollowUp(result.follow_up || []);
  renderImageAnalysis(result.image_analysis || null);
  renderAudioButton();
}

function renderCitations(citations) {
  if (!citations.length) {
    citationsEl.textContent = '';
    return;
  }
  citationsEl.innerHTML = '<h3>Citations</h3>' +
    '<ul>' + citations.map((citation) => `<li>${citation.label}: ${citation.source || 'unknown'}</li>`).join('') + '</ul>';
}

function renderWarnings(warnings) {
  if (!warnings.length) {
    warningsEl.textContent = '';
    return;
  }
  warningsEl.innerHTML = '<h3>Warnings</h3>' +
    '<ul>' + warnings.map((warning) => `<li>${warning}</li>`).join('') + '</ul>';
}

function renderFollowUp(items) {
  if (!items.length) {
    followUpEl.textContent = '';
    return;
  }
  followUpEl.innerHTML = '<h3>Follow-up</h3>' +
    '<ul>' + items.map((item) => `<li>${item}</li>`).join('') + '</ul>';
}

function renderImageAnalysis(analysis) {
  if (!analysis || !analysis.label) {
    imageAnalysisEl.textContent = '';
    return;
  }
  const confidence = analysis.confidence ? ` (${(analysis.confidence * 100).toFixed(1)}%)` : '';
  imageAnalysisEl.innerHTML = `<h3>Image Analysis</h3><p>${analysis.label}${confidence}</p>`;
}

function renderConfidence(profile, hitlFlagged) {
  const level = profile.confidence_level || 'unknown';
  const overall = (profile.overall_confidence * 100).toFixed(0);
  const levelClass = level === 'high' ? 'conf-high' : level === 'medium' ? 'conf-medium' : 'conf-low';
  
  let html = `<div class="confidence-box ${levelClass}">
    <strong>Confidence:</strong> ${overall}% (${level})`;
  
  if (hitlFlagged) {
    html += `<br><span class="hitl-flag">⚠️ Flagged for expert review</span>`;
  }
  
  html += '</div>';
  
  // Insert after answer text
  const answerDiv = answerEl.querySelector('.answer-text');
  if (answerDiv) {
    const confDiv = document.createElement('div');
    confDiv.innerHTML = html;
    answerDiv.appendChild(confDiv);
  }
}

function renderWebSources(webSources) {
  if (!webSources || !webSources.length) return;
  
  let html = '<h3>🌐 Web Sources</h3><ul class="web-sources">';
  webSources.forEach((source, i) => {
    html += `<li>
      <strong>[web${i+1}]</strong> <a href="${source.url}" target="_blank">${source.title}</a>
      <br><small>${source.snippet}</small>
    </li>`;
  });
  html += '</ul>';
  
  // Add to citations section
  const webDiv = document.createElement('div');
  webDiv.innerHTML = html;
  citationsEl.appendChild(webDiv);
}

function renderError(error) {
  warningsEl.innerHTML = `<strong>Error:</strong> ${error.message || String(error)}`;
}

function toggleBusy(isBusy) {
  form.querySelectorAll('input, textarea, button').forEach((el) => {
    el.disabled = isBusy && el !== recordBtn;
  });
  if (isBusy) {
    answerEl.textContent = 'Processing...';
    citationsEl.textContent = '';
    warningsEl.textContent = '';
    followUpEl.textContent = '';
    imageAnalysisEl.textContent = '';
  }
}

function renderAudioButton() {
  let button = document.getElementById('tts-btn');
  if (!button) {
    button = document.createElement('button');
    button.id = 'tts-btn';
    button.type = 'button';
    button.textContent = '🔊 Play answer';
    document.getElementById('answer-panel').appendChild(button);
    button.addEventListener('click', async () => {
      try {
        const response = await synthesizeSpeech(lastAnswer);
        const audio = new Audio(`data:audio/wav;base64,${response.audio_base64}`);
        audio.play();
      } catch (error) {
        renderError(error);
      }
    });
  }
}
