# Contributing Guide

Thank you for your interest in contributing to the QUAD FEST Audio AI Tutor project! This guide will help you understand the codebase and make effective contributions.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Workflow](#development-workflow)
3. [Code Style Guidelines](#code-style-guidelines)
4. [Architecture Overview](#architecture-overview)
5. [Common Tasks](#common-tasks)
6. [Testing](#testing)
7. [Submitting Changes](#submitting-changes)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.10+
- Google Cloud account (for Speech APIs)
- OpenAI API account
- Git
- Basic understanding of async/await and threading

### Initial Setup

1. **Clone and setup**:
```bash
git clone <repository-url>
cd audio-main
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure credentials**:
   - Create `.env` file with API keys
   - Add Google Cloud credentials JSON file
   - See [SETUP.md](SETUP.md) for details

3. **Verify setup**:
```bash
python test.py  # Should start listening
```

## Development Workflow

### Branch Strategy

- `main` - Stable production code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Typical Workflow

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and test locally

3. Commit with descriptive messages:
```bash
git commit -m "Add: Description of what you added"
```

4. Push and create pull request:
```bash
git push origin feature/your-feature-name
```

## Code Style Guidelines

### Python Style

Follow PEP 8 with these specifics:

**Imports**:
```python
# Standard library
import os
import json
from typing import Optional, List

# Third-party
import numpy as np
from fastapi import FastAPI

# Local
from VoiceHandlers.stt_handler import SpeechToTextHandler
```

**Naming Conventions**:
- Classes: `PascalCase` (e.g., `AudioProcessor`)
- Functions/methods: `snake_case` (e.g., `process_audio`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- Private methods: `_leading_underscore` (e.g., `_internal_method`)

**Docstrings**:
```python
def process_audio(audio_data: bytes, config: AudioConfig) -> str:
    """Process audio data and return transcript.
    
    This function handles the complete audio processing pipeline including
    noise reduction, normalization, and speech recognition.
    
    Args:
        audio_data: Raw audio bytes (PCM 16-bit)
        config: Audio processing configuration
        
    Returns:
        Transcribed text from the audio
        
    Raises:
        AudioProcessingError: If audio format is invalid
        
    Example:
        >>> config = AudioConfig(sample_rate=16000)
        >>> transcript = process_audio(audio_bytes, config)
    """
    # Implementation
```

**Type Hints**:
Always use type hints for function parameters and return values:
```python
def calculate_delay(is_complete: bool, timeout: float = 1.0) -> float:
    return 1.0 if is_complete else 2.0
```

**Comments**:
- Use inline comments sparingly, prefer descriptive variable names
- Add comments for complex logic or non-obvious decisions
- Explain "why" not "what"

```python
# Good
# Wait longer for incomplete sentences to allow user to continue speaking
delay = 2.0 if not is_complete else 1.0

# Bad
# Set delay to 2.0
delay = 2.0
```

### File Organization

**Module Structure**:
```python
"""Module docstring explaining purpose."""

# Imports
import ...

# Constants
MAX_RETRIES = 3

# Classes
class MyClass:
    ...

# Functions
def helper_function():
    ...

# Main execution
if __name__ == "__main__":
    main()
```

## Architecture Overview

### Key Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Loose Coupling**: Modules communicate through well-defined interfaces
3. **Thread Safety**: All shared resources use appropriate synchronization
4. **Error Handling**: Graceful degradation, never crash the entire system

### Component Responsibilities

| Component | Responsibility | Don't Use For |
|-----------|---------------|---------------|
| `stt_handler.py` | Speech recognition | Audio playback, AI processing |
| `tts_handler.py` | Speech synthesis | Speech recognition, state management |
| `state_manager.py` | State transitions | Audio processing, AI calls |
| `regular_response_generator.py` | AI responses | Audio handling, state management |
| `context_manager.py` | Context storage | AI processing, audio handling |

### Data Flow Rules

1. **Audio Pipeline**: `Microphone → STT → State Manager → AudioProcessor`
2. **AI Pipeline**: `AudioProcessor → OpenAI Service → TTS → Client`
3. **Context Flow**: `Context Manager ← → Prompt Handler ← → OpenAI Service`

**Never**:
- Skip state manager for state changes
- Directly modify shared state from multiple threads
- Call blocking operations in async functions

## Common Tasks

### Adding a New Voice Command

**File**: `VoiceHandlers/interruption.py`

```python
class InterruptionHandler:
    def __init__(self, ...):
        self.interrupt_commands = {
            "stop", "end", "shut up",
            # Add your new command here
            "be quiet", "hush"
        }
```

**Test**:
1. Start the system
2. Say the new command during AI response
3. Verify interruption works

### Adding a New Emotion Preset

**File**: `VoiceHandlers/tts_handler.py`

```python
self.emotion_presets = {
    # Existing presets...
    "your_emotion": {
        "pitch": 1.5,           # -20.0 to 20.0
        "speaking_rate": 1.1,   # 0.25 to 4.0
        "volume_gain_db": 2.0   # -96.0 to 16.0
    }
}
```

**Usage**:
```python
handler.set_emotion("Hello!", "your_emotion")
```

### Creating a New Generator

1. **Create file**: `OpenAIClients/your_generator.py`

```python
from .base_generator import BaseGenerator
from fastapi import WebSocket
from typing import Dict

class YourGenerator(BaseGenerator):
    def __init__(self):
        super().__init__()
        self.base_messages = [
            {"role": "system", "content": "Your system instructions..."}
        ]
    
    async def generate_your_content(self, message: Dict, websocket: WebSocket):
        """Generate your content type."""
        response = self.generate(message)
        
        # Process response as needed
        processed = self._process_response(response)
        
        # Send via WebSocket
        await websocket.send_json({
            "operation": "YOUR_OPERATION",
            "details": processed
        })
    
    def _process_response(self, response: str) -> str:
        """Process the raw response."""
        # Your processing logic
        return response
```

2. **Register in AudioProcessor** (`test.py`):

```python
class AudioProcessor:
    def __init__(self, ...):
        # Add your generator
        self.your_generator = YourGenerator()
    
    async def handle_command(self, command_json):
        # Add command handler
        if command_json.get("operation") == "YOUR_OPERATION":
            await self.your_generator.generate_your_content(
                command_json, 
                self.text_websocket
            )
```

3. **Update prompt handler** to include your operation in system instructions

### Modifying State Behavior

**File**: `VoiceHandlers/state_manager.py`

**Adding a new state**:
```python
class ListeningState(Enum):
    FULL_LISTENING = "full_listening"
    INTERRUPT_ONLY = "interrupt_only"
    YOUR_NEW_STATE = "your_new_state"  # Add here
```

**Adding state-specific behavior**:
```python
def update_text(self, text: str) -> None:
    if self.current_state == ListeningState.YOUR_NEW_STATE:
        # Your custom behavior
        self.handle_your_state(text)
    elif self.current_state == ListeningState.FULL_LISTENING:
        self.current_text = text
```

### Adjusting Processing Delays

**File**: `test.py`

```python
def handle_final(self, text: str):
    # Modify these delays
    if is_complete:
        self.process_after_delay(text, 0.5)  # Complete sentence delay
    else:
        self.process_after_delay(text, 2.0)  # Incomplete sentence delay
```

## Testing

### Manual Testing Checklist

Before submitting changes, test:

- [ ] Basic conversation works
- [ ] Interruption works (voice and keyboard)
- [ ] Code generation works
- [ ] Graph generation works
- [ ] Notes generation works
- [ ] Multiple clients can connect
- [ ] Graceful disconnection
- [ ] Error handling (bad audio, API failures)

### Testing Audio Components

```python
# Test STT Handler
from VoiceHandlers.stt_handler import SpeechToTextHandler, STTConfig

config = STTConfig()
handler = SpeechToTextHandler(config)

def on_final(text):
    print(f"Final: {text}")

handler.final_transcript_callback = on_final
handler.start_recognition()

# Feed test audio
with open("test_audio.wav", "rb") as f:
    audio_data = f.read()
    handler.add_audio_data(audio_data)
```

### Testing AI Components

```python
# Test OpenAI Service
from OpenAIClients.regular_response_generator import create_default_service, ChatConfig
from collections import deque

service = create_default_service()
config = ChatConfig()
queue = deque()

# Generate response
service.generate_chat_response(queue, config)

# Check results
while queue:
    chunk = queue.popleft()
    print(chunk, end="")
```

### Testing WebSocket Endpoints

```python
# Test with Python client
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/test-client"
    async with websockets.connect(uri) as websocket:
        # Send test message
        await websocket.send(json.dumps({
            "type": "interrupt"
        }))
        
        # Receive response
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
```

## Submitting Changes

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] All functions have docstrings
- [ ] Type hints are used
- [ ] Manual testing completed
- [ ] No debugging print statements (use logging)
- [ ] No commented-out code
- [ ] No sensitive data (API keys, credentials)
- [ ] Documentation updated if needed

### Commit Message Format

```
Type: Brief description (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain the problem this commit solves and why you chose
this approach.

- Bullet points are okay
- Use present tense ("Add feature" not "Added feature")
- Reference issues: "Fixes #123"
```

**Types**:
- `Add`: New feature
- `Fix`: Bug fix
- `Refactor`: Code restructuring
- `Docs`: Documentation changes
- `Style`: Formatting changes
- `Test`: Adding tests
- `Chore`: Maintenance tasks

**Examples**:
```
Add: Support for Spanish language in STT

Implements Spanish language support by adding es-ES language
code option to STTConfig. Updated voice handler to support
multiple language codes.

Fixes #45
```

```
Fix: Memory leak in TTS audio queue

The audio queue was not being properly cleared on interruption,
causing memory to grow over time. Added explicit queue clearing
in stop_playback method.
```

## Troubleshooting

### Common Issues

**Import Errors**:
```python
# Wrong
from stt_handler import SpeechToTextHandler

# Correct
from VoiceHandlers.stt_handler import SpeechToTextHandler
```

**Threading Issues**:
- Always use thread-safe queues for inter-thread communication
- Use locks for shared mutable state
- Never call blocking operations in async functions

**WebSocket Issues**:
- Ensure WebSocket is open before sending
- Handle disconnections gracefully
- Use try-except around WebSocket operations

**Audio Issues**:
- Verify sample rate matches (16kHz)
- Check audio format (PCM 16-bit)
- Ensure proper cleanup of audio resources

### Getting Help

1. Check existing documentation:
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System design
   - [API_REFERENCE.md](API_REFERENCE.md) - API details
   - [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - File organization

2. Search existing issues on GitHub

3. Ask in team chat/Discord

4. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant code snippets
   - Error messages/logs

## Best Practices

### Do's ✅

- Write clear, descriptive variable names
- Use type hints everywhere
- Handle errors gracefully
- Log important events
- Clean up resources properly
- Test edge cases
- Document complex logic
- Keep functions small and focused

### Don'ts ❌

- Don't commit API keys or credentials
- Don't use global mutable state
- Don't ignore exceptions silently
- Don't mix sync and async code incorrectly
- Don't create circular imports
- Don't leave debugging code
- Don't skip error handling
- Don't make assumptions about timing

## Code Review Guidelines

### As a Reviewer

- Be constructive and respectful
- Explain why changes are needed
- Suggest alternatives
- Approve when satisfied
- Check for:
  - Correctness
  - Style compliance
  - Test coverage
  - Documentation
  - Performance implications

### As an Author

- Respond to all comments
- Ask for clarification if needed
- Make requested changes
- Explain your reasoning
- Be open to feedback

## Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Speech API](https://cloud.google.com/speech-to-text/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## Questions?

If you have questions not covered here, please:
1. Check the documentation files
2. Search existing issues
3. Ask the team
4. Create a new issue

Thank you for contributing! 🎉

