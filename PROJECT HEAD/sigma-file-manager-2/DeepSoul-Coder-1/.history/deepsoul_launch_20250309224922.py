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
import gc

# Add implementation directory to path
sys.path.insert(0, str(Path(__file__).parent))

from implementation.deepsoul_system import DeepSoul
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich import print as rprint

# Import memory protection utilities
from utils.memory_manager import get_memory_manager
from implementation.oom_protected_execution import oom_protected, MemoryEfficientContext
from utils.memory_efficient_generation import create_generator

console = Console()

# Initialize memory manager
memory_manager = get_memory_manager()

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
        return file_path
    except Exception as e:
        console.print(f"[red]Error saving file:[/] {str(e)}")
        return None

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
        elif command.lower() == "memory":
            show_memory_status()
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
        elif command.lower().startswith("scrape "):
            parts = command.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[red]Error:[/] Missing URL for scraping")
                continue
            url = parts[1]
            
            # Get CAPTCHA API key from DeepSoul config
            captcha_api_key = deepsoul.config.get("api_keys", {}).get("2captcha")
            
            # Scrape the URL
            try:
                from implementation.legal_scraping import scrape_court_info
                result = scrape_court_info(url, captcha_api_key=captcha_api_key)
                console.print(f"[green]Successfully scraped URL:[/] {url}")
                console.print_json(data=result)
            except Exception as e:
                console.print(f"[red]Error scraping URL:[/] {str(e)}")
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
- `memory` - Show detailed memory usage
- `clear` - Clear the screen
- `help` - Show this help information
- `exit` or `quit` - Exit DeepSoul
"""
    console.print(Markdown(help_text))

def show_memory_status():
    """Show detailed memory status"""
    console.print("[bold cyan]DeepSoul Memory Status:[/]")
    
    # System memory info
    mem = psutil.virtual_memory()
    console.print(f"[bold]System RAM:[/]")
    console.print(f"  Total: {mem.total / (1024**3):.2f} GB")
    console.print(f"  Available: {mem.available / (1024**3):.2f} GB")
    console.print(f"  Used: {mem.percent:.1f}%")
    
    # GPU memory info if available
    if torch.cuda.is_available():
        console.print(f"\n[bold]GPU Memory:[/]")
        for i in range(torch.cuda.device_count()):
            device_name = torch.cuda.get_device_name(i)
            total_mem = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            allocated_mem = torch.cuda.memory_allocated(i) / (1024**3)
            reserved_mem = torch.cuda.memory_reserved(i) / (1024**3)
            
            console.print(f"  [bold]GPU {i}:[/] {device_name}")
            console.print(f"    Total: {total_mem:.2f} GB")
            console.print(f"    Allocated: {allocated_mem:.2f} GB")
            console.print(f"    Reserved: {reserved_mem:.2f} GB")
            console.print(f"    Utilization: {(allocated_mem / total_mem) * 100:.1f}%")
    
    # Create a memory dump file for detailed info
    dump_path = memory_manager.memory_dump("cli_command")
    if dump_path:
        console.print(f"\nDetailed memory dump created: {dump_path}")

@oom_protected(retry_on_cpu=True)
def analyze_code_file(deepsoul, file_path):
    """Analyze a code file with OOM protection"""
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
            # Use memory-efficient context
            with MemoryEfficientContext():
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
                        console.print(f"   [dim]Cyclomatic Complexity:[/] {metrics['cyclomatic_complexity']}")
                    
                    if 'lines_of_code' in metrics:
                        console.print(f"   [dim]Lines of Code:[/] {metrics['lines_of_code']}")
                
                # Show summary
                if name in result['summaries'] and result['summaries'][name]:
                    console.print(f"   [italic]{result['summaries'][name]}[/]")
                    
                console.print("")
                
        except Exception as e:
            console.print(f"[red]Error analyzing code:[/] {str(e)}")

@oom_protected(retry_on_cpu=True)
def enhance_code_file(deepsoul, file_path, enhancement_type="optimize"):
    """Enhance a code file with OOM protection"""
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
            # Use memory-efficient context for generation
            with MemoryEfficientContext():
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

@oom_protected(retry_on_cpu=True)
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
            # Use memory-efficient context
            with MemoryEfficientContext():
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

@oom_protected(retry_on_cpu=True)
def generate_code(deepsoul, prompt):
    """Generate code from prompt with memory protection"""
    console.print(f"[yellow]Generating code for:[/] {prompt}")
    
    # Use memory-efficient generator
    try:
        # Create memory efficient generator
        generator = create_generator(deepsoul.model, deepsoul.tokenizer)
        
        # Start spinner
        with console.status("[bold green]Generating code...[/]", spinner="dots"):
            # Generate code
            full_prompt = f"Generate code for the following:\n\n{prompt}\n\nCode:"
            generated_code = generator.generate(
                prompt=full_prompt,
                max_new_tokens=500,
                temperature=0.7,
                top_p=0.95
            )
            
            # Extract the code part (after the prompt)
            code = generated_code[len(full_prompt):].strip()
            
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
        # Try basic generation if memory-efficient generation failed
        try:
            with console.status("[bold yellow]Retrying with basic generation...[/]", spinner="dots"):
                # We'll use a simpler approach by constructing a prompt for the model
                full_prompt = f"Generate code for the following:\n\n{prompt}\n\nCode:"
                
                inputs = deepsoul.tokenizer(full_prompt, return_tensors="pt").to(deepsoul.device)
                
                with torch.no_grad():  # Disable gradient calculation to save memory
                    outputs = deepsoul.model.generate(
                        input_ids=inputs.input_ids,
                        attention_mask=inputs.attention_mask,
                        max_new_tokens=200,                        temperature=0.7,
                        top_p=0.95
                    )
                    
                    generated_code = deepsoul.tokenizer.decode(outputs[0], skip_special_tokens=True)
                    code = generated_code[len(full_prompt):].strip()
                    
                    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
                    console.print(syntax)

        except Exception as inner_e:
            console.print(f"[red]Failed to generate code: {str(inner_e)}[/]")

def show_status(deepsoul):
    """Show system status"""
    console.print("[bold cyan]DeepSoul System Status:[/]")
    console.print(f"Model: [bold]{deepsoul.model_name}[/]")
    console.print(f"Device: [bold]{deepsoul.device}[/]")
    console.print(f"Initialized: [bold]{'Yes' if deepsoul.initialized else 'No'}[/]")
    
    # Memory status
    try:
        import psutil
        mem = psutil.virtual_memory()
        console.print(f"System RAM: [bold]{mem.percent:.1f}%[/] used")
        
        if torch.cuda.is_available():
            device = torch.device("cuda:0")
            allocated = torch.cuda.memory_allocated(device) / (1024**3)  # GB
            total = torch.cuda.get_device_properties(device).total_memory / (1024**3)  # GB
            console.print(f"GPU Memory: [bold]{allocated:.2f}/{total:.2f} GB[/] used ([bold]{(allocated/total)*100:.1f}%[/])")
    except ImportError:
        pass
    
    # Show component status
    console.print("\n[bold]Active Components:[/]")
    for name, component in deepsoul.components.items():
        console.print(f"- {name}")

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
    parser.add_argument("--low-memory", action="store_true",
                       help="Optimize for systems with limited memory")
    
    args = parser.parse_args()
    
    try:
        # Import psutil for memory monitoring
        import psutil
    except ImportError:
        console.print("[yellow]Warning: psutil not installed. Memory monitoring will be limited.[/]")
    
    # Initialize DeepSoul with memory protection
    device = "cpu" if args.cpu else None
    console.print("[bold green]Initializing DeepSoul...[/]")
    
    # If low memory mode is enabled, use special settings
    if args.low_memory:
        console.print("[yellow]Low memory mode enabled. Using optimized settings.[/]")
        os.environ["USE_MEMORY_EFFICIENT_ATTENTION"] = "1"
        
        # Clear before initialization to maximize available memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
    
    # Initialize with memory protection
    try:
        with MemoryEfficientContext():
            deepsoul = DeepSoul(model_name=args.model, device=device)
    except Exception as e:
        console.print(f"[red]Error initializing DeepSoul: {str(e)}[/]")
        return 1
    
    # Handle one-off commands
    if args.analyze:
        analyze_code_file(deepsoul, args.analyze)
        return 0
    elif args.enhance:
        enhance_code_file(deepsoul, args.enhance, args.enhancement_type)
        return 0
    
    # Run in interactive mode
    try:
        interactive_mode(deepsoul)
    finally:
        console.print("[yellow]Shutting down DeepSoul...[/]")
        deepsoul.shutdown()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
