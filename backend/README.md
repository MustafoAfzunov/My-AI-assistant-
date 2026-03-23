# Backend - Digital Classroom AI System

This directory contains the backend server and AI processing logic for the Digital Classroom project.

## Overview

The backend handles:
- Real-time voice processing (Speech-to-Text and Text-to-Speech)
- AI conversation management using GPT-4
- Code generation from natural language
- Concept map/graph generation
- Automated note-taking
- WebSocket communication with frontend clients

## Quick Start

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create .env file with:
# OPENAI_API_KEY=your_key
# GOOGLE_APPLICATION_CREDENTIALS=../path/to/credentials.json

# Run the server
python app.py
```

Server will start on `http://0.0.0.0:8000`

## Project Structure

```
backend/
├── app.py                          # FastAPI WebSocket server
├── test.py                         # Core AudioProcessor
├── requirements.txt                # Python dependencies
│
├── OpenAIClients/                  # AI service integrations
│   ├── regular_response_generator.py
│   ├── code_generator.py
│   ├── graph_generator.py
│   └── notes_generator.py
│
├── VoiceHandlers/                  # Audio processing
│   ├── stt_handler.py             # Speech-to-Text
│   ├── tts_handler.py             # Text-to-Speech
│   ├── state_manager.py           # Conversation state
│   └── interruption.py            # Interruption handling
│
├── ContextHandlers/                # Context management
│   └── context_manager.py
│
├── PromptHandlers/                 # Prompt construction
│   └── regular_response_prompt_handler.py
│
└── voiceCashingSys/               # Voice caching
    └── random/                    # Filler sounds
```

## API Endpoints

### WebSocket Endpoints

- `ws://localhost:8000/ws/{client_id}` - Main audio/control WebSocket
- `ws://localhost:8000/ws/text/{client_id}` - Text data WebSocket

## Configuration

Edit `test.py` to configure:

```python
# AI Model
self.chat_config = ChatConfig(
    model_name="gpt-4",  # or "gpt-3.5-turbo"
    temperature=0.7,
    memory_limit=10
)

# Text-to-Speech
self.tts_config = TTSConfig(
    voice_name="en-US-Casual-K",
    speaking_rate=1.0
)

# Speech-to-Text
self.stt_config = STTConfig(
    language_code="en-US",
    enable_interim=True
)
```

## Dependencies

See `requirements.txt` for complete list:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `openai` - GPT API
- `google-cloud-speech` - STT
- `google-cloud-texttospeech` - TTS
- `sounddevice` - Audio I/O
- `numpy` - Array operations
- `pygame` - Audio playback

## Documentation

For complete documentation, see the root directory:
- `../README.md` - Project overview
- `../ARCHITECTURE.md` - System design
- `../SETUP.md` - Installation guide
- `../API_REFERENCE.md` - API documentation

## Development

Run in development mode:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Testing

```bash
# Test the server
python test.py
```

## Troubleshooting

See `../SETUP.md#troubleshooting` for common issues.

## License

See root directory for license information.

