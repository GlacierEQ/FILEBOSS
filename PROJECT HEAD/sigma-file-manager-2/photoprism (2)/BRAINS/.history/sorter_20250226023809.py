import os
import shutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FastSorter(FileSystemEventHandler):
    def __init__(self, target_directory):
        self.target_directory = target_directory

    def on_created(self, event):
        print(f"Detected new file: {event.src_path}")  # Debugging output
        if not event.is_directory:
            self.sort_file(event.src_path)

    def sort_file(self, file_path):
        # Fast sorting logic
        print(f"Fast sorting file: {file_path}")
        
        # Check if the file is part of a program folder
        if self.is_program_folder(file_path):
            self.keep_program_together(file_path)
        else:
            # Example: Move file to a specific directory based on its type
            file_extension = os.path.splitext(file_path)[1]
            destination_folder = os.path.join(self.target_directory, file_extension[1:])  # Remove the dot from extension
            os.makedirs(destination_folder, exist_ok=True)  # Create the folder if it doesn't exist
            shutil.move(file_path, os.path.join(destination_folder, os.path.basename(file_path)))  # Move the file

    def is_program_folder(self, file_path):
        # Logic to determine if the file is part of a program folder
        parent_folder = os.path.basename(os.path.dirname(file_path))
        known_programs = ["Foxit", "Adobe", "Microsoft"]  # Add more known program names as needed
        return any(program in parent_folder for program in known_programs)

    def keep_program_together(self, file_path):
        # Logic to keep the entire program folder together
        program_folder = os.path.dirname(file_path)
        destination_folder = os.path.join(self.target_directory, "Programs")
        os.makedirs(destination_folder, exist_ok=True)  # Create the folder if it doesn't exist
        shutil.move(program_folder, os.path.join(destination_folder, os.path.basename(program_folder)))  # Move the entire folder

class DeepUnderstanding:
    def __init__(self, target_directory):
        self.target_directory = target_directory

    def analyze_files(self):
        # Logic to analyze files for deeper understanding
        print("Analyzing files for deeper understanding...")
        for root, dirs, files in os.walk(self.target_directory):
            for file in files:
                file_path = os.path.join(root, file)
                self.process_file(file_path)

    def process_file(self, file_path):
        # Implement logic to process and analyze the file
        print(f"Processing file for deeper understanding: {file_path}")
        # Example: Read file content, analyze, and categorize

if __name__ == "__main__":
    target_directory = "C:/Users/casey/OrganizeFolder"  # Update to safe directory
    observer = Observer()
    fast_sorter = FastSorter(target_directory)
    observer.schedule(fast_sorter, path=target_directory, recursive=True)
    observer.start()
    
    # Create an instance of DeepUnderstanding and analyze files
    deep_understanding = DeepUnderstanding(target_directory)
    deep_understanding.analyze_files()
    
    try:
        while True:
            pass  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
