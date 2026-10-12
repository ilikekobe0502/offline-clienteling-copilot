"""Synthesise the benchmark memos with Gemini text-to-speech.

Usage: python3 bench/tts.py   (needs a Gemini API key in ~/.veloce/gemini.json and ffmpeg)
Writes bench/<id>.m4a for every case in bench/cases.json.
"""
import base64, json, os, subprocess, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG = os.environ.get("OCC_FFMPEG_BIN", "/opt/homebrew/bin/ffmpeg")
cfg = json.load(open(os.path.expanduser("~/.veloce/gemini.json")))
KEY = cfg.get("api_key") or cfg.get("key")
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key=" + KEY
VOICES = ["Kore", "Charon"]  # alternate a female and a male voice across memos


def speak(text: str, voice: str) -> bytes:
    body = {
        "contents": [{"parts": [{"text": f"用台灣口音的華語，像門市業務剛送走客人、自言自語做筆記一樣，自然口語地唸出來：{text}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}},
    }
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
            data = json.load(urllib.request.urlopen(req, timeout=120))
            return base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except Exception as e:  # rate limits and transient errors
            print(f"  retry {attempt + 1}: {e}")
            time.sleep(10 * (attempt + 1))
    raise RuntimeError("TTS failed")


for i, case in enumerate(json.load(open(os.path.join(HERE, "cases.json")))):
    pcm = speak(case["text"], VOICES[i % 2])
    with tempfile.NamedTemporaryFile(suffix=".pcm") as f:
        f.write(pcm); f.flush()
        out = os.path.join(HERE, f"{case['id']}.m4a")
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", f.name,
                        "-c:a", "aac", "-b:a", "96k", out], check=True)
    print(case["id"], VOICES[i % 2], "ok")
