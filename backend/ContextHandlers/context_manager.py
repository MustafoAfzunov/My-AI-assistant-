"""
Context Manager Module

This module provides a centralized storage system for conversation context,
generated graphs, and code snippets. The context is shared across all instances
using class-level storage, allowing different parts of the system to access
the same information.

Context Types:
- graphs: Visual concept maps and mind maps
- code: Generated code snippets
- context: Explanations and information about topics
"""

class ContextManager:
    # Static context storage shared across all instances
    # This allows the AI to reference previously discussed topics and generated content
    context_storage = {
        "graphs": {
            # Example: "Quantum Mechanics Tree": {"data": "Graph details..."}
            "Quantum Mechanics Tree": {"data": "Graph details for Quantum Mechanics Tree"},
            "Something Else Tree": {"data": "Graph details for Something Else Tree"}
        },
        "code": {
            # Example: "Binary Tree": {"data": "Code implementation..."}
            "Binary Tree": {"data": "Code details for Binary Tree"},
            "Binary Search": {"data": "Code details for Binary Search"}
        },
        "context": {
            # Example: "Quantum Mechanics": ["explanation 1", "explanation 2"]
            "Quantum Mechanics": ["is a field that studies...", "involves bla bla bla"],
            "Something Else": ["bla bla bla", "more bla"]
        }
    }

    def __init__(self):
        """Initialize ContextManager instance.
        
        Note: Context storage is class-level, so all instances share the same data.
        """
        # Initialize any instance-specific attributes if needed
        pass

    @classmethod
    def get_from_context(cls, context_type, keywords):
        """Retrieve items from the context based on type and keywords.
        
        This method is used to fetch relevant context when generating responses,
        code, or graphs. It allows the AI to reference previously discussed topics.
        
        Args:
            context_type: Type of context to retrieve ("graphs", "code", or "context")
            keywords: List of keys to retrieve from the specified context type
            
        Returns:
            Dictionary containing the requested context items
            
        Example:
            cm = ContextManager()
            context = cm.get_from_context("context", ["Quantum Mechanics"])
            # Returns: {"context": {"Quantum Mechanics": ["is a field...", "involves..."]}}
        """
        context_to_send = {context_type: {}}

        for key in keywords:
            if key in cls.context_storage.get(context_type, {}):
                context_to_send[context_type][key] = cls.context_storage[context_type][key]
            else:
                print(f"Warning: Key '{key}' not found in '{context_type}' context.")
        
        return context_to_send

    @classmethod
    def add_to_context(cls, context_type, keyword, value):
        """Add a new item to the context or append to existing item.
        
        If the keyword already exists, the new value is appended to the existing
        value with a period separator. This allows building up context over time.
        
        Args:
            context_type: Type of context ("graphs", "code", or "context")
            keyword: Key name for the context item
            value: Value to store or append
            
        Example:
            cm = ContextManager()
            cm.add_to_context("context", "Neural Networks", "A type of machine learning")
            cm.add_to_context("context", "Neural Networks", "Uses layers of neurons")
            # Result: {"Neural Networks": "A type of machine learning. Uses layers of neurons"}
        """
        # Create context type if it doesn't exist
        if context_type not in cls.context_storage:
            cls.context_storage[context_type] = {}
        
        # Add new or append to existing
        if keyword not in cls.context_storage[context_type]:
            cls.context_storage[context_type][keyword] = value
        else:
            # Append to existing context with period separator
            cls.context_storage[context_type][keyword] += ". " + value
        print(f"Added '{keyword}' to '{context_type}' context.")
        
        
