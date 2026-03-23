from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from test import AudioProcessor
import json
import base64
import numpy as np
from typing import Dict
import uvicorn
import wave
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

class WebSocketAudioProcessor:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.text_connections: Dict[str, WebSocket] = {}  # New dictionary for text connections
        self.processors: Dict[str, AudioProcessor] = {}
        self.sample_rate = 16000

    async def send_audio(self, client_id: str, audio_data: bytes):
        """Send audio data back to the client"""
        if client_id in self.connections:
            try:
                await self.connections[client_id].send_bytes(audio_data)
            except Exception as e:
                print(f"Error sending audio to client {client_id}: {e}")
                # Connection might be broken, clean up
                await self.cleanup_client(client_id)

    async def send_text(self, client_id: str, json_data: str):
        if client_id in self.connections:
            try:
                await self.connections[client_id].send(json.dumps(json_data))
            except Exception as e:
                print(f"Error sending text to client {client_id}: {e}")
                # Connection might be broken, clean up
                await self.cleanup_client(client_id)

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.connections[client_id] = websocket
        
        # Create callback for TTS handler
        async def audio_callback(audio_data):
            await self.send_audio(client_id, audio_data)
            
        self.processors[client_id] = AudioProcessor(audio_callback)
        self.processors[client_id].stt_handler.start_recognition();
        print(f"Client {client_id} connected")

    async def connect_text(self, websocket: WebSocket, client_id: str):
        """Handle text WebSocket connection"""
        await websocket.accept()
        self.text_connections[client_id] = websocket
        if client_id in self.processors:
            print("setting text websocket for client", client_id)
            self.processors[client_id].text_websocket = websocket
        print(f"Client {client_id} connected to text WebSocket")

    def process_audio(self, client_id: str, audio_data: bytes):
        """Process incoming audio data"""
        if client_id in self.processors:
            # Convert audio bytes to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
             
            self.processors[client_id].audio_callback(audio_np, None, None, None)

    # Somewhere in your AudioProcessor class, add this method
    async def send_text_message(self, message):
        """Send a text message through the text WebSocket if available"""
        try:
            if hasattr(self, 'text_websocket') and self.text_websocket is not None:
                await self.text_websocket.send_json(message)
            else:
                print(f"Warning: WebSocket is None, couldn't send: {message}")
        except Exception as e:
            print(f"Error sending text message: {e}")
            
    async def cleanup_client(self, client_id: str):
        """Clean up all resources for a client"""
        try:
            if client_id in self.processors:
                self.processors[client_id].cleanup()
                del self.processors[client_id]
            if client_id in self.connections:
                del self.connections[client_id]
            if client_id in self.text_connections:
                del self.text_connections[client_id]
            print(f"All resources cleaned up for client {client_id}")
        except Exception as e:
            print(f"Error during cleanup for client {client_id}: {e}")

    def disconnect(self, client_id: str):
        if client_id in self.processors:
            self.processors[client_id].cleanup()
            del self.processors[client_id]
        if client_id in self.connections:
            del self.connections[client_id]
        print(f"Client {client_id} disconnected")

    def disconnect_text(self, client_id: str):
        """Handle text WebSocket disconnection"""
        if client_id in self.text_connections:
            del self.text_connections[client_id]
        print(f"Client {client_id} disconnected from text WebSocket")


  
            
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ws_processor = WebSocketAudioProcessor()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    print(f"\n=== New WebSocket connection attempt from {client_id} ===")
    await ws_processor.connect(websocket, client_id)
    print(f"WebSocket connection accepted for {client_id}")
    
    try:
        while True:
            try:
                data = await websocket.receive_json()
                
                if data["type"] == "audio":
                    audio_bytes = base64.b64decode(data["data"])
                    ws_processor.process_audio(client_id, audio_bytes)
                elif data["type"] == "interrupt":
                    print(f"Received interrupt from {client_id}")
                    if client_id in ws_processor.processors:
                        ws_processor.processors[client_id].handle_interrupt_and_clearing()
                elif data["type"] == "playback_complete":
                    print(f"Client {client_id} completed audio playback")
                    if client_id in ws_processor.processors:
                        ws_processor.processors[client_id].tts_handler.is_playing = False
                        print(f"Reset playback state for client {client_id}")
                # Add this new handler for the register_text_websocket messages
                elif data["type"] == "register_text_websocket":
                    print(f"Registering text WebSocket for client {client_id}")
                    if client_id in ws_processor.processors and client_id in ws_processor.text_connections:
                        # Get the text WebSocket for this client
                        text_websocket = ws_processor.text_connections[client_id]
                        # Assign it to the processor
                        ws_processor.processors[client_id].text_websocket = text_websocket
                        print(f"Text WebSocket registered for client {client_id}")
                    else:
                        print(f"Cannot register text WebSocket: client {client_id} not found in processors or text_connections")
            except RuntimeError as e:
                if "disconnect message has been received" in str(e):
                    print(f"\n=== WebSocket disconnect detected for {client_id} ===")
                    break
                else:
                    raise
    
    except WebSocketDisconnect:
        print(f"\n=== WebSocket disconnected for {client_id} ===")
    except Exception as e:
        print(f"\n=== Error in WebSocket connection for {client_id}: {str(e)} ===")
    finally:
        await ws_processor.cleanup_client(client_id)
        print(f"Cleaned up resources for {client_id}")


@app.websocket("/ws/text/{client_id}")
async def text_websocket_endpoint(websocket: WebSocket, client_id: str):
    print(f"\n=== New Text WebSocket connection attempt from {client_id} ===")
    await ws_processor.connect_text(websocket, client_id)
    print(f"Text WebSocket connection accepted for {client_id}")
    
    try:
        while True:
            # Handle both string and JSON messages
            try:
                message = await websocket.receive()
                
                if "text" in message:
                    # This is a text message
                    text_data = message["text"]
                    print(f"Received text from client {client_id}: {text_data}")
                    
                    try:
                        # Try to parse as JSON
                        json_data = json.loads(text_data)
                        if isinstance(json_data, dict) and "type" in json_data:
                            if json_data["type"] == "keep-alive":
                                # Just a keep-alive, no need to process further
                                continue
                            elif json_data["type"] == "init":
                                # Client is initializing
                                print(f"Text WebSocket initialized for client {client_id}")
                                # Make sure the processor has this text WebSocket
                                if client_id in ws_processor.processors:
                                    ws_processor.processors[client_id].text_websocket = websocket
                            elif json_data["type"] == "playback_complete_notification":
                                # Client completed audio playback
                                print(f"Received playback completion notification for client {client_id}")
                                # Make sure the processor has this text WebSocket
                                if client_id in ws_processor.processors:
                                    ws_processor.processors[client_id].text_websocket = websocket
                    except json.JSONDecodeError:
                        # Not JSON, process as regular text
                        pass
                elif "type" in message and message["type"] == "websocket.disconnect":
                    # Handle disconnect message
                    print(f"\n=== Text WebSocket disconnect message received for {client_id} ===")
                    break
                    
                # Always ensure the processor has the latest text WebSocket
                if client_id in ws_processor.processors:
                    ws_processor.processors[client_id].text_websocket = websocket
                    
            except RuntimeError as e:
                if "disconnect message has been received" in str(e):
                    print(f"\n=== Text WebSocket disconnect detected for {client_id} ===")
                    break
                else:
                    raise
                
    except WebSocketDisconnect:
        print(f"\n=== Text WebSocket disconnected for {client_id} ===")
    except Exception as e:
        print(f"\n=== Error in Text WebSocket connection for {client_id}: {str(e)} ===")
    finally:
        ws_processor.disconnect_text(client_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 