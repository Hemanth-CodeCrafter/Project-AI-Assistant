# core/router.py
from core.actions import *
from core.intent_classifier import classify_all
from core.device_manager import DeviceManager
from core.device_actions import (
    execute_on_mobile,
    execute_on_tv
)
from core.context_manager import ContextManager
from typing import Optional

device_manager = DeviceManager()

APP_MAP = {
    "open_youtube": "youtube",
    "youtube_search": "youtube",
    "close_youtube": "youtube",

    "open_google": "chrome",
    "google_search": "chrome",

    "open_chrome": "chrome",
    "close_chrome": "chrome",

    "open_spotify": "spotify",
    "play_music": "spotify",
    "close_spotify": "spotify",

    "open_vscode": "vscode",
    "close_vscode": "vscode",

    "open_notepad": "notepad",
    "close_notepad": "notepad",

    "open_calculator": "calculator",
    "open_files": "explorer",
    "open_whatsapp": "whatsapp",
    "open_maps": "maps",
}

class Router:
    def __init__(self, context_manager: Optional[ContextManager] = None):
        self._context_manager = context_manager or ContextManager()

    def execute_intent(self, intent, query, entities):
        device = entities.get(
            "DEVICE",
            device_manager.get_active_device()
        )
        
        app = APP_MAP.get(intent)

        self._context_manager.update(
            app=app,
            intent=intent,
            query=query,
            device=device
        )


        if intent == "tell_time":       return tell_time()
        if intent == "world_time":
            return world_time(query)
        if intent == "tell_date":       return tell_date()
        if intent == "get_weather":     return get_weather(query)
        if intent == "screenshot":      return take_screenshot()
        if intent == "take_screenshot": return take_screenshot()
        if intent == "shutdown_pc":     return shutdown_pc()

        if intent == "open_youtube":
            if device == "laptop":
                return open_youtube()

            if device == "mobile":
                return execute_on_mobile(
                    "open_youtube"
                )

            if device == "tv":
                return execute_on_tv(
                    "open_youtube"
                )
        
        if intent == "open_google":
            if device == "laptop":
                return open_google()

            if device == "mobile":
                return execute_on_mobile(
                    "open_google"
                )

            if device == "tv":
                return execute_on_tv(
                    "open_google"
                )
        
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
    
    def optimize_intents(self, intents):
        """
        Remove redundant intents.

        Example:
        open_youtube + youtube_search
        -> keep only youtube_search
        """

        intent_names = {i[0] for i in intents}

        optimized = []

        for intent, query, entities in intents:

            # Search already opens YouTube
            if intent == "open_youtube" and "youtube_search" in intent_names:
                continue

            # Search already opens Google
            if intent == "open_google" and "google_search" in intent_names:
                continue

            # Spotify search/play already opens Spotify
            if intent == "open_spotify" and "play_music" in intent_names:
                continue

            optimized.append((intent, query, entities))

        return optimized

    def route(self, command):
        """
        Returns dict:
        {
          "responses": ["Done.", "Opening YouTube."],
          "llm_parts": ["explain quantum physics"]
        }
        Or None if everything goes to LLM.
        """

        intents = classify_all(command, self._context_manager)

        if len(intents) == 1 and intents[0][0] in ["affirm", "negate"]:
            return {"intent": intents[0][0]}

        intents = self.optimize_intents(intents)
        
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
