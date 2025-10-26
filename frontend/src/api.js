const API_BASE = window.API_BASE || 'http://localhost:8000/api';

async function handleResponse(response) {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

export async function processInput(payload) {
  const response = await fetch(`${API_BASE}/process_input`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

export async function transcribeAudio(blob, language) {
  const formData = new FormData();
  formData.append('audio', blob, 'input.webm');
  if (language) formData.append('language', language);
  const response = await fetch(`${API_BASE}/stt`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(response);
}

export async function synthesizeSpeech(text) {
  const response = await fetch(`${API_BASE}/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  return handleResponse(response);
}
