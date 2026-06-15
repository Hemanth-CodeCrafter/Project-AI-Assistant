# core/actions.py
import webbrowser
import subprocess
import datetime
import requests
import os
from zoneinfo import ZoneInfo


CITY_TIMEZONES = {
    "chicago": "America/Chicago",
    "new york": "America/New_York",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "tokyo": "Asia/Tokyo",
    "hyderabad": "Asia/Kolkata",
    "vijayawada": "Asia/Kolkata",
}

# ── Open Apps ─────────────────────────────────────
def open_youtube():
    webbrowser.open("https://youtube.com")
    return "Opening YouTube."

def open_google():
    webbrowser.open("https://google.com")
    return "Opening Google."

def open_whatsapp():
    webbrowser.open("https://web.whatsapp.com")
    return "Opening WhatsApp."

def open_maps():
    webbrowser.open("https://maps.google.com")
    return "Opening Maps."

def open_chrome():
    subprocess.Popen("start chrome", shell=True)
    return "Opening Chrome."

def open_spotify():
    subprocess.Popen("start spotify", shell=True)
    return "Opening Spotify."

def open_vscode():
    try:
        subprocess.Popen(["code"])
        return "Opening VS Code."
    except:
        return "Could not open VS Code."

def open_notepad():
    subprocess.Popen(["notepad"])
    return "Opening Notepad."

def open_calculator():
    subprocess.Popen(["calc"])
    return "Opening Calculator."

def open_files():
    subprocess.Popen(["explorer"])
    return "Opening File Explorer."

def open_camera():
    subprocess.Popen(
        "start microsoft.windows.camera:", shell=True
    )
    return "Opening Camera."

# ── Close Apps ────────────────────────────────────
def close_app(name):
    try:
        subprocess.call(
            f"taskkill /f /im {name}.exe",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return f"Closed {name}."
    except Exception as e:
        return f"Could not close {name}: {e}"

# ── Search ────────────────────────────────────────
def search_google(query):
    if not query:
        return "What should I search for?"
    webbrowser.open(
        f"https://google.com/search?q={query.replace(' ', '+')}"
    )
    return f"Searching Google for {query}."

def search_youtube(query):
    if not query:
        return "What should I search on YouTube?"
    webbrowser.open(
        f"https://youtube.com/results?"
        f"search_query={query.replace(' ', '+')}"
    )
    return f"Searching YouTube for {query}."

def play_on_spotify(query):
    if not query:
        return open_spotify()
    webbrowser.open(
        f"https://open.spotify.com/search/"
        f"{query.replace(' ', '%20')}"
    )
    return f"Playing {query} on Spotify."

# ── Time & Date ───────────────────────────────────
def tell_time():
    now = datetime.datetime.now().strftime("%I:%M %p")
    return f"The time is {now}."

def world_time(city):
    try:
        tz = CITY_TIMEZONES.get(city.lower())

        if not tz:
            return f"I don't know the timezone for {city}."

        now = datetime.now(ZoneInfo(tz))

        return (
            f"The time in {city.title()} is "
            f"{now.strftime('%I:%M %p')}."
        )

    except Exception:
        return f"Could not get time for {city}."

def tell_date():
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    return f"Today is {today}."

# ── Weather ───────────────────────────────────────
def get_weather(city=""):
    try:
        url = f"https://wttr.in/{city}?format=3"
        r   = requests.get(url, timeout=5)
        return r.text
    except:
        return "Could not fetch weather. Check internet."

# ── System ────────────────────────────────────────
def take_screenshot():
    try:
        import pyautogui
        path = os.path.expanduser(
            f"~/Desktop/screenshot_"
            f"{datetime.datetime.now().strftime('%H%M%S')}.png"
        )
        pyautogui.screenshot(path)
        return "Screenshot saved to Desktop."
    except:
        return "Install pyautogui for screenshots."

def volume_up():
    subprocess.call(
        "nircmd.exe changesysvolume 5000", shell=True
    )
    return "Volume increased."

def volume_down():
    subprocess.call(
        "nircmd.exe changesysvolume -5000", shell=True
    )
    return "Volume decreased."

def mute():
    subprocess.call(
        "nircmd.exe mutesysvolume 1", shell=True
    )
    return "Muted."

def shutdown_pc():
    subprocess.call("shutdown /s /t 5", shell=True)
    return "Shutting down in 5 seconds."