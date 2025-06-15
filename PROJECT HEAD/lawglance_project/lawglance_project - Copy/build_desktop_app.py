# Build script for creating the LawGlance desktop application
import PyInstaller.__main__

def create_installer():
    """Create an installer using Inno Setup."""
    # Logic to create installer goes here
    print("Creating installer...")

def build_executable():
    """Build the executable using PyInstaller."""
    try:
        PyInstaller.__main__.run([
            'build_desktop_app.py',
            '--onefile',
            '--name=LawGlance',
            '--distpath=dist/LawGlance',
            '--workpath=build',
            '--specpath=build',
            '--icon=C:\\Users\\casey\\Desktop\\lawglance_project\\logo\\logo.ico',  # Updated with actual icon path
        ])
        print("Executable built successfully.")
    except Exception as e:
        print(f"Error during executable build: {e}")







    """Build the executable using PyInstaller."""
    try:

    """Build the executable using PyInstaller."""
    try:

    """Build the executable using PyInstaller."""
    try:

    """Build the executable using PyInstaller."""
    try:

    """Build the executable using PyInstaller."""
    try:

    """Build the executable using PyInstaller."""
    PyInstaller.__main__.run([
        'build_desktop_app.py',
        '--onefile',
        '--name=LawGlance',
        '--distpath=dist/LawGlance',
        '--workpath=build',
        '--specpath=build',
        '--icon=C:\\Users\\casey\\Desktop\\lawglance_project\\logo\\logo.ico',  # Updated with actual icon path



    ])
        print("Executable built successfully.")
    except Exception as e:
        print(f"Error during executable build: {e}")

    except Exception as e:
        print(f"Error during executable build: {e}")

    except Exception as e:
        print(f"Error during executable build: {e}")

    except Exception as e:
        print(f"Error during executable build: {e}")

    except Exception as e:
        print(f"Error during executable build: {e}")


def main():
    print("Welcome to the LawGlance Desktop Application Builder!")
    print("Please select build options:")
    print("1. Build Executable")
    print("2. Create Installer")
    print("3. Generate Portable Version")
    
    choice = input("Enter your choice (1/2/3): ")
    
    if choice == '1':
        build_executable()
    elif choice == '2':
        create_installer()
    elif choice == '3':
        print("Generating portable version...")
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
