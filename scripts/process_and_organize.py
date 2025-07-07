#!/usr/bin/env python3
"""Process and organize files using FileBossIntegrator.

This script processes a directory of files and organizes them into an output
folder according to the chosen scheme. It is intended for quick automation in
CI pipelines or local workflows.
"""

import argparse
import asyncio

from casebuilder.services.fileboss_integration import FileBossIntegrator


async def main() -> None:
    parser = argparse.ArgumentParser(description="Process and organize evidence files")
    parser.add_argument("directory", help="Directory containing files to process")
    parser.add_argument("case_id", help="Case ID to associate with the files")
    parser.add_argument(
        "--output-dir",
        default="organized",
        help="Directory to store organized files",
    )
    parser.add_argument(
        "--scheme",
        default="type_date",
        choices=["type_date", "type", "date", "flat"],
        help="Organization scheme",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process directories recursively",
    )

    args = parser.parse_args()

    integrator = FileBossIntegrator()
    processed = await integrator.process_directory(
        directory=args.directory,
        case_id=args.case_id,
        recursive=args.recursive,
    )
    results = await integrator.organize_files(
        files=processed,
        output_dir=args.output_dir,
        organization_scheme=args.scheme,
    )

    for item in results:
        print(f"{item['original_path']} -> {item['new_path']}")

    print(f"Processed {len(processed)} files. Organized output in {args.output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
