import ollama

class Brain:
    def __init__(self):
        self.model = "qwen2.5:3b"
        self.history = []  # conversation memory

        self.system_prompt = """
        You are Jarvis, a personal AI assistant.
        Keep answers SHORT — maximum 2 sentences for simple questions.
        Never say "As an AI language model".
        Never list your capabilities unless asked.
        Be direct, helpful, conversational.
        If asked to do something on the computer, say "I'll handle that."
        """
        print("Jarvis brain initialized.")

    def think(self, prompt):
        # Add to history
        self.history.append({
            "role": "user",
            "content": prompt
        })

        # Keep only last 6 messages (saves RAM)
        if len(self.history) > 6:
            self.history = self.history[-6:]

        response = ollama.chat(
            model=self.model,
            options={
                "temperature": 0.4,
                "num_predict": 256,   # short answers = faster
                "num_ctx": 512,      # small context = less RAM
                "num_thread": 4,
            },
            messages=[
                {"role": "system", "content": self.system_prompt},
                *self.history
            ]
        )

        reply = response["message"]["content"]

        # Save reply to history
        self.history.append({
            "role": "assistant",
            "content": reply
        })

        return reply