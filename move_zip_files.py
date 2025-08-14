import os
import shutil
from pathlib import Path

def move_zip_files():
    """Move all ZIP files from C drive to E:\cold-storage"""
    
    # Create destination directory
    dest_dir = Path("E:/cold-storage")
    dest_dir.mkdir(exist_ok=True)
    
    moved_count = 0
    errors = []
    
    print("Searching for ZIP files on C drive...")
    
    # Search C drive for ZIP files
    c_drive = Path("C:/")
    
    for zip_file in c_drive.rglob("*.zip"):
        try:
            # Skip system directories and protected areas
            if any(part.startswith(('.', '$', 'Windows', 'Program Files')) for part in zip_file.parts):
                continue
                
            # Create relative path structure in destination
            relative_path = zip_file.relative_to(c_drive)
            dest_path = dest_dir / relative_path
            
            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(zip_file), str(dest_path))
            print(f"Moved: {zip_file} -> {dest_path}")
            moved_count += 1
            
        except (PermissionError, OSError) as e:
            errors.append(f"Error moving {zip_file}: {e}")
            continue
    
    print(f"\nCompleted! Moved {moved_count} ZIP files.")
    if errors:
        print(f"Encountered {len(errors)} errors:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  {error}")

if __name__ == "__main__":
    move_zip_files()