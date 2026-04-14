# Friday VA - Virtual Assistant

Friday VA is an advanced AI virtual assistant built with a modular, API-first architecture. It features a beautiful, glassmorphic **Next.js web dashboard** powered by a highly capable **FastAPI Python backend**. Utilizing blazing-fast local STT inference, Groq's high-speed completion API (Llama 3.3), and Edge TTS, it provides a seamless, Iron Man-style real-time voice assistant experience.

## New Features
- **Next.js Web Interface**: A sleek, dark-themed dashboard using Vanilla CSS. Speak directly into your browser using HTML5 MediaRecorder.
- **Retrieval-Augmented Generation (RAG)**: Drag and drop PDF files into the web panel to seamlessly embed them into a local `ChromaDB` vector database. FRIDAY searches this memory bank before answering your questions to provide accurate, context-aware responses.
- **FastAPI Backend**: The core processing logic operates as an independent REST API, capable of robust error-handling and easy deployment.
- **Streaming Responses**: Token-by-token Sever-Sent Event (SSE) streaming allows you to watch FRIDAY's thoughts compile in real-time in the chat UI before she begins speaking.
- **Local Speech-To-Text (STT)**: Utilizes `faster_whisper` locally for quick, private transcriptions of voice blobs sent from the browser.

---

## Prerequisites
- Python 3.8+
- Node.js & npm (for the Next.js UI)
- An active Groq API Key
- *(Optional)* Support for CUDA if you wish to run `faster-whisper` on an NVIDIA GPU locally.

## Installation

1. **Clone or Download the Project.**

2. **Install Python Dependencies (The Backend):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node Dependencies (The Frontend):**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Environment Setup:**
   Create a `.env` file in the root of the project to customize your configuration:
   ```env
   # Core AI
   GROQ_API_KEY="your_groq_api_key_here"
   OLLAMA_MODEL="llama-3.3-70b-versatile"
   
   # Audio Thresholds (If manually modifying backend/audio)
   SAMPLE_RATE=16000
   FRAME_MS=30
   
   # TTS
   VOICE="en-US-JennyNeural"
   
   # Persona
   # FRIDAY_PERSONA="You are FRIDAY..."
   ```

---

## Usage

### The Easy Way (Automated)
If you're on Windows, you can simply run the automated launch script from your root directory:
```bash
start.bat
```
This will simultaneously pop open the FastAPI Server (`localhost:8000`) and the Next.js Dev Server. Once running, go to **http://localhost:3000** in your web browser.

### The Manual Way (Two Terminals)
For complete control and raw logs, open two separate terminal instances.

**Terminal 1 (Backend Brain):**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
**Terminal 2 (Frontend GUI):**
```bash
cd frontend
npm run dev
```

### Interacting with FRIDAY
- Navigate to `http://localhost:3000`.
- **Add to Memory:** Upload a PDF using the dropzone on the left to securely embed it into her ChromaDB vector storage.
- **Voice Chat:** Click and hold the **Hold to Speak** button, ask her a question, and release to send it. She will process the request natively, stream her text response, and immediately synthesize the audio back to you!