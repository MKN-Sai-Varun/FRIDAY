import sounddevice as sd
import numpy as np
import webrtcvad
import wave, io, tempfile, asyncio, os, requests, subprocess
from faster_whisper import WhisperModel

# ── Config ────────────────────────────────────────────────────
SAMPLE_RATE     = 16000
FRAME_MS        = 30          # VAD frame size in ms
SILENCE_LIMIT   = 0.6        # seconds of silence to stop recording
VAD_AGGRESSIVENESS = 2        # 0–3, higher = more aggressive
OLLAMA_MODEL    = "mistral"
VOICE           = "en-US-JennyNeural"   # Edge TTS voice
FRIDAY_PERSONA  = """You are FRIDAY, an advanced AI assistant inspired by the system from Iron Man. You are highly intelligent, efficient, and composed under all circumstances. You speak in a calm, confident, and slightly formal tone. You always address the user as 'boss'. Your responses are concise, clear, and optimized for spoken delivery, as if interacting in real time. You prioritize usefulness, accuracy, and anticipation of the user’s needs, occasionally adding subtle wit when appropriate. Avoid unnecessary verbosity, formatting, or explanations unless explicitly requested. Always behave like a reliable, high-performance AI companion."""

# ── Load Whisper ──────────────────────────────────────────────
print("Loading Whisper model...")
whisper = WhisperModel("base", device="cuda", compute_type="int8")
print("FRIDAY online. Say something, boss.")

conversation = [{"role": "system", "content": FRIDAY_PERSONA}]

# ── Audio helpers ─────────────────────────────────────────────
def record_until_silence():
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    frame_samples = int(SAMPLE_RATE * FRAME_MS / 1000)
    silence_frames = int(SILENCE_LIMIT * 1000 / FRAME_MS)

    frames, silent_count, speaking = [], 0, False

    with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1,
                           dtype='int16', blocksize=frame_samples) as stream:
        print("Listening...", end=" ", flush=True)
        while True:
            data, _ = stream.read(frame_samples)
            chunk = bytes(data)
            is_speech = vad.is_speech(chunk, SAMPLE_RATE)

            if is_speech:
                frames.append(chunk)
                silent_count = 0
                speaking = True
            elif speaking:
                frames.append(chunk)
                silent_count += 1
                if silent_count > silence_frames:
                    break

    print("Got it.")
    return b"".join(frames)

def audio_to_wav_bytes(raw_audio):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw_audio)
    return buf.getvalue()

# ── Transcribe ────────────────────────────────────────────────
def transcribe(raw_audio):
    wav_bytes = audio_to_wav_bytes(raw_audio)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp_path = f.name
    segments, _ = whisper.transcribe(tmp_path, language="en")
    os.unlink(tmp_path)
    return " ".join(s.text for s in segments).strip()

# ── Ask Ollama ────────────────────────────────────────────────
def ask_friday(user_text):
    conversation.append({"role": "user", "content": user_text})
    response = requests.post("http://localhost:11434/api/chat", json={
        "model": OLLAMA_MODEL,
        "messages": conversation,
        "stream": False
    })
    reply = response.json()["message"]["content"]
    conversation.append({"role": "assistant", "content": reply})
    return reply

# ── Speak ─────────────────────────────────────────────────────
async def _speak_async(text):
    import edge_tts, pygame
    communicate = edge_tts.Communicate(text, VOICE)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    await communicate.save(tmp_path)

    pygame.mixer.init()
    pygame.mixer.music.load(tmp_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()
    os.unlink(tmp_path)

def speak(text):
    asyncio.run(_speak_async(text))

# ── Main loop ─────────────────────────────────────────────────
if __name__ == "__main__":
    speak("FRIDAY online. How can I help you, boss?")
    while True:
        try:
            raw = record_until_silence()
            text = transcribe(raw)
            if not text:
                continue
            print(f"You: {text}")
            reply = ask_friday(text)
            print(f"FRIDAY: {reply}\n")
            speak(reply)
        except KeyboardInterrupt:
            print("\nShutting down.")
            speak("Shutting Down, See ya later boss!")
            break