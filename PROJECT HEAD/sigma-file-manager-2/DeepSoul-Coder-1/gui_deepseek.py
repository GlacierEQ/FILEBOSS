#!/usr/bin/env python3
"""
GUI interface for DeepSeek-Coder with multilingual support
"""
import os
import sys
import threading
import re
import argparse
import torch
import gradio as gr
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Support for language detection
try:
    import langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("Warning: langdetect not available. Language detection will be disabled.")
    print("To enable, install with: pip install langdetect")

# Supported languages and their codes
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh": "Chinese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "ru": "Russian",
    "ko": "Korean",
    "it": "Italian",
    "pt": "Portuguese",
    "ar": "Arabic",
    "hi": "Hindi"
}

# Global variables for model and tokenizer
model = None
tokenizer = None
device = "cpu"
current_language = "en"

# Import hardware detection utilities
try:
    from hardware_utils import HardwareManager
    hardware_manager = HardwareManager()
    hardware_utils_available = True
except ImportError:
    hardware_utils_available = False

def detect_language(text):
    """Detect the language of the input text."""
    if not LANGDETECT_AVAILABLE or not text.strip():
        return "en"  # Default to English
    
    try:
        return langdetect.detect(text)
    except:
        return "en"  # Default to English on error

def format_code_blocks(text):
    """Format code blocks with syntax highlighting in markdown."""
    # Match code blocks with language specification
    pattern = r"```(\w+)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    for lang, code in matches:
        highlighted_code = f"```{lang}\n{code}\n```"
        text = text.replace(f"```{lang}\n{code}\n```", highlighted_code)
    return text

def initialize_model(model_name, use_gpu=True, precision="auto", trust_remote=True):
    """Initialize model and tokenizer."""
    global model, tokenizer, device
    
    # Determine device and precision
    if hardware_utils_available:
        if precision == "auto":
            torch_dtype = hardware_manager.get_optimal_dtype()
        else:
            # Convert precision string to torch dtype
            torch_dtype = {
                "bfloat16": torch.bfloat16,
                "float16": torch.float16,
                "float32": torch.float32
            }.get(precision, torch.float32)
        
        # Get the appropriate device
        if use_gpu:
            device_obj = hardware_manager.get_torch_device()
            device = device_obj.type
            device_name = device.upper()
            if device == "cuda" and torch.cuda.is_available():
                device_name = f"GPU: {torch.cuda.get_device_name(0)}"
        else:
            device = "cpu"
            device_name = "CPU"

        device_info = f"Using device: {device_name}"
    else:
        # Fallback to standard PyTorch device detection
        # Convert precision string to torch dtype
        if precision == "auto" or precision == "bfloat16":
            torch_dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float32
        elif precision == "float16":
            torch_dtype = torch.float16
        else:
            torch_dtype = torch.float32
        
        # Determine device
        device = "cpu"
        if use_gpu and torch.cuda.is_available():
            device = "cuda"
            device_info = f"Using GPU: {torch.cuda.get_device_name(0)}"
        else:
            device_info = "Using CPU (this will be slower)"
    
    # Initialize tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=trust_remote
        )
    except Exception as e:
        return f"Error loading tokenizer: {str(e)}"
    
    # Initialize model
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=trust_remote,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True
        )
    except Exception as e:
        return f"Error loading model: {str(e)}"
    
    # Move to GPU if available and requested
    if hardware_utils_available:
        if use_gpu and device != "cpu":
            # device_obj is already determined above
            model = model.to(device_obj)
    else:
        if device == "cuda":
            model = model.to(device)
    
    model_info = f"Loaded {model_name}"
    return f"{model_info}\n{device_info}\nUsing precision: {precision}"

def process_chat(message, history, system_prompt=None, max_tokens=1024, temperature=0.7):
    """Process a chat message and return the response."""
    global model, tokenizer, device, current_language
    
    # If model is not loaded, return error
    if model is None or tokenizer is None:
        yield "Model not initialized. Please load a model first."
        return
    
    # ...existing code...
    
    try:
        # Format input for the model using chat template
        tokenized = tokenizer.apply_chat_template(
            conversation, 
            add_generation_prompt=True,
            return_tensors="pt"
        )
        
        # Explicitly create inputs and attention mask
        input_ids = tokenized.to(device)
        attention_mask = torch.ones_like(input_ids).to(device)
        
        # Generate response with explicit attention mask
        outputs = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=True,
            temperature=temperature,
            top_p=0.95,
            max_new_tokens=max_tokens,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # ...existing code...
        
    except Exception as e:
        yield f"Error generating response: {str(e)}"

def create_gui(model_name="deepseek-ai/deepseek-coder-1.3b-instruct", use_gpu=True):
    """Create the Gradio interface for the chat."""
    
    # Initialization status
    init_status = gr.Textbox(
        value="Model not loaded yet. Click 'Load Model'.",
        label="Model Status",
        interactive=False
    )
    
    # Model selection
    with gr.Row():
        model_dropdown = gr.Dropdown(
            choices=[
                "deepseek-ai/deepseek-coder-1.3b-instruct",  # Changed order to put this first
                "deepseek-ai/deepseek-coder-6.7b-instruct",
                "deepseek-ai/deepseek-coder-33b-instruct",
                "deepseek-ai/deepseek-coder-1.3b-base",
                "deepseek-ai/deepseek-coder-6.7b-base",
                "deepseek-ai/deepseek-coder-33b-base"
            ],
            value=model_name,
            label="Model",
            interactive=True
        )
        
        # Generate the list of precision options
        precision_choices = ["auto", "float32", "float16"]
        if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
            precision_choices.insert(1, "bfloat16")
        elif hardware_utils_available:
            # Check for Apple Silicon which might support bfloat16
            if "mps" in hardware_manager.available_devices and hardware_manager.available_devices["mps"]["available"]:
                precision_choices.insert(1, "bfloat16")
                
        precision_dropdown = gr.Dropdown(
            choices=precision_choices,
            value="auto",
            label="Precision",
            interactive=True
        )
        
        # Generate device choices based on what's available
        if hardware_utils_available:
            device_choices = ["auto", "cpu"]
            for device_type in ["cuda", "mps", "directml", "rocm", "openvino"]:
                if device_type in hardware_manager.available_devices and hardware_manager.available_devices[device_type]["available"]:
                    device_choices.append(device_type)
            
            device_dropdown = gr.Dropdown(
                choices=device_choices,
                value="auto",
                label="Device",
                interactive=True
            )
        else:
            gpu_checkbox = gr.Checkbox(
                value=use_gpu and torch.cuda.is_available(),
                label="Use GPU",
                interactive=True
            )
        
        load_button = gr.Button("Load Model")
    
    # Load model function
    def load_model_fn(model_name, precision, device_choice=None, use_gpu=None):
        # Determine use_gpu based on device_choice or use_gpu checkbox
        if device_choice is not None:  # Using hardware_utils
            use_gpu_val = device_choice != "cpu"
            if device_choice != "auto" and device_choice != "cpu":
                os.environ["DEEPSEEK_DEVICE_PRIORITY"] = device_choice
        else:  # Using simple GPU checkbox
            use_gpu_val = use_gpu
            
        status = initialize_model(model_name, use_gpu_val, precision)
        return status
    
    # Connect the load button
    if hardware_utils_available:
        load_button.click(
            fn=load_model_fn,
            inputs=[model_dropdown, precision_dropdown, device_dropdown],
            outputs=init_status
        )
    else:
        load_button.click(
            fn=load_model_fn,
            inputs=[model_dropdown, precision_dropdown, None, gpu_checkbox],
            outputs=init_status
        )
    
    # ...existing code...

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeepSeek-Coder Chat GUI")
    parser.add_argument("--model", type=str, default="deepseek-ai/deepseek-coder-1.3b-instruct",
                        help="Model name or path")
    parser.add_argument("--cpu", action="store_true", help="Force CPU usage")
    parser.add_argument("--share", action="store_true", help="Create a public share link")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the interface on")
    parser.add_argument("--autoload", action="store_true", help="Automatically load the model on startup")
    parser.add_argument("--device", type=str, default="auto", help="Device to use (auto, cpu, cuda, mps, directml)")
    parser.add_argument("--precision", type=str, default="auto", help="Model precision (auto, float32, float16, bfloat16)")
    
    args = parser.parse_args()
    
    # Set device priority if specified and hardware_utils is available
    if hardware_utils_available and args.device != "auto":
        os.environ["DEEPSEEK_DEVICE_PRIORITY"] = args.device
    
    # Determine use_gpu based on arguments
    use_gpu = not args.cpu and args.device != "cpu"
    
    # Create the interface
    iface = create_gui(args.model, use_gpu)
    
    # If autoload is enabled, load the model on startup
    if args.autoload:
        # The model will be loaded when the interface is launched
        print(f"Auto-loading model: {args.model}")
        threading.Thread(target=initialize_model, args=(args.model, use_gpu, args.precision)).start()
    
    # Launch the interface
    iface.launch(
        share=args.share,
        server_port=args.port,
        inbrowser=True,
        server_name="0.0.0.0" if args.share else "127.0.0.1"
    )