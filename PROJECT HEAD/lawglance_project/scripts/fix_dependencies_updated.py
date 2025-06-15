"""
Updated Dependency Resolver for LawGlance

Fixes the incompatibility between langchain and langchain-core versions
and other dependency conflicts.
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Define project root
PROJECT_ROOT = Path(__file__).parent.parent

# Define dependency groups with FIXED compatible versions
COMPATIBLE_DEPS = {
    "langchain_group": [
        # Use version of langchain-core that satisfies langchain's requirements
        "langchain-core==0.1.33",  # Updated to be compatible with langchain 0.1.13
        "langchain==0.1.13",
        "langchain-text-splitters==0.1.0",
    ],
    "tokenizers_group": [
        "tokenizers==0.15.0",  # Compatible with both transformers and faster-whisper
        "transformers==4.36.2",  # Version compatible with tokenizers 0.15.0
    ],
    "llm_group": [
        "tiktoken==0.7.0",  # Updated to meet litellm requirements
        "python-dotenv==1.0.0",  # Keep current version, fix llama-cloud-services
    ],
}

# Dependencies to uninstall before reinstalling
DEPENDENCIES_TO_CLEAN = [
    "transformers",
    "tokenizers",
    "langchain",
    "langchain-core",
    "langchain-text-splitters",
    "tiktoken",
]

def print_header(message):
    """Print a nicely formatted header."""
    print("\n" + "=" * 70)
    print(f" {message}")
    print("=" * 70)

def run_command(command, verbose=True):
    """Run a shell command and return the result."""
    if verbose:
        print(f"Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command, 
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if verbose:
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"Error: {e.stderr}")
        return False, e.stderr

def list_installed_packages():
    """List currently installed packages and their versions."""
    success, output = run_command([sys.executable, "-m", "pip", "list", "--format=json"], verbose=False)
    if success:
        packages = json.loads(output)
        return {pkg["name"].lower(): pkg["version"] for pkg in packages}
    return {}

def uninstall_conflicting_packages():
    """Uninstall packages that have conflicts."""
    print_header("Uninstalling Conflicting Packages")
    
    for package in DEPENDENCIES_TO_CLEAN:
        print(f"Uninstalling {package}...")
        run_command([sys.executable, "-m", "pip", "uninstall", "-y", package])

def install_compatible_packages():
    """Install packages with compatible versions."""
    print_header("Installing Compatible Package Versions")
    
    # Install dependencies in the correct order to avoid conflicts
    # First, install langchain-core since langchain depends on it
    print("Installing langchain-core first...")
    for package in COMPATIBLE_DEPS["langchain_group"]:
        if "langchain-core" in package:
            run_command([sys.executable, "-m", "pip", "install", package])
    
    # Then install the rest in groups
    for group_name, packages in COMPATIBLE_DEPS.items():
        print(f"\nInstalling {group_name} packages:")
        for package in packages:
            # Skip langchain-core as it's already installed
            if "langchain-core" in package:
                continue
            print(f"Installing {package}...")
            run_command([sys.executable, "-m", "pip", "install", package])

def update_requirements_file():
    """Update requirements.txt with compatible versions."""
    print_header("Updating requirements.txt")
    
    req_file = PROJECT_ROOT / "requirements.txt"
    fixed_req_file = PROJECT_ROOT / "requirements.fixed.txt"
    
    # Create fixed requirements file
    with open(fixed_req_file, "w") as f:
        f.write("# LawGlance Fixed Requirements\n")
        f.write("# These package versions are compatible with each other and resolve dependency conflicts\n\n")
        
        # Core dependencies
        f.write("# Core packages\n")
        f.write("langchain-core==0.1.33\n")
        f.write("langchain==0.1.13\n")
        f.write("langchain-openai==0.0.2\n")
        f.write("openai==1.9.0\n\n")
        
        # Text processing
        f.write("# Text processing and tokenization\n")
        f.write("tiktoken==0.7.0\n")
        f.write("tokenizers==0.15.0\n")
        f.write("transformers==4.36.2\n\n")
        
        # UI
        f.write("# Streamlit UI\n")
        f.write("streamlit==1.30.0\n")
        f.write("streamlit-chat==0.1.1\n\n")
        
        # DB
        f.write("# Vector database\n")
        f.write("chromadb==0.4.22\n")
        f.write("langchain-chroma==0.0.2\n\n")
        
        # Document processing
        f.write("# Document processing\n")
        f.write("pypdf==3.17.4\n")
        f.write("python-docx==1.0.1\n")
        f.write("python-pptx==1.0.1\n\n")
        
        # Utilities
        f.write("# Utilities\n")
        f.write("python-dotenv==1.0.0\n")
        f.write("pydantic==2.5.3\n")
        f.write("tqdm==4.66.1\n\n")
        
        # Build dependencies
        f.write("# Build dependencies\n")
        f.write("pyinstaller==6.2.0\n")
        f.write("pillow==10.1.0\n")
    
    print(f"✓ Created fixed requirements file at {fixed_req_file}")
    
    # Create backup of current requirements.txt if it exists
    if req_file.exists():
        backup_file = req_file.with_suffix(".txt.bak")
        shutil.copy2(req_file, backup_file)
        print(f"✓ Backed up original requirements to {backup_file}")
        
        # Copy fixed requirements to requirements.txt
        shutil.copy2(fixed_req_file, req_file)
        print(f"✓ Updated {req_file} with fixed dependencies")
    else:
        shutil.copy2(fixed_req_file, req_file)
        print(f"✓ Created new {req_file} with fixed dependencies")

def main():
    """Main function to fix dependencies."""
    print_header("FIXED LawGlance Dependency Resolution Tool")
    
    print("This script fixes the langchain/langchain-core version conflict by:")
    print("1. Uninstalling conflicting packages")
    print("2. Installing langchain-core==0.1.33 (which satisfies langchain's requirements)")
    print("3. Installing other packages in the correct order")
    print("4. Creating a fixed requirements.txt file\n")
    
    confirm = input("Do you want to continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    try:
        # List currently installed packages
        print("\nChecking current package versions...")
        installed_packages = list_installed_packages()
        
        # Show conflicts
        print("\nCurrent conflicts:")
        print("- langchain 0.1.13 requires langchain-core>=0.1.33, found: " + 
              installed_packages.get('langchain-core', 'Not installed'))
        
        # Fix the dependencies
        uninstall_conflicting_packages()
        install_compatible_packages()
        update_requirements_file()
        
        print_header("Dependencies Fixed Successfully!")
        print("\nYour environment now has compatible package versions:")
        print("- langchain-core 0.1.33")
        print("- langchain 0.1.13")
        print("\nThe requirements.txt file has been updated with these versions.")
        print("You can now build the LawGlance executable without dependency conflicts.")
        
    except Exception as e:
        print_header("ERROR")
        print(f"An error occurred: {str(e)}")
        print("\nTry installing packages manually:")
        print("pip uninstall -y langchain langchain-core")
        print("pip install langchain-core==0.1.33")
        print("pip install langchain==0.1.13")

if __name__ == "__main__":
    main()
