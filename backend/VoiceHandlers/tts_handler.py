from google.cloud import texttospeech
from typing import Optional, Iterator, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import queue
import threading
import pygame
import os
import time
import asyncio
import json
from collections import deque


@dataclass
class TTSConfig:
    """Configuration for text-to-speech processing"""
    language_code: str = "en-US"
    voice_name: str = "en-US-Casual-K"
    speaking_rate: float = 1.0
    pitch: float = 0.0  # Default pitch (between -20.0 and 20.0)
    volume_gain_db: float = 0.0  # Default volume (between -96.0 and 16.0)
    output_dir: Path = Path("temp/tts_output")

class TextToSpeechHandler:
    def __init__(self, config: Optional[TTSConfig] = None, websocket_callback = None):
        self.config = config or TTSConfig()
        self.client = texttospeech.TextToSpeechClient()
        self.audio_queue = queue.Queue()
        self.is_playing = False
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize pygame mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Start playback thread
        self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()
        
        self._should_stop = False
        self.sentence_buffer = []
        self.is_first_sentence = True

        self.websocket_callback = websocket_callback
        self.stream_text_to_speech_thread_running = False
        
        # Emotion presets
        self.emotion_presets = {
            "happy": {"pitch": 2.0, "speaking_rate": 1.2, "volume_gain_db": 2.0},
            "sad": {"pitch": -2.0, "speaking_rate": 0.85, "volume_gain_db": -1.0},
            "excited": {"pitch": 4.0, "speaking_rate": 1.0, "volume_gain_db": 3.5},
            "calm": {"pitch": -1.0, "speaking_rate": 0.9, "volume_gain_db": 0.0},
            "angry": {"pitch": 0.0, "speaking_rate": 1.1, "volume_gain_db": 4.0},
            "fearful": {"pitch": 3.0, "speaking_rate": 1.25, "volume_gain_db": 1.0},
            "neutral": {"pitch": 0.0, "speaking_rate": 1.0, "volume_gain_db": 0.0}
        }

    def stream_text_to_speech(self, sentences_queue: queue.Queue, emotion: str = "excited") -> None:
        """Process streaming text input with immediate playback."""
        self.is_playing = True
        
        while True:
            if sentences_queue.empty():
                time.sleep(0.1)
                continue

            sentence = sentences_queue.get()
           
            # Check for END sentinel without processing it
            if sentence == "END":
                time.sleep(0.5)  # Add small delay
               
                break
            
            # Check if the sentence contains emotion control tags
            if sentence.startswith("[emotion:") and "]" in sentence:
                emotion_end = sentence.find("]")
                emotion_tag = sentence[1:emotion_end]
                emotion_parts = emotion_tag.split(":")
                if len(emotion_parts) == 2:
                    emotion = emotion_parts[1].strip().lower()
                    sentence = sentence[emotion_end+1:].strip()
            
            audio = self._generate_speech(sentence, emotion)
            self.audio_queue.put(audio)
            self._start_playback()

        print("TTS stream finished")
        self.stream_text_to_speech_thread_running = False

    def _generate_speech(self, text: str, emotion: str = "excited") -> bytes:
        """Generate speech from text with specified emotion and return audio content."""
        # Get emotion settings or use neutral if not found
        emotion_settings = self.emotion_presets.get(emotion, self.emotion_presets["neutral"])
        
        # Apply SSML for more control
        ssml_text = f"""
        <speak>
            <prosody rate="{emotion_settings['speaking_rate']}" 
                     pitch="{emotion_settings['pitch']}st"
                     volume="{emotion_settings['volume_gain_db']}dB">
                {text}
            </prosody>
        </speak>
        """
        
        response = self.client.synthesize_speech(
            input=texttospeech.SynthesisInput(ssml=ssml_text),
            voice=texttospeech.VoiceSelectionParams(
                language_code=self.config.language_code,
                name=self.config.voice_name
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
        )
        
        return response.audio_content

    def set_emotion(self, text: str, emotion: str) -> str:
        """Add emotion tag to text"""
        return f"[emotion:{emotion}] {text}"
        
    def _playback_worker(self) -> None:
        """Handle audio streaming in background thread."""
        CHUNK_SIZE = 4096  # Adjust chunk size as needed
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                audio_content = self.audio_queue.get()
                if audio_content is None:
                    break
                
                print("Setting is playing to true")
                
                # Stream audio in chunks
                loop.run_until_complete(self.websocket_callback(audio_content))
                        
            except Exception as e:
                print(f"Streaming error: {e}")
        
        # Clean up the event loop
        loop.close()

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'([.!?])\s+', text)
        result = []
        
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i + 1] in '.!?':
                result.append(sentences[i] + sentences[i + 1])
                i += 2
            else:
                result.append(sentences[i])
                i += 1
        
        return result

    def cleanup(self) -> None:
        """Cleanup resources."""
        self.audio_queue.put(None)
        if pygame.mixer.get_init():
            pygame.mixer.quit()

    def stop_playback(self) -> None:
        """Stop current audio playback and clear audio queue."""
        self._should_stop = True

        # Send stop signal to frontend via websocket callback
        if self.websocket_callback:
            try:
                # Create and set a new event loop for this thread
                loop = asyncio.get_event_loop()
                # Run the async function in this event loop
                loop.run_until_complete(self.websocket_callback(json.dumps({
                    "type": "should_stop",
                    "data": "stop_playback"
                })))

                # Close the loop after use to clean up
                
            except Exception as e:
                print(f"Error sending stop signal: {e}")

        # Clear the audio queue and reset internal state
        print("in stop playback")
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        self.audio_queue.put(None)
        self.is_playing = False
        self.is_first_sentence = True
        self.sentence_buffer = []

        # Clear the queue again
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def _start_playback(self) -> None:
        """Start the playback thread if not already running."""
        if not hasattr(self, 'playback_thread') or not self.playback_thread.is_alive():
            self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.playback_thread.start()
