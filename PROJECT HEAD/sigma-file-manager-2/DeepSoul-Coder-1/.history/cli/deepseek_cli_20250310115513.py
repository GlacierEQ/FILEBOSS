#!/usr/bin/env python
"""
DeepSeek-Coder CLI - Command Line Interface for DeepSeek-Coder

This tool allows users to interact with DeepSeek-Coder directly from the command line.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Union, Any
import requests
import importlib.util

# Check if rich is available for better formatting
try:
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.panel import Panel
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False


class DeepSeekCLI:
    """CLI wrapper for DeepSeek-Coder API."""
    
    def __init__(self):
        self.api_url = os.environ.get("DEEPSEEK_API_URL", "http://localhost:8000")
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", None)
        self.verbose = False
    
    def set_api_url(self, url: str) -> None:
        """Set the API URL."""
        self.api_url = url.rstrip("/")
    
    def set_api_key(self, api_key: str) -> None:
        """Set the API key."""
        self.api_key = api_key
    
    def set_verbose(self, verbose: bool) -> None:
        """Set verbose mode."""
        self.verbose = verbose
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the API."""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        url = f"{self.api_url}{endpoint}"
        
        if self.verbose:
            print(f"Request URL: {url}")
            print(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                error_message = error_data.get("detail", str(e))
            except:
                error_message = str(e)
            
            print(f"Error: {error_message}")
            if self.verbose:
                print(f"Response status: {e.response.status_code}")
                print(f"Response headers: {e.response.headers}")
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            print(f"Error: Could not connect to API at {self.api_url}")
            print("Please check that the API server is running and accessible.")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
    
    def complete(self, prompt: str, max_tokens: int = 100, 
                 temperature: float = 0.7, language: Optional[str] = None) -> str:
        """Generate completion for the given prompt."""
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if language:
            payload["language"] = language
        
        result = self._make_request("/api/v1/completion", payload)
        
        if self.verbose:
            print(f"Response: {json.dumps(result, indent=2)}")
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["text"]
        return ""
    
    def insert(self, prefix: str, suffix: str, max_tokens: int = 100, 
               temperature: float = 0.7) -> str:
        """Generate insertion between prefix and suffix."""
        payload = {
            "prefix": prefix,
            "suffix": suffix,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        result = self._make_request("/api/v1/insertion", payload)
        
        if self.verbose:
            print(f"Response: {json.dumps(result, indent=2)}")
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["text"]
        return ""
    
    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 500,
             temperature: float = 0.7) -> str:
        """Chat with the AI model."""
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        result = self._make_request("/api/v1/chat", payload)
        
        if self.verbose:
            print(f"Response: {json.dumps(result, indent=2)}")
        
        if "choices" in result and len(result["choices"]) > 0 and "message" in result["choices"][0]:
            return result["choices"][0]["message"]["content"]
        return ""
    
    def process_file(self, file_path: str, mode: str, max_tokens: int = 500,
                    temperature: float = 0.7, language: Optional[str] = None) -> str:
        """Process a file for completion or documentation."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if mode == "complete":
                return self.complete(content, max_tokens, temperature, language)
            elif mode == "document":
                message = f"Generate comprehensive documentation for the following code:\n\n{content}"
                messages = [{"role": "user", "content": message}]
                return self.chat(messages, max_tokens, temperature)
            elif mode == "explain":
                message = f"Explain the following code in detail:\n\n{content}"
                messages = [{"role": "user", "content": message}]
                return self.chat(messages, max_tokens, temperature)
            else:
                print(f"Error: Unknown file processing mode: {mode}")
                sys.exit(1)
        except IOError as e:
            print(f"Error reading file {file_path}: {str(e)}")
            sys.exit(1)
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy."""
        url = f"{self.api_url}/health"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error connecting to API: {str(e)}")
            sys.exit(1)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="DeepSeek-Coder CLI")
    parser.add_argument("--api-url", help="DeepSeek-Coder API URL (default: $DEEPSEEK_API_URL or http://localhost:8000)")
    parser.add_argument("--api-key", help="API key for authentication (default: $DEEPSEEK_API_KEY)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Completion command
    completion_parser = subparsers.add_parser("complete", help="Generate code completion")
    completion_parser.add_argument("prompt", help="Code prompt to complete (use '-' for stdin)")
    completion_parser.add_argument("-m", "--max-tokens", type=int, default=100, help="Maximum tokens to generate")
    completion_parser.add_argument("-t", "--temperature", type=float, default=0.7, help="Sampling temperature")
    completion_parser.add_argument("-l", "--language", help="Programming language")
    
    # Insertion command
    insertion_parser = subparsers.add_parser("insert", help="Generate code insertion")
    insertion_parser.add_argument("--prefix", required=True, help="Code prefix (use '-' for stdin)")
    insertion_parser.add_argument("--suffix", required=True, help="Code suffix")
    insertion_parser.add_argument("-m", "--max-tokens", type=int, default=100, help="Maximum tokens to generate")
    insertion_parser.add_argument("-t", "--temperature", type=float, default=0.7, help="Sampling temperature")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Chat with the AI model")
    chat_parser.add_argument("message", help="Chat message (use '-' for stdin)")
    chat_parser.add_argument("-s", "--system", help="System message to set context")
    chat_parser.add_argument("-f", "--file", help="Load conversation history from a JSON file")
    chat_parser.add_argument("-m", "--max-tokens", type=int, default=500, help="Maximum tokens to generate")
    chat_parser.add_argument("-t", "--temperature", type=float, default=0.7, help="Sampling temperature")
    
    # File commands
    file_parser = subparsers.add_parser("file", help="Process a file")
    file_parser.add_argument("file_path", help="Path to the file")
    file_parser.add_argument("--mode", choices=["complete", "document", "explain"], default="complete", 
                           help="Processing mode (complete, document, or explain)")
    file_parser.add_argument("-m", "--max-tokens", type=int, default=500, help="Maximum tokens to generate")
    file_parser.add_argument("-t", "--temperature", type=float, default=0.7, help="Sampling temperature")
    file_parser.add_argument("-l", "--language", help="Programming language for completion")
    file_parser.add_argument("-o", "--output", help="Output file path (stdout if not specified)")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check if the API is operational")
    
    return parser.parse_args()


def read_from_stdin() -> str:
    """Read input from stdin."""
    print("Reading from stdin. Press Ctrl+D (Unix) or Ctrl+Z (Windows) to end input.")
    return sys.stdin.read()


def main():
    """Main function."""
    args = parse_args()
    
    cli = DeepSeekCLI()
    
    # Set API URL
    if args.api_url:
        cli.set_api_url(args.api_url)
    
    # Set API key
    if args.api_key:
        cli.set_api_key(args.api_key)
    
    # Set verbose mode
    if args.verbose:
        cli.set_verbose(True)
    
    # Process command
    if args.command == "complete":
        # Handle stdin for prompt
        if args.prompt == "-":
            prompt = read_from_stdin()
        else:
            prompt = args.prompt
        
        result = cli.complete(prompt, args.max_tokens, args.temperature, args.language)
        
        # Print the result
        if RICH_AVAILABLE:
            language = args.language or 'python'
            console.print(Syntax(prompt + result, language, theme="monokai"))
        else:
            print(prompt + result)
    
    elif args.command == "insert":
        # Handle stdin for prefix
        if args.prefix == "-":
            prefix = read_from_stdin()
        else:
            prefix = args.prefix
        
        suffix = args.suffix
        
        result = cli.insert(prefix, suffix, args.max_tokens, args.temperature)
        
        # Print the result
        if RICH_AVAILABLE:
            code = prefix + result + suffix
            console.print(Syntax(code, "python", theme="monokai"))
        else:
            print(prefix + result + suffix)
    
    elif args.command == "chat":
        messages = []
        
        # Load conversation history from a file if specified
        if args.file:
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    messages = json.load(f)
            except Exception as e:
                print(f"Error loading conversation history: {str(e)}")
                sys.exit(1)
        
        # Add system message if specified
        if args.system:
            if not any(msg.get("role") == "system" for msg in messages):
                messages.insert(0, {"role": "system", "content": args.system})
        
        # Handle stdin for message
        if args.message == "-":
            message = read_from_stdin()
        else:
            message = args.message
        
        # Add user message
        messages.append({"role": "user", "content": message})
        
        result = cli.chat(messages, args.max_tokens, args.temperature)
        
        # Add assistant response to messages for saving
        messages.append({"role": "assistant", "content": result})
        
        # Print the result
        if RICH_AVAILABLE:
            console.print(Panel(Markdown(result), title="DeepSeek-Coder", subtitle="AI Assistant"))
        else:
            print("\n" + result)
        
        # Save updated conversation if file was specified
        if args.file:
            try:
                with open(args.file, "w", encoding="utf-8") as f:
                    json.dump(messages, f, indent=2)
            except Exception as e:
                print(f"Error saving conversation history: {str(e)}")
    
    elif args.command == "file":
        result = cli.process_file(args.file_path, args.mode, args.max_tokens, 
                                args.temperature, args.language)
        
        # Write output to file or stdout
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"Output written to {args.output}")
            except Exception as e:
                print(f"Error writing output: {str(e)}")
                sys.exit(1)
        else:
            if RICH_AVAILABLE and args.mode == "complete":
                language = args.language or "python"
                console.print(Syntax(result, language, theme="monokai"))
            elif RICH_AVAILABLE and args.mode in ["document", "explain"]:
                console.print(Markdown(result))
            else:
                print(result)
    
    elif args.command == "health":
        result = cli.health_check()
        print(f"API Status: {result.get('status', 'unknown')}")
        print(f"API Model: {result.get('model', 'unknown')}")
    
    else:
        print("No command specified.")
        print("Use one of: complete, insert, chat, file, health")
        sys.exit(1)


if __name__ == "__main__":
    main()
