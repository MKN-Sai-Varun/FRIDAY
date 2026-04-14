# Friday VA - Virtual Assistant (Ongoing)

Friday VA is an advanced AI virtual assistant inspired by Iron Man's FRIDAY system. It listens to your voice commands, processes the transcribed audio using Groq's high-speed completion API (Llama 3.3), and speaks the responses back to you in real-time.

## Features

- **Voice Activity Detection (VAD)**: Automatically detects when you stop speaking to capture audio without requiring push-to-talk.
- **Speech-to-Text (Local)**: Uses `faster_whisper` locally for quick and private transcription of voice inputs.
- **High-Speed AI Inference**: Connects to the Groq API (running `llama-3.3-70b-versatile` by default) for lightning-fast and intelligent responses.
- **Text-to-Speech (TTS)**: Utilizes Microsoft Edge TTS seamlessly integrated with `pygame` to read the assistant's responses aloud.
- **Customizable Persona**: Easy to edit the system prompts via `.env` to create exactly the persona you want (defaults to FRIDAY).

## Prerequisites
- Python 3.8+
- An active Groq API Key
- If using an NVIDIA GPU for faster Whisper transcription locally, ensure you have appropriate CUDA libraries installed.

## Installation

1. **Clone or Download the Project.**

2. **Install the dependencies:**
   You can install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: You might need additional system libraries for `PyAudio` / `sounddevice` depending on your OS).*

3. **Environment Setup:**
   Create a `.env` file in the root of the project (if one doesn't exist) and customize your configuration. An example:
   ```env
   SAMPLE_RATE=16000
   FRAME_MS=30
   SILENCE_LIMIT=0.6
   VAD_AGGRESSIVENESS=2
   OLLAMA_MODEL="llama-3.3-70b-versatile"
   GROQ_API_KEY="your_groq_api_key_here"
   VOICE="en-US-JennyNeural"
   ```
   *You can also uncomment or add the `FRIDAY_PERSONA` variable to change how the assistant perceives its own identity.*

## Usage

Run the main python script to start the assistant:

```bash
python main.py
```

- Wait for the **"FRIDAY online. How can I help you, boss?"** voice prompt.
- Start speaking. The assistant listens until it detects silence, transcribes your speech, and quickly replies with generated audio.
- Press `Ctrl + C` in the console to gracefully shut down the assistant.

## Configuration Details

- `SILENCE_LIMIT`: Adjusts how many seconds of silence denote the end of speech.
- `VAD_AGGRESSIVENESS`: An integer from 0 to 3. 3 is the most aggressive at filtering out non-speech noise.
- `VOICE`: Change the Edge TTS voice (e.g., `en-US-AriaNeural`, `en-US-GuyNeural`, Default: `en-US-JennyNeural`).