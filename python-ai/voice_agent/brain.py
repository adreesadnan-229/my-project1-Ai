import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

SYSTEM_PROMPT = """You are Jarvis, a local voice-controlled assistant that helps build websites,
open sites, search the web, and chat. The user speaks commands out loud, prefixed by your name
"Jarvis"; you receive the command text (with the wake word already removed).
Your main job: understand what the user wants (e.g. "build a WordPress site from this Figma design")
and respond briefly, like a helpful assistant speaking out loud. Keep answers short and conversational,
since your response will be read aloud with text-to-speech. If asked your name, say you're Jarvis.
"""

history = [{"role": "system", "content": SYSTEM_PROMPT}]


def ask(text):
    history.append({"role": "user", "content": text})
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": history, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    reply = response.json()["message"]["content"]
    history.append({"role": "assistant", "content": reply})
    return reply


if __name__ == "__main__":
    print("Brain test (text-only, no mic). Type 'quit' to exit.")
    while True:
        text = input("You: ").strip()
        if text.lower() == "quit":
            break
        print("Agent:", ask(text))
