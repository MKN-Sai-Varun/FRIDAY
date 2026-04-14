import os
import tempfile
from faster_whisper import WhisperModel
from backend.audio import audio_to_wav_bytes

print("Loading Whisper model...")
whisper_model = WhisperModel("base", device="cuda", compute_type="int8")

def transcribe(raw_audio):
    wav_bytes = audio_to_wav_bytes(raw_audio)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp_path = f.name
    try:
        segments, _ = whisper_model.transcribe(tmp_path, language="en")
        return " ".join(s.text for s in segments).strip()
    finally:
        os.unlink(tmp_path)
