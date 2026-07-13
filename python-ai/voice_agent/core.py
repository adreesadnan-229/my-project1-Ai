import queue
import re

import sounddevice as sd
import whisper
import pyttsx3

import os

import actions
import brain
import config
import documents
import downloader
import figma_client
import generator
import intent_parser

SAMPLE_RATE = 16000
DURATION = 5
EXIT_WORDS = ("exit", "stop listening", "quit")
WAKE_WORD = "jarvis"

_model = None
_engine = None
_typed_commands = queue.Queue()


def submit_text_command(text):
    """Called from the GUI's text box - queues a typed command to be
    processed by the same loop that handles voice, no wake word needed."""
    text = text.strip()
    if text:
        _typed_commands.put(text)


def load_models(on_status=None):
    global _model, _engine
    if on_status:
        on_status("Loading voice models...")
    _model = whisper.load_model("base")
    _engine = pyttsx3.init()
    return _model, _engine


def speak(text, on_status=None, on_speak_start=None, on_speak_end=None):
    if on_status:
        on_status(f"Speaking: {text}")
    if on_speak_start:
        on_speak_start()
    _engine.say(text)
    _engine.runAndWait()
    if on_speak_end:
        on_speak_end()


def listen(on_status=None):
    if on_status:
        on_status("Listening...")
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    audio = audio.flatten()
    if on_status:
        on_status("Thinking...")
    result = _model.transcribe(audio, fp16=False, language="en")
    return result["text"].strip()


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "my-site"


def strip_wake_word(text):
    """Returns the command text with the wake word removed, or None if the
    wake word wasn't said at all."""
    lowered = text.lower()
    idx = lowered.find(WAKE_WORD)
    if idx == -1:
        return None
    remainder = lowered[:idx] + lowered[idx + len(WAKE_WORD):]
    return re.sub(r"\s+", " ", remainder).strip(" ,.")


def detect_platform_from_reply(reply_text):
    lowered = reply_text.lower()
    if "shopify" in lowered:
        return "shopify"
    if "wordpress" in lowered:
        return "wordpress"
    return "html"


def detect_doctype_from_reply(reply_text):
    lowered = (reply_text or "").lower()
    if "card" in lowered or "greeting" in lowered:
        return "card"
    if "excel" in lowered or "spreadsheet" in lowered or "sheet" in lowered:
        return "excel"
    if "powerpoint" in lowered or "presentation" in lowered or "slides" in lowered:
        return "powerpoint"
    if "banner" in lowered or "image" in lowered or "poster" in lowered:
        return "banner"
    return "word"


def has_figma_config():
    cfg = config.load_config()
    return bool(cfg.get("figma_token") and cfg.get("figma_file_key"))


def build_site(spoken_text, platform, callbacks):
    on_status = callbacks.get("on_status")
    on_speak_start = callbacks.get("on_speak_start")
    on_speak_end = callbacks.get("on_speak_end")

    cfg = config.load_config()
    token = cfg.get("figma_token")
    file_key = cfg.get("figma_file_key")

    if not token or not file_key:
        speak("I don't have your Figma details yet. Please set them up first.", on_status, on_speak_start, on_speak_end)
        return

    speak("Got it. Reading your Figma design now, this may take a moment.", on_status, on_speak_start, on_speak_end)
    try:
        data = figma_client.get_file(file_key, token)
        elements = figma_client.simplify_design(data)
    except Exception as e:
        speak("I couldn't read the Figma file. Please check the token and file key.", on_status, on_speak_start, on_speak_end)
        if on_status:
            on_status(f"Figma error: {e}")
        return

    speak(f"Design loaded. Generating your responsive {platform} site now.", on_status, on_speak_start, on_speak_end)
    try:
        theme_name = slugify(spoken_text) or "my-site"
        out_dir, next_steps = generator.generate_site(elements, platform, theme_name)
    except Exception as e:
        speak("Something went wrong while generating the site.", on_status, on_speak_start, on_speak_end)
        if on_status:
            on_status(f"Generator error: {e}")
        return

    speak(f"Done. Your {platform} site is ready, named {theme_name}.", on_status, on_speak_start, on_speak_end)
    if on_status:
        on_status(f"Site written to: {out_dir}")
    speak(next_steps, on_status, on_speak_start, on_speak_end)


def handle_build(spoken_text, intent, callbacks):
    on_status = callbacks.get("on_status")
    on_speak_start = callbacks.get("on_speak_start")
    on_speak_end = callbacks.get("on_speak_end")

    platform = intent.get("platform")
    if platform not in ("wordpress", "shopify", "html"):
        speak("Which platform do you want? WordPress, Shopify, or a plain HTML site?", on_status, on_speak_start, on_speak_end)
        reply = listen(on_status)
        platform = detect_platform_from_reply(reply)
    build_site(spoken_text, platform, callbacks)


def process_command(command, callbacks):
    """Runs one already-extracted command (from voice or typed text) through
    intent detection and dispatches it to the right handler."""
    on_status = callbacks.get("on_status")
    on_speak_start = callbacks.get("on_speak_start")
    on_speak_end = callbacks.get("on_speak_end")

    intent = intent_parser.parse_intent(command)
    if on_status:
        on_status(f"Intent: {intent}")

    if intent["action"] == "build_site":
        handle_build(command, intent, callbacks)
        return

    if intent["action"] == "open_site":
        site = intent.get("site") or "google"
        query = (intent.get("query") or "").strip()
        if query:
            # a search term slipped in here anyway - search instead of just opening blank
            url = actions.web_search(query, site)
            if on_status:
                on_status(f"Searching: {url}")
            speak(f"Searching {site} for {query}.", on_status, on_speak_start, on_speak_end)
            return
        url = actions.open_site(site)
        if on_status:
            on_status(f"Opened: {url}")
        speak(f"Opening {site}.", on_status, on_speak_start, on_speak_end)
        return

    if intent["action"] == "web_search":
        site = intent.get("site") or "google"
        query = (intent.get("query") or "").strip()
        if not query:
            # nothing specific to search for - just open the site instead
            url = actions.open_site(site)
            if on_status:
                on_status(f"Opened: {url}")
            speak(f"Opening {site}.", on_status, on_speak_start, on_speak_end)
            return
        url = actions.web_search(query, site)
        if on_status:
            on_status(f"Searching: {url}")
        speak(f"Searching {site} for {query}.", on_status, on_speak_start, on_speak_end)
        return

    if intent["action"] == "open_folder":
        target = intent.get("target") or command
        path = actions.open_folder(target)
        if path:
            if on_status:
                on_status(f"Opened folder: {path}")
            speak(f"Opening {target}.", on_status, on_speak_start, on_speak_end)
        else:
            if on_status:
                on_status(f"Could not find a folder matching: {target}")
            speak(f"I couldn't find a folder called {target}. Try being more specific.", on_status, on_speak_start, on_speak_end)
        return

    if intent["action"] == "download":
        url = intent.get("url") or downloader.extract_url(command)
        query = intent.get("query")

        if url:
            speak("Downloading that file now, this may take a moment.", on_status, on_speak_start, on_speak_end)
            path = downloader.download_from_url(url)
        elif query:
            speak(f"Downloading {query} from YouTube now, this may take a moment.", on_status, on_speak_start, on_speak_end)
            path = downloader.download_from_youtube(query)
        else:
            speak("What would you like me to download?", on_status, on_speak_start, on_speak_end)
            return

        if path:
            if on_status:
                on_status(f"Saved to: {path}")
            speak("Done. It's saved in your Downloads folder.", on_status, on_speak_start, on_speak_end)
        else:
            if on_status:
                on_status("Download failed.")
            speak("Sorry, that download didn't work.", on_status, on_speak_start, on_speak_end)
        return

    if intent["action"] == "create_document":
        doc_type = intent.get("doc_type")
        topic = intent.get("topic") or command

        if doc_type not in ("excel", "word", "powerpoint", "banner", "card"):
            speak("Should that be an Excel sheet, a Word document, a PowerPoint, a banner image, or a greeting card?", on_status, on_speak_start, on_speak_end)
            reply = listen(on_status)
            doc_type = detect_doctype_from_reply(reply)

        speak(f"Creating your {doc_type} now, this may take a moment.", on_status, on_speak_start, on_speak_end)
        try:
            if doc_type == "excel":
                path = documents.create_excel(topic)
            elif doc_type == "word":
                path = documents.create_word(topic)
            elif doc_type == "powerpoint":
                path = documents.create_pptx(topic)
            elif doc_type == "card":
                path = documents.create_card_pptx(topic)
            else:
                path = documents.create_banner(topic)
        except Exception as e:
            speak("Something went wrong while creating that.", on_status, on_speak_start, on_speak_end)
            if on_status:
                on_status(f"Document error: {e}")
            return

        if on_status:
            on_status(f"Saved to: {path}")
        os.startfile(path)
        speak(f"Done. Your {doc_type} is ready and saved.", on_status, on_speak_start, on_speak_end)
        return

    reply = brain.ask(command)
    speak(reply, on_status, on_speak_start, on_speak_end)


def run_forever(callbacks, should_stop=None):
    """Main loop. `callbacks` is a dict with keys:
    on_status(text), on_speak_start(), on_speak_end().
    `should_stop` is an optional callable returning True to break the loop."""
    on_status = callbacks.get("on_status")
    on_speak_start = callbacks.get("on_speak_start")
    on_speak_end = callbacks.get("on_speak_end")

    speak("Jarvis is ready. Say Jarvis, or type a command below.", on_status, on_speak_start, on_speak_end)

    while True:
        if should_stop and should_stop():
            break

        try:
            typed = _typed_commands.get_nowait()
        except queue.Empty:
            typed = None

        if typed is not None:
            if on_status:
                on_status(f"Typed: {typed}")
            if typed.lower().strip(".") in EXIT_WORDS:
                speak("Goodbye.", on_status, on_speak_start, on_speak_end)
                break
            process_command(typed, callbacks)
            continue

        if on_status:
            on_status("Waiting for 'Jarvis'...")
        text = listen(on_status)
        if not text:
            if on_status:
                on_status("(heard silence / nothing understood)")
            continue

        lowered = text.lower().strip(".")
        if lowered in EXIT_WORDS:
            speak("Goodbye.", on_status, on_speak_start, on_speak_end)
            break

        command = strip_wake_word(text)
        if command is None:
            if on_status:
                on_status(f"(no 'Jarvis' heard - I heard: \"{text}\")")
            # wake word wasn't said - ignore this and keep listening quietly
            continue

        if on_status:
            on_status(f"Heard wake word. You said: {text}")

        if not command:
            # they only said "Jarvis" with no command attached - ask what they need
            speak("Yes?", on_status, on_speak_start, on_speak_end)
            command = listen(on_status)
            if not command:
                continue
            if command.lower().strip(".") in EXIT_WORDS:
                speak("Goodbye.", on_status, on_speak_start, on_speak_end)
                break

        process_command(command, callbacks)
