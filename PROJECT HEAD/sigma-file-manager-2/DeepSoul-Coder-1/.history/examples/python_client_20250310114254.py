"""
Python client library for DeepSeek-Coder API.
This example demonstrates how to interact with the DeepSeek-Coder API endpoints.
"""

import os
import requests
import json
from typing import List, Dict, Any, Optional, Union
import time

class DeepSeekCoderClient:
    """Client for interacting with the DeepSeek-Coder API."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize the DeepSeek-Coder client.
        
        Args:
            base_url: The base URL of the DeepSeek-Coder API server
            api_key: API key for authentication (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.session = requests.Session()
        
        # Setup headers
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        if response.status_code == 200:
            return response.json()
        
        error_message = f"API request failed with status code {response.status_code}"
        try:
            error_data = response.json()
            if "detail" in error_data:
                error_message = f"{error_message}: {error_data['detail']}"
        except:
            error_message = f"{error_message}: {response.text}"
        
        raise Exception(error_message)
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API server is healthy."""
        response = self.session.get(f"{self.base_url}/health", headers=self.headers)
        return self._handle_response(response)
    
    def code_completion(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.95,
        language: Optional[str] = None,
        stop: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate code completion based on the provided prompt.
        
        Args:
            prompt: The code prompt to complete
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)
            top_p: Nucleus sampling parameter (0.0 to 1.0)
            language: Programming language for better results (optional)
            stop: Stop sequences to end generation (optional)
            
        Returns:
            API response containing the generated completion
        """
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if language:
            payload["language"] = language
        
        if stop:
            payload["stop"] = stop
            
        response = self.session.post(
            f"{self.base_url}/api/v1/completion",
            headers=self.headers,
            json=payload
        )
        
        return self._handle_response(response)
    
    def code_insertion(
        self,
        prefix: str,
        suffix: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate code to insert between prefix and suffix.
        
        Args:
            prefix: Code that comes before the insertion point
            suffix: Code that comes after the insertion point
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)
            top_p: Nucleus sampling parameter (0.0 to 1.0)
            stop: Stop sequences to end generation (optional)
            
        Returns:
            API response containing the generated insertion
        """
        payload = {
            "prefix": prefix,
            "suffix": suffix,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if stop:
            payload["stop"] = stop
            
        response = self.session.post(
            f"{self.base_url}/api/v1/insertion",
            headers=self.headers,
            json=payload
        )
        
        return self._handle_response(response)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Chat with the AI model for interactive coding help.
        
        Args:
            messages: List of message dictionaries, each with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)
            top_p: Nucleus sampling parameter (0.0 to 1.0)
            stop: Stop sequences to end generation (optional)
            
        Returns:
            API response containing the chat completion
        """
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if stop:
            payload["stop"] = stop
            
        response = self.session.post(
            f"{self.base_url}/api/v1/chat",
            headers=self.headers,
            json=payload
        )
        
        return self._handle_response(response)


# Example usage
def main():
    """Example usage of the DeepSeek-Coder client."""
    # Initialize client
    client = DeepSeekCoderClient(
        base_url="http://localhost:8000",
        api_key=os.environ.get("DEEPSEEK_API_KEY")
    )
    
    # Check if the API is healthy
    try:
        health = client.health_check()
        print(f"API Status: {health['status']}, Model: {health.get('model', 'unknown')}")
    except Exception as e:
        print(f"API health check failed: {str(e)}")
        return
    
    # Example 1: Code completion
    print("\n=== Code Completion Example ===")
    try:
        completion_response = client.code_completion(
            prompt="def fibonacci(n):",
            max_tokens=150,
            temperature=0.7
        )
        print("Generated code:")
        print(completion_response["choices"][0]["text"])
    except Exception as e:
        print(f"Code completion failed: {str(e)}")
    
    # Example 2: Code insertion
    print("\n=== Code Insertion Example ===")
    try:
        insertion_response = client.code_insertion(
            prefix="def calculate_sum(a, b):",
            suffix="    return result",
            max_tokens=50
        )
        print("Inserted code:")
        print(insertion_response["choices"][0]["text"])
    except Exception as e:
        print(f"Code insertion failed: {str(e)}")
    
    # Example 3: Chat
    print("\n=== Chat Example ===")
    try:
        chat_response = client.chat(
            messages=[
                {"role": "user", "content": "Write a function to calculate the factorial of a number in Python"}
            ],
            max_tokens=300
        )
        print("AI response:")
        print(chat_response["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"Chat failed: {str(e)}")


if __name__ == "__main__":
    main()
