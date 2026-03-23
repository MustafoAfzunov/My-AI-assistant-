from openai import OpenAI
from typing import Iterator
from dataclasses import dataclass

@dataclass
class NotesGeneratorConfig:
    """Configuration for chat completion"""
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7



class NotesGenerator:
    def __init__(self):
        self.client = OpenAI()  # Will use OPENAI_API_KEY from environment

   
    def generate_notes(self, text: str, config: NotesGeneratorConfig) -> str:
        """Generate streaming chat response with improved chunking."""
        try:
            response = self.client.chat.completions.create(
                model=config.model_name,
                messages=[
                    {"role": "system", "content": """You are a notes generator. Given a text input, extract and convert key explanations into concise, structured notes—similar to how a teacher summarizes key points on a board while lecturing. If you feel like a new concept is introduced, return the name of that concept in the following format: <strong> Name of the concept </strong> Focus only on explanatory content, omitting greetings, user references, or conversational elements. Ensure the notes are clear, well-organized, and capture only essential information. If the text contains greetings or user-specific dialogue (e.g., "Good morning, how can I assist you?"), ignore them and return an empty string"""},
                    {"role": "user", "content": text}
                ],
                temperature=config.temperature
                
            )

            return response.choices[0].message.content

                 
        except Exception as e:
           print("Error in notes_generator.py", e)

