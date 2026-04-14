import tempfile
import asyncio
import os
import edge_tts
import pygame
from backend.config import VOICE

async def _speak_async(text):
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
