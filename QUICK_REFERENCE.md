# Quick Reference Guide

Fast lookup for common tasks and configurations.

## 🚀 Quick Start

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
echo "OPENAI_API_KEY=your_key" > .env
echo "GOOGLE_APPLICATION_CREDENTIALS=./credentials.json" >> .env

# Run
python app.py
```

## 📁 File Locations

| What | Where |
|------|-------|
| Main server | `app.py` |
| Core processor | `test.py` |
| STT handler | `VoiceHandlers/stt_handler.py` |
| TTS handler | `VoiceHandlers/tts_handler.py` |
| AI service | `OpenAIClients/regular_response_generator.py` |
| Context storage | `ContextHandlers/context_manager.py` |
| State manager | `VoiceHandlers/state_manager.py` |
| Prompts | `PromptHandlers/regular_response_prompt_handler.py` |

## ⚙️ Configuration Quick Access

### Change AI Model
**File**: `test.py`
```python
self.chat_config = ChatConfig(
    model_name="gpt-4",  # or "gpt-3.5-turbo"
    temperature=0.7
)
```

### Change Voice
**File**: `test.py`
```python
self.tts_config = TTSConfig(
    voice_name="en-US-Casual-K"  # See voice list below
)
```

### Change Language
**File**: `test.py`
```python
self.stt_config = STTConfig(
    language_code="en-US"  # See language codes below
)
```

### Adjust Processing Delay
**File**: `test.py`, method `handle_final`
```python
self.process_after_delay(text, 0.5)  # seconds
```

### Change Memory Limit
**File**: `test.py`
```python
self.chat_config = ChatConfig(
    memory_limit=10  # number of conversation turns
)
```

## 🎤 Voice Settings

### Available Voices

| Voice Name | Gender | Style |
|------------|--------|-------|
| `en-US-Casual-K` | Male | Casual |
| `en-US-Neural2-A` | Male | Standard |
| `en-US-Neural2-C` | Female | Standard |
| `en-US-Neural2-D` | Male | Standard |
| `en-US-Neural2-F` | Female | Standard |
| `en-US-Neural2-J` | Male | Standard |
| `en-US-Studio-M` | Male | Studio |
| `en-US-Studio-O` | Female | Studio |

[Full voice list](https://cloud.google.com/text-to-speech/docs/voices)

### Emotion Presets

| Emotion | Pitch | Speed | Volume |
|---------|-------|-------|--------|
| `happy` | +2.0 | 1.2x | +2.0 dB |
| `sad` | -2.0 | 0.85x | -1.0 dB |
| `excited` | +4.0 | 1.0x | +3.5 dB |
| `calm` | -1.0 | 0.9x | 0.0 dB |
| `angry` | 0.0 | 1.1x | +4.0 dB |
| `fearful` | +3.0 | 1.25x | +1.0 dB |
| `neutral` | 0.0 | 1.0x | 0.0 dB |

**Location**: `VoiceHandlers/tts_handler.py`

## 🌍 Language Codes

| Language | Code |
|----------|------|
| English (US) | `en-US` |
| English (UK) | `en-GB` |
| Spanish (Spain) | `es-ES` |
| Spanish (Mexico) | `es-MX` |
| French (France) | `fr-FR` |
| German (Germany) | `de-DE` |
| Italian (Italy) | `it-IT` |
| Portuguese (Brazil) | `pt-BR` |
| Japanese | `ja-JP` |
| Korean | `ko-KR` |
| Chinese (Mandarin) | `zh-CN` |

[Full language list](https://cloud.google.com/speech-to-text/docs/languages)

## 🎮 Voice Commands

### Interruption Commands

Say any of these during AI response:
- "stop"
- "shut up"
- "end"
- "silence"
- "pause"
- "please stop"
- "okay stop"
- "can you stop"

Or press: **`** (backtick key)

**Location**: `VoiceHandlers/interruption.py`

### Special Commands

| Say this | What happens |
|----------|--------------|
| "Generate code for [task]" | Creates code snippet |
| "Create a graph about [topic]" | Generates concept map |
| Any question | Gets AI response |

## 🔌 WebSocket API

### Endpoints

```
ws://localhost:8000/ws/{client_id}           # Audio + control
ws://localhost:8000/ws/text/{client_id}      # Text data
```

### Send Messages

```javascript
// Audio data
ws.send(JSON.stringify({
    type: "audio",
    data: base64_audio
}));

// Interrupt
ws.send(JSON.stringify({
    type: "interrupt"
}));

// Playback complete
ws.send(JSON.stringify({
    type: "playback_complete"
}));
```

### Receive Messages

```javascript
ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
        // Audio data (MP3)
    } else {
        const msg = JSON.parse(event.data);
        switch(msg.operation) {
            case "NOTES": // Notes generated
            case "CODE_GENERATION": // Code generated
            case "GRAPH": // Graph generated
        }
    }
};
```

## 🐛 Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Audio Devices

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Test STT

```python
from VoiceHandlers.stt_handler import SpeechToTextHandler, STTConfig

handler = SpeechToTextHandler(STTConfig())
handler.final_transcript_callback = lambda t: print(f"Got: {t}")
handler.start_recognition()
```

### Test TTS

```python
from VoiceHandlers.tts_handler import TextToSpeechHandler, TTSConfig
import queue

handler = TextToSpeechHandler(TTSConfig())
q = queue.Queue()
q.put("Hello, world!")
q.put("END")
handler.stream_text_to_speech(q)
```

### View Logs

```bash
# Server logs
python app.py 2>&1 | tee server.log

# Filter errors only
python app.py 2>&1 | grep -i error
```

## 📊 Performance Tuning

### Reduce Latency

```python
# Use faster model
model_name="gpt-3.5-turbo"

# Reduce memory
memory_limit=5

# Faster speech
speaking_rate=1.2
```

### Improve Quality

```python
# Better model
model_name="gpt-4"

# More context
memory_limit=15

# Natural speech
speaking_rate=1.0
voice_name="en-US-Neural2-C"
```

### Save Costs

```python
# Cheaper model
model_name="gpt-3.5-turbo"

# Less memory = fewer tokens
memory_limit=5

# Shorter responses
temperature=0.5  # More focused
```

## 🔐 Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=./path/to/credentials.json

# Optional
LOG_LEVEL=INFO
MAX_CONNECTIONS=10
PORT=8000
```

## 📝 Common Code Snippets

### Add New Interrupt Command

```python
# VoiceHandlers/interruption.py
self.interrupt_commands = {
    "stop", "end", "shut up",
    "your new command"  # Add here
}
```

### Add New Emotion

```python
# VoiceHandlers/tts_handler.py
self.emotion_presets = {
    "your_emotion": {
        "pitch": 2.0,
        "speaking_rate": 1.1,
        "volume_gain_db": 1.5
    }
}
```

### Modify System Prompt

```python
# PromptHandlers/regular_response_prompt_handler.py
LLMPrompt = {
    "messages": [
        {
            "role": "system",
            "content": "Your new instructions here..."
        }
    ]
}
```

### Change Processing Delays

```python
# test.py
def handle_final(self, text: str):
    self.process_after_delay(text, 0.5)  # Change this
```

## 🔄 State Machine

```
┌─────────────────┐
│ FULL_LISTENING  │ ◄─── Default state
└────────┬────────┘
         │ Sentence complete
         ▼
┌─────────────────┐
│ INTERRUPT_ONLY  │ ◄─── During AI response
└────────┬────────┘
         │ Response done / Interrupted
         ▼
┌─────────────────┐
│ FULL_LISTENING  │
└─────────────────┘
```

## 📦 Dependencies

```bash
# Core
sounddevice      # Audio I/O
numpy           # Array operations
fastapi         # Web framework
uvicorn         # ASGI server

# AI Services
openai          # GPT API
google-cloud-speech  # STT
google-cloud-texttospeech  # TTS

# Audio
pygame          # Audio playback
pynput          # Keyboard input

# Utilities
python-dotenv   # Environment variables
websockets      # WebSocket support
```

## 🚨 Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `OPENAI_API_KEY not set` | Missing API key | Add to `.env` |
| `GOOGLE_APPLICATION_CREDENTIALS not set` | Missing credentials | Add to `.env` |
| `Connection refused` | Server not running | Start with `python app.py` |
| `Rate limit exceeded` | Too many API calls | Wait or upgrade plan |
| `Audio device not found` | No microphone | Check device settings |
| `WebSocket closed` | Connection lost | Check network/server |

## 📞 Quick Help

| Issue | Check |
|-------|-------|
| No audio input | Microphone permissions, device list |
| No audio output | Speaker settings, pygame init |
| Slow responses | Model choice, internet speed |
| High costs | Memory limit, model choice |
| Crashes | Logs, error messages |
| Wrong transcription | Language code, audio quality |

## 🔗 Useful Links

- [OpenAI API Docs](https://platform.openai.com/docs)
- [Google Cloud Speech](https://cloud.google.com/speech-to-text/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## 💡 Tips

1. **Test locally first** before deploying
2. **Monitor API usage** to control costs
3. **Use .gitignore** for credentials
4. **Log important events** for debugging
5. **Handle errors gracefully** for better UX
6. **Keep memory limit reasonable** (5-15 turns)
7. **Use appropriate model** (GPT-3.5 for speed, GPT-4 for quality)
8. **Cache TTS output** when possible
9. **Clean up resources** on disconnect
10. **Test with multiple clients** before production

## 🎯 Performance Benchmarks

| Metric | Target | Typical |
|--------|--------|---------|
| STT Latency | < 500ms | 200-400ms |
| TTS Latency | < 1s | 500-800ms |
| AI Response Time | < 3s | 2-5s |
| Total Round Trip | < 5s | 3-7s |
| Memory Usage | < 500MB | 200-400MB |
| Concurrent Users | 10+ | Depends on hardware |

---

**Need more details?** See:
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [SETUP.md](SETUP.md) - Installation guide
- [API_REFERENCE.md](API_REFERENCE.md) - Complete API docs
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide

