import sounddevice as sd
import webrtcvad
import io
import wave
from core.config import SAMPLE_RATE, FRAME_MS, SILENCE_LIMIT, VAD_AGGRESSIVENESS

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
