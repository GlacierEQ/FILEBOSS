#!/usr/bin/env python
"""
Apply Fractal Theme to Sorting Hat

This script sets up the fractal theme for the Sorting Hat system.
It generates the necessary assets and updates configuration files.
"""
import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

def print_header(text):
    """Print a styled header"""
    print("\n" + "=" * 70)
    print(f"{text.center(70)}")
    print("=" * 70 + "\n")

def print_step(text):
    """Print a step in the process"""
    print(f"➤ {text}")

def print_success(text):
    """Print a success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print an error message"""
    print(f"❌ {text}")

def ensure_dir(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print_step(f"Created directory: {directory}")

def copy_file(src, dst):
    """Copy a file with directory creation"""
    ensure_dir(os.path.dirname(dst))
    shutil.copy2(src, dst)
    print_step(f"Copied {os.path.basename(src)} to {dst}")

def main():
    """Main function to apply fractal theme"""
    print_header("SORTING HAT FRACTAL THEME SETUP")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "static")
    templates_dir = os.path.join(base_dir, "templates")
    
    # Ensure directories exist
    ensure_dir(static_dir)
    ensure_dir(os.path.join(static_dir, "css"))
    ensure_dir(os.path.join(static_dir, "js"))
    ensure_dir(os.path.join(static_dir, "images"))
    ensure_dir(templates_dir)
    
    print_step("Setting up fractal theme...")
    
    # Generate fractal images
    try:
        fractal_generator = os.path.join(base_dir, "fractal_generator.py")
        if os.path.exists(fractal_generator):
            print_step("Generating fractal images...")
            subprocess.run([sys.executable, fractal_generator, "--all"], check=True)
            print_success("Fractal images generated successfully")
        else:
            print_error(f"Fractal generator script not found: {fractal_generator}")
            print_step("Creating placeholder images instead")
            # Create placeholder images if needed
    except Exception as e:
        print_error(f"Error generating fractal images: {e}")
    
    # Apply the theme to the dashboard
    dashboard_template = os.path.join(templates_dir, "fractal_dashboard.html")
    dashboard_file = os.path.join(base_dir, "dashboard.html")
    if os.path.exists(dashboard_template):
        try:
            print_step("Applying dashboard template...")
            shutil.copy2(dashboard_template, dashboard_file)
            print_success(f"Applied fractal dashboard theme to {dashboard_file}")
        except Exception as e:
            print_error(f"Error applying dashboard template: {e}")
    else:
        print_error(f"Dashboard template not found: {dashboard_template}")
    
    # Update the main index file if it exists
    index_file = os.path.join(base_dir, "index.html")
    if os.path.exists(index_file):
        try:
            print_step("Updating index.html to use fractal theme...")
            
            # Read the current file
            with open(index_file, 'r') as f:
                content = f.read()
            
            # Add CSS link if not present
            if '<link href="/static/css/fractal-theme.css"' not in content:
                content = content.replace('</head>', 
                                         '<link href="/static/css/fractal-theme.css" rel="stylesheet">\n</head>')
            
            # Add JS script if not present
            if '<script src="/static/js/fractal-effects.js"' not in content:
                content = content.replace('</body>', 
                                         '<script src="/static/js/fractal-effects.js"></script>\n</body>')
            
            # Write back the updated content
            with open(index_file, 'w') as f:
                f.write(content)
                
            print_success("Updated index.html with fractal theme references")
        except Exception as e:
            print_error(f"Error updating index.html: {e}")
    
    # Create a configuration link for the theme
    config_dir = os.path.join(base_dir, "config")
    theme_config = os.path.join(config_dir, "theme.json")
    ensure_dir(config_dir)
    
    try:
        config = {
            "theme": "fractal",
            "colors": {
                "primary-dark": "#0f3443",
                "primary-light": "#34e89e",
                "accent-blue": "#00c3ff",
                "accent-green": "#11998e"
            },
            "fonts": {
                "primary": "Nunito, 'Segoe UI', Roboto, sans-serif"
            }
        }
        
        with open(theme_config, 'w') as f:
            json.dump(config, f, indent=2)
            
        print_success(f"Created theme configuration: {theme_config}")
    except Exception as e:
        print_error(f"Error creating theme configuration: {e}")
    
    print_header("THEME SETUP COMPLETE")
    print("The fractal theme has been applied to the Sorting Hat interface.")
    print("\nTo experience the new theme:")
    print("1. Open dashboard.html in your web browser")
    print("2. Restart any running services or the web server")
    print("3. Launch the application to see the updated interface\n")

if __name__ == "__main__":
    main()