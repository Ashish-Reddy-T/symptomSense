"""Quick local test for Piper CLI, Piper model path, and faster-whisper import.

Run with venv activated. The script inserts `backend` on PYTHONPATH so imports resolve
when executed from the repo root:

    source venv/bin/activate
    python scripts/test_tts_stt.py

It prints diagnostic info and attempts to load the Whisper model (may download weights).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# Make sure backend package is importable when running from repo root
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

try:
    from app.core.settings import Settings
except Exception as e:
    print("Failed to import Settings from backend.app.core.settings:", e)
    raise 

s = Settings()
print("Loaded settings from .env (via pydantic-settings):")
print("  PIPER_MODEL_PATH:", s.PIPER_MODEL_PATH)
print("  WHISPER_MODEL:", s.WHISPER_MODEL)
print("  TORCH_DEVICE:", s.TORCH_DEVICE)
print()

piper_bin = shutil.which("piper")
print("piper binary on PATH:", piper_bin)

piper_path = Path(s.PIPER_MODEL_PATH) if s.PIPER_MODEL_PATH else None
print("piper model path exists:", piper_path.exists() if piper_path else False)

# If piper exists, run --help to validate invocation
if piper_bin:
    try:
        proc = subprocess.run([piper_bin, "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True, timeout=10)
        print('\n-- piper --help (truncated) --')
        print(proc.stdout[:800])
    except Exception as exc:
        print("Calling piper failed:", exc)
else:
    print("piper not found on PATH (activate venv or install piper-tts)")

# Test faster-whisper import and instantiate model (this may download weights)
print("\nTesting faster-whisper import and model instantiation...")
try:
    from faster_whisper import WhisperModel

    print("faster-whisper import OK")
    try:
        print("Instantiating WhisperModel (this may download weights; be patient)...")
        model = WhisperModel(s.WHISPER_MODEL, device=s.TORCH_DEVICE)
        print("WhisperModel instantiated:", type(model))
        # Close / cleanup
        try:
            model.cpu()
        except Exception:
            pass
        try:
            del model
        except Exception:
            pass
    except Exception as inst_e:
        print("WhisperModel instantiation failed:", inst_e)
except Exception as imp_e:
    print("faster-whisper import failed:", imp_e)

print("\nDone.")
