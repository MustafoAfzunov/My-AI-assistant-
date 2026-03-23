from openai import OpenAI
from os import getenv
from typing import List, Dict, Optional
from ContextHandlers.context_manager import ContextManager

class BaseGenerator:
    def __init__(self):
        """Initialize the OpenAI client with API key from environment variables."""
        self.api_key = getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=self.api_key)
        
        # Base system messages to be overridden by child classes
        self.base_messages = []

    def _create_dynamic_prompt(self, prompt: str, context: str) -> List[Dict[str, str]]:
        """Create the complete prompt with context"""
        messages = self.base_messages.copy()
        messages.extend([
            {"role": "system", "content": prompt},
            {"role": "system", "content": context}
        ])
        return messages

    def _send_request(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        top_p: float = 0.9,
        frequency_penalty: float = 0,
        presence_penalty: float = 0,
        max_tokens: Optional[int] = None
    ) -> str:
        """Send request to OpenAI API and get the response."""
        try:
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"OpenAI API request failed: {str(e)}")
            
    def generate(self, message: Dict) -> str:
        """Base generate method to be used by all generators."""
        try:
            
            cm = ContextManager()
            
            context = cm.get_from_context("context", message["details"]["context_keys"])
            prompt = message["details"]["PROMPT"]
            
            messages = self._create_dynamic_prompt(prompt, str(context))
            response = self._send_request(messages)
            
            return response
            
        except KeyError as e:
            raise ValueError(f"Missing required field in message: {e}")
        except Exception as e:
            raise Exception(f"Error generating content: {e}")