#!/usr/bin/env python3
"""
DeepSoul Launcher - Interactive interface for DeepSoul code intelligence system
"""
import os
import sys
import argparse
import torch
from pathlib import Path
import tempfile
import time

# Add implementation directory to path
sys.path.insert(0, str(Path(__file__).parent))

from implementation.deepsoul_system import DeepSoul
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import print as rprint

console = Console()

def print_header():
    """Print the DeepSoul header"""
    console.print("\n[bold cyan]================================[/]")
    console.print("[bold cyan]  DeepSoul Code Intelligence  [/]")
    console.print("[bold cyan]================================[/]")
    console.print("Type '[bold green]help[/]' to see available commands")
    console.print("Type '[bold green]exit[/]' or '[bold green]quit[/]' to exit\n")

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def save_to_file(content, file_path=None):
    """Save content to a file"""
    if not file_path:
        # Generate a timestamped filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_path = f"deepsoul_output_{timestamp}.txt"
    
    try:
        with open(file_path, "w") as f:
            f.write(content)
        console.print(f"[green]Content saved to[/] [bold]{file_path}[/]")
    except Exception as e:
        console.print(f"[red]Error saving file:[/] {str(e)}")

def read_file(file_path):
    """Read content from a file"""
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        console.print(f"[red]Error reading file:[/] {str(e)}")
        return None

def interactive_mode(deepsoul):
    """Run in interactive mode"""
    print_header()
    
    # Command history
    history = []
    
    while True:
        # Get command
        try:
            command = input("DeepSoul> ").strip()
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting DeepSoul...[/]")
            break
            
        # Add to history
        if command and (not history or command != history[-1]):
            history.append(command)
            
        # Process command
        if command.lower() in ["exit", "quit"]:
            break
        elif not command:
            continue
        elif command.lower() == "help":
            show_help()
        elif command.lower() == "clear":
            clear_screen()
            print_header()
        elif command.lower().startswith("analyze "):
            _, *args = command.split(maxsplit=1)
            if not args:
                console.print("[red]Error:[/] Missing file path for analysis")
                continue
            file_path = args[0]
            analyze_code_file(deepsoul, file_path)
        elif command.lower().startswith("enhance "):
            parts = command.split(maxsplit=2)
            if len(parts) < 2:
                console.print("[red]Error:[/] Missing file path for enhancement")
                continue
            
            file_path = parts[1]
            enhancement_type = parts[2] if len(parts) > 2 else "optimize"
            enhance_code_file(deepsoul, file_path, enhancement_type)
        elif command.lower().startswith("learn "):
            _, *args = command.split(maxsplit=1)
            if not args:
                console.print("[red]Error:[/] Missing path for knowledge acquisition")
                continue
            source_path = args[0]
            acquire_knowledge(deepsoul, source_path)
        elif command.lower().startswith("generate "):
            _, *args = command.split(maxsplit=1)
            if not args:
                console.print("[red]Error:[/] Missing prompt for code generation")
                continue
            prompt = args[0]
            generate_code(deepsoul, prompt)
        elif command.lower() == "status":
            show_status(deepsoul)
        else:
            console.print(f"[red]Unknown command:[/] {command}")
            console.print("Type '[bold green]help[/]' to see available commands")

def show_help():
    """Show help information"""
    help_text = """
# DeepSoul Commands

## Code Analysis
- `analyze <file_path>` - Analyze a code file
- `enhance <file_path> [optimize|document|refactor]` - Enhance code (default: optimize)

## Knowledge and Learning
- `learn <file_path|directory>` - Acquire knowledge from file or directory
- `generate <description>` - Generate code from description

## System
- `status` - Show system status
- `clear` - Clear the screen
- `help` - Show this help information
- `exit` or `quit` - Exit DeepSoul
"""
    console.print(Markdown(help_text))

def analyze_code_file(deepsoul, file_path):
    """Analyze a code file"""
    console.print(f"[yellow]Analyzing file:[/] {file_path}")
    
    # Read file
    code = read_file(file_path)
    if code is None:
        return
        
    # Get extension for language detection
    ext = os.path.splitext(file_path)[1][1:]
    language_map = {
        'py': 'python', 'js': 'javascript', 'ts': 'typescript',
        'java': 'java', 'c': 'c', 'cpp': 'cpp', 'cs': 'csharp',
        'rb': 'ruby', 'go': 'go', 'rs': 'rust', 'php': 'php'
    }
    language = language_map.get(ext, 'python')
    
    # Start spinner
    with console.status("[bold green]Analyzing code...[/]", spinner="dots"):
        try:
            result = deepsoul.analyze_code(code, language)
            
            # Display results
            console.print("\n[bold cyan]Analysis Results:[/]")
            
            # Show entities
            console.print(f"\n[bold]Found {len(result['entities'])} code entities:[/]")
            for i, entity in enumerate(result['entities']):
                entity_type = entity.get('entity_type', 'unknown')
                name = entity.get('name', f'Entity {i+1}')
                console.print(f"[bold]{i+1}. {entity_type}:[/] {name}")
                
                # Show docstring if available
                docstring = entity.get('docstring')
                if docstring:
                    console.print(f"   [dim]Docstring:[/] {docstring}")
                
                # Show complexity metrics
                if name in result['complexity_metrics']:
                    metrics = result['complexity_metrics'][name]
                    if 'cyclomatic_complexity' in metrics:
                        complexity = metrics['cyclomatic_complexity']
                        color = "green" if complexity < 10 else "yellow" if complexity < 20 else "red"
                        console.print(f"   Complexity: [{color}]{complexity}[/]")
                    
                    if 'lines_of_code' in metrics:
                        loc = metrics['lines_of_code']
                        console.print(f"   Lines: {loc}")
                
                # Show summary
                if name in result['summaries'] and result['summaries'][name]:
                    console.print(f"   [italic]{result['summaries'][name]}[/]")
                    
                console.print("")
                
        except Exception as e:
            console.print(f"[red]Error analyzing code:[/] {str(e)}")

def enhance_code_file(deepsoul, file_path, enhancement_type="optimize"):
    """Enhance a code file"""
    valid_types = ["optimize", "document", "refactor"]
    if enhancement_type not in valid_types:
        console.print(f"[red]Invalid enhancement type:[/] {enhancement_type}")
        console.print(f"Valid types: {', '.join(valid_types)}")
        return
        
    console.print(f"[yellow]Enhancing file:[/] {file_path} (Type: {enhancement_type})")
    
    # Read file
    code = read_file(file_path)
    if code is None:
        return
        
    # Get extension for language detection
    ext = os.path.splitext(file_path)[1][1:]
    language_map = {
        'py': 'python', 'js': 'javascript', 'ts': 'typescript',
        'java': 'java', 'c': 'c', 'cpp': 'cpp', 'cs': 'csharp',
        'rb': 'ruby', 'go': 'go', 'rs': 'rust', 'php': 'php'
    }
    language = language_map.get(ext, 'python')
    
    # Start spinner
    with console.status(f"[bold green]Enhancing code ({enhancement_type})...[/]", spinner="dots"):
        try:
            enhanced_code = deepsoul.enhance_code(code, language, enhancement_type)
            
            # Display result
            console.print(f"\n[bold cyan]Enhanced Code ({enhancement_type}):[/]")
            syntax = Syntax(enhanced_code, language, theme="monokai", line_numbers=True)
            console.print(syntax)
            
            # Save enhanced code
            output_path = f"{file_path}.enhanced.{enhancement_type}"
            save_to_file(enhanced_code, output_path)
            
        except Exception as e:
            console.print(f"[red]Error enhancing code:[/] {str(e)}")

def acquire_knowledge(deepsoul, source_path):
    """Acquire knowledge from file or directory"""
    console.print(f"[yellow]Acquiring knowledge from:[/] {source_path}")
    
    # Determine source type
    source_type = "auto"
    if os.path.isfile(source_path):
        source_type = "file"
    elif os.path.isdir(source_path):
        source_type = "repo"
    elif source_path.startswith(("http://", "https://")):
        source_type = "doc"
    
    # Start spinner
    with console.status("[bold green]Acquiring knowledge...[/]", spinner="dots"):
        try:
            knowledge_acquisition = deepsoul.get_component("knowledge_acquisition")
            
            if source_type == "file":
                item_ids = knowledge_acquisition.ingest_file(source_path)
            elif source_type == "repo":
                item_ids = knowledge_acquisition.ingest_repository(source_path)
            else:
                # Use DeepSoul's acquire_knowledge method for automatic detection
                item_ids = deepsoul.acquire_knowledge(source_path, source_type)
            
            console.print(f"[green]Successfully acquired {len(item_ids)} knowledge items[/]")
            
        except Exception as e:
            console.print(f"[red]Error acquiring knowledge:[/] {str(e)}")

def generate_code(deepsoul, prompt):
    """Generate code from prompt"""
    console.print(f"[yellow]Generating code for:[/] {prompt}")
    
    # Start spinner
    with console.status("[bold green]Generating code...[/]", spinner="dots"):
        try:
            # We'll use a simpler approach by constructing a prompt for the model
            full_prompt = f"Generate code for the following:\n\n{prompt}\n\nCode:"
            
            inputs = deepsoul.tokenizer(full_prompt, return_tensors="pt").to(deepsoul.device)
            
            outputs = deepsoul.model.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=500,
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
                num_return_sequences=1
            )
            
            generated_text = deepsoul.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the code part (after the prompt)
            code = generated_text[len(full_prompt):].strip()
            
            # Display result
            console.print("\n[bold cyan]Generated Code:[/]")
            
            # Try to determine language from the prompt
            language_keywords = {
                "python": ["python", "def ", "import ", "class "],
                "javascript": ["javascript", "js", "function", "const ", "let "],
                "java": ["java", "class ", "public ", "private "],
                "c++": ["c++", "cpp", "#include", "namespace"]
            }
            
            language = "python"  # Default
            for lang, keywords in language_keywords.items():
                if any(kw.lower() in prompt.lower() for kw in keywords):
                    language = lang
                    break
            
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            console.print(syntax)
            
            # Offer to save
            console.print("\nWould you like to save this code? [y/N]", end=" ")
            choice = input().strip().lower()
            if choice == 'y':
                save_to_file(code)
            
        except Exception as e:
            console.print(f"[red]Error generating code:[/] {str(e)}")

def show_status(deepsoul):
    """Show system status"""
    console.print("[bold cyan]DeepSoul System Status:[/]")
    console.print(f"Model: [bold]{deepsoul.model_name}[/]")
    console.print(f"Device: [bold]{deepsoul.device}[/]")
    console.print(f"Initialized: [bold]{'Yes' if deepsoul.initialized else 'No'}[/]")
    
    # Show component status
    console.print("\n[bold]Active Components:[/]")
    for name, component in deepsoul.components.items():
        console.print(f"- {name}")
    
    # Show memory usage if on CUDA
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**2
        reserved = torch.cuda.memory_reserved() / 1024**2
        console.print(f"\n[bold]GPU Memory:[/]")
        console.print(f"Allocated: {allocated:.2f} MB")
        console.print(f"Reserved: {reserved:.2f} MB")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DeepSoul Code Intelligence System")
    parser.add_argument("--model", type=str, default="deepseek-ai/deepseek-coder-1.3b-instruct",
                       help="Model name or path")
    parser.add_argument("--cpu", action="store_true",
                       help="Force CPU usage")
    parser.add_argument("--analyze", type=str,
                       help="Analyze a code file and exit")
    parser.add_argument("--enhance", type=str,
                       help="Enhance a code file and exit")
    parser.add_argument("--enhancement-type", type=str, default="optimize",
                       choices=["optimize", "document", "refactor"],
                       help="Type of enhancement to perform")
    
    args = parser.parse_args()
    
    # Initialize DeepSoul
    device = "cpu" if args.cpu else None
    
    console.print("[bold green]Initializing DeepSoul...[/]")
    deepsoul = DeepSoul(model_name=args.model, device=device)
    
    # Handle one-off commands
    if args.analyze:
        analyze_code_file(deepsoul, args.analyze)
        return
    elif args.enhance:
        enhance_code_file(deepsoul, args.enhance, args.enhancement_type)
        return
    
    # Run in interactive mode
    try:
        interactive_mode(deepsoul)
    finally:
        console.print("[yellow]Shutting down DeepSoul...[/]")
        deepsoul.shutdown()

if __name__ == "__main__":
    main()
