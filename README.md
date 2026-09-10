<div align="center">

# 🤖 F.R.I.D.A.Y. - Voice Assistant

**A fully local, Iron Man-inspired AI voice assistant with a sleek web dashboard.**

*Powered by Groq · faster-whisper · Edge TTS · ChromaDB · Next.js*

---

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=flat-square)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## 📌 What is FRIDAY?

FRIDAY is a modular, **API-first voice assistant** that runs directly in your browser. Inspired by Tony Stark's AI companion, it combines blazing-fast local speech recognition, cloud-accelerated LLM inference, and natural-sounding text-to-speech into a seamless, real-time conversational experience.

Unlike traditional cloud-locked assistants, FRIDAY is designed to be **private by default** - your voice is transcribed locally, and your documents never leave your machine.

### ✨ Key Highlights

| Feature | Details |
|---|---|
| 🎙️ **Voice Input** | Browser-based recording via HTML5 MediaRecorder |
| 🧠 **LLM Backend** | Groq API (Llama 3.3 70B) for ultra-low-latency responses |
| 🔊 **Text-to-Speech** | Microsoft Edge TTS with the `en-US-JennyNeural` voice |
| 📄 **Document Memory** | Drag-and-drop PDF ingestion with ChromaDB RAG |
| 📡 **Streaming UI** | Token-by-token SSE streaming - watch FRIDAY think in real-time |
| 🔒 **Local STT** | `faster-whisper` runs on your machine - your audio stays private |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────┐
│               Browser (localhost:3000)           │
│                                                  │
│  ┌──────────────────┐   ┌─────────────────────┐ │
│  │  Chat Interface  │   │   PDF Dropzone      │ │
│  │  (SSE Stream)    │   │   (RAG Ingestion)   │ │
│  └────────┬─────────┘   └──────────┬──────────┘ │
└───────────┼──────────────────────────┼───────────┘
            │  HTTP / SSE              │ Upload
            ▼                          ▼
┌─────────────────────────────────────────────────┐
│           FastAPI Backend (localhost:8000)       │
│                                                  │
│   Voice Blob ──► faster-whisper ──► Transcript  │
│                                         │        │
│   PDF ──► Embeddings ──► ChromaDB       │        │
│                              │          ▼        │
│                          RAG Context ──► Groq    │
│                                         │        │
│                              Edge TTS ◄─┘        │
│                                  │               │
│                           Audio Stream           │
└─────────────────────────────────────────────────┘
```

---

## 🔧 Prerequisites

Before getting started, make sure you have the following installed:

- **Python 3.8+** - [Download](https://python.org/downloads)
- **Node.js & npm** - [Download](https://nodejs.org)
- **A Groq API Key** - [Get one free](https://console.groq.com) (takes ~30 seconds)
- *(Optional)* **CUDA-compatible NVIDIA GPU** - for faster local STT with `faster-whisper`

---

## 🚀 Installation

### Step 1 - Clone the Repository

```bash
git clone https://github.com/your-username/friday-va.git
cd friday-va
```

### Step 2 - Install Python Dependencies

```bash
pip install -r requirements.txt
```

> 💡 If you have a CUDA GPU, also install the GPU build of `faster-whisper` for significantly faster transcription:
> ```bash
> pip install faster-whisper[cuda]
> ```

### Step 3 - Install Node.js Dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 4 - Configure Your Environment

Create a `.env` file in the **root of the project** and populate it:

```env
# ─────────────────────────────────────────────
#  REQUIRED
# ─────────────────────────────────────────────
GROQ_API_KEY="your_groq_api_key_here"

# ─────────────────────────────────────────────
#  MODEL SETTINGS
# ─────────────────────────────────────────────
OLLAMA_MODEL="llama-3.3-70b-versatile"   # Groq model to use

# ─────────────────────────────────────────────
#  AUDIO SETTINGS
# ─────────────────────────────────────────────
SAMPLE_RATE=16000
FRAME_MS=30

# ─────────────────────────────────────────────
#  TEXT-TO-SPEECH
# ─────────────────────────────────────────────
VOICE="en-US-JennyNeural"   # Edge TTS voice name

# ─────────────────────────────────────────────
#  PERSONA (Optional - uncomment to customize)
# ─────────────────────────────────────────────
# FRIDAY_PERSONA="You are FRIDAY, an advanced AI assistant..."
```

> 🔎 Browse all available Edge TTS voices by running:
> ```bash
> python -c "import edge_tts, asyncio; asyncio.run(edge_tts.list_voices())" | grep Name
> ```

---

## ▶️ Running FRIDAY

### Option A - One-Click Launch (Windows)

From the project root, simply run:

```bat
start.bat
```

This script automatically starts both the FastAPI backend and the Next.js frontend in parallel. Once ready, open your browser and navigate to:

```
http://localhost:3000
```

---

### Option B - Manual Launch (All Platforms)

Open **two separate terminals** from the project root.

**Terminal 1 - Start the Backend:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start the Frontend:**
```bash
cd frontend
npm run dev
```

Then visit `http://localhost:3000`.

---

## 🗣️ Using FRIDAY

Once the dashboard is open, here's what you can do:

### 💬 Voice Chat

1. Click and **hold** the `Hold to Speak` button.
2. Ask your question clearly.
3. **Release** the button to send.
4. Watch FRIDAY's response stream into the chat - and listen as she speaks it back.

### 📄 Add to Memory (RAG)

1. On the left panel, find the **PDF dropzone**.
2. **Drag and drop** any PDF file - a research paper, a manual, your notes - onto it.
3. FRIDAY will chunk, embed, and store it in her local **ChromaDB** vector database.
4. She will now automatically search this knowledge base before answering relevant questions.

> 💡 **Tip:** You can upload multiple documents. FRIDAY will retrieve context from all of them.

---

## 📁 Project Structure

```
friday-va/
├── backend/
│   ├── main.py             # FastAPI app - routes, SSE streaming, orchestration
│   ├── stt.py              # faster-whisper transcription logic
│   ├── llm.py              # Groq API client and prompt construction
│   ├── tts.py              # Edge TTS synthesis
│   └── rag.py              # ChromaDB ingestion and retrieval
│
├── frontend/
│   ├── pages/
│   │   └── index.js        # Main dashboard page
│   ├── components/         # Reusable UI components
│   └── styles/             # Vanilla CSS (dark glassmorphic theme)
│
├── .env                    # Your local config (never commit this)
├── requirements.txt        # Python dependencies
└── start.bat               # Windows one-click launcher
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `GROQ_API_KEY` error on startup | Make sure your `.env` file is in the project root and the key is valid |
| Microphone not working in browser | Allow microphone permissions when prompted; use Chrome or Edge for best compatibility |
| `faster-whisper` is slow | Run on GPU (CUDA) or switch to the `tiny` or `base` Whisper model in `backend/stt.py` |
| Port 8000 already in use | Run `netstat -ano \| findstr :8000` (Windows) and terminate the conflicting process |
| ChromaDB errors on PDF upload | Ensure the PDF is text-based (not a scanned image). OCR support is not yet included |

---

## 🗺️ Roadmap

- [ ] Wake word detection (e.g., `"Hey FRIDAY"`) using `openWakeWord`
- [ ] Multi-session conversation history
- [ ] OCR support for scanned PDFs
- [ ] Plugin system for custom tools (web search, calendar, etc.)
- [ ] Docker Compose deployment

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue to report a bug or suggest a feature, then fork the repo and submit a pull request.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
Built with ❤️ and way too much caffeine.
</div>
