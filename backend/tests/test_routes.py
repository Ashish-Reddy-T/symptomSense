from __future__ import annotations

import base64

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_process_input_requires_payload(client: TestClient) -> None:
    response = client.post("/api/process_input", json={})
    assert response.status_code == 400


def test_process_input_success(client: TestClient) -> None:
    response = client.post("/api/process_input", json={"text_query": "What is AS03?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("Echo")
    assert body["citations"]
    assert isinstance(body["follow_up"], list)


def test_stt_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/stt",
        files={"audio": ("sample.wav", b"fake", "audio/wav")},
        data={"language": "en"},
    )
    assert response.status_code == 200
    assert response.json()["text"] == "transcript"


def test_tts_endpoint(client: TestClient) -> None:
    response = client.post("/api/tts", json={"text": "hello"})
    assert response.status_code == 200
    payload = response.json()
    assert base64.b64decode(payload["audio_base64"]) == b"hello"
