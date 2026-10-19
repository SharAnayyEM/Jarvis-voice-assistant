import sys
import pyaudiowpatch as pyaudio
sys.modules['pyaudio'] = pyaudio

import speech_recognition as sr
import pyttsx3
import os
import re
import random
import webbrowser
import urllib.parse
import psutil
import pyautogui
import requests
from datetime import datetime, timedelta
from google import genai
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Initialize Text-To-Speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 170)

WAKE_WORD = "jarvis"

# Apps that can be closed by killing their process
CLOSE_APPS = {
    "chrome": "chrome.exe",
    "spotify": "Spotify.exe",
    "notepad": "notepad.exe",
    "calculator": "CalculatorApp.exe",
    "vs code": "Code.exe",
    "visual studio code": "Code.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "youtube": "chrome.exe",
    "google": "chrome.exe",
    "whatsapp": "chrome.exe",
    "gmail": "chrome.exe",
    "email": "chrome.exe",
    "instagram": "chrome.exe",
}

WEATHER_CODES = {
    0: "clear sky",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "foggy with frost",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "light rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorms",
    96: "thunderstorms with hail",
}

def speak(text):
    print(f"JARVIS: {text}")
    engine.say(text)
    engine.runAndWait()

def listen(timeout=None, phrase_time_limit=None):
    """Listens once and returns recognized text, or empty string if nothing understood."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            return ""

    try:
        query = recognizer.recognize_google(audio)
        print(f"You: {query}")
        return query
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        speak("Speech service is currently unavailable.")
        return ""

def listen_for_wake_word():
    """Quietly listens in short bursts until 'jarvis' is heard. Returns any text spoken after the wake word."""
    print("\n(Waiting for wake word 'Hey Jarvis'...)")
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
                text = recognizer.recognize_google(audio).lower()
                print(f"(heard: {text})")
                if WAKE_WORD in text:
                    remainder = text.split(WAKE_WORD, 1)[1].strip()
                    return remainder
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                continue

def get_llm_response(prompt):
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=f"You are JARVIS, a concise desktop AI assistant. Keep responses under 2 sentences.\nUser: {prompt}"
        )
        return response.text
    except Exception as e:
        print(f"\nAPI Error Details: {e}")
        return "Sorry, I ran into an issue connecting to my brain."

def extract_query(command, trigger_words):
    """Strip out trigger/platform words and return what's left as the search term."""
    text = command
    for word in trigger_words:
        text = text.replace(word, "")
    return text.strip()

def extract_number(command):
    """Pull the first number out of a spoken command, e.g. 'volume to 70' -> 70."""
    match = re.search(r'\d+', command)
    if match:
        return int(match.group())
    return None

def close_application(app_key):
    """Kill the process for a known app. Returns True if attempted."""
    process_name = CLOSE_APPS.get(app_key)
    if process_name:
        os.system(f"taskkill /IM {process_name} /F >nul 2>&1")
        return True
    return False

def get_first_youtube_result(query):
    """Scrapes YouTube search results and returns the first video URL, or None if not found."""
    try:
        search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers, timeout=6)
        video_ids = re.findall(r"\"videoId\":\"(.*?)\"", response.text)
        if video_ids:
            return f"https://www.youtube.com/watch?v={video_ids[0]}"
        return None
    except Exception as e:
        print(f"\nYouTube Search Error: {e}")
        return None

def get_first_spotify_track(query):
    """Best-effort scrape for a Spotify track link. Spotify's search page is JS-rendered,
    so this often won't find anything — that's expected, not a bug."""
    try:
        search_url = "https://open.spotify.com/search/" + urllib.parse.quote(query)
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers, timeout=6)
        track_ids = re.findall(r"open\.spotify\.com/track/([a-zA-Z0-9]+)", response.text)
        if track_ids:
            return f"https://open.spotify.com/track/{track_ids[0]}"
        return None
    except Exception as e:
        print(f"\nSpotify Search Error: {e}")
        return None

# --- Date & time functions ---
def get_current_time():
    now = datetime.now()
    return f"The current time is {now.strftime('%I:%M %p')}, sir."

def get_today_date():
    now = datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}, sir."

def get_today_day():
    now = datetime.now()
    return f"Today is {now.strftime('%A')}, sir."

def get_tomorrow_day():
    tomorrow = datetime.now() + timedelta(days=1)
    return f"Tomorrow is {tomorrow.strftime('%A')}, sir."

# --- Weather ---
def get_weather():
    try:
        loc_response = requests.get("http://ip-api.com/json/", timeout=5).json()
        city = loc_response.get("city", "your area")
        lat = loc_response.get("lat")
        lon = loc_response.get("lon")

        if lat is None or lon is None:
            return "I couldn't detect your location, sir."

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
        )
        weather_response = requests.get(weather_url, timeout=5).json()
        current = weather_response.get("current", {})
        temp = current.get("temperature_2m")
        code = current.get("weather_code")
        condition = WEATHER_CODES.get(code, "unclear conditions")

        return f"It's currently {temp} degrees Celsius in {city}, with {condition}, sir."
    except Exception as e:
        print(f"\nWeather Error Details: {e}")
        return "Sorry, I couldn't fetch the weather right now, sir."

# --- Small talk ---
SMALL_TALK = {
    "how are you": [
        "I'm functioning at full capacity, sir. Thank you for asking. How can I help?",
        "All systems running smoothly, sir. What can I do for you?",
    ],
    "who are you": [
        "I'm JARVIS, your personal desktop assistant, sir.",
    ],
    "what is your name": [
        "You can call me JARVIS, sir.",
    ],
    "thank you": [
        "Anytime, sir.",
        "Happy to help, sir.",
    ],
    "thanks": [
        "You're welcome, sir.",
    ],
    "good morning": [
        "Good morning, sir. Hope you slept well.",
    ],
    "good night": [
        "Good night, sir. I'll be here whenever you need me.",
    ],
    "i love you": [
        "That's kind of you to say, sir. I'm just doing my job.",
    ],
    "what can you do": [
        "I can open and close apps and websites, play music or videos, check your battery, CPU, RAM, control your volume, lock your screen, tell you the time, date, and weather, and chat with you, sir.",
    ],
}

def check_small_talk(command):
    for phrase, responses in SMALL_TALK.items():
        if phrase in command:
            return random.choice(responses)
    return None

# --- Volume control (exact percentage) ---
def get_volume_interface():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))

def set_volume(percent):
    percent = max(0, min(100, percent))
    volume = get_volume_interface()
    volume.SetMasterVolumeLevelScalar(percent / 100, None)

def get_volume():
    volume = get_volume_interface()
    return round(volume.GetMasterVolumeLevelScalar() * 100)

# --- System control functions ---
def get_battery_status():
    battery = psutil.sensors_battery()
    if battery is None:
        return "I couldn't detect a battery on this system, sir. It might be a desktop."
    percent = battery.percent
    plugged = battery.power_plugged
    status = "and it's currently charging" if plugged else "and it's running on battery"
    return f"Your battery is at {percent} percent, {status}, sir."

def get_cpu_usage():
    usage = psutil.cpu_percent(interval=1)
    return f"CPU usage is currently at {usage} percent, sir."

def get_ram_usage():
    ram = psutil.virtual_memory()
    return f"RAM usage is at {ram.percent} percent, sir. {round(ram.used / (1024**3), 1)} gigabytes used out of {round(ram.total / (1024**3), 1)} gigabytes."

def lock_screen():
    os.system("rundll32.exe user32.dll,LockWorkStation")

def handle_command(user_input):
    command = user_input.lower()

    small_talk_reply = check_small_talk(command)
    if small_talk_reply:
        speak(small_talk_reply)
        return

    # --- Close app commands (checked first) ---
    if "close" in command or ("stop" in command and any(app in command for app in CLOSE_APPS)):
        matched_app = None
        for app_key in CLOSE_APPS:
            if app_key in command:
                matched_app = app_key
                break
        if matched_app:
            closed = close_application(matched_app)
            if closed:
                speak(f"Closing {matched_app} now, sir. Task done.")
            return

    # --- General web search: "search X on google/chrome" ---
    if "search" in command and ("google" in command or "chrome" in command) and "youtube" not in command and "spotify" not in command:
        query = extract_query(command, ["search", "on google", "google", "on chrome", "chrome", "for me", "please"])
        if query:
            speak(f"Searching for {query} on Google now, sir. Task done.")
            search_url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
            webbrowser.open(search_url)
        else:
            speak("What would you like me to search for, sir?")
        return

    if "weather" in command:
        speak(get_weather())

    elif "time" in command:
        speak(get_current_time())

    elif "tomorrow" in command and "day" in command:
        speak(get_tomorrow_day())

    elif "what day" in command or "which day" in command:
        speak(get_today_day())

    elif "date" in command:
        speak(get_today_date())

    elif "volume" in command and ("increase" in command or "reduce" in command or "decrease" in command or "set" in command or "to" in command):
        number = extract_number(command)
        if number is not None:
            set_volume(number)
            speak(f"Volume set to {number} percent, sir. Task done.")
        elif "up" in command or "increase" in command:
            pyautogui.press("volumeup", presses=5)
            speak(f"Volume increased. It's now at {get_volume()} percent, sir. Task done.")
        elif "down" in command or "decrease" in command or "reduce" in command:
            pyautogui.press("volumedown", presses=5)
            speak(f"Volume decreased. It's now at {get_volume()} percent, sir. Task done.")
        else:
            speak(f"Current volume is {get_volume()} percent, sir.")

    elif "mute" in command:
        pyautogui.press("volumemute")
        speak("Audio muted, sir. Task done.")

    elif "battery" in command:
        speak(get_battery_status())

    elif "cpu" in command or "processor" in command:
        speak(get_cpu_usage())

    elif "ram" in command or "memory" in command:
        speak(get_ram_usage())

    elif "lock" in command and "screen" in command:
        speak("Locking the screen now, sir. Task done.")
        lock_screen()

    elif "youtube" in command:
        if "play" in command or "search" in command:
            query = extract_query(command, ["play", "search", "on youtube", "youtube", "for me", "please"])
            if query:
                video_url = get_first_youtube_result(query)
                if video_url:
                    speak(f"Playing {query} on YouTube now, sir. Task done.")
                    webbrowser.open(video_url)
                else:
                    speak("I couldn't find that on YouTube, sir. Opening search results instead.")
                    search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
                    webbrowser.open(search_url)
            else:
                speak("Opening YouTube now, sir. Task done.")
                webbrowser.open("https://youtube.com")
        else:
            speak("Opening YouTube now, sir. Task done.")
            webbrowser.open("https://youtube.com")

    elif "spotify" in command:
        if "play" in command or "search" in command:
            query = extract_query(command, ["play", "search", "on spotify", "spotify", "for me", "please"])
            if query:
                track_url = get_first_spotify_track(query)
                if track_url:
                    speak(f"Playing {query} on Spotify now, sir. Task done.")
                    webbrowser.open(track_url)
                else:
                    speak(f"I couldn't auto-play that on Spotify, sir. Opening search results instead.")
                    search_url = "https://open.spotify.com/search/" + urllib.parse.quote(query)
                    webbrowser.open(search_url)
            else:
                speak("Opening Spotify now, sir. Task done.")
                try:
                    os.startfile("spotify")
                except Exception:
                    webbrowser.open("https://open.spotify.com")
        else:
            speak("Opening Spotify now, sir. Task done.")
            try:
                os.startfile("spotify")
            except Exception:
                webbrowser.open("https://open.spotify.com")

    elif "google" in command and "chrome" not in command:
        speak("Opening Google now, sir. Task done.")
        webbrowser.open("https://google.com")

    elif "chrome" in command:
        speak("Opening Chrome now, sir. Task done.")
        os.startfile("chrome")

    elif "notepad" in command:
        speak("Opening Notepad now, sir. Task done.")
        os.startfile("notepad")

    elif "calculator" in command:
        speak("Opening Calculator now, sir. Task done.")
        os.startfile("calc")

    elif "vs code" in command or "visual studio code" in command:
        speak("Opening VS Code now, sir. Task done.")
        os.startfile("code")

    elif "file explorer" in command or "files" in command:
        speak("Opening File Explorer now, sir. Task done.")
        os.startfile("explorer")

    elif "whatsapp" in command:
        speak("Opening WhatsApp now, sir. Task done.")
        webbrowser.open("https://web.whatsapp.com")

    elif "gmail" in command or "email" in command:
        speak("Opening Gmail now, sir. Task done.")
        webbrowser.open("https://mail.google.com")

    elif "instagram" in command:
        speak("Opening Instagram now, sir. Task done.")
        webbrowser.open("https://instagram.com")

    else:
        reply = get_llm_response(user_input)
        speak(reply)

if __name__ == "__main__":
    speak("JARVIS system online. Say 'Hey Jarvis' to wake me up.")
    while True:
        remainder = listen_for_wake_word()

        if remainder:
            user_input = remainder
        else:
            speak("Yes, sir?")
            user_input = listen()

        if not user_input:
            speak("I didn't catch that, sir.")
            continue

        command_lower = user_input.lower()
        mentions_known_app = any(app in command_lower for app in CLOSE_APPS)

        stop_words = ["exit", "quit", "shutdown"]
        bare_stop_words = ["close", "stop", "bye", "sleep"]

        if any(word in command_lower for word in stop_words) or (
            any(word in command_lower for word in bare_stop_words) and not mentions_known_app
        ):
            speak("Shutting down systems. Goodbye!")
            break

        handle_command(user_input)