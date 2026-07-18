# core/conversation_memory.py

import re
import spacy

nlp = spacy.load("en_core_web_sm")


class ConversationMemory:

    def __init__(self):
        self.last_topic = None
        self.last_person = None
        self.last_entity = None
        self.history = []

    def _normalize_topic(self, topic):
        if topic is None:
            return None

        cleaned = re.sub(r"\s+", " ", str(topic).strip())
        cleaned = cleaned.strip(" .,!?:;")
        return cleaned or None

    def _is_command_like(self, text):
        if not text:
            return False

        command_verbs = [
            "open", "close", "start", "launch", "stop", "exit",
            "quit", "play", "pause", "search", "find", "look",
            "watch", "listen", "navigate", "show", "take", "use"
        ]
        return any(text.startswith(f"{verb} ") for verb in command_verbs)



    def _extract_question_subject(self, text):
        if not text:
            return None

        normalized = re.sub(r"\s+", " ", str(text).strip()).lower()
        patterns = [
            r"\bwhat(?:'s)?\s+(?:is|are|was|were)\s+(.+)$",
            r"\bwho\s+(?:is|was|were)\s+(.+)$",
            r"\bwhich\s+(?:is|are|was|were)\s+(.+)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                candidate = match.group(1).strip()
                candidate = re.sub(r"^(?:the|a|an)\s+", "", candidate)
                candidate = re.sub(r"\s+", " ", candidate).strip(" .,!?:;")
                if candidate and candidate not in {"it", "this", "that", "these", "those", "he", "she", "they"}:
                    return candidate

        return None

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
        normalized = self._normalize_topic(topic)
        if not normalized:
            return
        self.last_topic = normalized

    def get_topic(self):
        return self.last_topic

    def clear_topic(self):
        self.last_topic = None
        self.last_person = None
        self.last_entity = None
    
    def update_entities(self, text):
        """
        Update conversational entities from assistant replies.
        """

        if not text:
            return

        doc = nlp(str(text))

        for ent in doc.ents:
            self.last_entity = ent.text

            if ent.label_ == "PERSON":
                self.last_person = ent.text

    # ------------------------
    # Topic Extraction
    # ------------------------
    def extract_topic(self, text):
        if not text:
            return None

        normalized_text = re.sub(r"\s+", " ", str(text).strip()).lower()
        if self._is_command_like(normalized_text):
            return None

        doc = nlp(str(text))

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
                return self._normalize_topic(ent.text)

        # Fallback: use last noun phrase
        noun_chunks = list(doc.noun_chunks)

        if noun_chunks:
            for chunk in reversed(noun_chunks):
                candidate = chunk.text.strip()
                candidate_norm = candidate.lower().strip()

                if candidate_norm in [
                    "what",
                    "who",
                    "where",
                    "when",
                    "why",
                    "how",
                    "it",
                    "this",
                    "that",
                    "these",
                    "those",
                    "them",
                    "he",
                    "she",
                    "they"
                ]:
                    continue

                if len(candidate.split()) <= 2:
                    return self._normalize_topic(candidate)

        return None

    # ------------------------
    # Resolve follow-up questions
    # ------------------------
    def resolve(self, text):
        topic = self.last_topic
        person = self.last_person

        if not topic and not person:
            return text

        resolved = str(text).strip()

        if not resolved:
            return text
        
        topic_text = str(topic).strip() if topic else ""
        person_text = str(person).strip() if person else ""

        replacements = {}

        if person_text:
            replacements.update({
                r"\bhe\b": person_text,
                r"\bshe\b": person_text,
                r"\bhim\b": person_text,
                r"\bher\b": person_text,
            })

        if topic_text:
            replacements.update({
                r"\bit\b": topic_text,
                r"\bthat\b": topic_text,
                r"\bthis\b": topic_text,
                r"\bthese\b": topic_text,
                r"\bthose\b": topic_text,
                r"\bthey\b": topic_text,
                r"\bthem\b": topic_text,
            })

        for pattern, replacement in replacements.items():
            resolved = re.sub(
                pattern,
                replacement,
                resolved,
                flags=re.IGNORECASE
            )

        return resolved

