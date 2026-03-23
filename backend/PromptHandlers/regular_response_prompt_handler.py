"""
Regular Response Prompt Handler

This module manages the dynamic prompt construction for the main conversational AI.
It maintains the conversation history and context information that gets sent to
the GPT model with each request.

The prompt structure includes:
- System instructions for the AI tutor
- Dynamic context (graphs, code, keywords)
- Conversation history
- Current user input

The AI is instructed to use special JSON commands to trigger code/graph generation.
"""

import json

# Dynamic prompt structure that gets updated during conversation
# This contains references to available graphs, code, and context
dynamicPrompt = {
    "graphKeys": [],        # List of available graph names
    "graphList": {},        # Dictionary of graph data
    "contextKeys": [],      # List of available context topics
    "context": {},          # Dictionary of context information
    "recent_conversation": []  # Recent conversation turns
}

# Current conversation text (updated after each exchange)
conversation = ""

# Main prompt structure sent to GPT-4
# This is the complete message array that includes system instructions and conversation
LLMPrompt = {
    "messages": [
        {
            "role": "system",
            "content": r'You\'re an AI tutor...You will find keywords for the context below along with the graph and code names. If the user requests you to generate code, you will need to send a signaling message to the code generator in the following format: {"operation":"GENERATE_CODE", "details": {"context_keys": [], "PROMPT": "Prompt for the code generator"}} . Before you send the signalling message, make sure you have the correct format. Also when sending signalling message also say something like wait a minute. If the user request to generate a graph then you should send a signalling command in the following format: {"operation":"GENERATE_GRAPH", "details": {"context_keys": [], "PROMPT": "Prompt for the code generator"}}'
        },
        {
            "role": "system",
            "content": "You will find everything that is related to the context below"
        },
        {
            "role": "system",
            "content": json.dumps(dynamicPrompt)  # Serialized dynamic context
        },
        {
            "role": "system",
            "content": "You will find the conversation history below"
        },
        {
            "role": "user",
            "content": conversation  # Current conversation state
        }
    ]
}


def add_to_dynamic_prompt(context_type, context_key, context_value):
    """Add or update an item in the dynamic prompt.
    
    This function updates the context information that gets sent to the AI
    with each request. It allows adding new graphs, code, or context topics.
    
    Args:
        context_type: Type of context to update (e.g., "graphKeys", "context")
        context_key: Key name within that context type
        context_value: Value to store
        
    Example:
        add_to_dynamic_prompt("context", "Machine Learning", "A subset of AI...")
    """
    dynamicPrompt[context_type][context_key] = context_value
