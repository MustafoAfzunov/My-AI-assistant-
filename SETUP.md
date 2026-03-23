# Setup Guide

This guide will help you set up and run the QUAD FEST Audio AI Tutor system.

## Prerequisites

- Python 3.10 or higher
- Google Cloud Platform account with Speech-to-Text and Text-to-Speech APIs enabled
- OpenAI API account with GPT-4 access
- Microphone and speakers/headphones
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Installation Steps

### 1. Clone the Repository

```bash
cd /path/to/your/projects
git clone <repository-url>
cd audio-main
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `sounddevice` - Audio I/O
- `numpy` - Numerical operations
- `python-dotenv` - Environment variable management
- `google-cloud-speech` - Speech-to-Text API
- `google-cloud-texttospeech` - Text-to-Speech API
- `openai` - OpenAI API client
- `pynput` - Keyboard input handling
- `pygame` - Audio playback
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `websockets` - WebSocket support

### 4. Set Up Google Cloud Credentials

#### Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Cloud Speech-to-Text API
   - Cloud Text-to-Speech API

#### Create Service Account

1. Navigate to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Give it a name (e.g., "audio-tutor-service")
4. Grant roles:
   - Cloud Speech Client
   - Cloud Text-to-Speech Client
5. Click **Create Key** → **JSON**
6. Save the JSON file to your project directory

#### Configure Credentials Path

The project expects credentials at:
```
audio-main/beaming-source-446514-s8-14ddee96f549.json
```

Or you can use a different path and update the `.env` file.

### 5. Set Up OpenAI API

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to **API Keys**
4. Create a new API key
5. Copy the key (you won't be able to see it again!)

### 6. Create Environment File

Create a `.env` file in the project root:

```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=./beaming-source-446514-s8-14ddee96f549.json
```

**Important**: Never commit the `.env` file to version control!

### 7. Verify Audio Devices

Test your microphone and speakers:

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

This will list all available audio devices. Make sure your microphone and speakers are detected.

## Running the Application

### Option 1: WebSocket Server Mode (Recommended)

This mode runs a FastAPI server that clients can connect to via WebSocket.

```bash
# Make sure you're in the project directory and virtual environment is activated
python app.py
```

The server will start on `http://0.0.0.0:8000`

**WebSocket Endpoints:**
- Audio WebSocket: `ws://localhost:8000/ws/{client_id}`
- Text WebSocket: `ws://localhost:8000/ws/text/{client_id}`

### Option 2: Standalone Mode

Run the audio processor directly (for testing):

```bash
python test.py
```

This will start the audio processor in standalone mode without the WebSocket server.

## Using the Frontend

1. Open `index.html` in a web browser
2. Allow microphone access when prompted
3. The system will start listening automatically
4. Speak naturally into your microphone
5. The AI will respond with voice output

## Configuration

### Adjusting Voice Settings

Edit `test.py` to modify TTS configuration:

```python
self.tts_config = TTSConfig(
    language_code="en-US",
    voice_name="en-US-Casual-K",  # Change voice
    speaking_rate=1.0              # Adjust speed (0.25 to 4.0)
)
```

**Available voices:**
- `en-US-Casual-K` - Casual male voice
- `en-US-Neural2-A` - Female voice
- `en-US-Neural2-C` - Female voice
- `en-US-Neural2-D` - Male voice
- `en-US-Neural2-F` - Female voice

[Full list of voices](https://cloud.google.com/text-to-speech/docs/voices)

### Adjusting AI Model

Edit `test.py` to change the AI model:

```python
self.chat_config = ChatConfig(
    model_name="gpt-4",      # or "gpt-4-turbo", "gpt-3.5-turbo"
    temperature=0.7,         # Creativity (0.0 to 2.0)
    memory_limit=10          # Conversation history turns
)
```

### Adjusting Speech Recognition

Edit `test.py` to modify STT configuration:

```python
self.stt_config = STTConfig(
    language_code="en-US",        # Change language
    enable_interim=True,          # Show partial results
    enable_punctuation=True       # Auto-punctuation
)
```

**Supported languages:**
- `en-US` - English (US)
- `en-GB` - English (UK)
- `es-ES` - Spanish (Spain)
- `fr-FR` - French (France)
- `de-DE` - German (Germany)

[Full list of languages](https://cloud.google.com/speech-to-text/docs/languages)

## Testing the Setup

### Test 1: Basic Conversation

1. Start the server: `python app.py`
2. Open the frontend in a browser
3. Say: "Hello, how are you?"
4. The AI should respond with voice

### Test 2: Code Generation

Say: "Generate code for a binary search algorithm"

The system should:
1. Respond verbally acknowledging the request
2. Send generated code to the frontend

### Test 3: Graph Generation

Say: "Create a graph about machine learning concepts"

The system should:
1. Respond verbally
2. Generate and send a visual concept map

### Test 4: Interruption

1. Start a conversation
2. While the AI is speaking, say "stop" or press the backtick (`) key
3. The AI should immediately stop and acknowledge

## Troubleshooting

### Issue: "GOOGLE_APPLICATION_CREDENTIALS not set"

**Solution**: Make sure your `.env` file exists and contains the correct path to your Google Cloud credentials JSON file.

```bash
# Check if .env file exists
ls -la .env

# Verify contents
cat .env
```

### Issue: "OpenAI API key not found"

**Solution**: Verify your `.env` file contains the OpenAI API key:

```bash
OPENAI_API_KEY=sk-...
```

### Issue: No audio input detected

**Solution**: 
1. Check microphone permissions in your browser
2. Verify microphone is working: `python -c "import sounddevice as sd; print(sd.query_devices())"`
3. Try specifying a device explicitly in `test.py`:

```python
with sd.InputStream(callback=self.audio_callback,
                   channels=1,
                   samplerate=16000,
                   dtype=np.int16,
                   device=YOUR_DEVICE_INDEX):  # Add device index
```

### Issue: "pygame mixer error"

**Solution**: Install pygame audio dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install python3-pygame

# Mac
brew install sdl sdl_mixer

# Then reinstall pygame
pip install --force-reinstall pygame
```

### Issue: WebSocket connection fails

**Solution**:
1. Check if server is running: `curl http://localhost:8000`
2. Check firewall settings
3. Try using `127.0.0.1` instead of `localhost`
4. Check browser console for errors

### Issue: High latency in responses

**Solution**:
1. Use a faster model: `model_name="gpt-3.5-turbo"`
2. Reduce audio buffer size in `test.py`
3. Check internet connection speed
4. Consider using a local AI model

### Issue: "Rate limit exceeded" errors

**Solution**:
1. Check your OpenAI API usage limits
2. Add rate limiting in the code
3. Upgrade your OpenAI plan

## Performance Optimization

### For Better Latency

1. **Use GPT-3.5-turbo** instead of GPT-4 for faster responses
2. **Reduce memory_limit** to send fewer messages to the API
3. **Increase speaking_rate** in TTS config for faster speech
4. **Use local audio processing** instead of streaming when possible

### For Better Quality

1. **Use GPT-4** for more accurate responses
2. **Increase temperature** for more creative responses
3. **Use Neural2 voices** for more natural speech
4. **Enable enhanced models** in STT config

## Development Tips

### Debugging Audio Issues

Enable debug logging in `test.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Audio chunks are saved to `audio_debug/` directory for inspection.

### Testing Without Audio

You can test the AI processing without audio by directly calling:

```python
processor = AudioProcessor()
processor.handle_final("Your test text here")
```

### Monitoring WebSocket Connections

Use browser developer tools:
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "WS" (WebSocket)
4. Monitor messages in real-time

## Production Deployment

### Security Checklist

- [ ] Update CORS settings in `app.py` to allow only specific origins
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS/WSS for encrypted communication
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Set up monitoring and logging
- [ ] Configure firewall rules

### Recommended Setup

1. **Use a reverse proxy** (nginx/Apache) for SSL termination
2. **Deploy with Docker** for consistency
3. **Use a process manager** (systemd/supervisor) for auto-restart
4. **Set up monitoring** (Prometheus/Grafana)
5. **Implement logging** (ELK stack or similar)

### Example nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Getting Help

If you encounter issues:

1. Check the [ARCHITECTURE.md](ARCHITECTURE.md) for system details
2. Review logs in the console output
3. Check the `audio_debug/` directory for audio issues
4. Verify all API keys and credentials are correct
5. Ensure all dependencies are installed correctly

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- Review [API_REFERENCE.md](API_REFERENCE.md) for API details
- Customize the system prompt in `PromptHandlers/regular_response_prompt_handler.py`
- Add custom voice commands in `VoiceHandlers/interruption.py`
- Extend functionality by creating new generators in `OpenAIClients/`

