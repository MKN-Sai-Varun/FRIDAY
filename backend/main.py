import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
import tempfile
import os

from backend.llm import ask_friday_stream
from backend.rag import ingest_pdf

app = FastAPI(title="Friday VA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/status")
def status():
    return {"status": "FRIDAY is online"}

@app.post("/transcribe")
async def api_transcribe(audio: UploadFile = File(...)):
    raw_audio = await audio.read()
    
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(raw_audio)
        tmp_path = f.name
        
    try:
        from backend.stt import whisper_model
        segments, _ = whisper_model.transcribe(tmp_path, language="en")
        text = " ".join(s.text for s in segments).strip()
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}
    finally:
        os.unlink(tmp_path)

@app.post("/chat")
async def api_chat(text: str = Form(...), session_id: str = Form(...)):
    return StreamingResponse(ask_friday_stream(text, session_id), media_type="text/event-stream")

@app.post("/speak")
async def api_speak(text: str = Form(...)):
    import edge_tts
    from backend.config import VOICE
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(tmp_path)
    
    from fastapi.background import BackgroundTasks
    background_tasks = BackgroundTasks()
    background_tasks.add_task(os.unlink, tmp_path)
    
    return FileResponse(tmp_path, background=background_tasks, media_type="audio/mpeg")

@app.post("/ingest")
async def api_ingest(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDFs are supported."}
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(await file.read())
        tmp_path = f.name
        
    success, msg = ingest_pdf(tmp_path)
    os.unlink(tmp_path)
    
    if success:
        return {"message": msg}
    return {"error": msg}

@app.get("/documents")
def get_docs():
    from backend.rag import get_all_documents
    return {"documents": get_all_documents()}

@app.delete("/documents/{filename:path}")
def del_doc(filename: str):
    from backend.rag import delete_document
    success, msg = delete_document(filename)
    if success:
        return {"message": msg}
    return {"error": msg}
