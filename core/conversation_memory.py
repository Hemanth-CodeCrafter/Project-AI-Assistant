# core/conversation_memory.py

import re
import spacy

nlp = spacy.load("en_core_web_sm")


class ConversationMemory:

    def __init__(self):
        self.last_topic = None
        self.history = []

    # ------------------------
    # Conversation History
    # ------------------------
    def add(self, user, assistant=None):
        self.history.append({
            "user": user,
            "assistant": assistant
        })

        # Keep only last 10 conversations
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []

    # ------------------------
    # Topic Management
    # ------------------------
    def set_topic(self, topic):
        self.last_topic = topic

    def get_topic(self):
        return self.last_topic

    def clear_topic(self):
        self.last_topic = None

    # ------------------------
    # Topic Extraction
    # ------------------------
    def extract_topic(self, text):

        doc = nlp(text)

        # Prefer named entities
        for ent in doc.ents:
            if ent.label_ in [
                "PERSON",
                "ORG",
                "PRODUCT",
                "GPE",
                "LOC",
                "EVENT",
                "WORK_OF_ART"
            ]:
                return ent.text

        # Fallback:
        # use last noun phrase

        noun_chunks = list(doc.noun_chunks)

        if noun_chunks:
            for chunk in reversed(noun_chunks):

                text = chunk.text.lower().strip()

                if text not in [
                    "what",
                    "who",
                    "where",
                    "when",
                    "why",
                    "how",
                    "it",
                    "this",
                    "that"
                ]:
                    return chunk.text

        return None

    # ------------------------
    # Resolve follow-up questions
    # ------------------------
    def resolve(self, text):

        topic = self.get_topic()

        if not topic:
            return text

        resolved = text.lower()

        replacements = {
            r"\bhe\b": topic,
            r"\bshe\b": topic,
            r"\bhim\b": topic,
            r"\bher\b": topic,
            r"\bit\b": topic,
            r"\bthey\b": topic,
            r"\bthem\b": topic,
            r"\bthat\b": topic,
            r"\bthis\b": topic
        }

        for pattern, replacement in replacements.items():
            resolved = re.sub(
                pattern,
                replacement,
                resolved,
                flags=re.IGNORECASE
            )

        return resolved


# Global instance
conversation_memory = ConversationMemory()