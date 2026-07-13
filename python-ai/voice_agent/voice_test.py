import sounddevice as sd
import numpy as np
import whisper
import pyttsx3

SAMPLE_RATE = 16000
DURATION = 5  # seconds per listen

print("Loading Whisper model (base)...")
model = whisper.load_model("base")

engine = pyttsx3.init()


def speak(text):
    print(f"Agent: {text}")
    engine.say(text)
    engine.runAndWait()


def listen():
    print(f"\nListening for {DURATION} seconds... speak now.")
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    audio = audio.flatten()
    result = model.transcribe(audio, fp16=False, language="en")
    return result["text"].strip()


if __name__ == "__main__":
    speak("Voice test ready. I will listen for five seconds after you press enter.")
    input("Press Enter then start speaking...")
    text = listen()
    if text:
        print(f"You said: {text}")
        speak(f"I heard you say: {text}")
    else:
        speak("I didn't catch anything.")
