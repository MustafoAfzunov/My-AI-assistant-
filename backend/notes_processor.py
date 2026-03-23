from queue import Queue, Empty
import threading
from typing import Optional
from time import sleep



from OpenAIClients.notes_generator import NotesGenerator

class NotesProcessor:
    def __init__(self, notes_generator: NotesGenerator, batch_size: int = 2):
        self.notes_generator = notes_generator
        self.sentence_queue = Queue()
        self.batch_size = batch_size
        self.is_running = False
        self.processing_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.notes_generation_thread_running = False



    def add_sentence(self, sentence: str) -> None:
        """Thread-safe method to add sentences to the queue"""
        self.sentence_queue.put(sentence)

    async def process_continuously(self, websocket, config) -> None:
        """Process sentences in batches as they arrive"""
        self.is_running = True
        current_batch = []

      

        while self.is_running:
            
           
                
            try:
                # Try to fill the batch
                while len(current_batch) < self.batch_size:
                    try:
                        sentence = self.sentence_queue.get(timeout=0.1)
                        
                        if sentence == "END":  # Check for sentinel value
                            self.is_running = False
                            break
                        current_batch.append(sentence)
                    except Empty:  # Use the imported Empty exception
                        break  # No new sentences, process what we have

                if current_batch:
                    with self._lock:
                        text_to_process = " \n ".join(current_batch)
                        result = self.notes_generator.generate_notes(text_to_process, config)
                        print(result)
                        if websocket:  # Check if websocket exists
                            await websocket.send_json({
                                "operation": "NOTES", 
                                "result": result
                            })
                        else:
                            print(f"Warning: WebSocket is None, couldn't send: {result}")
                    current_batch = []

            except Exception as e:
                print(f"Error processing notes: {str(e)}")  # Fallback to print
                current_batch = []

        self.notes_generation_thread_running = False

    def start(self, websocket) -> None:
        """Start the processing thread"""
        self.processing_thread = threading.Thread(
            target=self.process_continuously,
            args=(websocket,),
            daemon=True
        )
        self.processing_thread.start()

    def stop(self) -> None:
        """Stop the processing thread"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)