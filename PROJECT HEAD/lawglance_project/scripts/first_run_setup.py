"""
First Run Setup for LawGlance
This script helps users configure LawGlance when first running the executable.
It sets up API keys, creates a .env file, and validates the configuration.
"""
import os
import sys
import platform
from pathlib import Path

# Determine application directory
if getattr(sys, 'frozen', False):  # Running as compiled executable
    APP_DIR = Path(os.path.dirname(sys.executable))
else:  # Running in development mode
    APP_DIR = Path(__file__).parent.parent

ENV_FILE = APP_DIR / ".env"

def print_header():
    """Print a welcome header."""
    print("\n" + "=" * 60)
    print("            LawGlance - First Run Setup")
    print("=" * 60)
    print("\nWelcome to LawGlance! Let's set up your configuration.\n")


def setup_api_keys():
    """Set up API keys for LawGlance."""
    print("LawGlance requires an OpenAI API key to function.")
    print("You can get one from: https://platform.openai.com/api-keys\n")
    
    api_key = input("Please enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("\nWarning: No API key provided. LawGlance will not function properly without a valid API key.")
        return False
    
    # Save to .env file
    with open(ENV_FILE, "w") as f:
        f.write(f"OPENAI_API_KEY={api_key}\n")
        f.write("# Uncomment and modify these optional settings as needed\n")
        f.write("# MODEL_NAME=gpt-4o-mini\n")
        f.write("# MODEL_TEMPERATURE=0.9\n")
    
    print(f"\nAPI key saved to {ENV_FILE}")
    return True


def setup_optional_settings():
    """Set up optional settings."""
    print("\nWould you like to configure optional settings? (y/n)")
    choice = input("> ").strip().lower()
    
    if choice != 'y':
        return
    
    # Read current .env file
    with open(ENV_FILE, "r") as f:
        env_contents = f.readlines()
    
    # Modify based on user input
    print("\nSelect model (default: gpt-4o-mini):")
    print("1. gpt-4o-mini (recommended)")
    print("2. gpt-3.5-turbo")
    print("3. gpt-4o")
    model_choice = input("> ").strip()
    
    model_name = "gpt-4o-mini"  # default
    if model_choice == "2":
        model_name = "gpt-3.5-turbo"
    elif model_choice == "3":
        model_name = "gpt-4o"
    
    # Update model name in env contents
    for i, line in enumerate(env_contents):
        if line.startswith("# MODEL_NAME="):
            env_contents[i] = f"MODEL_NAME={model_name}\n"
    
    # Write back to .env
    with open(ENV_FILE, "w") as f:
        f.writelines(env_contents)
    
    print(f"\nSettings updated. Using model: {model_name}")


def validate_setup():
    """Validate the setup configuration."""
    if not ENV_FILE.exists():
        print("\nError: Configuration file not found.")
        return False
    
    print("\nValidating configuration...")
    
    try:
        with open(ENV_FILE, "r") as f:
            env_contents = f.read()
            
        if "OPENAI_API_KEY=" not in env_contents or "OPENAI_API_KEY=your_openai_api_key_here" in env_contents:
            print("\nWarning: OpenAI API key not properly configured.")
            return False
            
        print("Configuration validated successfully!")
        return True
        
    except Exception as e:
        print(f"\nError validating configuration: {str(e)}")
        return False


def main():
    """Main setup function."""
    print_header()
    
    # Skip if .env already exists and looks valid
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            content = f.read()
            if "OPENAI_API_KEY=" in content and "your_openai_api_key_here" not in content:
                print("Existing configuration found. Skipping setup.")
                validate_setup()
                print("\nPress Enter to continue...")
                input()
                return
    
    # Perform setup
    if setup_api_keys():
        setup_optional_settings()
        validate_setup()
    
    print("\nSetup complete! You can now start using LawGlance.")
    print("\nPress Enter to start LawGlance...")
    input()


if __name__ == "__main__":
    main()
