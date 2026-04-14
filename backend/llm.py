from groq import Groq
from backend.config import GROQ_API_KEY, GROQ_MODEL, FRIDAY_PERSONA

client = Groq(api_key=GROQ_API_KEY)

conversation = [{"role": "system", "content": FRIDAY_PERSONA}]

from backend.rag import query_documents

def check_groq_health():
    if not GROQ_API_KEY:
        raise ValueError(f"CRITICAL ERROR: GROQ_API_KEY is not set in .env!")
    try:
        print("Checking Groq API Health...")
        client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        print("Groq API connected successfully.")
    except Exception as e:
        raise ConnectionError(f"CRITICAL ERROR: Failed to connect to Groq API. Please check your GROQ_API_KEY or connection. Details: {e}")

check_groq_health()

def ask_friday(user_text):
    context = query_documents(user_text)
    
    if context:
        prompt_with_context = f"Context from documents:\n{context}\n\nUser says: {user_text}"
        conversation.append({"role": "user", "content": prompt_with_context})
    else:
        conversation.append({"role": "user", "content": user_text})
        
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=conversation,
            max_tokens=150,
            temperature=0.7
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = f"Having trouble reaching my brain, boss. {str(e)}"
        
    # We append the reply to history
    conversation.append({"role": "assistant", "content": reply})
    return reply

def ask_friday_stream(user_text):
    context = query_documents(user_text)
    
    if context:
        prompt_with_context = f"Context from documents:\n{context}\n\nUser says: {user_text}"
        conversation.append({"role": "user", "content": prompt_with_context})
    else:
        conversation.append({"role": "user", "content": user_text})
        
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=conversation,
            max_tokens=150,
            temperature=0.7,
            stream=True
        )
        full_reply = ""
        for chunk in response:
            if getattr(chunk.choices[0].delta, "content", None):
                text = chunk.choices[0].delta.content
                full_reply += text
                yield f"data: {text}\n\n"
                
        conversation.append({"role": "assistant", "content": full_reply})
        
    except Exception as e:
        yield f"data: Having trouble reaching my brain, boss. {str(e)}\n\n"
