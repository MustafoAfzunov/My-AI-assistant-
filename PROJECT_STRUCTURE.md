# Project Structure Guide

This document provides a detailed overview of the project's file organization and the purpose of each component.

## Directory Tree

```
audio-main/
├── 📄 app.py                           # FastAPI WebSocket server (main entry point)
├── 📄 test.py                          # AudioProcessor class (core orchestrator)
├── 📄 requirements.txt                 # Python dependencies
├── 📄 index.html                       # Frontend web interface
├── 📄 .env                            # Environment variables (not in repo)
├── 📄 attention_mechanism.py          # Attention signaling for graph nodes
├── 📄 notes_processor.py              # Batch processing for note generation
│
├── 📁 OpenAIClients/                  # AI service integrations
│   ├── 📄 base_generator.py           # Abstract base class for generators
│   ├── 📄 regular_response_generator.py  # Main conversational AI handler
│   ├── 📄 code_generator.py           # Code generation service
│   ├── 📄 graph_generator.py          # Mind map/concept map generator
│   └── 📄 notes_generator.py          # Automated note-taking service
│
├── 📁 VoiceHandlers/                  # Audio processing modules
│   ├── 📄 stt_handler.py              # Speech-to-Text (Google Cloud)
│   ├── 📄 tts_handler.py              # Text-to-Speech (Google Cloud)
│   ├── 📄 state_manager.py            # Conversation state machine
│   └── 📄 interruption.py             # Interruption detection/handling
│
├── 📁 PromptHandlers/                 # Prompt management
│   └── 📄 regular_response_prompt_handler.py  # Dynamic prompt construction
│
├── 📁 ContextHandlers/                # Context management
│   └── 📄 context_manager.py          # Context storage and retrieval
│
├── 📁 voiceCashingSys/                # Voice caching system
│   ├── 📁 contextBased/               # Context-specific audio files
│   │   └── *.mp3                      # Pre-generated responses
│   ├── 📁 random/                     # Random filler sounds
│   │   ├── Hmm_let_me_think.mp3
│   │   ├── So.mp3
│   │   ├── Umm_well_well_well.mp3
│   │   └── You_know.mp3
│   └── 📄 voiceCashingSys.py          # Voice caching logic
│
├── 📁 temp/                           # Temporary files
│   └── 📁 tts_output/                 # Generated TTS audio cache
│       └── tts_*.mp3                  # Cached audio files
│
├── 📁 audio_debug/                    # Debug audio recordings
│   └── audio_chunk_*.wav              # Raw audio chunks for debugging
│
├── 📁 recordings/                     # User audio recordings
│   └── test_recording.wav
│
├── 📁 ai_responses/                   # AI-generated audio responses
│   └── latest_response.mp3
│
├── 📄 beaming-source-*.json           # Google Cloud credentials
├── 📄 client_secret_*.json            # OAuth credentials
├── 📄 quadKey.json                    # Additional API keys
├── 📄 interruption.mp3                # Interruption acknowledgment sound
└── 📄 todo.txt                        # Development notes and TODOs
```

## Core Files

### Entry Points

#### `app.py` - WebSocket Server
**Purpose**: FastAPI server that handles WebSocket connections from clients.

**Key Components**:
- `WebSocketAudioProcessor`: Manages client connections and routes data
- `/ws/{client_id}`: Audio/control WebSocket endpoint
- `/ws/text/{client_id}`: Text data WebSocket endpoint

**When to modify**: 
- Adding new WebSocket endpoints
- Changing CORS settings
- Modifying connection handling logic

#### `test.py` - Audio Processor
**Purpose**: Core orchestrator that coordinates all system components.

**Key Components**:
- `AudioProcessor`: Main class that ties everything together
- Audio pipeline management
- State transitions
- AI response processing
- Thread coordination

**When to modify**:
- Changing processing delays
- Adjusting audio settings
- Modifying AI interaction flow
- Adding new processing steps

### Configuration Files

#### `requirements.txt`
**Purpose**: Lists all Python package dependencies.

**Key Dependencies**:
- `sounddevice`: Audio I/O
- `google-cloud-speech`: STT API
- `google-cloud-texttospeech`: TTS API
- `openai`: GPT API
- `fastapi`: Web framework
- `pygame`: Audio playback

#### `.env` (Not in repository)
**Purpose**: Stores sensitive environment variables.

**Required Variables**:
```bash
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS=./path-to-credentials.json
```

## Module Breakdown

### OpenAIClients/

This directory contains all AI service integrations.

#### `base_generator.py`
**Purpose**: Abstract base class for all content generators.

**Provides**:
- OpenAI client initialization
- Dynamic prompt construction
- Request handling with error management
- Context integration

**Inheritance**: Extended by `CodeGenerator` and `GraphGenerator`

#### `regular_response_generator.py`
**Purpose**: Main conversational AI handler.

**Key Features**:
- Streaming response generation
- Conversation memory management (configurable limit)
- Sentence completion analysis
- Context integration

**Classes**:
- `OpenAIService`: Main service class
- `ChatConfig`: Chat configuration dataclass
- `AnalysisConfig`: Analysis configuration dataclass

#### `code_generator.py`
**Purpose**: Generates code snippets from natural language.

**Process**:
1. Receives generation request with context
2. Constructs prompt with relevant information
3. Generates code using GPT-4
4. Strips markdown formatting
5. Sends pure code via WebSocket

**Trigger Format**:
```json
{"operation": "GENERATE_CODE", "details": {...}}
```

#### `graph_generator.py`
**Purpose**: Creates visual concept maps and mind maps.

**Output**: JSON structure with nodes and connections

**Features**:
- 10-15 nodes with logical relationships
- Automatic layout (500-600px spacing)
- Valid connection rules
- Hierarchical organization

#### `notes_generator.py`
**Purpose**: Extracts key concepts from conversations.

**Features**:
- Batch processing (2 sentences at a time)
- Filters conversational fluff
- Highlights new concepts
- Teacher-style formatting

### VoiceHandlers/

This directory handles all audio processing.

#### `stt_handler.py`
**Purpose**: Converts speech to text using Google Cloud STT.

**Key Features**:
- Streaming recognition
- Interim results
- Automatic punctuation
- Thread-safe audio queue
- Stream reset capability

**Callbacks**:
- `partial_transcript_callback`: Called for interim results
- `final_transcript_callback`: Called for final transcripts

#### `tts_handler.py`
**Purpose**: Converts text to speech using Google Cloud TTS.

**Key Features**:
- Streaming text-to-speech
- Multiple emotion presets
- SSML support for prosody control
- WebSocket-based audio streaming
- Sentence-by-sentence generation

**Emotion Presets**:
- happy, sad, excited, calm, angry, fearful, neutral

#### `state_manager.py`
**Purpose**: Manages conversation states and transitions.

**States**:
1. `FULL_LISTENING`: Captures all user speech
2. `INTERRUPT_ONLY`: Monitors for interruptions only

**Features**:
- State transition callbacks
- Text buffer management
- State-specific text handling

#### `interruption.py`
**Purpose**: Detects and handles interruption requests.

**Interrupt Commands**:
- Voice: "stop", "shut up", "end", "silence", etc.
- Keyboard: Backtick (`) key

**Process**:
1. Detect interruption
2. Stop audio playback
3. Play acknowledgment sound
4. Clear all queues
5. Reset state

### PromptHandlers/

#### `regular_response_prompt_handler.py`
**Purpose**: Constructs dynamic prompts for GPT-4.

**Components**:
- `dynamicPrompt`: Dynamic context structure
- `conversation`: Current conversation text
- `LLMPrompt`: Complete message array for GPT

**Message Structure**:
1. System instructions
2. Context information
3. Conversation history
4. Current user input

### ContextHandlers/

#### `context_manager.py`
**Purpose**: Centralized storage for conversation context.

**Storage Types**:
- `graphs`: Visual concept maps
- `code`: Generated code snippets
- `context`: Topic explanations

**Features**:
- Class-level storage (shared across instances)
- Keyword-based retrieval
- Append-to-existing capability

### Supporting Files

#### `attention_mechanism.py`
**Purpose**: Signals attention to specific graph nodes.

**Usage**: Highlights nodes in visual concept maps

#### `notes_processor.py`
**Purpose**: Batch processes sentences for note generation.

**Features**:
- Queue-based processing
- Configurable batch size (default: 2 sentences)
- Thread-safe operation
- Async WebSocket communication

## Data Flow

### Typical Conversation Flow

```
1. User speaks → Microphone
2. Audio data → stt_handler.py
3. Transcript → state_manager.py
4. Complete sentence → test.py (AudioProcessor)
5. Process with context → regular_response_generator.py
6. Stream response → test.py
7. Parse commands (code/graph) → code_generator.py / graph_generator.py
8. Convert to speech → tts_handler.py
9. Stream audio → app.py (WebSocket)
10. Play audio → Client browser
```

### Interruption Flow

```
1. User says "stop" / presses ` → interruption.py
2. Stop playback → tts_handler.py
3. Clear queues → test.py (AudioProcessor)
4. Reset stream → stt_handler.py
5. Play acknowledgment → interruption.py
6. Return to listening → state_manager.py
```

## File Naming Conventions

- **Handlers**: `*_handler.py` - Process specific types of data
- **Generators**: `*_generator.py` - Generate content using AI
- **Managers**: `*_manager.py` - Manage state or resources
- **Processors**: `*_processor.py` - Process data through pipelines

## Configuration Locations

| Setting | File | Variable |
|---------|------|----------|
| STT Config | `test.py` | `self.stt_config` |
| TTS Config | `test.py` | `self.tts_config` |
| Chat Config | `test.py` | `self.chat_config` |
| Voice Name | `test.py` | `TTSConfig.voice_name` |
| Model Name | `test.py` | `ChatConfig.model_name` |
| Memory Limit | `test.py` | `ChatConfig.memory_limit` |
| CORS Origins | `app.py` | `CORSMiddleware` |
| Interrupt Commands | `VoiceHandlers/interruption.py` | `interrupt_commands` |
| System Prompt | `PromptHandlers/regular_response_prompt_handler.py` | `LLMPrompt` |

## Adding New Features

### Adding a New Generator

1. Create new file in `OpenAIClients/`
2. Extend `BaseGenerator` class
3. Define `base_messages` with system instructions
4. Implement generation method
5. Add command parsing in `test.py`
6. Update prompt handler with new operation type

### Adding a New Voice Command

1. Open `VoiceHandlers/interruption.py`
2. Add command to `interrupt_commands` set
3. Test with voice input

### Adding a New Emotion Preset

1. Open `VoiceHandlers/tts_handler.py`
2. Add preset to `emotion_presets` dictionary
3. Define pitch, speaking_rate, and volume_gain_db

### Modifying System Prompt

1. Open `PromptHandlers/regular_response_prompt_handler.py`
2. Edit `LLMPrompt["messages"][0]["content"]`
3. Update instructions for code/graph generation format

## Debugging Tips

### Audio Issues
- Check `audio_debug/` for raw audio chunks
- Verify microphone in `sounddevice.query_devices()`
- Check sample rate matches (16kHz)

### API Issues
- Verify `.env` file exists and is correct
- Check API key validity
- Monitor rate limits

### WebSocket Issues
- Check browser console for errors
- Verify server is running on correct port
- Test with `curl http://localhost:8000`

### State Issues
- Add logging in `state_manager.py`
- Monitor state transitions
- Check callback registration

## Performance Considerations

### Latency Optimization
- Streaming responses reduce perceived latency
- Sentence-level TTS starts speaking immediately
- Memory limits reduce API token usage

### Resource Management
- Conversation history capped at configurable limit
- TTS output cached in `temp/tts_output/`
- Queues are bounded to prevent memory overflow

### Scalability
- Per-client AudioProcessor instances
- Thread pools for background processing
- WebSocket supports multiple concurrent clients

## Security Notes

- API keys stored in environment variables
- Credentials files excluded from version control
- CORS configured (update for production)
- Input validation on WebSocket messages
- Resource limits prevent DoS

## Testing Locations

### Unit Tests
(To be added in future)

### Integration Tests
- Test full conversation flow
- Test interruption handling
- Test code/graph generation
- Test WebSocket connections

### Manual Testing
- Use `index.html` for frontend testing
- Run `python test.py` for standalone testing
- Monitor console output for debugging

