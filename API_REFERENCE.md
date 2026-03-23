# API Reference

## WebSocket API

The system uses WebSocket connections for real-time bidirectional communication between the client and server.

### Connection Endpoints

#### Audio WebSocket
```
ws://localhost:8000/ws/{client_id}
```

**Purpose**: Main connection for audio streaming and control messages.

**URL Parameters**:
- `client_id` (string): Unique identifier for the client session

**Connection Flow**:
1. Client initiates WebSocket connection
2. Server accepts and creates AudioProcessor instance
3. Server starts STT recognition
4. Connection remains open for bidirectional communication

#### Text WebSocket
```
ws://localhost:8000/ws/text/{client_id}
```

**Purpose**: Dedicated connection for text data (notes, code, graphs).

**URL Parameters**:
- `client_id` (string): Must match the audio WebSocket client_id

**Connection Flow**:
1. Client initiates text WebSocket connection
2. Server accepts and links to existing AudioProcessor
3. Connection used for sending generated content

---

## Message Formats

All messages are sent as JSON objects.

### Client → Server Messages

#### 1. Audio Data

```json
{
    "type": "audio",
    "data": "base64_encoded_audio_data"
}
```

**Fields**:
- `type`: Always "audio"
- `data`: Base64-encoded audio data (PCM 16-bit, 16kHz, mono)

**Usage**: Send continuous audio chunks from microphone

**Example**:
```javascript
const audioData = new Int16Array(buffer);
const base64Audio = btoa(String.fromCharCode(...new Uint8Array(audioData.buffer)));
websocket.send(JSON.stringify({
    type: "audio",
    data: base64Audio
}));
```

#### 2. Interrupt Command

```json
{
    "type": "interrupt"
}
```

**Fields**:
- `type`: Always "interrupt"

**Usage**: Request immediate interruption of current AI response

**Effect**:
- Stops TTS playback
- Clears all queues
- Plays acknowledgment sound
- Returns to FULL_LISTENING state

#### 3. Playback Complete

```json
{
    "type": "playback_complete"
}
```

**Fields**:
- `type`: Always "playback_complete"

**Usage**: Notify server that audio playback finished on client side

**Effect**:
- Resets `is_playing` flag in TTS handler
- Allows system to transition states

#### 4. Register Text WebSocket

```json
{
    "type": "register_text_websocket"
}
```

**Fields**:
- `type`: Always "register_text_websocket"

**Usage**: Link text WebSocket to audio processor

**Effect**:
- Associates text WebSocket with the client's AudioProcessor
- Enables sending of notes, code, and graphs

### Server → Client Messages

#### 1. Audio Data (Binary)

**Format**: Raw binary audio data (MP3 format)

**Usage**: Audio response from TTS system

**Handling**:
```javascript
websocket.onmessage = (event) => {
    if (event.data instanceof Blob) {
        // Audio data
        playAudio(event.data);
    }
};
```

#### 2. Stop Playback

```json
{
    "type": "should_stop",
    "data": "stop_playback"
}
```

**Fields**:
- `type`: Always "should_stop"
- `data`: Always "stop_playback"

**Usage**: Instructs client to stop audio playback immediately

**Effect**: Client should stop playing audio and clear audio buffers

#### 3. Notes Generation

```json
{
    "operation": "NOTES",
    "result": "Structured notes content here..."
}
```

**Fields**:
- `operation`: Always "NOTES"
- `result`: Generated notes in text/HTML format

**Usage**: Sends automatically generated notes from conversation

**Example Result**:
```
<strong>Quantum Mechanics</strong>
- Studies behavior of matter at atomic scale
- Key principles: superposition, entanglement
- Applications: quantum computing, cryptography
```

#### 4. Code Generation

```json
{
    "operation": "CODE_GENERATION",
    "details": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    ..."
}
```

**Fields**:
- `operation`: Always "CODE_GENERATION"
- `details`: Generated code (pure code, no markdown)

**Usage**: Sends generated code based on user request

**Triggering**: User says something like "generate code for [description]"

#### 5. Graph Generation

```json
{
    "operation": "GRAPH",
    "details": "{\"nodes\": [...], \"connections\": [...]}"
}
```

**Fields**:
- `operation`: Always "GRAPH"
- `details`: JSON string containing graph structure

**Usage**: Sends generated concept map/mind map

**Graph Structure**:
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

**Node Fields**:
- `id`: Unique identifier (format: "note-{number}")
- `position`: {x, y} coordinates in pixels
- `content`: Text content of the node
- `color`: Hex color code

**Connection Fields**:
- `from`: Source node ID
- `to`: Target node ID
- `sourceHandle`: Connection point on source ("rs", "ls", "b")
- `targetHandle`: Connection point on target ("l", "r", "t")

**Handle Types**:
- `rs`: Right side
- `ls`: Left side
- `b`: Bottom
- `t`: Top
- `l`: Left
- `r`: Right

#### 6. Attention Signal

```json
{
    "operation": "ATTENTION",
    "node_id": "note-5"
}
```

**Fields**:
- `operation`: Always "ATTENTION"
- `node_id`: ID of node to highlight

**Usage**: Directs user attention to specific graph node

---

## Internal API

These are internal Python APIs used within the system.

### AudioProcessor

Main orchestrator class in `test.py`.

#### Constructor

```python
AudioProcessor(tts_websocket_callback=None)
```

**Parameters**:
- `tts_websocket_callback` (callable, optional): Async function to send audio data via WebSocket

**Example**:
```python
async def audio_callback(audio_data):
    await websocket.send_bytes(audio_data)

processor = AudioProcessor(audio_callback)
```

#### Methods

##### `audio_callback(indata, frames, time, status)`

Handles incoming audio data from microphone.

**Parameters**:
- `indata` (numpy.ndarray): Audio data
- `frames` (int): Number of frames
- `time` (object): Timing information
- `status` (object): Status flags

##### `handle_final(text: str)`

Processes final transcript from STT.

**Parameters**:
- `text` (str): Final transcribed text

##### `handle_partial(text: str)`

Processes partial transcript from STT.

**Parameters**:
- `text` (str): Partial transcribed text

##### `handle_interrupt_and_clearing()`

Handles interruption request.

**Effect**:
- Stops all processing
- Clears queues
- Resets state

##### `cleanup()`

Cleans up all resources.

**Effect**:
- Stops STT/TTS handlers
- Closes connections
- Terminates threads

### SpeechToTextHandler

Speech recognition handler in `VoiceHandlers/stt_handler.py`.

#### Constructor

```python
SpeechToTextHandler(config: Optional[STTConfig] = None)
```

**Parameters**:
- `config` (STTConfig, optional): Configuration object

#### Configuration

```python
@dataclass
class STTConfig:
    language_code: str = "en-US"
    sample_rate: int = 16000
    enable_interim: bool = True
    enable_punctuation: bool = True
```

#### Methods

##### `start_recognition()`

Starts speech recognition in background thread.

##### `add_audio_data(audio_chunk: bytes)`

Adds audio data to processing queue.

**Parameters**:
- `audio_chunk` (bytes): Raw audio data

##### `stop_recognition()`

Stops speech recognition.

##### `clear_state()`

Clears internal state and resets stream.

#### Callbacks

Set these properties to receive transcripts:

```python
handler.partial_transcript_callback = lambda text: print(f"Partial: {text}")
handler.final_transcript_callback = lambda text: print(f"Final: {text}")
```

### TextToSpeechHandler

Speech synthesis handler in `VoiceHandlers/tts_handler.py`.

#### Constructor

```python
TextToSpeechHandler(config: Optional[TTSConfig] = None, websocket_callback=None)
```

**Parameters**:
- `config` (TTSConfig, optional): Configuration object
- `websocket_callback` (callable, optional): Async function for audio streaming

#### Configuration

```python
@dataclass
class TTSConfig:
    language_code: str = "en-US"
    voice_name: str = "en-US-Casual-K"
    speaking_rate: float = 1.0
    pitch: float = 0.0
    volume_gain_db: float = 0.0
    output_dir: Path = Path("temp/tts_output")
```

#### Methods

##### `stream_text_to_speech(sentences_queue: queue.Queue, emotion: str = "excited")`

Processes streaming text with immediate playback.

**Parameters**:
- `sentences_queue` (Queue): Queue of sentences to synthesize
- `emotion` (str): Emotion preset name

**Emotion Presets**:
- "happy"
- "sad"
- "excited"
- "calm"
- "angry"
- "fearful"
- "neutral"

##### `set_emotion(text: str, emotion: str) -> str`

Adds emotion tag to text.

**Parameters**:
- `text` (str): Text to tag
- `emotion` (str): Emotion name

**Returns**: Tagged text

**Example**:
```python
tagged = handler.set_emotion("Hello!", "excited")
# Returns: "[emotion:excited] Hello!"
```

##### `stop_playback()`

Stops current playback and clears queue.

### StateManager

Conversation state manager in `VoiceHandlers/state_manager.py`.

#### States

```python
class ListeningState(Enum):
    FULL_LISTENING = "full_listening"
    INTERRUPT_ONLY = "interrupt_only"
```

#### Methods

##### `transition_to(new_state: ListeningState)`

Transitions to new state.

**Parameters**:
- `new_state` (ListeningState): Target state

**Effect**: Clears text buffers and notifies callbacks

##### `register_state_change_callback(callback)`

Registers callback for state changes.

**Parameters**:
- `callback` (callable): Function(old_state, new_state)

**Example**:
```python
def on_state_change(old, new):
    print(f"State: {old} → {new}")

manager.register_state_change_callback(on_state_change)
```

##### `update_text(text: str)`

Updates text buffer for current state.

**Parameters**:
- `text` (str): New text

##### `get_current_text() -> str`

Returns text for current state.

**Returns**: Current text buffer

### OpenAI Service

Main AI service in `OpenAIClients/regular_response_generator.py`.

#### Constructor

```python
OpenAIService(memory_limit: int = 10)
```

**Parameters**:
- `memory_limit` (int): Number of conversation turns to remember

#### Methods

##### `generate_chat_response(queue: deque, config: ChatConfig) -> Iterator[str]`

Generates streaming chat response.

**Parameters**:
- `queue` (deque): Output queue for response chunks
- `config` (ChatConfig): Configuration object

**Effect**: Populates queue with response chunks, ends with "END"

##### `analyze_completion(text: str, config: AnalysisConfig) -> bool`

Analyzes if text forms complete thought.

**Parameters**:
- `text` (str): Text to analyze
- `config` (AnalysisConfig): Configuration object

**Returns**: True if complete, False otherwise

### Context Manager

Context storage in `ContextHandlers/context_manager.py`.

#### Methods

##### `get_from_context(context_type: str, keywords: list) -> dict`

Retrieves context items.

**Parameters**:
- `context_type` (str): Type ("graphs", "code", "context")
- `keywords` (list): List of keys to retrieve

**Returns**: Dictionary with requested items

**Example**:
```python
cm = ContextManager()
context = cm.get_from_context("context", ["Quantum Mechanics"])
```

##### `add_to_context(context_type: str, keyword: str, value: any)`

Adds item to context.

**Parameters**:
- `context_type` (str): Type ("graphs", "code", "context")
- `keyword` (str): Key name
- `value` (any): Value to store

**Example**:
```python
cm.add_to_context("context", "Quantum Mechanics", "Studies atomic behavior")
```

---

## Error Handling

### Common Errors

#### WebSocket Errors

**Connection Refused**:
```json
{
    "error": "Connection refused",
    "message": "Server not running or port blocked"
}
```

**Solution**: Ensure server is running on correct port

**Authentication Failed**:
```json
{
    "error": "Authentication failed",
    "message": "Invalid client_id"
}
```

**Solution**: Use valid client_id

#### API Errors

**Rate Limit Exceeded**:
```
Error: Rate limit exceeded for OpenAI API
```

**Solution**: Wait or upgrade API plan

**Invalid Credentials**:
```
Error: Invalid Google Cloud credentials
```

**Solution**: Check GOOGLE_APPLICATION_CREDENTIALS path

---

## Rate Limits

### OpenAI API
- GPT-4: Varies by plan (typically 40,000 tokens/min)
- GPT-3.5-turbo: Higher limits (typically 90,000 tokens/min)

### Google Cloud APIs
- Speech-to-Text: 1,000 requests/min
- Text-to-Speech: 1,000 requests/min

**Recommendation**: Implement client-side rate limiting and request queuing for production use.

---

## Best Practices

### Client Implementation

1. **Reconnection Logic**: Implement exponential backoff for reconnections
2. **Audio Buffering**: Buffer audio locally before sending
3. **Error Handling**: Handle all message types gracefully
4. **State Sync**: Keep client state in sync with server
5. **Resource Cleanup**: Close connections properly on page unload

### Server Implementation

1. **Connection Limits**: Limit concurrent connections per IP
2. **Message Validation**: Validate all incoming messages
3. **Resource Cleanup**: Clean up on disconnect
4. **Logging**: Log all errors and important events
5. **Monitoring**: Monitor WebSocket connection health

### Example Client Implementation

```javascript
class AudioTutorClient {
    constructor(clientId) {
        this.clientId = clientId;
        this.audioWs = null;
        this.textWs = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        this.audioWs = new WebSocket(`ws://localhost:8000/ws/${this.clientId}`);
        this.textWs = new WebSocket(`ws://localhost:8000/ws/text/${this.clientId}`);

        this.audioWs.onopen = () => {
            console.log('Audio WebSocket connected');
            this.reconnectAttempts = 0;
        };

        this.audioWs.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.audioWs.onclose = () => {
            console.log('WebSocket closed');
            this.reconnect();
        };

        this.audioWs.onmessage = (event) => {
            this.handleMessage(event);
        };

        this.textWs.onmessage = (event) => {
            this.handleTextMessage(event);
        };
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`Reconnecting in ${delay}ms...`);
            setTimeout(() => this.connect(), delay);
        }
    }

    sendAudio(audioData) {
        if (this.audioWs.readyState === WebSocket.OPEN) {
            this.audioWs.send(JSON.stringify({
                type: 'audio',
                data: audioData
            }));
        }
    }

    interrupt() {
        if (this.audioWs.readyState === WebSocket.OPEN) {
            this.audioWs.send(JSON.stringify({
                type: 'interrupt'
            }));
        }
    }

    handleMessage(event) {
        if (event.data instanceof Blob) {
            // Audio data
            this.playAudio(event.data);
        } else {
            // JSON message
            const message = JSON.parse(event.data);
            if (message.type === 'should_stop') {
                this.stopAudio();
            }
        }
    }

    handleTextMessage(event) {
        const message = JSON.parse(event.data);
        switch (message.operation) {
            case 'NOTES':
                this.displayNotes(message.result);
                break;
            case 'CODE_GENERATION':
                this.displayCode(message.details);
                break;
            case 'GRAPH':
                this.displayGraph(JSON.parse(message.details));
                break;
        }
    }
}
```

---

## Versioning

Current API Version: 1.0

Future versions will maintain backward compatibility where possible. Breaking changes will be announced with migration guides.

