# QUAD FEST Audio AI Tutor

An intelligent voice-based AI tutoring system that provides real-time conversational assistance with support for code generation, graph visualization, and automated note-taking.

## 🎯 Overview

This project implements a sophisticated voice-controlled AI tutor that:
- Listens to user speech and converts it to text (Speech-to-Text)
- Processes queries using GPT-4
- Responds with natural voice output (Text-to-Speech)
- Generates code snippets on demand
- Creates visual concept maps and graphs
- Automatically generates structured notes from conversations
- Supports voice interruptions for natural conversation flow

## 🌟 Key Features

### 1. **Real-Time Voice Interaction**
- Continuous speech recognition using Google Cloud Speech-to-Text
- Natural language processing with OpenAI GPT-4
- High-quality voice synthesis with Google Cloud Text-to-Speech
- Multiple emotion presets for expressive speech output

### 2. **Intelligent State Management**
- **FULL_LISTENING**: Default mode for capturing user input
- **INTERRUPT_ONLY**: Active during AI responses, monitors for interruption commands

### 3. **Smart Interruption System**
- Voice commands: "stop", "shut up", "end", "silence", etc.
- Keyboard shortcut: backtick (`) key
- Immediate response with audio acknowledgment

### 4. **Context-Aware Processing**
- Maintains conversation history with configurable memory limits
- Context manager for storing and retrieving relevant information
- Dynamic prompt generation based on conversation context

### 5. **Advanced Content Generation**
- **Code Generation**: Creates code snippets based on natural language descriptions
- **Graph Generation**: Produces visual concept maps with 10-15 interconnected nodes
- **Note Generation**: Automatically extracts and structures key concepts from conversations

### 6. **WebSocket Architecture**
- Dual WebSocket connections (audio + text data)
- Real-time bidirectional communication
- Supports multiple concurrent clients

## 📁 Project Structure

```
digital_classroom/
├── backend/                        # Backend server and AI processing
│   ├── app.py                      # FastAPI WebSocket server
│   ├── test.py                     # Core AudioProcessor class
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── OpenAIClients/              # AI service integrations
│   │   ├── regular_response_generator.py   # Main chat response handler
│   │   ├── base_generator.py              # Base class for all generators
│   │   ├── code_generator.py              # Code generation service
│   │   ├── graph_generator.py             # Graph/mindmap generation
│   │   └── notes_generator.py             # Automated note-taking
│   │
│   ├── VoiceHandlers/              # Audio processing modules
│   │   ├── stt_handler.py              # Speech-to-Text handler
│   │   ├── tts_handler.py              # Text-to-Speech handler
│   │   ├── state_manager.py            # State machine for conversation flow
│   │   └── interruption.py             # Interruption detection and handling
│   │
│   ├── PromptHandlers/             # Prompt management
│   │   └── regular_response_prompt_handler.py  # Dynamic prompt construction
│   │
│   ├── ContextHandlers/            # Context management
│   │   └── context_manager.py          # Context storage and retrieval
│   │
│   └── voiceCashingSys/            # Voice caching system
│       ├── contextBased/               # Context-specific audio files
│       └── random/                     # Random filler sounds
│
├── frontend/                       # Frontend application (to be added)
│   └── (Your frontend code will go here)
│
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md                # System design
│   ├── SETUP.md                       # Installation guide
│   ├── API_REFERENCE.md               # API documentation
│   ├── CONTRIBUTING.md                # Development guidelines
│   └── ...
│
└── temp/                          # Temporary files (gitignored)
    ├── tts_output/                    # Generated TTS audio cache
    ├── recordings/                    # Audio recordings
    └── audio_debug/                   # Debug audio files
```

## 🔧 Technical Stack

- **Backend Framework**: FastAPI
- **Speech Recognition**: Google Cloud Speech-to-Text API
- **Speech Synthesis**: Google Cloud Text-to-Speech API
- **AI Model**: OpenAI GPT-4
- **Audio Processing**: sounddevice, pygame, numpy
- **Real-time Communication**: WebSockets
- **Environment Management**: python-dotenv

## 🚀 Quick Start

### Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure API keys (see SETUP.md)
# Create .env file with OPENAI_API_KEY and GOOGLE_APPLICATION_CREDENTIALS

# Run the server
python app.py
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# (Frontend setup instructions will be added when frontend is pushed)
```

See [SETUP.md](SETUP.md) for detailed installation and configuration instructions.

## 📖 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed system architecture and data flow
- [SETUP.md](SETUP.md) - Installation and setup guide
- [API_REFERENCE.md](API_REFERENCE.md) - API endpoints and WebSocket protocols

## 🎮 Usage

### Voice Commands

**Regular Conversation:**
- Simply speak naturally into your microphone
- The system will detect sentence completion and respond automatically

**Interruption Commands:**
- Say: "stop", "shut up", "end", "silence", "pause"
- Or press the backtick (`) key

**Special Operations:**
- "Generate code for [description]" - Creates code snippets
- "Create a graph about [topic]" - Generates visual concept maps

### WebSocket Endpoints

- `/ws/{client_id}` - Main audio WebSocket connection
- `/ws/text/{client_id}` - Text data WebSocket connection

## 🔒 Security Notes

- API keys are managed through environment variables
- Google Cloud credentials stored in JSON key files
- CORS configured for development (update for production)

## 🐛 Debugging

Debug audio files are stored in:
- `audio_debug/` - Raw audio chunks for troubleshooting
- `temp/tts_output/` - Generated TTS audio files

## 📝 License

[Add your license information here]

## 👥 Contributors

QUAD FEST Team

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Google Cloud for Speech services
- FastAPI community

