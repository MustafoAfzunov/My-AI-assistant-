# System Architecture

## Overview

The QUAD FEST Audio AI Tutor is built on a multi-layered architecture that handles real-time voice interactions, AI processing, and content generation through a sophisticated state machine and WebSocket-based communication system.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Browser)                    │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │  Audio Stream   │              │  Text Display   │      │
│  │   WebSocket     │              │   WebSocket     │      │
│  └────────┬────────┘              └────────┬────────┘      │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server (app.py)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         WebSocketAudioProcessor                       │  │
│  │  - Manages client connections                         │  │
│  │  - Routes audio/text data                            │  │
│  │  - Handles interruptions                             │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────┬──────────────────────────────────┬──────────────┘
            │                                  │
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 AudioProcessor (test.py)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ STT Handler  │  │ State Manager│  │ TTS Handler  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│                  ┌──────────────────┐                       │
│                  │  AI Processing   │                       │
│                  │   - GPT-4        │                       │
│                  │   - Context Mgmt │                       │
│                  └────────┬─────────┘                       │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         ▼                 ▼                 ▼               │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│  │   Code   │     │  Graph   │     │  Notes   │           │
│  │Generator │     │Generator │     │Generator │           │
│  └──────────┘     └──────────┘     └──────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. FastAPI Server (`app.py`)

**Purpose**: Manages WebSocket connections and routes data between clients and processors.

**Key Classes**:
- `WebSocketAudioProcessor`: Central hub for managing client connections and data flow

**Responsibilities**:
- Accept and manage WebSocket connections (audio + text)
- Route audio data to AudioProcessor instances
- Handle client disconnections and cleanup
- Process interruption signals
- Send generated audio back to clients

**WebSocket Endpoints**:
- `/ws/{client_id}` - Main audio/control WebSocket
- `/ws/text/{client_id}` - Text data WebSocket for notes, code, graphs

### 2. AudioProcessor (`test.py`)

**Purpose**: Core orchestrator that coordinates all voice processing, AI interactions, and content generation.

**Key Components**:

#### State Management
- Maintains conversation state (FULL_LISTENING vs INTERRUPT_ONLY)
- Coordinates transitions between states
- Manages text buffers for each state

#### Audio Pipeline
```
Microphone Input → STT Handler → State Manager → AI Processing → TTS Handler → Audio Output
                                       ↓
                              Interruption Handler
```

#### Processing Flow
1. **Audio Capture**: Continuous audio stream from microphone
2. **Speech Recognition**: Real-time transcription via Google Cloud STT
3. **Sentence Analysis**: Determines if speech is complete
4. **AI Processing**: Sends complete thoughts to GPT-4
5. **Response Generation**: Streams AI response in chunks
6. **Speech Synthesis**: Converts text chunks to audio
7. **Playback**: Streams audio to client

### 3. Voice Handlers

#### STT Handler (`VoiceHandlers/stt_handler.py`)

**Purpose**: Converts speech to text using Google Cloud Speech-to-Text API.

**Features**:
- Streaming recognition with interim results
- Automatic punctuation
- Thread-safe audio queue
- Stream reset capability for interruptions

**Configuration**:
- Language: en-US
- Sample Rate: 16kHz
- Audio Encoding: LINEAR16
- Enhanced models enabled

#### TTS Handler (`VoiceHandlers/tts_handler.py`)

**Purpose**: Converts text to speech with emotional expression.

**Features**:
- Streaming text-to-speech processing
- Multiple emotion presets (happy, sad, excited, calm, angry, fearful, neutral)
- SSML support for prosody control
- Sentence-by-sentence audio generation
- WebSocket-based audio streaming

**Emotion Presets**:
```python
{
    "excited": {"pitch": 4.0, "speaking_rate": 1.0, "volume_gain_db": 3.5},
    "calm": {"pitch": -1.0, "speaking_rate": 0.9, "volume_gain_db": 0.0},
    # ... more presets
}
```

#### State Manager (`VoiceHandlers/state_manager.py`)

**Purpose**: Manages conversation states and transitions.

**States**:
1. **FULL_LISTENING**: 
   - Captures all user speech
   - Analyzes for sentence completion
   - Accumulates conversation context

2. **INTERRUPT_ONLY**:
   - Active during AI response playback
   - Monitors for interruption commands only
   - Ignores regular speech input

**State Transitions**:
```
FULL_LISTENING ──[Sentence Complete]──> INTERRUPT_ONLY
       ▲                                       │
       │                                       │
       └────[Response Complete/Interrupted]────┘
```

#### Interruption Handler (`VoiceHandlers/interruption.py`)

**Purpose**: Detects and handles interruption requests.

**Interrupt Commands**:
- Voice: "stop", "shut up", "end", "silence", "pause", etc.
- Keyboard: Backtick (`) key

**Interrupt Flow**:
1. Detect interruption command/key
2. Stop current audio playback
3. Play acknowledgment sound
4. Clear all queues (audio, response, sentences)
5. Reset STT stream
6. Transition back to FULL_LISTENING

### 4. OpenAI Clients

#### Base Generator (`OpenAIClients/base_generator.py`)

**Purpose**: Abstract base class for all AI-powered generators.

**Common Functionality**:
- OpenAI API client initialization
- Dynamic prompt construction with context
- Request handling with configurable parameters
- Error handling and logging

#### Regular Response Generator (`OpenAIClients/regular_response_generator.py`)

**Purpose**: Handles main conversational AI responses.

**Features**:
- Streaming response generation
- Conversation memory management (configurable limit)
- Context integration from prompt handler
- Chunk-by-chunk response delivery

**Memory Management**:
- Configurable memory limit (default: 10 turns)
- Automatic message history trimming
- Preserves system message + recent N messages

#### Code Generator (`OpenAIClients/code_generator.py`)

**Purpose**: Generates code snippets based on natural language descriptions.

**Process**:
1. Receives code generation request with context
2. Constructs prompt with relevant context
3. Generates code using GPT-4
4. Strips markdown formatting
5. Sends pure code via WebSocket

**Signaling Format**:
```json
{
    "operation": "GENERATE_CODE",
    "details": {
        "context_keys": [],
        "PROMPT": "Generate a binary search tree implementation"
    }
}
```

#### Graph Generator (`OpenAIClients/graph_generator.py`)

**Purpose**: Creates visual concept maps and mind maps.

**Output Format**:
```json
{
    "nodes": [
        {
            "id": "note-1",
            "position": {"x": 500, "y": 500},
            "content": "Main Concept",
            "color": "#FFD700"
        }
    ],
    "connections": [
        {
            "from": "note-1",
            "to": "note-2",
            "sourceHandle": "rs",
            "targetHandle": "l"
        }
    ]
}
```

**Features**:
- 10-15 nodes with logical relationships
- Automatic layout with 500-600px spacing
- Valid connection rules (rs→l, ls→r, b→t, etc.)
- Hierarchical organization

#### Notes Generator (`OpenAIClients/notes_generator.py`)

**Purpose**: Extracts and structures key concepts from conversations.

**Features**:
- Batch processing (2 sentences at a time)
- Filters out greetings and conversational fluff
- Highlights new concepts with `<strong>` tags
- Structured, teacher-style note formatting

### 5. Context Management

#### Context Manager (`ContextHandlers/context_manager.py`)

**Purpose**: Stores and retrieves conversation context, graphs, and code.

**Storage Structure**:
```python
{
    "graphs": {
        "Quantum Mechanics Tree": {"data": "..."}
    },
    "code": {
        "Binary Tree": {"data": "..."}
    },
    "context": {
        "Quantum Mechanics": ["explanation 1", "explanation 2"]
    }
}
```

**Operations**:
- `get_from_context(type, keywords)`: Retrieve specific context items
- `add_to_context(type, keyword, value)`: Add or append to context

#### Prompt Handler (`PromptHandlers/regular_response_prompt_handler.py`)

**Purpose**: Constructs dynamic prompts for AI interactions.

**Dynamic Prompt Structure**:
```python
{
    "graphKeys": [],
    "graphList": {},
    "contextKeys": [],
    "context": {},
    "recent_conversation": []
}
```

**Message Flow**:
1. System message with instructions
2. Context information (graphs, code, keywords)
3. Conversation history
4. Current user input

## Data Flow Diagrams

### Main Conversation Flow

```
User Speech
    │
    ▼
[Microphone] ──────────────────┐
    │                          │
    ▼                          │
[STT Handler]                  │
    │                          │
    ├─► Partial Transcript     │
    │   (continuous updates)   │
    │                          │
    └─► Final Transcript       │
         │                     │
         ▼                     │
    [State Manager]            │
         │                     │
         ├─► FULL_LISTENING    │
         │   - Accumulate text │
         │   - Check completion│
         │                     │
         └─► Sentence Complete │
              │                │
              ▼                │
         [AI Processing]       │
              │                │
              ├─► GPT-4 Request│
              │                │
              └─► Stream Response
                   │
                   ├─► Parse Commands
                   │   (code/graph gen)
                   │
                   └─► Text Chunks
                        │
                        ▼
                   [TTS Handler]
                        │
                        ├─► Generate Audio
                        │
                        └─► Stream to Client
                             │
                             ▼
                        [Audio Playback]
                             │
                             ▼
                        [INTERRUPT_ONLY]
                             │
                             ├─► Monitor for
                             │   interruptions
                             │
                             └─► On Complete
                                  │
                                  ▼
                             [FULL_LISTENING]
```

### Interruption Flow

```
User Says "Stop" / Presses `
         │
         ▼
[Interruption Handler]
         │
         ├─► Detect Command
         │
         ├─► Stop TTS Playback
         │
         ├─► Clear Audio Queue
         │
         ├─► Clear Response Queue
         │
         ├─► Reset STT Stream
         │
         ├─► Play Acknowledgment
         │
         └─► Transition to FULL_LISTENING
```

### Code/Graph Generation Flow

```
AI Response Contains Command
         │
         ▼
Parse JSON Command
         │
         ├─► {"operation": "GENERATE_CODE"}
         │        │
         │        ▼
         │   [Code Generator]
         │        │
         │        ├─► Get Context
         │        │
         │        ├─► Generate Code
         │        │
         │        └─► Send via WebSocket
         │
         └─► {"operation": "GENERATE_GRAPH"}
                  │
                  ▼
             [Graph Generator]
                  │
                  ├─► Get Context
                  │
                  ├─► Generate Graph JSON
                  │
                  └─► Send via WebSocket
```

## Threading Model

The system uses multiple threads for concurrent operations:

### Main Threads

1. **FastAPI Server Thread**: Handles HTTP/WebSocket connections
2. **STT Recognition Thread**: Processes audio stream continuously
3. **TTS Playback Thread**: Streams audio to client
4. **AI Response Generation Thread**: Generates GPT-4 responses
5. **Notes Processing Thread**: Batch processes sentences for notes
6. **Keyboard Listener Thread**: Monitors for interrupt key

### Thread Safety

- **Queues**: Thread-safe queues for audio, sentences, and responses
- **Locks**: Used in NotesProcessor for batch processing
- **Events**: Threading events for cleanup and stopping
- **Deques**: Thread-safe deques for response streaming

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/google-credentials.json
```

### Configurable Parameters

**STT Config**:
- `language_code`: "en-US"
- `sample_rate`: 16000 Hz
- `enable_interim`: True
- `enable_punctuation`: True

**TTS Config**:
- `language_code`: "en-US"
- `voice_name`: "en-US-Casual-K"
- `speaking_rate`: 1.0
- `pitch`: 0.0
- `volume_gain_db`: 0.0

**Chat Config**:
- `model_name`: "gpt-4"
- `temperature`: 0.7
- `memory_limit`: 10 turns

**Analysis Config**:
- `model_name`: "gpt-4"
- `temperature`: 0 (deterministic)

## Error Handling

### Graceful Degradation

1. **STT Stream Errors**: Automatic stream restart
2. **TTS Errors**: Logged but doesn't crash system
3. **WebSocket Disconnects**: Automatic cleanup
4. **API Failures**: Error messages logged, system continues

### Cleanup Procedures

**On Client Disconnect**:
1. Stop STT recognition
2. Stop TTS playback
3. Clear all queues
4. Terminate threads
5. Remove client from connection registry

**On Interruption**:
1. Cancel processing timer
2. Clear response queue
3. Clear sentence queue
4. Reset STT stream
5. Stop TTS playback
6. Reset state manager

## Performance Considerations

### Latency Optimization

- **Streaming Responses**: Chunk-by-chunk processing reduces perceived latency
- **Sentence-Level TTS**: Start speaking before full response is generated
- **Audio Buffering**: Minimal buffering for real-time feel

### Resource Management

- **Memory Limits**: Conversation history capped at configurable limit
- **Temporary Files**: TTS output cached and reused when possible
- **Queue Sizes**: Bounded queues prevent memory overflow

### Scalability

- **Per-Client Processors**: Each client gets isolated AudioProcessor instance
- **Thread Pools**: Daemon threads for background processing
- **WebSocket Connections**: Supports multiple concurrent clients

## Security Considerations

1. **API Keys**: Stored in environment variables, never committed
2. **CORS**: Configured for specific origins in production
3. **Input Validation**: WebSocket messages validated before processing
4. **Resource Limits**: Per-client resource allocation prevents DoS

## Future Enhancements

Potential areas for improvement:
- Add authentication/authorization
- Implement rate limiting
- Add conversation persistence (database)
- Support multiple languages
- Add voice activity detection (VAD) for better silence detection
- Implement speaker diarization for multi-user scenarios
- Add caching layer for frequently generated content

