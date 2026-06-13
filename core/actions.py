import webbrowser
import subprocess
import datetime


def open_youtube():
    webbrowser.open("https://youtube.com")
    return "Opening YouTube."


def open_google():
    webbrowser.open("https://google.com")
    return "Opening Google."


def open_vscode():
    try:
        subprocess.Popen(["code"])
        return "Opening Visual Studio Code."

    except Exception:
        return "Unable to open Visual Studio Code."


def tell_time():

    current_time = datetime.datetime.now().strftime("%I:%M %p")

    return f"The time is {current_time}."