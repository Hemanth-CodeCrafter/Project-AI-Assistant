from core.actions import *


class Router:

    def route(self, command):

        command = command.lower()

        # YouTube
        if "youtube" in command:
            return open_youtube()

        # Google
        elif "google" in command:
            return open_google()

        # VS Code
        elif "vscode" in command or "visual studio code" in command:
            return open_vscode()

        # Time
        elif "time" in command:
            return tell_time()

        # Not Found
        return None