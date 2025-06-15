#!/usr/bin/env python3
"""
DeepSoul Launch - Main entry point for DeepSeek-Coder system
"""
import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Optional, List, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("deepsoul.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DeepSoul")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="DeepSeek-Coder - AI-powered code intelligence system")
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--gui", action="store_true", help="Launch GUI application")
    mode_group.add_argument("--cli", action="store_true", help="Launch command line interface")
    mode_group.add_argument("--background", action="store_true", help="Run as background service")
    mode_group.add_argument("--api", action="store_true", help="Run API server")
    
    # Action arguments
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--analyze", metavar="FILE", help="Analyze code file")
    action_group.add_argument("--enhance", metavar="FILE", help="Enhance code file")
    action_group.add_argument("--learn", metavar="SOURCE", help="Learn from file or directory")
    action_group.add_argument("--generate", metavar="PROMPT", help="Generate code from prompt")
    action_group.add_argument("--url", metavar="URL", help="Process DeepSeek URL")
    
    # Model options
    parser.add_argument("--model", metavar="NAME", help="Model name or path")
    parser.add_argument("--low-memory", action="store_true", help="Enable low memory mode")
    parser.add_argument("--cpu-only", action="store_true", help="Run on CPU only")
    
    # Enhancement type
    parser.add_argument("--type", choices=["optimize", "document", "refactor"], 
                      default="optimize", help="Enhancement type")
    
    # Output options
    parser.add_argument("--output", metavar="FILE", help="Output file")
    parser.add_argument("--format", choices=["text", "json", "markdown"], 
                      default="text", help="Output format")
    
    # Server options
    parser.add_argument("--host", default="127.0.0.1", help="API server host")
    parser.add_argument("--port", type=int, default=8765, help="API server port")
    
    # Configuration options
    parser.add_argument("--config", metavar="FILE", help="Configuration file path")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    # Positional file argument (for GUI mode)
    parser.add_argument("file", nargs="?", help="File to open")
    
    args = parser.parse_args()
    return args

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or use defaults
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    # Default configuration
    default_config = {
        "model_name": "deepseek-ai/deepseek-coder-1.3b-instruct",
        "device": "cuda",
        "knowledge_store_path": "knowledge_store.db",
        "learning_output_dir": "fine_tuned_models",
        "task_checkpoint_dir": "task_checkpoints",
        "max_concurrent_tasks": 4,
        "auto_learning_enabled": False,
        "auto_knowledge_acquisition": False
    }
    
    # Load custom configuration if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
                # Update default config with custom values
                default_config.update(custom_config)
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {str(e)}")
    
    # Find and load appropriate system_config.json if it exists
    system_config_path = Path("deepsoul_config/system_config.json")
    if not config_path and system_config_path.exists():
        try:
            with open(system_config_path, 'r') as f:
                system_config = json.load(f)
                # Update default config with system values
                default_config.update(system_config)
        except Exception as e:
            logger.error(f"Error loading system configuration: {str(e)}")
    
    return default_config

def initialize_memory_protection(config: Dict[str, Any], debug: bool = False) -> None:
    """
    Initialize memory protection subsystem
    
    Args:
        config: Configuration dictionary
        debug: Whether to enable debug logging
    """
    try:
        from utils.memory_manager import get_memory_manager, setup_memory_protection
        
        # Configure memory manager
        memory_manager = get_memory_manager()
        memory_manager.ram_warning_threshold = config.get("ram_warning_threshold", 85) / 100
        memory_manager.ram_critical_threshold = config.get("ram_critical_threshold", 95) / 100
        memory_manager.gpu_warning_threshold = config.get("gpu_warning_threshold", 85) / 100
        memory_manager.gpu_critical_threshold = config.get("gpu_critical_threshold", 95) / 100
        memory_manager.memory_dump_enabled = config.get("memory_dump_enabled", True)
        
        # Set up warning and critical hooks
        def warning_hook(data):
            if "ram_usage" in data:
                logger.warning(f"RAM usage warning: {data['ram_usage']*100:.1f}%")
            elif "gpu_usage" in data:
                logger.warning(f"GPU memory warning: {data['gpu_usage']*100:.1f}%")
        
        def critical_hook(data):
            if "ram_usage" in data:
                logger.critical(f"CRITICAL RAM usage: {data['ram_usage']*100:.1f}%")
                # Trigger memory dump
                memory_manager.memory_dump("ram_critical")
            elif "gpu_usage" in data:
                logger.critical(f"CRITICAL GPU memory: {data['gpu_usage']*100:.1f}%")
                # Trigger memory dump
                memory_manager.memory_dump("gpu_critical")
        
        # Set up memory protection with hooks
        setup_memory_protection(warning_hook, critical_hook)
        
    except ImportError as e:
        logger.warning(f"Memory protection not available: {str(e)}")

def initialize_deepsoul(config: Dict[str, Any], low_memory: bool = False, cpu_only: bool = False) -> Any:
    """
    Initialize DeepSoul system
    
    Args:
        config: Configuration dictionary
        low_memory: Whether to enable low memory mode
        cpu_only: Whether to force CPU-only operation
        
    Returns:
        DeepSoul instance
    """
    try:
        from implementation.deepsoul_system import DeepSoul
        
        # Determine device
        device = "cpu" if cpu_only else config.get("device", "cuda")
        
        # Get model name from config
        model_name = config.get("model_name", "deepseek-ai/deepseek-coder-1.3b-instruct")
        
        # Memory optimization settings
        memory_settings = {
            "low_memory": low_memory or config.get("low_memory", False),
            "use_flash_attention": config.get("use_flash_attention", True),
            "auto_offload": config.get("auto_offload_to_cpu", True)
        }
        
        # Create DeepSoul instance
        deepsoul = DeepSoul(
            model_name=model_name,
            device=device,
            knowledge_store_path=config.get("knowledge_store_path", "knowledge_store.db"),
            memory_settings=memory_settings
        )
        
        # Initialize components
        deepsoul.initialize()
        
        return deepsoul
        
    except Exception as e:
        logger.error(f"Error initializing DeepSoul: {str(e)}")
        raise

def run_gui(args, config: Dict[str, Any]) -> int:
    """
    Launch the GUI application
    
    Args:
        args: Parsed command line arguments
        config: Configuration dictionary
        
    Returns:
        Exit code
    """
    try:
        # Add GUI directory to path
        sys.path.insert(0, str(Path("gui").absolute()))
        
        # Import GUI components
        from gui.desktop_app import main
        
        # Launch GUI
        return main()
        
    except ModuleNotFoundError:
        logger.error("GUI components not found. Make sure PyQt6 is installed.")
        return 1
    except Exception as e:
        logger.error(f"Error launching GUI: {str(e)}")
        return 1

def run_cli(args, config: Dict[str, Any]) -> int:
    """
    Run in command-line interface mode
    
    Args:
        args: Parsed command line arguments
        config: Configuration dictionary
        
    Returns:
        Exit code
    """
    try:
        # Initialize DeepSoul with given settings
        deepsoul = initialize_deepsoul(config, args.low_memory, args.cpu_only)
        
        # Process based on provided action
        if args.analyze:
            # Analyze code file
            file_path = args.analyze
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return 1
                
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            # Determine language from file extension
            language = os.path.splitext(file_path)[1][1:]  # Remove the dot
            
            # Analyze code
            logger.info(f"Analyzing file: {file_path}")
            result = deepsoul.analyze_code(code, language)
            
            # Output result
            output_result(result, args.output, args.format)
            
        elif args.enhance:
            # Enhance code file
            file_path = args.enhance
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return 1
                
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            # Determine language from file extension
            language = os.path.splitext(file_path)[1][1:]  # Remove the dot
            
            # Enhance code
            logger.info(f"Enhancing file: {file_path} ({args.type})")
            result = deepsoul.enhance_code(code, language, args.type)
            
            # Output result
            output_result(result, args.output, args.format)
            
        elif args.learn:
            # Learn from source
            source = args.learn
            if not os.path.exists(source):
                logger.error(f"Source not found: {source}")
                return 1
                
            # Determine source type
            source_type = "file" if os.path.isfile(source) else "repo"
            
            # Learn from source
            logger.info(f"Learning from {source_type}: {source}")
            result = deepsoul.acquire_knowledge(source, source_type)
            
            # Output result
            output_result(result, args.output, args.format)
            
        elif args.generate:
            # Generate code
            prompt = args.generate
            
            # Generate code
            logger.info("Generating code...")
            result = deepsoul.generate_code(prompt)
            
            # Output result
            output_result(result, args.output, args.format)
            
        elif args.url:
            # Process URL
            url = args.url
            if not url.startswith(("http://", "https://", "deepseek://")):
                logger.error(f"Invalid URL: {url}")
                return 1
                
            # Process URL
            logger.info(f"Processing URL: {url}")
            result = deepsoul.process_url(url)
            
            # Output result
            output_result(result, args.output, args.format)
            
        else:
            # Interactive mode
            import readline  # For history
            
            print("DeepSeek-Coder CLI")
            print("Type 'exit' or 'quit' to exit")
            print("Type 'help' for help")
            
            while True:
                try:
                    command = input("\nDeepSeek> ")
                    
                    if command.lower() in ["exit", "quit"]:
                        break
                        
                    if command.lower() == "help":
                        print("Available commands:")
                        print("  analyze <file> - Analyze code file")
                        print("  enhance <file> [optimize|document|refactor] - Enhance code file")
                        print("  learn <file|directory> - Learn from source")
                        print("  generate <prompt> - Generate code from prompt")
                        print("  help - Show this help")
                        print("  exit/quit - Exit the program")
                        continue
                        
                    # Parse command
                    parts = command.split()
                    if not parts:
                        continue
                        
                    if parts[0] == "analyze" and len(parts) > 1:
                        file_path = parts[1]
                        if not os.path.exists(file_path):
                            print(f"File not found: {file_path}")
                            continue
                            
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code = f.read()
                            
                        # Determine language from file extension
                        language = os.path.splitext(file_path)[1][1:]  # Remove the dot
                        
                        # Analyze code
                        print(f"Analyzing file: {file_path}")
                        result = deepsoul.analyze_code(code, language)
                        print(json.dumps(result, indent=2))
                        
                    elif parts[0] == "enhance" and len(parts) > 1:
                        file_path = parts[1]
                        if not os.path.exists(file_path):
                            print(f"File not found: {file_path}")
                            continue
                            
                        # Get enhancement type
                        enhancement_type = "optimize"
                        if len(parts) > 2 and parts[2] in ["optimize", "document", "refactor"]:
                            enhancement_type = parts[2]
                            
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            code = f.read()
                            
                        # Determine language from file extension
                        language = os.path.splitext(file_path)[1][1:]  # Remove the dot
                        
                        # Enhance code
                        print(f"Enhancing file: {file_path} ({enhancement_type})")
                        result = deepsoul.enhance_code(code, language, enhancement_type)
                        print(result)
                        
                    elif parts[0] == "learn" and len(parts) > 1:
                        source = parts[1]
                        if not os.path.exists(source):
                            print(f"Source not found: {source}")
                            continue
                            
                        # Determine source type
                        source_type = "file" if os.path.isfile(source) else "repo"
                        
                        # Learn from source
                        print(f"Learning from {source_type}: {source}")
                        result = deepsoul.acquire_knowledge(source, source_type)
                        print(f"Learned {len(result)} items")
                        
                    elif parts[0] == "generate":
                        if len(parts) > 1:
                            prompt = " ".join(parts[1:])
                        else:
                            prompt = input("Enter prompt: ")
                            
                        # Generate code
                        print("Generating code...")
                        result = deepsoul.generate_code(prompt)
                        print("\n" + result)
                        
                    else:
                        print(f"Unknown command: {parts[0]}")
                        print("Type 'help' for available commands")
                        
                except KeyboardInterrupt:
                    print("\nOperation cancelled")
                except Exception as e:
                    print(f"Error: {str(e)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in CLI mode: {str(e)}")
        return 1

def run_background_service(args, config: Dict[str, Any]) -> int:
    """
    Run as a background service
    
    Args:
        args: Parsed command line arguments
        config: Configuration dictionary
        
    Returns:
        Exit code
    """
    try:
        # Import background service
        from services.background_service import BackgroundService
        
        # Create and start service
        service = BackgroundService(config_path=args.config)
        service.start()
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping service...")
        finally:
            service.stop()
            
        return 0
        
    except ModuleNotFoundError:
        logger.error("Background service components not found.")
        return 1
    except Exception as e:
        logger.error(f"Error running background service: {str(e)}")
        return 1

def run_api_server(args, config: Dict[str, Any]) -> int:
    """
    Run the API server
    
    Args:
        args: Parsed command line arguments
        config: Configuration dictionary
        
    Returns:
        Exit code
    """
    try:
        # Import API server
        from services.api_server import APIServer
        
        # Create and start API server
        server = APIServer(host=args.host, port=args.port)
        server.start()
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping API server...")
            
        return 0
        
    except ModuleNotFoundError:
        logger.error("API server components not found. Make sure FastAPI and uvicorn are installed.")
        return 1
    except Exception as e:
        logger.error(f"Error running API server: {str(e)}")
        return 1

def output_result(result, output_file: Optional[str], output_format: str) -> None:
    """
    Output the result in the specified format
    
    Args:
        result: Result to output
        output_file: Output file path (None for stdout)
        output_format: Output format (text, json, markdown)
    """
    # Convert result to the desired format
    if output_format == "text":
        if isinstance(result, dict) or isinstance(result, list):
            formatted_result = json.dumps(result, indent=2)
        else:
            formatted_result = str(result)
    elif output_format == "json":
        if isinstance(result, dict) or isinstance(result, list):
            formatted_result = json.dumps(result, indent=2)
        else:
            formatted_result = json.dumps({"result": str(result)}, indent=2)
    elif output_format == "markdown":
        if isinstance(result, dict):
            formatted_result = "# DeepSeek-Coder Result\n\n"
            for key, value in result.items():
                formatted_result += f"## {key}\n\n"
                if isinstance(value, dict) or isinstance(value, list):
                    formatted_result += f"```json\n{json.dumps(value, indent=2)}\n```\n\n"
                else:
                    formatted_result += f"{value}\n\n"
        elif isinstance(result, list):
            formatted_result = "# DeepSeek-Coder Result\n\n"
            formatted_result += f"```json\n{json.dumps(result, indent=2)}\n```\n\n"
        else:
            formatted_result = str(result)
    
    # Output to file or stdout
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_result)
    else:
        print(formatted_result)

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Initialize memory protection
    initialize_memory_protection(config, args.debug)
    
    # Run based on selected mode
    if args.gui:
        return run_gui(args, config)
    elif args.cli:
        return run_cli(args, config)
    elif args.background:
        return run_background_service(args, config)
    elif args.api:
        return run_api_server(args, config)
    else:
        logger.error("No mode selected. Use --gui, --cli, --background, or --api.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
