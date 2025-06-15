import os


def is_safe_path(target_path: str) -> bool:
    # Define the base path for your GitHub repositories
    github_base_path = os.path.realpath(
        "C:/Users/casey/OneDrive/Documents/GitHub/")

    # Check if the target path is within the GitHub base path
    return not target_path.startswith(github_base_path)


def sort_files_in_sorting_hat():
    sorting_hat_path = "C:/Users/casey/SortingHat"
    # Implement your sorting logic here
    # Example: Check if the target path is safe
    if not is_safe_path(sorting_hat_path):
        print("Skipping action because it’s in the GitHub repo.")
        return
    else:
        # Proceed with sorting or renaming files in the Sorting Hat directory
        pass
