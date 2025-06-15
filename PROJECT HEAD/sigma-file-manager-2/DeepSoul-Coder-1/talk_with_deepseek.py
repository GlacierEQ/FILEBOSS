#!/usr/bin/env python3
"""
Interactive chat with DeepSeek-Coder model
"""
import os
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from pathlib import Path

# Import hardware detection utilities
try:
    from hardware_utils import HardwareManager
    hardware_manager = HardwareManager()
    hardware_utils_available = True
except ImportError:
    hardware_utils_available = False

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(model_name):
    """Print a nice header for the chat interface."""
    print("=" * 80)
    print(f"  DeepSeek-Coder Chat - {model_name}")
    print("=" * 80)
    print("Type 'exit', 'quit', or 'q' to end the conversation.")
    print("Type 'clear' to clear the conversation history.")
    print("Type 'save filename.txt' to save the conversation.")
    print("=" * 80)

def initialize_model(model_name, use_gpu=True, precision="auto", trust_remote=True):
    """Initialize model and tokenizer."""
    print(f"Initializing DeepSeek-Coder model: {model_name}")
    print("This may take a while depending on your internet connection and hardware...")
    
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
            device = hardware_manager.get_torch_device()
            device_name = device.type.upper()
            if device_name == "CUDA" and torch.cuda.is_available():
                device_name = f"GPU: {torch.cuda.get_device_name(0)}"
        else:
            device = torch.device("cpu")
            device_name = "CPU"

        print(f"Using device: {device_name}")
        print(f"Using precision: {torch_dtype}")
    else:
        # Fallback to standard PyTorch device detection
        # Convert precision to torch dtype
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
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("Using CPU for inference. This will be slower.")
    
    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=trust_remote
    )
    
    # Initialize model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=trust_remote,
        torch_dtype=torch_dtype
    )
    
    # Move to selected device
    if hardware_utils_available:
        model = model.to(device)
    else:
        if device == "cuda":
            model = model.cuda()
    
    return model, tokenizer, device

def chat_with_model(model, tokenizer, device, use_instruct_model=True, max_tokens=1024):
    """Run an interactive chat with the model."""
    clear_screen()
    print_header(model.config._name_or_path)
    
    # Import token utilities if available
    try:
        from token_utils import TokenProcessor, CustomLogitsProcessor
        token_processor = TokenProcessor(tokenizer)
        logits_processor = CustomLogitsProcessor(tokenizer)
        print("Advanced token processing enabled.")
    except ImportError:
        token_processor = None
        logits_processor = None
        
    conversation = []
    conversation_text = []
    
    while True:
        # Get user input
        user_input = input("\n\033[92mYou: \033[0m")
        
        # Handle special commands
        if user_input.lower() in ["exit", "quit", "q"]:
            print("\nGoodbye!")
            break
        elif user_input.lower() == "clear":
            conversation = []
            conversation_text = []
            clear_screen()
            print_header(model.config._name_or_path)
            continue
        elif user_input.lower().startswith("save "):
            filename = user_input[5:].strip()
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(conversation_text))
            print(f"\nConversation saved to {filename}")
            continue
        
        # Add user message to conversation
        conversation.append({"role": "user", "content": user_input})
        conversation_text.append(f"User: {user_input}")
        
        # Format input for the model
        if use_instruct_model:
            # For instruct models, we use the chat template
            tokenized = tokenizer.apply_chat_template(
                conversation, 
                add_generation_prompt=True,
                return_tensors="pt"
            )
            
            # Get input_ids tensor and create attention mask
            input_ids = tokenized.to(device)
            attention_mask = torch.ones_like(input_ids).to(device)
        else:
            # For base models, we need to format the prompt manually
            prompt = ""
            for msg in conversation:
                if msg["role"] == "user":
                    prompt += f"User: {msg['content']}\n"
                else:
                    prompt += f"Assistant: {msg['content']}\n"
            prompt += "Assistant: "
            
            # Tokenize with explicit attention mask
            tokenized = tokenizer(prompt, return_tensors="pt")
            input_ids = tokenized.input_ids.to(device)
            attention_mask = tokenized.attention_mask.to(device)
        
        # Generate response
        print("\n\033[93mDeepSeek-Coder: \033[0m", end="", flush=True)
        
        # Set appropriate token for stopping
        if use_instruct_model:
            eos_token_id = tokenizer.eos_token_id
        else:
            eos_token_id = None
        
        # Generate with advanced token processing if available
        if token_processor:
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                max_new_tokens=max_tokens,
                eos_token_id=eos_token_id,
                pad_token_id=tokenizer.eos_token_id,
                logits_processor=[
                    # Here you can add custom logit processors
                    # For example: MyCustomLogitsProcessor()
                ]
            )
        else:
            # Use the basic generation
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                max_new_tokens=max_tokens,
                eos_token_id=eos_token_id,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Get the generated text
        if use_instruct_model:
            response_text = tokenizer.decode(outputs[0][len(input_ids[0]):], skip_special_tokens=True)
        else:
            response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # For base models, we need to extract the assistant's response
            response_text = response_text.split("Assistant: ")[-1].strip()
        
        print(response_text)
        
        # Add assistant response to conversation
        conversation.append({"role": "assistant", "content": response_text})
        conversation_text.append(f"DeepSeek-Coder: {response_text}")

def main():
    parser = argparse.ArgumentParser(description="Chat with DeepSeek-Coder")
    parser.add_argument("--model", type=str, default="deepseek-ai/deepseek-coder-1.3b-instruct",
                        help="Model name or path (default: deepseek-ai/deepseek-coder-1.3b-instruct)")
    parser.add_argument("--cpu", action="store_true", help="Force CPU usage even if GPU is available")
    parser.add_argument("--precision", type=str, default="auto", 
                      choices=["auto", "float32", "float16", "bfloat16"],
                      help="Model precision (default: auto - automatically selects best precision)")
    parser.add_argument("--base", action="store_true", help="Use base (non-instruct) model")
    parser.add_argument("--max-tokens", type=int, default=1024, help="Maximum tokens for response (default: 1024)")
    parser.add_argument("--device", type=str, default="auto", 
                       choices=["auto", "cpu", "cuda", "mps", "directml"],
                       help="Device to use for inference (default: auto)")
    parser.add_argument("--tensor-processing", action="store_true", 
                      help="Enable advanced tensor processing for tokens")
    parser.add_argument("--logit-bias", type=str, default=None,
                      help="JSON string with token IDs and their bias values")
    
    args = parser.parse_args()
    
    # Override use_gpu based on device argument
    use_gpu = True
    if args.cpu or args.device == "cpu":
        use_gpu = False
    
    # If using hardware_utils and a specific device is selected
    if hardware_utils_available and args.device != "auto" and args.device != "cpu":
        os.environ["DEEPSEEK_DEVICE_PRIORITY"] = args.device
    
    # Default to the lighter instruct model if user wants CPU
    if not use_gpu and args.model == "deepseek-ai/deepseek-coder-6.7b-instruct":
        if input("Using 6.7B model on CPU might be slow. Would you like to switch to 1.3B model? (y/n): ").lower() == 'y':
            args.model = "deepseek-ai/deepseek-coder-1.3b-instruct"
    
    # Initialize model and tokenizer
    model, tokenizer, device = initialize_model(
        args.model, 
        use_gpu=use_gpu,
        precision=args.precision
    )
    
    # Enable tensor processing if requested
    if args.tensor_processing:
        try:
            from token_utils import TokenProcessor
            print("Advanced token tensor processing enabled")
        except ImportError:
            print("Warning: token_utils module not found. Run without advanced token processing.")
    
    # Parse logit bias if provided
    if args.logit_bias:
        try:
            import json
            logit_bias = json.loads(args.logit_bias)
            print(f"Using logit bias: {logit_bias}")
        except Exception as e:
            print(f"Error parsing logit bias: {e}")
    
    # Check if this is an instruct model from the name
    use_instruct = not args.base and "instruct" in args.model
    
    # Start the chat
    chat_with_model(model, tokenizer, device, use_instruct_model=use_instruct, max_tokens=args.max_tokens)

if __name__ == "__main__":
    main()
