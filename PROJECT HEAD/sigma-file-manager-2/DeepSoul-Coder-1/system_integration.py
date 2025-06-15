#!/usr/bin/env python3
"""
System-wide integration for DeepSeek-Coder
Provides:
- Global hotkeys
- System tray icon
- Clipboard monitoring
- Natural language commands
"""
import os
import sys
import threading
import time
import json
import re
import tempfile
import argparse
from pathlib import Path
import torch
import pyperclip

# Check OS and import appropriate modules
if os.name == 'nt':  # Windows
    import pystray
    from PIL import Image, ImageDraw
    import keyboard
    IS_WINDOWS = True
    try:
        from win10toast import ToastNotifier
        TOAST_AVAILABLE = True
    except ImportError:
        TOAST_AVAILABLE = False
else:  # Linux/Mac
    IS_WINDOWS = False
    try:
        import pystray
        from PIL import Image, ImageDraw
        TRAY_AVAILABLE = True
    except ImportError:
        TRAY_AVAILABLE = False
    
    try:
        import gi
        gi.require_version('Notify', '0.7')
        from gi.repository import Notify
        NOTIFY_AVAILABLE = True
        Notify.init("DeepSeek-Coder")
    except (ImportError, ValueError):
        NOTIFY_AVAILABLE = False

# Import transformers conditionally (can be slow)
transformers_loaded = False
tokenizer = None
model = None
device = "cpu"

# Command patterns
COMMAND_PATTERNS = {
    "explain": r"explain|understand|describe|tell me about",
    "fix": r"fix|correct|resolve|debug|solve",
    "generate": r"generate|create|write|implement",
    "translate": r"translate|convert|change language",
    "refactor": r"refactor|improve|optimize|clean",
    "document": r"document|add comments|explain code",
}

def load_transformers():
    """Load transformers lazily when needed."""
    global transformers_loaded, tokenizer, model, device
    
    if transformers_loaded:
        return True
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        # Use a smaller model by default for system integration
        model_name = "deepseek-ai/deepseek-coder-1.3b-instruct"
        
        # Check for GPU
        use_gpu = torch.cuda.is_available()
        torch_dtype = torch.bfloat16 if use_gpu and torch.cuda.is_bf16_supported() else torch.float32
        
        # Load the model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True
        )
        
        # Move to GPU if available
        if use_gpu:
            device = "cuda"
            model = model.to(device)
        
        transformers_loaded = True
        return True
    except Exception as e:
        show_notification(f"Error loading model: {str(e)}", "DeepSeek-Coder Error")
        return False

def create_tray_icon():
    """Create a system tray icon."""
    if not (IS_WINDOWS or TRAY_AVAILABLE):
        print("System tray not supported on this platform")
        return None
    
    # Create an icon image
    icon_size = 64
    image = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    # Draw a simple code icon
    dc.rectangle((10, 10, icon_size-10, icon_size-10), fill=(52, 152, 219))
    dc.text((20, 20), "</> AI", fill=(255, 255, 255))
    
    # Create menu
    def on_open_gui(icon, item):
        import subprocess
        subprocess.Popen([sys.executable, "gui_deepseek.py"])
    
    def on_quit(icon, item):
        icon.stop()
        os._exit(0)
    
    menu = pystray.Menu(
        pystray.MenuItem("Open DeepSeek GUI", on_open_gui),
        pystray.MenuItem("Exit", on_quit)
    )
    
    # Create tray icon
    icon = pystray.Icon("DeepSeek-Coder", image, "DeepSeek-Coder", menu)
    
    # Run the icon in a separate thread
    threading.Thread(target=icon.run, daemon=True).start()
    
    return icon

def show_notification(message, title="DeepSeek-Coder"):
    """Show a system notification."""
    if IS_WINDOWS and TOAST_AVAILABLE:
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=5, threaded=True)
    elif not IS_WINDOWS and NOTIFY_AVAILABLE:
        notification = Notify.Notification.new(title, message, "dialog-information")
        notification.show()
    else:
        print(f"{title}: {message}")

def setup_hotkeys(callback):
    """Set up global hotkeys."""
    if IS_WINDOWS:
        # Ctrl+Alt+D for DeepSeek
        keyboard.add_hotkey('ctrl+alt+d', callback)
        return True
    else:
        print("Hotkeys not supported on this platform")
        return False

def detect_command_type(text):
    """Detect the type of natural language command."""
    text_lower = text.lower()
    
    for cmd_type, pattern in COMMAND_PATTERNS.items():
        if re.search(pattern, text_lower):
            return cmd_type
    
    return "general"  # Default command type

def process_clipboard(text=None):
    """Process text from clipboard or provided text."""
    if not load_transformers():
        show_notification("Failed to load the AI model", "DeepSeek-Coder Error")
        return
    
    # Get text from clipboard if not provided
    if text is None:
        try:
            text = pyperclip.paste()
        except:
            show_notification("Failed to access clipboard", "DeepSeek-Coder Error")
            return
    
    if not text or len(text.strip()) < 5:
        show_notification("Clipboard is empty or too short", "DeepSeek-Coder Warning")
        return
    
    # Detect command type
    cmd_type = detect_command_type(text)
    
    # Set up prompt based on command type
    system_prompt = "You are an AI programming assistant. Respond concisely and helpfully."
    
    if cmd_type == "explain":
        prefix = "Explain this code concisely: "
    elif cmd_type == "fix":
        prefix = "Fix issues in this code and explain what was wrong: "
    elif cmd_type == "generate":
        prefix = "Generate code based on this request: "
    elif cmd_type == "translate":
        prefix = "Translate this code to the requested language: "
    elif cmd_type == "refactor":
        prefix = "Refactor this code to improve it: "
    elif cmd_type == "document":
        prefix = "Add documentation to this code: "
    else:
        prefix = "Help with this: "
    
    # Prepare the conversation
    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prefix + text}
    ]
    
    try:
        # Format input for the model with explicit attention mask
        tokenized = tokenizer.apply_chat_template(
            conversation, 
            add_generation_prompt=True,
            return_tensors="pt"
        )
        
        # Create input_ids and attention_mask tensors
        input_ids = tokenized.to(device)
        attention_mask = torch.ones_like(input_ids).to(device)
        
        # Generate response with explicit attention mask
        outputs = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            max_new_tokens=1024,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Get the response
        response = tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
        
        # Save response to temporary file and open it
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write(f"Command type: {cmd_type.upper()}\n\n")
            f.write(f"Input:\n{text[:200]}{'...' if len(text) > 200 else ''}\n\n")
            f.write(f"Response:\n{response}")
            temp_file = f.name
        
        # Show notification and open the file
        show_notification(f"AI response ready for your {cmd_type} command!", "DeepSeek-Coder")
        
        # Open the file with the default application
        if IS_WINDOWS:
            os.startfile(temp_file)
        else:
            import subprocess
            subprocess.call(('xdg-open', temp_file))
            
    except Exception as e:
        show_notification(f"Error generating response: {str(e)}", "DeepSeek-Coder Error")

def clipboard_hotkey_callback():
    """Callback for clipboard hotkey."""
    threading.Thread(target=process_clipboard).start()
    show_notification("Processing clipboard content...", "DeepSeek-Coder")

def main():
    parser = argparse.ArgumentParser(description="DeepSeek-Coder System Integration")
    parser.add_argument("--no-tray", action="store_true", help="Don't show system tray icon")
    parser.add_argument("--no-hotkeys", action="store_true", help="Don't register global hotkeys")
    
    args = parser.parse_args()
    
    print("Starting DeepSeek-Coder System Integration")
    print("Press Ctrl+Alt+D to process clipboard with DeepSeek-Coder")
    
    # Create system tray icon if requested
    tray_icon = None
    if not args.no_tray:
        tray_icon = create_tray_icon()
    
    # Set up hotkeys if requested
    if not args.no_hotkeys and IS_WINDOWS:
        if setup_hotkeys(clipboard_hotkey_callback):
            print("Hotkeys registered successfully")
        else:
            print("Failed to register hotkeys")
    
    # Show startup notification
    show_notification(
        "DeepSeek-Coder is running in the background.\n"
        "Press Ctrl+Alt+D to analyze clipboard content.", 
        "DeepSeek-Coder Active"
    )
    
    # If no tray icon, just wait forever (or until Ctrl+C)
    if tray_icon is None:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting...")
            return

if __name__ == "__main__":
    main()
