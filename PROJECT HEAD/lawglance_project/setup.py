"""Setup script for the LawGlance project."""
import os
import subprocess
import sys

def setup_environment():
    """Set up the project environment."""
    print("Setting up LawGlance environment...")
    
    # Create necessary directories
    directories = [
        'data',
        'logo',
        'chroma_db_legal_bot_part1'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        try:
            with open('.env.example', 'r', encoding='utf-8') as example_file:
                with open('.env', 'w', encoding='utf-8') as env_file:
                    env_file.write(example_file.read())
            print("✓ Created .env file from template")
        except FileNotFoundError:
            print("❌ .env.example file not found")
    else:
        print("✓ .env file already exists")
    
    # Create placeholder logo if not exists
    if not os.path.exists('logo/logo.png'):
        try:
            from logo.create_placeholder_logo import create_placeholder_logo
            create_placeholder_logo()
            print("✓ Created placeholder logo")
        except ImportError:
            print("❌ Could not create logo - PIL package may be missing")
    else:
        print("✓ Logo file already exists")
    
    # Install dependencies
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Installed dependencies")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
    
    print("\nSetup complete! Next steps:")
    print("1. Add your OpenAI API key to the .env file")
    print("2. Run the Streamlit app with: streamlit run app.py")
    print("3. Or run the FastAPI server with: cd src && uvicorn main:app --reload")
    print("4. Build the desktop application with: python build_desktop_app.py")

if __name__ == "__main__":
    setup_environment()
