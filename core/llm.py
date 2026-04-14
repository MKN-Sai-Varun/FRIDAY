from groq import Groq
from core.config import GROQ_API_KEY, GROQ_MODEL, FRIDAY_PERSONA

client = Groq(api_key=GROQ_API_KEY)

conversation = [{"role": "system", "content": FRIDAY_PERSONA}]

def ask_friday(user_text):
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
    conversation.append({"role": "assistant", "content": reply})
    return reply
