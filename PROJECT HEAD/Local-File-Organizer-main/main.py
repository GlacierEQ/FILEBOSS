import os
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from file_utils import (
    display_directory_tree,
    collect_file_paths,
    separate_files_by_type,
    read_file_data,
    is_legal_document
)

from data_processing_common import (
    compute_operations,
    execute_operations,
    process_files_by_date,
    process_files_by_type,
)

from text_data_processing import process_text_files
from image_data_processing import process_image_files
from output_filter import filter_specific_output

# Import legal document processing
from legal_processor import (
    process_legal_document,
    LegalDocument,
    MotionTemplate
)

# Import models if available
try:
    from nexa.gguf import NexaVLMInference, NexaTextInference
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    print("Note: Nexa models not available. Some features may be limited.")

def ensure_nltk_data():
    """Ensure that NLTK data is downloaded efficiently and quietly."""
    import nltk
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('wordnet', quiet=True)

# Initialize models
image_inference = None
text_inference = None

def initialize_models():
    """Initialize the models if they haven't been initialized yet."""
    global image_inference, text_inference
    if image_inference is None or text_inference is None:
        # Initialize the models
        model_path = "llava-v1.6-vicuna-7b:q4_0"
        model_path_text = "Llama3.2-3B-Instruct:q3_K_M"

        # Use the filter_specific_output context manager
        with filter_specific_output():
            # Initialize the image inference model
            image_inference = NexaVLMInference(
                model_path=model_path,
                local_path=None,
                stop_words=[],
                temperature=0.3,
                max_new_tokens=3000,
                top_k=3,
                top_p=0.2,
                profiling=False
                # add n_ctx if out of context window usage: n_ctx=2048
            )

            # Initialize the text inference model
            text_inference = NexaTextInference(
                model_path=model_path_text,
                local_path=None,
                stop_words=[],
                temperature=0.5,
                max_new_tokens=3000,  # Adjust as needed
                top_k=3,
                top_p=0.3,
                profiling=False
                # add n_ctx if out of context window usage: n_ctx=2048

            )
        print("**----------------------------------------------**")
        print("**       Image inference model initialized      **")
        print("**       Text inference model initialized       **")
        print("**----------------------------------------------**")

def simulate_directory_tree(operations, base_path):
    """Simulate the directory tree based on the proposed operations."""
    tree = {}
    for op in operations:
        rel_path = os.path.relpath(op['destination'], base_path)
        parts = rel_path.split(os.sep)
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
    return tree

def print_simulated_tree(tree, prefix=''):
    """Print the simulated directory tree."""
    pointers = ['├── '] * (len(tree) - 1) + ['└── '] if tree else []
    for pointer, key in zip(pointers, tree):
        print(prefix + pointer + key)
        if tree[key]:  # If there are subdirectories or files
            extension = '│   ' if pointer == '├── ' else '    '
            print_simulated_tree(tree[key], prefix + extension)

def get_yes_no(prompt):
    """Prompt the user for a yes/no response."""
    while True:
        response = input(prompt).strip().lower()
        if response in ('yes', 'y'):
            return True
        elif response in ('no', 'n'):
            return False
        elif response == '/exit':
            print("Exiting program.")
            exit()
        else:
            print("Please enter 'yes' or 'no'. To exit, type '/exit'.")

def get_mode_selection():
    """Prompt the user to select a mode."""
    print("\nSelect processing mode:")
    print("1. Automatic organization by type and date")
    print("2. Manual organization with preview")
    print("3. Process text files only")
    print("4. Process image files only")
    print("5. Process legal documents")
    print("6. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-6): ").strip()
        if choice in ['1', '2', '3', '4', '5', '6']:
            return choice
        print("Invalid choice. Please enter a number between 1 and 6.")

def process_legal_documents(files: List[str], output_dir: str, dry_run: bool = False) -> Dict[str, Any]:
    """Process legal documents and organize them appropriately.
    
    Args:
        files: List of file paths to process
        output_dir: Base output directory
        dry_run: If True, only simulate the operations
        
    Returns:
        Dictionary with processing results
    """
    results = {
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'documents': []
    }
    
    # Create output directories if they don't exist
    legal_dir = os.path.join(output_dir, "Legal")
    os.makedirs(legal_dir, exist_ok=True)
    
    for file_path in files:
        try:
            # Check if file is a legal document
            if not is_legal_document(file_path):
                results['skipped'] += 1
                continue
                
            # Process the legal document
            doc = process_legal_document(file_path)
            results['documents'].append(doc.to_dict())
            
            # Determine output path based on document type
            doc_type_dir = os.path.join(legal_dir, doc.doc_type)
            os.makedirs(doc_type_dir, exist_ok=True)
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{doc.doc_type}_{timestamp}{os.path.splitext(file_path)[1]}"
            output_path = os.path.join(doc_type_dir, filename)
            
            if not dry_run:
                # Copy the file to the new location
                import shutil
                shutil.copy2(file_path, output_path)
                
            results['processed'] += 1
            
            print(f"Processed: {os.path.basename(file_path)} -> {output_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            results['errors'] += 1
    
    return results

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='FILEBOSS - File Organization System')
    
    # Main arguments
    parser.add_argument('path', nargs='?', help='Directory path to organize')
    parser.add_argument('-o', '--output', help='Output directory (default: <path>/organized)')
    parser.add_argument('--mode', type=int, choices=range(1, 7), 
                       help='Processing mode (1-6)')
    
    # Legal document options
    legal_group = parser.add_argument_group('Legal Document Options')
    legal_group.add_argument('--legal-only', action='store_true',
                           help='Process only legal documents')
    legal_group.add_argument('--generate-motion', action='store_true',
                           help='Generate a motion from template')
    legal_group.add_argument('--motion-type', 
                           choices=['vacate', 'summary_judgment', 'dismiss'],
                           help='Type of motion to generate')
    
    # General options
    parser.add_argument('--dry-run', action='store_true',
                       help='Simulate operations without making changes')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Auto-confirm all prompts')
    
    return parser.parse_args()

def main():
    ensure_nltk_data()
    
    # Parse command line arguments
    args = parse_arguments()
    
    print("\n" + "="*50)
    print("FILEBOSS - File Organization System")
    print("="*50)
    
    # Get the directory to organize
    while True:
        path = args.path
        if not path:
            path = input("\nEnter the directory path to organize (or 'q' to quit): ").strip()
            if path.lower() == 'q':
                print("Exiting...")
                operations = process_files_by_type(file_paths, output_path, dry_run=False, silent=silent_mode, log_file=log_file)
            else:
                print("Invalid mode selected.")
                return

            # Simulate and display the proposed directory tree
            print("-" * 50)
            message = "Proposed directory structure:"
            if silent_mode:
                with open(log_file, 'a') as f:
                    f.write(message + '\n')
            else:
                print(message)
                print(os.path.abspath(output_path))
                simulated_tree = simulate_directory_tree(operations, output_path)
                print_simulated_tree(simulated_tree)
                print("-" * 50)

            # Ask user if they want to proceed
            proceed = get_yes_no("Would you like to proceed with these changes? (yes/no): ")
            if proceed:
                # Create the output directory now
                os.makedirs(output_path, exist_ok=True)

                # Perform the actual file operations
                message = "Performing file operations..."
                if silent_mode:
                    with open(log_file, 'a') as f:
                        f.write(message + '\n')
                else:
                    print(message)
                execute_operations(
                    operations,
                    dry_run=False,
                    silent=silent_mode,
                    log_file=log_file
                )

                message = "The files have been organized successfully."
                if silent_mode:
                    with open(log_file, 'a') as f:
                        f.write("-" * 50 + '\n' + message + '\n' + "-" * 50 + '\n')
                else:
                    print("-" * 50)
                    print(message)
                    print("-" * 50)
                break  # Exit the sorting method loop after successful operation
            else:
                # Ask if the user wants to try another sorting method
                another_sort = get_yes_no("Would you like to choose another sorting method? (yes/no): ")
                if another_sort:
                    continue  # Loop back to mode selection
                else:
                    print("Operation canceled by the user.")
                    break  # Exit the sorting method loop

        # Ask if the user wants to organize another directory
        another_directory = get_yes_no("Would you like to organize another directory? (yes/no): ")
        if not another_directory:
            break  # Exit the main loop


if __name__ == '__main__':
    main()
