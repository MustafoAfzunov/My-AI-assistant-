from .base_generator import BaseGenerator
import json
from fastapi import WebSocket
from typing import Dict

class GraphGenerator(BaseGenerator):
    def __init__(self):
        super().__init__()
        self.base_messages = [
            {"role": "system", "content": """You are a graph generation assistant. Your task is to create a JSON structure representing a mind map or concept map. The structure must follow this exact format:

{
  "nodes": [
    {
      "id": "note-[unique_identifier]",
      "position": {
        "x": [number],
        "y": [number]
      },
      "content": "[text content]",
      "color": "[hex color code]"
    }
  ],
  "connections": [
    {
      "from": "[source node id]",
      "to": "[target node id]",
      "sourceHandle": "[one of: 'rs', 'ls', 'b']",
      "targetHandle": "[one of: 'l', 'r', 't']"
    }
  ]
}

Requirements:

Node Structure:

Generate unique IDs for each node, starting with "note-" followed by a unique identifier (e.g., "note-1", "note-2").
Nodes should be spaced 500 - 600 pixels apart to prevent overlap(both horizontally and vertically).
Position the nodes such that they seem natural(not in a strict grid)
Each node must have meaningful text content.
Assign each node a valid hex color code (e.g., #FFD700, #6EEDC8).
Logical Positioning and Connections:

Main concept should be centrally positioned, with related concepts branching outward.
If a node is positioned directly below another, connect the bottom (b) of the upper node to the top (t) of the lower node.
If a node is positioned directly to the right of another, connect the right (rs) of the left node to the left (l) of the right node.
If a node is positioned directly to the left of another, connect the left (ls) of the right node to the right (r) of the left node.
If a node is positioned diagonally, choose the most logical connection based on its relative placement.
Valid Connection Rules:
The following are the only valid connections:

"rs" (right side) → "l" (left side)
"ls" (left side) → "r" (right side)
"b" (bottom) → "t" (top)
"rs" (right side) → "t" (top)
"ls" (left side) → "t" (top)
"b" (bottom) → "l" (left)
"b" (bottom) → "r" (right)
Node Count & Layout:

Create 10 - 15 nodes with logical hierarchical relationships.
Ensure nodes follow a structured, readable layout, avoiding random placement.
Do not create connections to non-existent nodes.
Task:
Generate a graph structure about [topic] based on key concepts and their relationships. Ensure clear organization and logical flow. Respond ONLY with the pure JSON structure, no additional text or markdown formatting. Do not include ```json or ``` markers."""},
            {"role": "system", "content": "You will find all the necessary context below"}
        ]
        
    async def generate_graph(self, message: Dict, websocket: WebSocket) -> str:
        """Wrapper method for generate"""
        response = self.generate(message)

        # Remove any markdown formatting that might be present
        clean_response = self._clean_json_response(response)
        
        print(clean_response)
        await websocket.send_json({
            "operation": "GRAPH",
            "details": clean_response
        })
        
    def _clean_json_response(self, response: str) -> str:
        """
        Clean the response to ensure it's valid JSON without markdown formatting.
        """
        # Remove markdown code blocks if present
        if response.startswith("```"):
            # Find the first and last ``` markers
            first_marker_end = response.find("\n", 3)
            last_marker_start = response.rfind("```")
            
            if first_marker_end != -1 and last_marker_start > first_marker_end:
                response = response[first_marker_end + 1:last_marker_start].strip()
        
        # Ensure we have a valid JSON object
        try:
            # Parse and re-stringify to ensure valid JSON format
            json_obj = json.loads(response)
            return json.dumps(json_obj)
        except json.JSONDecodeError:
            # If parsing fails, return a minimal valid graph
            return json.dumps({
                "nodes": [
                    {
                        "id": "note-1",
                        "position": {"x": 500, "y": 500},
                        "content": "Error: Could not generate valid graph",
                        "color": "#FF0000"
                    }
                ],
                "connections": []
            })