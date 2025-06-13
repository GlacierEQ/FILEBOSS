import os
import argparse
from auto_file_organizer.autoorganizer import organize_files
from auto_file_organizer.model import Config
from auto_file_organizer.undo import undo_last_operation

# ----------------------- CLI INTERFACE ---------------------------


def cli():
    base_dir = os.getcwd()

    parser = argparse.ArgumentParser(
        prog="organize",
        description="🗂️ Auto File Organizer: Organizes files in the current directory by type, date, or pattern.\n"
                    "By default, it organizes the current working directory.\n"
                    "Use --undo to revert the last operation.",
        epilog="Example usage:\n  organize           # to start organizing\n  organize --undo    # to undo the last sort",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Undo the last file organization operation in the current directory"
    )

    args = parser.parse_args()

    if args.undo:
        undo_last_operation(base_dir)
    else:
        print("Choose sorting strategy:")
        print("1. Type")
        print("2. Date")
        print("3. Pattern")
        sort_input = input("Enter number: ").strip()
        sort_by_map = {"1": "type", "2": "date", "3": "pattern"}
        sort_by = sort_by_map.get(sort_input, "type")

        ex_input = input("Enter exceptions (comma-separated): ").strip()
        exceptions = [e.strip() for e in ex_input.split(",") if e.strip()]

        config = Config(sort_by=sort_by, depth=1, exceptions=exceptions)
        organize_files(base_dir, config)


if __name__ == "__main__":
    cli()
