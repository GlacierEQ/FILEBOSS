#!/usr/bin/env python3
"""
MemoryPlugin MCP Server Setup for Claude Desktop
This script generates proper configuration for Claude Desktop to use MemoryPlugin.
"""
import os
import sys
import json
import argparse
from pathlib import Path
import subprocess
from nodejs_utils import get_nodejs_path, get_nodejs_info

def print_header():
    """Print the script header"""
    print("\n========================================================")
    print("   MemoryPlugin MCP Server Setup for Claude Desktop")
    print("========================================================\n")

def find_npm_package_path(package_name):
    """Find the installation path of an npm package"""
    nodejs_info = get_nodejs_info()
    if nodejs_info.get("status") != "found":
        print("ERROR: Node.js not found. Please install Node.js first.")
        return None
        
    nodejs_path = nodejs_info["path"]
    npm_path = nodejs_info.get("npm_path")
    
    if not npm_path:
        # Try to find npm relative to node path
        node_dir = os.path.dirname(nodejs_path)
        possible_npm_paths = [
            os.path.join(node_dir, "npm"),
            os.path.join(node_dir, "npm.cmd"),
            os.path.join(node_dir, "npm.exe")
        ]
        
        for path in possible_npm_paths:
            if os.path.exists(path):
                npm_path = path
                break
    
    if not npm_path:
        print("WARNING: npm not found. Cannot determine package installation path.")
        return None
    
    # Execute npm list command to find the package path
    try:
        cmd = [npm_path, "list", "-g", package_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse the output to find the package path
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if package_name in line:
                    # Extract the path from npm list output
                    node_modules_dir = lines[0].strip()
                    if node_modules_dir.startswith("/"):
                        # This is likely the absolute path to node_modules
                        return os.path.join(node_modules_dir, package_name, "dist/index.js")
                    elif "node_modules" in node_modules_dir:
                        # Try to extract the path up to node_modules
                        base_path = node_modules_dir.split("node_modules")[0] + "node_modules"
                        return os.path.join(base_path, package_name, "dist/index.js")
        
        # Backup approach: try to find in standard locations
        node_dir = os.path.dirname(nodejs_path)
        lib_dir = os.path.join(os.path.dirname(node_dir), "lib", "node_modules")
        if os.path.exists(os.path.join(lib_dir, package_name)):
            return os.path.join(lib_dir, package_name, "dist/index.js")
            
        print(f"WARNING: Could not determine installation path for {package_name}.")
        print("Output from npm list:")
        print(result.stdout)
        
    except Exception as e:
        print(f"ERROR: Failed to find package path: {str(e)}")
    
    return None

def install_memory_plugin():
    """Install the MemoryPlugin MCP Server package globally"""
    print("Installing @memoryplugin/mcp-server globally...")
    
    nodejs_info = get_nodejs_info()
    if nodejs_info.get("status") != "found":
        print("ERROR: Node.js not found. Please install Node.js first.")
        return False
        
    npm_path = nodejs_info.get("npm_path")
    if not npm_path:
        print("ERROR: npm not found. Cannot install package.")
        return False
    
    try:
        cmd = [npm_path, "install", "-g", "@memoryplugin/mcp-server"]
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("MemoryPlugin MCP Server installed successfully!")
            return True
        else:
            print("ERROR: Failed to install MemoryPlugin MCP Server.")
            return False
            
    except Exception as e:
        print(f"ERROR: Installation failed: {str(e)}")
        return False

def generate_claude_config(api_token, output_path=None, use_npx=False):
    """
    Generate Claude Desktop configuration file for MemoryPlugin
    
    Args:
        api_token: MemoryPlugin API token
        output_path: Path to save the configuration file (or None to print)
        use_npx: Use npx instead of direct node path (recommended but may have issues)
    """
    if use_npx:
        # Use npx configuration (recommended but may have issues)
        config = {
            "mcpServers": {
                "memoryplugin": {
                    "command": "npx",
                    "args": ["-y", "@memoryplugin/mcp-server"],
                    "env": {
                        "MEMORY_PLUGIN_TOKEN": api_token
                    }
                }
            }
        }
    else:
        # Use direct node path configuration
        nodejs_path = get_nodejs_path()
        if not nodejs_path:
            print("ERROR: Node.js not found. Please install Node.js first.")
            return False
        
        # Find the package installation path
        package_path = find_npm_package_path("@memoryplugin/mcp-server")
        if not package_path:
            print("WARNING: Could not find @memoryplugin/mcp-server installation path.")
            print("Attempting to install it...")
            install_success = install_memory_plugin()
            if install_success:
                package_path = find_npm_package_path("@memoryplugin/mcp-server")
            
            if not package_path:
                print("ERROR: Could not determine package path even after installation.")
                print("Please install the package manually with: npm install -g @memoryplugin/mcp-server")
                return False
        
        # Create configuration with direct node path
        config = {
            "mcpServers": {
                "memoryplugin": {
                    "command": nodejs_path,
                    "args": [package_path],
                    "env": {
                        "MEMORY_PLUGIN_TOKEN": api_token
                    }
                }
            }
        }
    
    # Output the configuration
    config_json = json.dumps(config, indent=2)
    
    if output_path:
        try:
            # Make sure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Write the configuration to the file
            with open(output_path, 'w') as f:
                f.write(config_json)
            print(f"Configuration written to: {output_path}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to write configuration: {str(e)}")
            return False
    else:
        print("\nClaude Desktop Configuration:")
        print("-----------------------------")
        print(config_json)
        return True

def find_default_claude_config_path():
    """Find the default Claude Desktop configuration path based on OS"""
    home = Path.home()
    
    if sys.platform == 'win32':  # Windows
        return home / "AppData" / "Roaming" / "Claude" / "config.json"
    elif sys.platform == 'darwin':  # macOS
        return home / "Library" / "Application Support" / "Claude" / "config.json"
    else:  # Linux and others
        return home / ".config" / "Claude" / "config.json"

def update_existing_config(api_token, config_path, use_npx=False):
    """Update existing Claude configuration file with MemoryPlugin settings"""
    if not os.path.exists(config_path):
        print(f"Config file doesn't exist at {config_path}")
        return generate_claude_config(api_token, config_path, use_npx)
    
    try:
        # Load existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Generate the MemoryPlugin configuration
        if use_npx:
            memory_config = {
                "command": "npx",
                "args": ["-y", "@memoryplugin/mcp-server"],
                "env": {
                    "MEMORY_PLUGIN_TOKEN": api_token
                }
            }
        else:
            nodejs_path = get_nodejs_path()
            package_path = find_npm_package_path("@memoryplugin/mcp-server")
            
            if not nodejs_path or not package_path:
                return generate_claude_config(api_token, config_path, use_npx)
            
            memory_config = {
                "command": nodejs_path,
                "args": [package_path],
                "env": {
                    "MEMORY_PLUGIN_TOKEN": api_token
                }
            }
        
        # Add or update the MemoryPlugin MCP server config
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        config["mcpServers"]["memoryplugin"] = memory_config
        
        # Write the updated config back
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Successfully updated Claude configuration at: {config_path}")
        return True
    
    except Exception as e:
        print(f"ERROR: Failed to update configuration: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="MemoryPlugin MCP Server Setup for Claude Desktop")
    parser.add_argument("--token", help="MemoryPlugin API token")
    parser.add_argument("--config", help="Path to Claude Desktop config file")
    parser.add_argument("--npx", action="store_true", help="Use npx configuration (recommended but may have issues)")
    parser.add_argument("--print-only", action="store_true", help="Print configuration without writing to file")
    
    args = parser.parse_args()
    
    print_header()
    
    # Get API token
    api_token = args.token
    if not api_token:
        print("Please enter your MemoryPlugin API token")
        print("(You can find this at www.memoryplugin.com/dashboard)")
        api_token = input("API Token: ").strip()
    
    if not api_token:
        print("ERROR: API token is required.")
        return 1
    
    # Determine config path
    if args.print_only:
        config_path = None
    else:
        config_path = args.config
        if not config_path:
            config_path = find_default_claude_config_path()
            print(f"Using default Claude config path: {config_path}")
    
    # Generate or update configuration
    if config_path and os.path.exists(config_path):
        success = update_existing_config(api_token, config_path, args.npx)
    else:
        success = generate_claude_config(api_token, config_path, args.npx)
    
    if success:
        print("\nMemoryPlugin MCP Server setup completed successfully!")
        print("\nAvailable tools in Claude:")
        print("- store_memory: Store new memories in your account")
        print("- get_memories: Query your memories with filters")
        print("- list_buckets: View all your memory buckets")
        print("- create_bucket: Create new memory buckets")
        print("- get_memories_and_buckets: Combined query for efficiency")
    else:
        print("\nSetup encountered some issues. Please check the error messages above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
