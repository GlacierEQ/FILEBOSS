"""
Dependency Resolver for LawGlance

This script fixes conflicting package dependencies by installing
compatible versions and creating a clean environment.
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Define project root
PROJECT_ROOT = Path(__file__).parent.parent

# Define dependency groups with compatible versions
COMPATIBLE_DEPS = {
    "langchain_group": [
        "langchain==0.1.13",
        "langchain-core==0.1.16",
        "langchain-text-splitters==0.1.0",  # Downgrade to compatible version
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
    
    for group_name, packages in COMPATIBLE_DEPS.items():
        print(f"\nInstalling {group_name} packages:")
        for package in packages:
            print(f"Installing {package}...")
            run_command([sys.executable, "-m", "pip", "install", package])

def update_requirements_file():
    """Update requirements.txt with compatible versions."""
    print_header("Updating requirements.txt")
    
    req_file = PROJECT_ROOT / "requirements.txt"
    
    # Read existing requirements if file exists
    existing_reqs = []
    if req_file.exists():
        with open(req_file, "r") as f:
            existing_reqs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    # Get packages to remove from requirements
    to_remove = []
    for line in existing_reqs:
        for pkg in DEPENDENCIES_TO_CLEAN:
            if line.lower().startswith(f"{pkg.lower()}"):
                to_remove.append(line)
                break
    
    # Remove conflicting packages
    for line in to_remove:
        if line in existing_reqs:
            existing_reqs.remove(line)
    
    # Add compatible versions
    compatible_versions = []
    for group in COMPATIBLE_DEPS.values():
        compatible_versions.extend(group)
    
    # Create updated requirements file with a special section
    with open(req_file, "w") as f:
        f.write("# LawGlance Requirements\n\n")
        
        # Write existing requirements
        if existing_reqs:
            f.write("# Existing Requirements\n")
            for req in existing_reqs:
                f.write(f"{req}\n")
            f.write("\n")
        
        # Write fixed dependencies
        f.write("# Fixed Compatible Dependencies\n")
        for pkg in sorted(compatible_versions):
            f.write(f"{pkg}\n")
    
    print(f"✓ Updated requirements file at {req_file}")

def main():
    """Main function to fix dependencies."""
    print_header("LawGlance Dependency Resolution Tool")
    
    print("This tool will fix package dependency conflicts by:")
    print("1. Uninstalling conflicting packages")
    print("2. Installing compatible versions")
    print("3. Updating requirements.txt with fixed versions\n")
    
    confirm = input("Do you want to continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Operation cancelled.")
        return
    
    # List currently installed packages
    print("\nChecking current package versions...")
    installed_packages = list_installed_packages()
    
    # Show conflicts
    print("\nCurrent conflicts:")
    print("- faster-whisper 1.0.0 requires tokenizers<0.16,>=0.13, found: " + 
          installed_packages.get('tokenizers', 'Not installed'))
    print("- langchain-text-splitters 0.3.6 requires langchain-core<1.0.0,>=0.3.34, found: " + 
          installed_packages.get('langchain-core', 'Not installed'))
    print("- litellm 1.61.16 requires tiktoken>=0.7.0, found: " + 
          installed_packages.get('tiktoken', 'Not installed'))
    print("- llama-cloud-services 0.6.2 requires python-dotenv<2.0.0,>=1.0.1, found: " + 
          installed_packages.get('python-dotenv', 'Not installed'))
    
    # Fix the dependencies
    uninstall_conflicting_packages()
    install_compatible_packages()
    update_requirements_file()
    
    print_header("Dependencies Fixed Successfully!")
    print("\nYour environment now has compatible package versions.")
    print("The requirements.txt file has been updated with these versions.")
    print("\nYou can now build the LawGlance executable without dependency conflicts.")

if __name__ == "__main__":
    main()
