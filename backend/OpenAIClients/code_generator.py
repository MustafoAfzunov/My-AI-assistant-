from .base_generator import BaseGenerator
from fastapi import WebSocket
from typing import Dict
import json
import re


class CodeGenerator(BaseGenerator):
    def __init__(self):
        super().__init__()
        self.base_messages = [
            {"role": "system", "content": "You are a code generator. You will be given a task description and a context. You need to generate code based on the descritpion and also it must be relevant to the context given to you. You must output the code in the following format: a = 1 /n b = 2 /n c = a + b' ...."},
            {"role": "system", "content": "You will find all the necessary context below"},
            {"role": "system", "content": "IMPORTANT: Do not include markdown code blocks or language identifiers. Just return the raw code directly."}
        ]
        
    def _extract_pure_code(self, response: str) -> str:
        """Extract pure code from response, removing markdown formatting"""
        # Remove markdown code blocks if present
        code_block_pattern = r"```(?:python|[a-zA-Z]*)\n([\s\S]*?)\n```"
        code_blocks = re.findall(code_block_pattern, response)
        
        if code_blocks:
            # If code blocks were found, join them together
            return "\n\n".join(code_blocks)
        else:
            # If no code blocks, return the original response
            return response.strip()
        
    async def generate_code(self, message: Dict, websocket: WebSocket) -> str:
        """Wrapper method for generate"""
        response = self.generate(message)
        
        # Extract pure code from the response
        pure_code = self._extract_pure_code(response)

        await websocket.send_json({
            "operation": "CODE_GENERATION",
            "details": pure_code
        })