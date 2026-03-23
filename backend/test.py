import sounddevice as sd
import numpy as np
import time
from pathlib import Path
from dotenv import load_dotenv
from VoiceHandlers.stt_handler import SpeechToTextHandler, STTConfig
from VoiceHandlers.tts_handler import TextToSpeechHandler, TTSConfig
from OpenAIClients.regular_response_generator import create_default_service, ChatConfig, AnalysisConfig
from VoiceHandlers.state_manager import StateManager, ListeningState
from VoiceHandlers.interruption import InterruptionHandler
from ContextHandlers.context_manager import ContextManager
import os
import threading
from pynput import keyboard as kb
import pygame
import queue
import json
from attention_mechanism import attention_to
from OpenAIClients.code_generator import CodeGenerator
import PromptHandlers.regular_response_prompt_handler as regular_response_prompt_handler
import asyncio
from notes_processor import NotesProcessor
from OpenAIClients.notes_generator import NotesGenerator, NotesGeneratorConfig
from OpenAIClients.graph_generator import GraphGenerator


from collections import deque


class AudioProcessor:
    def __init__(self, tts_websocket_callback = None):
        # Load environment variables
        load_dotenv()
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            raise Exception("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

        # Initialize configurations
        self.stt_config = STTConfig(
            language_code="en-US",
            enable_interim=True,
            enable_punctuation=True
        )
        
        self.tts_config = TTSConfig(
            language_code="en-US",
            voice_name="en-US-Casual-K",
            speaking_rate=1.0
        )
        
        self.chat_config = ChatConfig(
            model_name="gpt-4",
            temperature=0.7
        )
        
        self.analysis_config = AnalysisConfig(
            model_name="gpt-4",
            temperature=0
        )

        self.note_generator_config = NotesGeneratorConfig(
            model_name="gpt-4",
            temperature=1
        )

        # Initialize handlers and managers
        self.state_manager = StateManager()
        self.interruption_handler = InterruptionHandler()
        self.stt_handler = SpeechToTextHandler(self.stt_config)
        self.tts_handler = TextToSpeechHandler(self.tts_config, tts_websocket_callback)
        self.ai_service = create_default_service()
        self.context_manager = ContextManager()
        self.code_generator = CodeGenerator()
        self.graph_generator = GraphGenerator()

        # Initialize processing variables
        self.processing_timer = None
        self.accumulated_text = ""

        # Set up callbacks
        self.state_manager.register_state_change_callback(self.handle_state_change)
        self.stt_handler.partial_transcript_callback = self.handle_partial
        self.stt_handler.final_transcript_callback = self.handle_final

        self.text_websocket = None

        self.response_stream_queue = deque()
        self.regular_response_sentences_queue = queue.Queue()
        self.notes_sentences_queue = queue.Queue()

        self.response_generation_thread = None
        self._response_thread_running = False
        self.response_process = None


        self.notes_generator_running = False


        self.notes_generator_ai_service = NotesGenerator()
        self.notes_processor = NotesProcessor(self.notes_generator_ai_service)

    def generate_response_thread(self):
        """Process function for generating AI responses"""
        self.ai_service.generate_chat_response(self.response_stream_queue, self.chat_config)
        

    def process_after_delay(self, text: str, delay: float):
        """Process text after specified delay, unless new text arrives"""
        if self.processing_timer:
            self.processing_timer.cancel()
        
        self.accumulated_text = text
        
        def delayed_process():
            self.state_manager.transition_to(ListeningState.INTERRUPT_ONLY)

            regular_response_prompt_handler.LLMPrompt["messages"][-1]["content"] = text
            
            threading.Thread(target=self.process_ai_response, daemon=True).start()
            self.processing_timer = None
            self.accumulated_text = ""
            
        self.processing_timer = threading.Timer(delay, delayed_process)
        self.processing_timer.start()

    async def handle_command(self, command_json):

        if command_json.get("operation") == "GENERATE_CODE":
            await self.code_generator.generate_code(command_json, self.text_websocket)

        if command_json.get("operation") == "GENERATE_GRAPH":
            await self.graph_generator.generate_graph(command_json, self.text_websocket)


    def process_ai_response(self):
        """Process AI response and handle TTS."""

        try:
            self._response_thread_running = True
            self.response_generation_thread = threading.Thread(target=self.generate_response_thread, daemon=True)
            self.response_generation_thread.start()

            in_command = False
            command_text = ""
            accumulated_text = ""

            braces_array = []

            while True:
               
                try:
                    if len(self.response_stream_queue) == 0:
                        time.sleep(0.1)
                        continue

                    chunk = self.response_stream_queue.popleft()
                    

                    if chunk == "END":
                        # Process any remaining text before breaking
                        self.regular_response_sentences_queue.put("END")
                        break

                    for char in chunk:
                        
                        if char == '{':
                            
                            if len(braces_array) == 0 or braces_array[-1] == '{':
                                braces_array.append(char)
                                print(braces_array)
                            

                            in_command = True
                            
                            if len(braces_array) == 0:
                                command_text = "{"
                            else:
                                command_text += "{"
                           
                            continue
                        elif char == '}':

                            braces_array.pop()
                            print(braces_array)

                            if len(braces_array) == 0:
                                in_command = False

                                command_text += '}'

                                

                            else:
                                command_text += '}'
                                continue
                            
                            print(command_text)

                           

                            #Converting the command text to a json object; checking the operation and sending it to the appropriate handler
                            command_json = json.loads(command_text)
                           

                            asyncio.run(self.handle_command(command_json))

                            
                           

                        if in_command:
                            command_text += char
                            print(command_text)
                        else:
                            accumulated_text += char
                           

                            if char in '.!?' and accumulated_text.strip():
                                sentence = accumulated_text.strip()
                                
                                self.regular_response_sentences_queue.put(sentence)
                                self.notes_processor.add_sentence(sentence)
                                print("starting tts-----------------------------------------")
                                self._start_text_to_speech_thread_if_not_running()
                                self._start_notes_generating_thread_if_not_running()
                                accumulated_text = ""

                   
            
                except Exception as e:

                    print(f"Error processing AI response: {e}")

            

            # Wait for TTS to complete before cleanup
            print("Waiting for TTS to complete...")
            while self.tts_handler.is_playing:
               
                time.sleep(0.1)
            
            print("\nAudio response complete")
            
            self.stt_handler.clear_state()
            self.state_manager.reset_text()
            self.response_stream_queue.clear()
            
            # Empty the Queue properly instead of using clear()
            while not self.regular_response_sentences_queue.empty():
                try:
                    self.regular_response_sentences_queue.get_nowait()
                except queue.Empty:
                    break
            
            self.state_manager.transition_to(ListeningState.FULL_LISTENING)
            
        except Exception as e:
            print(f"Error processing AI response: {e}")
            self.stt_handler.clear_state()
            self.response_stream_queue.clear()
            
            # Empty the Queue properly in the exception handler too
            while not self.regular_response_sentences_queue.empty():
                try:
                    self.regular_response_sentences_queue.get_nowait()
                except queue.Empty:
                    break
                    
            self.state_manager.reset_text()
            self.state_manager.transition_to(ListeningState.FULL_LISTENING)

    def _start_text_to_speech_thread_if_not_running(self):

        if not self.tts_handler.stream_text_to_speech_thread_running:
            self.tts_handler.stream_text_to_speech_thread_running = True

            print("Thread for notes started")
            threading.Thread(target=self.tts_handler.stream_text_to_speech, args=(self.regular_response_sentences_queue,), daemon=True).start()


    def _start_notes_generating_thread_if_not_running(self):
        print(self.notes_processor.notes_generation_thread_running)
        if not self.notes_processor.notes_generation_thread_running:
            self.notes_processor.notes_generation_thread_running = True
            print("starting the thread for notes generation")
            threading.Thread(
                target=lambda: asyncio.run(self.notes_processor.process_continuously(self.text_websocket, self.note_generator_config)), 
                daemon=True
            ).start()

    def handle_state_change(self, old_state: ListeningState, new_state: ListeningState):
        """Handle state transitions."""
        if new_state == ListeningState.FULL_LISTENING:
            print("\nListening... (Press ` or say \"shut up\" to interrupt)")
        elif new_state == ListeningState.INTERRUPT_ONLY:
            print("\nNow in INTERRUPT_ONLY mode - monitoring for interrupt commands")

    def handle_interrupt_and_clearing(self):
        """Handle interruption by stopping playback and clearing queues."""
        if self.response_process and self.response_process.is_alive():
            self.response_process.terminate()  # This forcefully kills the process
            self.response_process.join()
            
        # Clear queues and reset state
        self.response_stream_queue.clear()

        # Clear the sentences queue
        while not self.regular_response_sentences_queue.empty():
                try:
                    self.regular_response_sentences_queue.get_nowait()
                except queue.Empty:
                    break
        
        self.state_manager.transition_to(ListeningState.INTERRUPT_ONLY)
        
        if self.processing_timer:
            self.processing_timer.cancel()
        
        self.tts_handler.stop_playback()
        time.sleep(0.2)
        self.stt_handler.clear_state()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.interruption_handler.handle_interrupt()
                start_time = time.time()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    if time.time() - start_time > 2.0:
                        pygame.mixer.music.stop()
                        break
                break
            except Exception as e:
                print(f"Retry {attempt + 1}/{max_retries}: {e}")
                time.sleep(0.1)
        
        self.tts_handler.stop_playback()
        self.stt_handler.clear_state()
        self.state_manager.reset_text()
        self.accumulated_text = ""
        time.sleep(0.1)
        
        self.tts_handler.stop_playback()
        self.stt_handler.clear_state()
        self.state_manager.transition_to(ListeningState.FULL_LISTENING)
        
        print("\nReady for new input...")

    def handle_partial(self, text: str):
        """Handle partial transcripts."""
        self.state_manager.update_text(text)
        
        if self.state_manager.current_state == ListeningState.INTERRUPT_ONLY:
            current_text = self.state_manager.get_current_text()
            if self.interruption_handler.is_interrupt_command(current_text.lower().strip()):
                print("\nInterrupt command detected!")
                self.handle_interrupt_and_clearing()

    def handle_final(self, text: str):
        """Handle final transcripts."""
        if not text.strip():
            return
        
        if self.state_manager.current_state == ListeningState.FULL_LISTENING:
            if self.processing_timer:
                self.state_manager.update_text(text)
                print(f"\nUpdating transcript: {text}")
                self.process_after_delay(text, .5)
                return
                
            self.state_manager.update_text(text)
            print(f"\nFinal transcript: {self.state_manager.get_current_text()}")
            
            #is_complete = self.ai_service.analyze_completion(text, self.analysis_config)
            
            # if is_complete:
            #     print("\nSentence complete, processing in 1 second...")
            #     self.process_after_delay(text, .5)
            # else:
            #     print("\nIncomplete sentence, processing in 2 seconds...")
            #     self.process_after_delay(text, .5)

            self.process_after_delay(text, .5)

    def on_press(self, key):
        """Handle keyboard press events."""
        try:
            if key.char == '`' and self.state_manager.current_state == ListeningState.INTERRUPT_ONLY:
                print("\nKeyboard interrupt detected!")
                self.handle_interrupt_and_clearing()
        except AttributeError:
            pass

    def handle_keyboard_interrupt(self):
        """Handle keyboard interrupts in a separate thread."""
        with kb.Listener(on_press=self.on_press) as listener:
            listener.join()

    def audio_callback(self, indata, frames, time, status):
        """Handle audio input data"""
        if status:
            print(f"Status: {status}")

        
        self.stt_handler.add_audio_data(indata.tobytes())

    def run(self):
        """Main execution loop"""
        # Start STT recognition
        self.stt_handler.start_recognition()

        # Start keyboard interrupt handler
        keyboard_thread = threading.Thread(target=self.handle_keyboard_interrupt, daemon=True)
        keyboard_thread.start()

        try:
            print("\nListening... (Press ` or say \"shut up\" to interrupt)")
            with sd.InputStream(callback=self.audio_callback,
                              channels=1,
                              samplerate=16000,
                              dtype=np.int16,
                              blocksize=4000,
                              device=None,
                              latency=0.1):
                while True:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup all resources"""
        self.stt_handler.cleanup()
        self.tts_handler.cleanup()
        self.interruption_handler.cleanup()

def main():
    processor = AudioProcessor()
    processor.run()

if __name__ == "__main__":
    main()
