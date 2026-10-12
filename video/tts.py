"""Generate English narration per scene with Gemini TTS. Usage: python3 tts.py scene_id "text" """
import base64, json, os, struct, sys, urllib.request
key = json.load(open(os.path.expanduser('~/.veloce/gemini.json'))).get('api_key') or json.load(open(os.path.expanduser('~/.veloce/gemini.json'))).get('key')
scene, text = sys.argv[1], sys.argv[2]
body = {
    "contents": [{"parts": [{"text": f"Read this in a calm, confident, warm product-demo voice, natural pace: {text}"}]}],
    "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Charon"}}}},
}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={key}",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
resp = json.load(urllib.request.urlopen(req, timeout=180))
pcm = base64.b64decode(resp["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
rate = 24000
with open(f"public/vo/{scene}.wav", "wb") as f:
    f.write(b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16) + b"data" + struct.pack("<I", len(pcm)) + pcm)
print(scene, round(len(pcm) / (rate * 2), 2), "s")
