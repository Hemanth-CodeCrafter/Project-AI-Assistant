# core/router.py
from core.actions import *
from core.intent_classifier import classify_all

class Router:

    def execute_intent(self, intent, query, entities):
        if intent == "tell_time":       return tell_time()
        if intent == "world_time":
            return world_time(query)
        if intent == "tell_date":       return tell_date()
        if intent == "get_weather":     return get_weather(query)
        if intent == "screenshot":      return take_screenshot()
        if intent == "take_screenshot": return take_screenshot()
        if intent == "shutdown_pc":     return shutdown_pc()
        if intent == "open_youtube":    return open_youtube()
        if intent == "open_google":     return open_google()
        if intent == "open_whatsapp":   return open_whatsapp()
        if intent == "open_maps":       return open_maps()
        if intent == "open_vscode":     return open_vscode()
        if intent == "open_calculator": return open_calculator()
        if intent == "open_notepad":    return open_notepad()
        if intent == "open_chrome":     return open_chrome()
        if intent == "open_spotify":    return open_spotify()
        if intent == "open_files":      return open_files()
        if intent == "close_youtube":   return close_app("msedge")
        if intent == "close_chrome":    return close_app("chrome")
        if intent == "close_spotify":   return close_app("spotify")
        if intent == "close_vscode":    return close_app("code")
        if intent == "close_notepad":   return close_app("notepad")
        if intent == "youtube_search":  return search_youtube(query)
        if intent == "google_search":   return search_google(query)
        if intent == "play_music":      return play_on_spotify(query)
        if intent == "volume_up":       return volume_up()
        if intent == "volume_down":     return volume_down()
        if intent == "mute":            return mute()
        return None

    def route(self, command):
        """
        Returns dict:
        {
          "responses": ["Done.", "Opening YouTube."],
          "llm_parts": ["explain quantum physics"]
        }
        Or None if everything goes to LLM.
        """
        intents = classify_all(command)

        # Everything is LLM
        if all(i[0] == "llm" for i in intents):
            return None

        responses = []
        llm_parts = []

        for intent, query, entities in intents:
            if intent == "llm":
                llm_parts.append(query)
                continue
            result = self.execute_intent(
                intent, query, entities
            )
            if result:
                responses.append(result)

        return {
            "responses": responses,
            "llm_parts": llm_parts
        }