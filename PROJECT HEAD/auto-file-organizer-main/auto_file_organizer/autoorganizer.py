import os
import shutil
from datetime import datetime
from auto_file_organizer.file_ignore import is_file_to_be_ignored
from auto_file_organizer.model import Config
from auto_file_organizer.type_map import TYPE_RULES
import json


def find_category(file_extension, type_map=TYPE_RULES):
    for category, details in type_map.items():
        extensions = details.get("extensions", [])
        if file_extension in extensions:
            return category

        subfolders = details.get("subfolders", {})
        if subfolders:
            sub_category = find_category(file_extension, subfolders)
            if sub_category and sub_category != "Other":  # Only return if it's a valid match
                return os.path.join(category, sub_category)

    return "Other"  # Default fallback, only after all checks fail


def get_file_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return find_category(ext)


def get_file_date(file_path):
    try:
        mtime = os.path.getmtime(file_path)
        date = datetime.fromtimestamp(mtime)
        return date.strftime("%Y-%m")  # Year-Month format
    except Exception:
        return "Unknown"


def get_pattern_folder(file_name):
    name = file_name.lower()
    if "invoice" in name:
        return "Invoices"
    elif "resume" in name:
        return "Resumes"
    elif "report" in name:
        return "Reports"
    else:
        return "Misc"


def save_history(history, base_dir):
    history_path = os.path.join(base_dir, "organize_history.json")
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

# ----------------------- ORGANIZATION LOGIC ---------------------------


def organize_files(base_dir, config: Config):
    history = []
    print('Organizing files...')
    try:
        for root, dirs, files in os.walk(base_dir):
            if config.depth == 1 and root != base_dir:
                continue

            if is_file_to_be_ignored(root, config.exceptions):
                continue

            for file in files:

                file_path = os.path.join(root, file)

                if is_file_to_be_ignored(file_path, config.exceptions):
                    continue

                if not os.path.isfile(file_path):
                    continue

                if config.sort_by == "type":
                    folder_name = get_file_type(file_path)
                elif config.sort_by == "date":
                    folder_name = get_file_date(file_path)
                elif config.sort_by == "pattern":
                    folder_name = get_pattern_folder(file)
                else:
                    folder_name = "Unsorted"
                target_dir = os.path.join(base_dir, folder_name)
                os.makedirs(target_dir, exist_ok=True)
                history.append({"created_folder": target_dir})

                new_path = os.path.join(target_dir, file)
                if file_path != new_path:
                    if os.path.exists(new_path):
                        print(
                            f"Skipped: '{file}' already exists in '{target_dir}'")
                    else:
                        shutil.move(file_path, new_path)
                        history.append({
                            "original_path": file_path,
                            "new_path": new_path
                        })

        save_history(history, base_dir)
        print("Files organized successfully.")

    except Exception as e:
        print(f"Error during file organization: {e}")
