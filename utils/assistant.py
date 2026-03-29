import whisper
import pyttsx3
import sounddevice as sd
import numpy as np
import ollama
import sys
import speech_recognition as sr

# ── Load models ──────────────────────────────────────────────
print("Loading Whisper model...")
stt = whisper.load_model("base")
print("Whisper ready!")

print("Initializing TTS...")
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 1.0)
print("TTS ready!")

OLLAMA_MODEL  = "llama3.2:1b"
ASSISTANT_NAME = "Saturday"
WAKE_WORDS     = ["hey jarvis", "jarvis", "hey saturday", "saturday"]

recognizer = sr.Recognizer()
mic        = sr.Microphone()

# calibrate mic to background noise once at startup
with mic as source:
    print("Calibrating microphone to background noise...")
    recognizer.adjust_for_ambient_noise(source, duration=2)
    print("Mic calibrated!")

# ── Wake word ─────────────────────────────────────────────────
def wait_for_wake_word():
    print(f"\n😴 {ASSISTANT_NAME} sleeping... say 'Hey Jarvis' or 'Hey Saturday'")
    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
            text = recognizer.recognize_google(audio).lower()
            print(f"   heard: {text}")
            if any(w in text for w in WAKE_WORDS):
                return True
        except sr.WaitTimeoutError:
            pass   # nothing heard, keep looping
        except sr.UnknownValueError:
            pass   # heard noise but couldn't understand, keep looping
        except Exception as e:
            print(f"Wake word error: {e}")

# ── Listen for command ────────────────────────────────────────
def listen(duration=6, samplerate=16000):
    print(f"\n🎤 {ASSISTANT_NAME} listening... speak your command!")
    try:
        audio = sd.rec(
            int(duration * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        audio_flat = audio.flatten()

        if abs(audio_flat).max() < 0.001:
            print("⚠️  Mic too quiet — check Ubuntu Settings → Sound → Input")
            return ""

        print("Transcribing...")
        result = stt.transcribe(audio_flat, fp16=False)
        text   = result["text"].strip()
        return text

    except Exception as e:
        print(f"❌ Listen error: {e}")
        return ""

# ── Think ─────────────────────────────────────────────────────
def think(text):
    print("Thinking...")
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are {ASSISTANT_NAME}, a helpful personal voice assistant. "
                        f"Your name is {ASSISTANT_NAME}. "
                        "Keep answers short and clear — 2 to 3 sentences max. "
                        "You run locally on the user's Ubuntu laptop. "
                        "Be friendly and conversational."
                    )
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )
        return response['message']['content']

    except Exception as e:
        print(f"❌ Ollama error: {e}")
        return "Sorry, I had trouble thinking. Is Ollama running?"

# ── Speak ─────────────────────────────────────────────────────
def speak(text):
    print(f"🔊 {ASSISTANT_NAME}: {text}")
    try:
        tts.say(text)
        tts.runAndWait()
    except Exception as e:
        print(f"❌ TTS error: {e}")

# ── Ollama check ──────────────────────────────────────────────
def check_ollama():
    try:
        ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "hi"}]
        )
        return True
    except Exception as e:
        print(f"\n❌ Ollama not reachable: {e}")
        print("   Fix: open a new terminal and run → ollama serve")
        return False

# ── Main ──────────────────────────────────────────────────────
def main():
    print("\n" + "="*45)
    print(f"   🤖 {ASSISTANT_NAME} — Starting up")
    print("="*45)

    print("\nChecking Ollama...")
    if not check_ollama():
        sys.exit(1)
    print("✅ Ollama connected!")

    speak(f"Hello! I am {ASSISTANT_NAME}, your personal assistant. Say Hey Saturday or Hey Jarvis to wake me up!")

    while True:
        try:
            # step 1 — wait for wake word
            wait_for_wake_word()

            # step 2 — wake up
            print(f"\n🟢 Wake word detected! {ASSISTANT_NAME} is awake!")
            speak("Yes, I am listening.")

            # step 3 — get command
            user_input = listen()

            if not user_input.strip():
                speak("I did not catch that. Try again.")
                continue

            print(f"You said: {user_input}")

            # step 4 — exit commands
            if any(w in user_input.lower() for w in ["exit", "quit", "bye", "goodbye", "stop"]):
                speak("Goodbye! Have a great day!")
                print("👋 Exiting...")
                break

            # step 5 — think and reply
            reply = think(user_input)
            print(f"{ASSISTANT_NAME}: {reply}")
            speak(reply)

        except KeyboardInterrupt:
            print(f"\n\n👋 {ASSISTANT_NAME} shutting down!")
            speak("Goodbye!")
            break

if __name__ == "__main__":
    main()