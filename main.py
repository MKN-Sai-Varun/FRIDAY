from core.audio import record_until_silence
from core.stt import transcribe
from core.llm import ask_friday
from core.tts import speak

def main():
    print("FRIDAY online. Say something, boss.")
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
            speak("Shutting down. See you later, boss.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
