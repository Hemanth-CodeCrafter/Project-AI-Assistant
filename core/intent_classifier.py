# core/intent_classifier.py
import re
import spacy
from rapidfuzz import fuzz

nlp = spacy.load("en_core_web_sm")

# ── Per-intent query removal words ────────────────
INTENT_REMOVE_WORDS = {
    "google_search":  ["search", "google", "find",
                       "look", "up", "for"],
    "youtube_search": ["search", "youtube", "find",
                       "look", "up", "for", "watch",
                       "play", "on"],
    "play_music":     ["play", "listen", "to", "put",
                       "on", "music", "song", "spotify"],
    "open_maps":      ["open", "navigate", "to",
                       "directions", "take", "me",
                       "show", "maps"],
    "open_app":       ["open", "launch", "start"],
}

# ── Context-injectable verbs ───────────────────────
# Only inject previous context for these verbs
# Fixes: "tell me the time on youtube"
CONTEXT_VERBS = [
    "search", "find", "play", "watch",
    "listen", "look", "stream"
]

# ── Target keywords ───────────────────────────────
TARGET_KEYWORDS = {
    "visual studio code": "vscode",
    "vs code":   "vscode",
    "vscode":    "vscode",
    "youtube":   "youtube",
    "google":    "google",
    "spotify":   "spotify",
    "maps":      "maps",
    "whatsapp":  "whatsapp",
    "chrome":    "chrome",
    "notepad":   "notepad",
    "calculator": "calculator",
    "explorer":  "files",
    "files":     "files",
}

# ── Non-injectable intents ─────────────────────────
# These should NEVER receive context injection
NO_INJECT_INTENTS = [
    "tell_time", "tell_date", "get_weather",
    "volume_up", "volume_down", "mute",
    "screenshot", "shutdown_pc", "tell_joke"
]

# ── Helpers ───────────────────────────────────────
def fuzzy_match(text, phrases, threshold=80):
    for phrase in phrases:
        if fuzz.partial_ratio(phrase, text) >= threshold:
            return True
        if all(w in text for w in phrase.split()):
            return True
    return False

def has_phrase(text, phrases):
    return any(phrase in text for phrase in phrases)

def has_verb(doc, verbs):
    lemmas = [t.lemma_.lower() for t in doc]
    return any(v in lemmas for v in verbs)

def has_concept(tokens, concepts):
    return any(c in tokens for c in concepts)

def is_about_now(text):
    not_now = [
        "tomorrow", "yesterday", "next", "last",
        "when i", "when will", "woke", "slept",
        "schedule", "meeting", "appointment", "event",
        "tonight", "this evening", "upcoming", "later",
        "did i", "have i", "will i", "going to",
        "flight", "class", "birthday", "deadline"
    ]
    return not any(w in text for w in not_now)

def extract_entities(doc):
    entities = {}
    for ent in doc.ents:
        entities[ent.label_] = ent.text
    return entities

def extract_query(doc, remove_words):
    stop = set(w.lower() for w in remove_words) | {
        "the", "a", "an", "please", "can",
        "you", "could", "would", "jarvis", "hey"
    }
    words = [
        t.text for t in doc
        if t.text.lower() not in stop
        and not t.is_punct
        and not t.is_space
    ]
    return " ".join(words).strip()

def detect_target(text):
    """Detect app/platform mentioned — longest match first"""
    for keyword in sorted(TARGET_KEYWORDS,
                          key=len, reverse=True):
        if keyword in text:
            return TARGET_KEYWORDS[keyword]
    return None

# ── Splitter ──────────────────────────────────────
def split_into_commands(command: str):
    text  = command.lower().strip()
    parts = re.split(
        r'\s*(?:and then|and also|after that'
        r'|then|and|also|,)\s*',
        text
    )
    parts = [p.strip() for p in parts
             if p.strip() and len(p.strip()) > 2]
    return parts if len(parts) > 1 else [text]

# ── Context injector — Fix 3 ──────────────────────
def inject_context(parts: list):
    """
    Only injects context when command uses
    a search/play/watch verb.
    Prevents: 'tell me the time on youtube'
    """
    current_context = None
    enriched        = []

    for part in parts:
        doc    = nlp(part)
        target = detect_target(part)

        if target:
            current_context = target
            enriched.append(part)

        elif current_context and \
             has_verb(doc, CONTEXT_VERBS):
            # Only inject for search/play type commands
            injected = f"{part} on {current_context}"
            print(f"  [context] '{part}' → '{injected}'")
            enriched.append(injected)

        else:
            # No injection — time, date, weather, etc.
            enriched.append(part)

    return enriched

# ── Single command classifier ─────────────────────
def classify(command: str):
    text   = command.lower().strip()
    doc    = nlp(text)
    tokens = [t.lemma_.lower() for t in doc]
    ents   = extract_entities(doc)

    # ── Time ──────────────────────────────────────
    '''if fuzzy_match(text, [
        "what time is it", "current time",
        "what is the time", "tell me the time",
        "whats the time", "time right now"
    ]) and is_about_now(text):
        return "tell_time", None, ents
    '''
    if "time" in text and is_about_now(text):
        city = ents.get("GPE", ents.get("LOC", ""))

        if not city and " in " in text:
            city = text.split(" in ", 1)[1].strip()
        
        if city:
            return "world_time", city, ents
        return "tell_time", None, ents
    



    # ── Date ──────────────────────────────────────
    if fuzzy_match(text, [
        "what is the date", "what's the date",
        "today's date", "what day is it",
        "current date", "date today"
    ]) and is_about_now(text):
        return "tell_date", None, ents

    # ── Weather — Fix 1 ───────────────────────────
    # Catches: 'weather in vijayawada',
    #          'temperature in bangalore', 'forecast'
    if (
        "weather"     in text or
        "temperature" in text or
        "forecast"    in text
    ) and is_about_now(text):
        # Try spaCy NER first
        city = ents.get("GPE", ents.get("LOC", ""))
        # Fallback: extract after 'in'
        if not city and " in " in text:
            city = text.split(" in ", 1)[1].strip()
        return "get_weather", city, ents

    # ── VS Code ───────────────────────────────────
    if has_verb(doc, ["open", "launch", "start"]):
        if has_phrase(text, ["vs code", "vscode",
                             "visual studio code"]):
            return "open_vscode", None, ents

    # ── Open Apps ─────────────────────────────────
    if has_verb(doc, ["open", "launch", "start"]):

        if has_phrase(text, ["youtube"]) and \
           not has_verb(doc, ["close", "stop", "exit"]):
            return "open_youtube", None, ents

        if has_phrase(text, ["google"]) and \
           not has_verb(doc, ["search", "find"]):
            return "open_google", None, ents

        if has_phrase(text, ["whatsapp", "whats app"]):
            return "open_whatsapp", None, ents

        if has_phrase(text, ["maps", "google maps"]):
            return "open_maps", None, ents

        if has_phrase(text, ["calculator", "calc"]):
            return "open_calculator", None, ents

        if has_phrase(text, ["notepad", "text editor",
                             "note pad"]):
            return "open_notepad", None, ents

        if has_phrase(text, ["chrome", "browser"]):
            return "open_chrome", None, ents

        if has_phrase(text, ["spotify"]):
            return "open_spotify", None, ents

        if has_phrase(text, ["file explorer", "explorer",
                             "my files", "file manager"]):
            return "open_files", None, ents

    # ── Close Apps ────────────────────────────────
    if has_verb(doc, ["close", "exit", "quit",
                      "stop", "shut", "kill"]):

        if has_phrase(text, ["youtube"]):
            return "close_youtube", None, ents
        if has_phrase(text, ["chrome", "browser"]):
            return "close_chrome", None, ents
        if has_phrase(text, ["spotify"]):
            return "close_spotify", None, ents
        if has_phrase(text, ["vs code", "vscode",
                             "visual studio code"]):
            return "close_vscode", None, ents
        if has_phrase(text, ["notepad"]):
            return "close_notepad", None, ents

    # ── YouTube Search ────────────────────────────
    if has_phrase(text, ["youtube", "on youtube"]) and \
       has_verb(doc, ["search", "find", "look",
                      "play", "watch"]):
        query = extract_query(
            doc, INTENT_REMOVE_WORDS["youtube_search"]
        )
        return "youtube_search", query, ents

    # ── Play Music — Fix 2 ────────────────────────
    # Removed requirement for music-related words.
    # 'play believer' now works — any play/listen
    # command with a query goes to play_music
    if has_verb(doc, ["play", "listen"]):
        query = extract_query(
            doc, INTENT_REMOVE_WORDS["play_music"]
        )
        if query:
            return "play_music", query, ents

    # ── Google Search ─────────────────────────────
    if has_verb(doc, ["search", "google",
                      "find", "look"]) and \
       not has_phrase(text, ["youtube", "spotify"]):
        query = extract_query(
            doc, INTENT_REMOVE_WORDS["google_search"]
        )
        return "google_search", query, ents

    # ── Volume ────────────────────────────────────
    if has_concept(tokens, ["volume", "sound"]):
        if fuzzy_match(text, ["volume up",
                              "increase volume",
                              "louder", "raise volume"]):
            return "volume_up", None, ents
        if fuzzy_match(text, ["volume down",
                              "decrease volume",
                              "quieter", "lower volume"]):
            return "volume_down", None, ents

    if fuzzy_match(text, ["mute", "silent", "silence"]):
        return "mute", None, ents

    # ── Screenshot ────────────────────────────────
    if fuzzy_match(text, ["screenshot",
                          "capture screen",
                          "screen capture"]):
        return "screenshot", None, ents

    # ── Shutdown ──────────────────────────────────
    if fuzzy_match(text, ["shutdown computer",
                          "shut down laptop",
                          "power off",
                          "turn off computer"]):
        return "shutdown_pc", None, ents

    return None, None, ents

# ── Multi-intent classifier ───────────────────────
def classify_all(command: str):
    """
    Split → inject context → classify each part.
    Returns list of (intent, query, entities)
    """
    parts    = split_into_commands(command)
    enriched = inject_context(parts)
    results  = []

    print(f"\n  [multi-intent] {enriched}")

    for part in enriched:
        intent, query, ents = classify(part)
        if intent:
            results.append((intent, query, ents))
        else:
            results.append(("llm", part, {}))

    return results