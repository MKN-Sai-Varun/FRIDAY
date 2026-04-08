import sounddevice as sd
import numpy as np
import webrtcvad
import wave, io, tempfile, asyncio, os, requests, json, threading
import pygame
from faster_whisper import WhisperModel
from openwakeword.model import Model as WakeWordModel
from datetime import datetime

# ── Config ────────────────────────────────────────────────────
SAMPLE_RATE        = 16000
FRAME_MS           = 80
SILENCE_LIMIT      = 1.5
VAD_AGGRESSIVENESS = 2
OLLAMA_MODEL       = "llama3.2"
VOICE              = "en-US-GuyNeural"
MEMORY_FILE        = "friday_memory.json"
WAKE_WORD_SCORE    = 0.5

SHUTDOWN_PHRASES   = ["goodbye friday", "go offline", "shut down", "shutdown", "goodbye"]

FRIDAY_PERSONA = """You are FRIDAY, an advanced AI assistant inspired by the AI from Iron Man.
You are efficient, sharp, and slightly witty. You address the user as 'boss'.
You have a memory of past conversations and use it naturally when relevant.
Keep ALL responses concise and spoken-friendly — no markdown, no bullet points, no lists.
Just plain, natural sentences as if speaking aloud. Max 3 sentences per reply unless asked for more."""

# ── State ─────────────────────────────────────────────────────
interrupted        = threading.Event()   # set when wake word fires mid-speech
pygame_lock        = threading.Lock()

# ── Memory ────────────────────────────────────────────────────
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_memory(conversation):
    with open(MEMORY_FILE, "w") as f:
        json.dump(conversation[-40:], f, indent=2)

def build_system_message():
    now = datetime.now().strftime("%A, %B %d %Y, %I:%M %p")
    return f"{FRIDAY_PERSONA}\n\nCurrent date and time: {now}"

# ── Load models ───────────────────────────────────────────────
print("[ FRIDAY ] Loading Whisper...")
whisper = WhisperModel("small", device="cuda", compute_type="int8")

print("[ FRIDAY ] Loading wake word detector...")
wakeword = WakeWordModel(wakeword_models=["hey_jarvis"], inference_framework="onnx")

print("[ FRIDAY ] Loading memory...")
conversation_history = load_memory()
if not conversation_history:
    conversation_history.append({"role": "system", "content": build_system_message()})
else:
    conversation_history[0] = {"role": "system", "content": build_system_message()}

print("[ FRIDAY ] All systems online.\n")

# ── Speak (interruptible) ─────────────────────────────────────
async def _speak_async(text):
    import edge_tts
    communicate = edge_tts.Communicate(text, VOICE)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    await communicate.save(tmp_path)

    with pygame_lock:
        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if interrupted.is_set():
                pygame.mixer.music.stop()
                break
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()

    try:
        os.unlink(tmp_path)
    except Exception:
        pass

def speak(text):
    print(f"FRIDAY: {text}")
    interrupted.clear()
    asyncio.run(_speak_async(text))

# ── Background wake word listener (for interrupts) ────────────
def _interrupt_listener():
    """Runs in a background thread while FRIDAY is speaking."""
    frame_samples = int(SAMPLE_RATE * FRAME_MS / 1000)
    with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1,
                           dtype='int16', blocksize=frame_samples) as stream:
        while not interrupted.is_set():
            data, _ = stream.read(frame_samples)
            audio_np = np.frombuffer(bytes(data), dtype=np.int16).astype(np.float32) / 32768.0
            scores = wakeword.predict(audio_np)
            for score in scores.values():
                if score > WAKE_WORD_SCORE:
                    interrupted.set()
                    return

def speak_interruptible(text):
    """Speak while listening for a wake word interrupt in the background."""
    interrupted.clear()
    listener = threading.Thread(target=_interrupt_listener, daemon=True)
    listener.start()
    speak(text)
    listener.join(timeout=0)  # don't block, it's a daemon

# ── Wake word listener (foreground) ──────────────────────────
def wait_for_wake_word():
    frame_samples = int(SAMPLE_RATE * FRAME_MS / 1000)
    print("Listening for 'Hey Jarvis'...", end="\r")
    with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1,
                           dtype='int16', blocksize=frame_samples) as stream:
        while True:
            data, _ = stream.read(frame_samples)
            audio_np = np.frombuffer(bytes(data), dtype=np.int16).astype(np.float32) / 32768.0
            scores = wakeword.predict(audio_np)
            for score in scores.values():
                if score > WAKE_WORD_SCORE:
                    print("\n")
                    wakeword.reset()
                    return

# ── Record speech ─────────────────────────────────────────────
def record_until_silence():
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    vad_frame_samples = int(SAMPLE_RATE * 30 / 1000)
    silence_frames = int(SILENCE_LIMIT * 1000 / 30)
    frames, silent_count, speaking = [], 0, False

    with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=1,
                           dtype='int16', blocksize=vad_frame_samples) as stream:
        print("Listening...", end=" ", flush=True)
        while True:
            data, _ = stream.read(vad_frame_samples)
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

    return b"".join(frames)

# ── Transcribe ────────────────────────────────────────────────
def transcribe(raw_audio):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw_audio)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(buf.getvalue())
        tmp_path = f.name
    try:
        segments, _ = whisper.transcribe(tmp_path, language="en")
        return " ".join(s.text for s in segments).strip()
    finally:
        os.unlink(tmp_path)

# ── Shutdown check ────────────────────────────────────────────
def is_shutdown_command(text):
    lowered = text.lower()
    return any(phrase in lowered for phrase in SHUTDOWN_PHRASES)

# ── Ask FRIDAY ────────────────────────────────────────────────
def ask_friday(user_text):
    conversation_history.append({"role": "user", "content": user_text})
    try:
        response = requests.post("http://localhost:11434/api/chat", json={
            "model": OLLAMA_MODEL,
            "messages": conversation_history,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 150}
        }, timeout=30)
        reply = response.json()["message"]["content"].strip()
    except Exception as e:
        reply = f"Having trouble reaching my brain, boss. {str(e)}"

    conversation_history.append({"role": "assistant", "content": reply})
    save_memory(conversation_history)
    return reply

# ── Main loop ─────────────────────────────────────────────────
if __name__ == "__main__":
    speak("FRIDAY online. Say Hey Jarvis whenever you need me, boss.")
    while True:
        try:
            wait_for_wake_word()

            # If interrupted mid-speech, skip "Yes boss?" and go straight to listening
            if not interrupted.is_set():
                speak("Yes boss?")

            raw = record_until_silence()
            text = transcribe(raw)

            if not text:
                speak_interruptible("I didn't catch that, boss.")
                continue

            print(f"You: {text}\n")

            if is_shutdown_command(text):
                speak("Going offline. Goodbye, boss.")
                save_memory(conversation_history)
                break

            reply = ask_friday(text)
            speak_interruptible(reply)

        except KeyboardInterrupt:
            speak("Going offline. Goodbye, boss.")
            save_memory(conversation_history)
            break
        except Exception as e:
            print(f"[ ERROR ] {e}")
            continue
