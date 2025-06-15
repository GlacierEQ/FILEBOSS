"""
Node.js utilities for DeepSoul - Provides functions to interact with Node.js
"""
import os
import json
import subprocess
from pathlib import Path
import logging
import sys

logger = logging.getLogger("DeepSoul-NodeJS")

def get_nodejs_path():
    """
    Get the Node.js executable path from environment info or by detection
    
    Returns:
        str: Path to the Node.js executable or None if not found
    """
    # First, check if we have saved environment info
    env_file = Path("deepsoul_config/environment_info.json")
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                env_info = json.load(f)
                if "nodejs_path" in env_info and env_info["nodejs_path"]:
                    # Verify the path still exists and works
                    nodejs_path = env_info["nodejs_path"]
                    if os.path.exists(nodejs_path):
                        # Test if node works
                        try:
                            result = subprocess.run([nodejs_path, '--version'], 
                                                   capture_output=True, text=True)
                            if result.returncode == 0:
                                return nodejs_path
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Error reading environment info: {str(e)}")
    
    # If we get here, we need to detect Node.js
    return detect_nodejs()

def detect_nodejs():
    """
    Detect Node.js installation and return the executable path
    
    Returns:
        str: Path to the Node.js executable or None if not found
    """
    nodejs_path = None
    
    # Check if node is in PATH
    try:
        if os.name == 'nt':  # Windows
            # Use where command on Windows
            result = subprocess.run(['where', 'node'], capture_output=True, text=True)
            if result.returncode == 0:
                nodejs_path = result.stdout.strip().split('\n')[0]
        else:  # macOS/Linux
            # Try which command first
            result = subprocess.run(['which', 'node'], capture_output=True, text=True)
            if result.returncode == 0:
                nodejs_path = result.stdout.strip()
            else:
                # Check common NVM locations
                home = os.path.expanduser("~")
                nvm_paths = [
                    os.path.join(home, ".nvm/versions/node"),
                    os.path.join(home, ".nodenv/versions")
                ]
                
                for nvm_path in nvm_paths:
                    if os.path.exists(nvm_path):
                        # Find the highest version
                        versions = sorted([d for d in os.listdir(nvm_path) if d.startswith('v')], 
                                        key=lambda x: [int(n) for n in x[1:].split('.')])
                        if versions:
                            latest = os.path.join(nvm_path, versions[-1], 'bin', 'node')
                            if os.path.exists(latest):
                                nodejs_path = latest
                                break
        
        # Test if node works
        if nodejs_path:
            version_cmd = [nodejs_path, '--version']
            result = subprocess.run(version_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                nodejs_path = None
    
    except Exception as e:
        logger.error(f"Error detecting Node.js: {str(e)}")
    
    return nodejs_path

def execute_javascript(code, args=None):
    """
    Execute JavaScript code using Node.js
    
    Args:
        code (str): JavaScript code to execute
        args (list): Optional command line arguments to pass to the script
        
    Returns:
        tuple: (return_code, stdout, stderr)
    """
    nodejs_path = get_nodejs_path()
    if not nodejs_path:
        return 1, "", "Node.js not found. Cannot execute JavaScript code."
    
    # Create a temporary file
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Build command
        cmd = [nodejs_path, temp_file]
        if args:
            cmd.extend(args)
        
        # Execute command
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file)
        except Exception:
            pass

def get_nodejs_info():
    """
    Get detailed information about the Node.js installation
    
    Returns:
        dict: Node.js information
    """
    nodejs_path = get_nodejs_path()
    if not nodejs_path:
        return {"status": "not_found"}
    
    info = {
        "status": "found",
        "path": nodejs_path
    }
    
    # Get version
    try:
        result = subprocess.run([nodejs_path, '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            info["version"] = result.stdout.strip()
    except Exception:
        pass
    
    # Get NPM version if available
    npm_path = None
    if os.path.exists(os.path.join(os.path.dirname(nodejs_path), "npm")):
        npm_path = os.path.join(os.path.dirname(nodejs_path), "npm")
    elif os.path.exists(os.path.join(os.path.dirname(nodejs_path), "npm.cmd")):
        npm_path = os.path.join(os.path.dirname(nodejs_path), "npm.cmd")
    
    if npm_path:
        try:
            result = subprocess.run([npm_path, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                info["npm_version"] = result.stdout.strip()
                info["npm_path"] = npm_path
        except Exception:
            pass
    
    return info

if __name__ == "__main__":
    # Basic test when run directly
    nodejs_path = get_nodejs_path()
    if nodejs_path:
        print(f"Found Node.js: {nodejs_path}")
        
        # Execute simple test script
        code = """
        console.log("Node.js version:", process.version);
        console.log("Arguments:", process.argv.slice(2));
        console.log("Current directory:", process.cwd());
        """
        
        returncode, stdout, stderr = execute_javascript(code, ["test", "arg1"])
        print("\nTest script output:")
        print(stdout)
        if stderr:
            print("Error output:", stderr)
    else:
        print("Node.js not found")
