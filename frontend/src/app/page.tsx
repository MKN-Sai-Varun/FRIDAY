"use client";

import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [status, setStatus] = useState("Online");
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const [docs, setDocs] = useState<string[]>([]);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  
  const fetchDocs = async () => {
    try {
      const res = await fetch("http://localhost:8000/documents");
      const data = await res.json();
      setDocs(data.documents || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.current.push(e.data);
      };

      mediaRecorder.current.onstop = processAudio;
      mediaRecorder.current.start();
      setStatus("Listening...");
    } catch (err) {
      console.error("Mic access denied", err);
      setStatus("Mic error");
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && mediaRecorder.current.state === "recording") {
      mediaRecorder.current.stop();
      mediaRecorder.current.stream.getTracks().forEach(t => t.stop());
    }
  };

  const processAudio = async () => {
    setStatus("Transcribing...");
    const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");

    try {
      // 1. Transcribe
      const tRes = await fetch("http://localhost:8000/transcribe", {
        method: "POST",
        body: formData
      });
      const tData = await tRes.json();
      const userText = tData.text;
      
      if (!userText) {
        setStatus("Online");
        return;
      }
      
      setMessages(p => [...p, { role: "user", content: userText }, { role: "assistant", content: "" }]);
      setStatus("Processing...");

      // 2. Chat SSE stream
      const chatForm = new FormData();
      chatForm.append("text", userText);
      
      const chatRes = await fetch("http://localhost:8000/chat", {
        method: "POST",
        body: chatForm
      });
      
      const reader = chatRes.body?.getReader();
      const decoder = new TextDecoder();
      let fullReply = "";
      
      setStatus("Speaking...");

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");
          for (let line of lines) {
            if (line.startsWith("data: ")) {
              const text = line.substring(6);
              fullReply += text;
              setMessages(p => {
                const newM = [...p];
                newM[newM.length - 1].content = fullReply;
                return newM;
              });
            }
          }
        }
      }

      // 3. Output Audio
      const speakForm = new FormData();
      speakForm.append("text", fullReply);
      const audioRes = await fetch("http://localhost:8000/speak", {
        method: "POST",
        body: speakForm
      });
      
      const audioBlobReturn = await audioRes.blob();
      const audioUrl = URL.createObjectURL(audioBlobReturn);
      const audioEl = new Audio(audioUrl);
      audioEl.play();
      
      audioEl.onended = () => {
        setStatus("Online");
      };

    } catch (e) {
      console.error(e);
      setStatus("Error");
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setStatus("Ingesting...");
    const form = new FormData();
    form.append("file", e.target.files[0]);
    
    try {
      await fetch("http://localhost:8000/ingest", { method: "POST", body: form });
      await fetchDocs();
      setStatus("Online");
    } catch {
      setStatus("Upload failed");
    }
  };

  const getStatusClass = () => {
    if (status === "Listening...") return "listening";
    if (status === "Processing..." || status === "Transcribing..." || status === "Speaking...") return "processing";
    return "";
  };

  const deleteDoc = async (filename: string) => {
      await fetch(`http://localhost:8000/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });
      await fetchDocs();
  }

  return (
    <div className="container">
      {/* File Upload Panel */}
      <div className="doc-panel">
        <h2 style={{ marginBottom: "1rem" }}>RAG Memory</h2>
        
        <label className="doc-upload">
          <input type="file" accept=".pdf" hidden onChange={handleFileUpload} />
          <div>Drop PDF here to Add to FRIDAY's Brain</div>
        </label>
        
        <div className="doc-list">
          <h4 style={{ marginBottom: "0.5rem", color: "var(--text-muted)" }}>Current Documents:</h4>
          {docs.map(d => (
            <div key={d} style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem", background: "rgba(255,255,255,0.05)", borderRadius: "8px", marginBottom: "0.5rem" }}>
              <span>📄 {d}</span>
              <button 
                onClick={() => deleteDoc(d)}
                style={{ background: "transparent", color: "#f43f5e", border: "none", cursor: "pointer" }}>
                ✕
              </button>
            </div>
          ))}
          {docs.length === 0 && <span style={{color: "gray"}}>No documents ingested.</span>}
        </div>
      </div>

      {/* Chat UI Panel */}
      <div className="chat-panel">
        <div className="chat-header">
          <div className={`status-dot ${getStatusClass()}`}></div>
          <h2>FRIDAY Core - {status}</h2>
        </div>

        <div className="chat-history">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.role}`}>
              <strong>{m.role === 'user' ? 'You' : 'FRIDAY'}</strong>
              <div style={{ marginTop: "0.5rem" }}>{m.content}</div>
            </div>
          ))}
          <div ref={chatBottomRef} />
        </div>

        <div className="mic-container">
          <button 
            className="mic-button"
            onMouseDown={startRecording} 
            onMouseUp={stopRecording}
            onMouseLeave={stopRecording}
          >
            {status === "Listening..." ? "Release to Send" : "Hold to Speak"}
          </button>
        </div>
      </div>
    </div>
  );
}
