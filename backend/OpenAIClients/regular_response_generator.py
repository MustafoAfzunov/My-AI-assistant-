"""
OpenAI Service Module

This module handles interactions with OpenAI's GPT models for:
- Generating conversational AI responses
- Analyzing sentence completion
- Managing conversation memory/context

The service supports streaming responses and maintains conversation history
with configurable memory limits to optimize API usage.
"""

from openai import OpenAI
from typing import Iterator
from dataclasses import dataclass
from collections import deque
import PromptHandlers.regular_response_prompt_handler as regular_response_prompt_handler

@dataclass
class ChatConfig:
    """Configuration for chat completion
    
    Attributes:
        model_name: OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
        temperature: Randomness in responses (0.0 = deterministic, 2.0 = very random)
        memory_limit: Number of conversation turns to remember (helps manage token usage)
    """
    model_name: str = "gpt-4"
    temperature: float = 0.7
    memory_limit: int = 10  # Number of conversation turns to remember

@dataclass
class AnalysisConfig:
    """Configuration for sentence analysis
    
    Uses temperature=0 for deterministic analysis of sentence completion.
    
    Attributes:
        model_name: OpenAI model to use for analysis
        temperature: Set to 0 for consistent analysis results
    """
    model_name: str = "gpt-4"
    temperature: float = 0

class OpenAIService:
    def __init__(self, memory_limit: int = 10):
        """Initialize OpenAI service with conversation memory management.
        
        Args:
            memory_limit: Maximum number of conversation turns to keep in memory.
                         Older messages are automatically trimmed to save tokens.
        """
        self.client = OpenAI()  # Will use OPENAI_API_KEY from environment
        self.context = ""  # Accumulated conversation context
        self.memory_limit = memory_limit
        self.conversation_history = []  # Stores message history

    def analyze_completion(self, text: str, config: AnalysisConfig) -> bool:
        """Analyze if the given text forms a complete thought/sentence.
        
        This is used to determine when to process user input. Complete sentences
        trigger faster processing (1s delay) while incomplete ones wait longer (2s)
        to allow the user to continue speaking.
        
        Args:
            text: The text to analyze
            config: Analysis configuration (model and temperature)
            
        Returns:
            True if the text forms a complete thought, False otherwise
        """
        try:
            response = self.client.chat.completions.create(
                model=config.model_name,
                messages=[
                    {"role": "system", "content": "You are a sentence completion analyzer. "
                     "Respond with ONLY 'true' or 'false' to indicate if the input forms a complete thought."},
                    {"role": "user", "content": text}
                ],
                temperature=config.temperature
            )
            return response.choices[0].message.content.strip().lower() == 'true'
        except Exception as e:
            print(f"Analysis error: {e}")
            return False

    def generate_chat_response(self, queue: deque, config: ChatConfig) -> Iterator[str]:
        """Generate streaming chat response with improved chunking.
        
        This method streams the AI response in real-time, allowing the TTS system
        to start speaking before the full response is generated. This significantly
        reduces perceived latency.
        
        Args:
            queue: Deque to store response chunks as they arrive
            config: Chat configuration (model, temperature, memory limit)
            
        The response is streamed chunk-by-chunk into the queue, ending with "END"
        sentinel value to signal completion.
        """

        print("Request sent---------------------------------------------------------")
        try:
            # Use memory limit from config if provided, otherwise use instance default
            memory_limit = getattr(config, 'memory_limit', self.memory_limit)
            
            # Get messages from prompt handler (includes system prompt, context, and conversation)
            messages = regular_response_prompt_handler.LLMPrompt["messages"]
            
            # Apply memory limit to prevent sending too many tokens to the API
            # This keeps only the system message + the most recent N messages
            if len(messages) > memory_limit + 1:  # +1 for the system message
                # Keep system message and last memory_limit messages
                limited_messages = [messages[0]] + messages[-(memory_limit):]
                messages = limited_messages
            
            response = self.client.chat.completions.create(
                model=config.model_name,
                messages=messages,
                temperature=config.temperature,
                stream=True
            )

            buffer = ""  # Accumulate full response for context storage

            print("Got the response-------------------------------------------------------")
            # Stream response chunks as they arrive
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    
                    buffer += content  # Build complete response
                    queue.append(content)  # Send chunk to TTS immediately
                    

            # Signal end of response stream
            queue.append("END")

            # Update conversation context with the complete response
            self.context = self.context + " " +  buffer
            
            # Update conversation history and trim if needed
            self.conversation_history.append({"role": "assistant", "content": buffer})
            if len(self.conversation_history) > self.memory_limit * 2:  # *2 for user+assistant pairs
                # Keep only recent history to manage memory
                self.conversation_history = self.conversation_history[-self.memory_limit*2:]
                
            # Update the prompt handler with latest conversation state
            regular_response_prompt_handler.conversation = self.context
            

            print(regular_response_prompt_handler.LLMPrompt["messages"][-1])

            print(self.context)

           
                    
        except Exception as e:
            print(f"Error generating chat response: {e}")

def create_default_service() -> OpenAIService:
    """Factory function to create OpenAI service with default settings.
    
    Returns:
        OpenAIService instance with 10-turn memory limit
    """
    return OpenAIService(memory_limit=10)
