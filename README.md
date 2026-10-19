# Jarvis - Voice-Controlled Desktop Assistant

A Python terminal-based voice assistant that listens for voice commands and can respond with speech, provide basic system information, open websites/apps, and answer questions using the Google Gemini API.

## Requirements

- Python 3.10+ (a compatible Python version may be required by the audio dependencies)
- A working microphone and speakers
- A Google Gemini API key for AI responses

## Setup (Windows)

1. Install Python.
2. Open Command Prompt in this project folder.
3. Create and activate a virtual environment (optional but recommended):
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   ```
4. Install dependencies:
   ```bat
   pip install -r requirements.txt
   ```
5. Set your Gemini API key in the current Command Prompt session (replace the placeholder with your own key):
   ```bat
   set GEMINI_API_KEY=YOUR_API_KEY_HERE
   ```
6. Run the assistant:
   ```bat
   python jarvis.py
   ```

Do not publish your real API key or commit it to GitHub. The API key is read from the `GEMINI_API_KEY` environment variable.

## Notes

- This project uses speech recognition and text-to-speech, so microphone permissions and audio dependencies matter.
- Some commands control local Windows apps and system settings.
- The project is a command-line/terminal assistant, not a graphical web application.
