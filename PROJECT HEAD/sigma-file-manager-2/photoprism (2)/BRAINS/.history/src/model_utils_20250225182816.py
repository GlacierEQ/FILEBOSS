import os
from typing import Dict, Any, List, Optional, Tuple

# For improved models
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Default system prompts
SYSTEM_PROMPTS = {
    "general": "You are a helpful assistant that helps users manage their files and folders.",
    "technical": "You are a technical assistant with expertise in file systems and organization.",
    "creative": "You are a creative assistant that helps users organize and manage their digital assets."
}

# Natural language instruction keywords
INSTRUCTION_KEYWORDS = {
    "list": ["list", "show", "display", "see"],
    "move": ["move", "relocate", "transfer", "shift"],
    "copy": ["copy", "duplicate", "replicate"],
    "delete": ["delete", "remove", "erase"],
    "create": ["create", "make", "new"],
    "organize": ["organize", "sort", "arrange", "classify"],
    "evolve": ["evolve", "improve", "enhance", "optimize"],
}

def load_chat_model(model_name: str = "gpt2-large"):
    """Load a more powerful language model for chat functionality"""
    try:
        return pipeline(
            "text-generation",
            model=model_name,
            tokenizer=model_name,
            max_new_tokens=200
        )
    except Exception as e:
        # Fallback to smaller model if loading fails
        print(f"Error loading model {model_name}: {e}. Falling back to gpt2.")
        return pipeline("text-generation", model="gpt2")

def detect_instruction(message: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Detect if a message contains a natural language instruction
    Returns (instruction_type, parameters)
    """
    message = message.lower().strip()
    
    for instruction, keywords in INSTRUCTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message:
                # Extract parameters (simple version)
                params = {}
                if instruction == "list":
                    params["path"] = extract_path_from_message(message)
                elif instruction in ["move", "copy"]:
                    params["source"], params["destination"] = extract_source_dest_from_message(message)
                elif instruction == "evolve":
                    params["prompt"] = message  # Use full message as prompt
                
                return instruction, params
    
    return None, None

def extract_path_from_message(message: str) -> Optional[str]:
    """Extract a file path from a message"""
    # Very basic extraction - in a real system, use NLP or regex
    parts = message.split(" in ")
    if len(parts) > 1:
        return parts[1].strip()
    return None

def extract_source_dest_from_message(message: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract source and destination paths from a message"""
    # Very basic extraction - would use more sophisticated parsing in production
    if " from " in message and " to " in message:
        parts = message.split(" from ")
        before_from = parts[0]
        after_from = parts[1]
        if " to " in after_from:
            to_parts = after_from.split(" to ")
            return to_parts[0].strip(), to_parts[1].strip()
    return None, None

def format_prompt(message: str, system_prompt: str = None, history: List[Dict] = None) -> str:
    """
    Format a message with a system prompt and chat history
    Returns a structured prompt for the model
    """
    prompt = ""
    
    # Add system prompt
    if system_prompt:
        prompt += f"System: {system_prompt}\n\n"
    
    # Add chat history
    if history:
        for entry in history:
            if "user" in entry:
                prompt += f"User: {entry['user']}\n"
            if "assistant" in entry:
                prompt += f"Assistant: {entry['assistant']}\n"
    
    # Add current message
    prompt += f"User: {message}\nAssistant:"
    
    return prompt

def process_response(generated_text: str) -> str:
    """Clean up and extract the model's response"""
    # Find where the assistant's response starts
    if "Assistant:" in generated_text:
        response = generated_text.split("Assistant:")[-1].strip()
    else:
        response = generated_text.strip()
    
    # Remove any trailing "User:" or incomplete sentences
    if "User:" in response:
        response = response.split("User:")[0].strip()
    
    return response
