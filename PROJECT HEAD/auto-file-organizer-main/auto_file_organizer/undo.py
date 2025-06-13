import json
import os
import shutil


def undo_last_operation(base_dir):
    history_path = os.path.join(base_dir, "organize_history.json")

    if not os.path.exists(history_path):
        print("No history found to undo.")
        return

    try:
        with open(history_path, "r") as f:
            history = json.load(f)

        # Move files back first
        for entry in history:
            if "original_path" in entry and "new_path" in entry:
                original = entry["original_path"]
                moved = entry["new_path"]

                if os.path.exists(moved):
                    os.makedirs(os.path.dirname(original), exist_ok=True)
                    shutil.move(moved, original)
                    # print(f"Moved back: {moved} → {original}")
                else:
                    print(f"File not found: {moved}")

        # Now delete folders we created (only if empty)
        created_folders = [
            entry["created_folder"] for entry in history if "created_folder" in entry
        ]

        # Sort deeper folders first
        for folder in sorted(created_folders, key=lambda f: -f.count(os.sep)):
            if os.path.exists(folder) and not os.listdir(folder):
                try:
                    os.rmdir(folder)
                    # print(f"Deleted empty folder: {folder}")
                except Exception as e:
                    print(f"Failed to delete folder {folder}: {e}")

        os.remove(history_path)
        print("Undo completed successfully.")

    except Exception as e:
        print(f"Undo failed: {e}")
