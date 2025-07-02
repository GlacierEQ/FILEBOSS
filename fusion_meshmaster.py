"""Scan multiple Python repositories and build a fusion manifest."""

import argparse
import ast
import json
import os


class RepoNode:
    def __init__(self, path: str):
        self.path = path
        self.modules = []
        self.functions = []
        self.classes = []
        self.docstrings = []

    def analyze(self) -> None:
        """Walk through the repository and parse Python files."""
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    with open(
                        full_path,
                        "r",
                        encoding="utf-8",
                        errors="ignore",
                    ) as f:
                        try:
                            node = ast.parse(f.read(), filename=file)
                            self.extract_definitions(node)
                        except Exception:
                            continue

    def extract_definitions(self, node: ast.AST) -> None:
        """Extract class and function definitions along with docstrings."""
        for n in ast.walk(node):
            if isinstance(n, ast.FunctionDef):
                self.functions.append(n.name)
                doc = ast.get_docstring(n)
                if doc:
                    self.docstrings.append(doc)
            elif isinstance(n, ast.ClassDef):
                self.classes.append(n.name)
                doc = ast.get_docstring(n)
                if doc:
                    self.docstrings.append(doc)

    def to_dict(self) -> dict:
        """Represent the repository node as a serializable dictionary."""
        return {
            "path": self.path,
            "functions": self.functions,
            "classes": self.classes,
            "docstrings": [d for d in self.docstrings if d],
        }


def fuse_repos(base_directory: str) -> list[dict]:
    """Analyze all repositories under the base directory."""
    fusion_manifest = []
    for repo_name in os.listdir(base_directory):
        repo_path = os.path.join(base_directory, repo_name)
        if os.path.isdir(repo_path):
            node = RepoNode(repo_path)
            node.analyze()
            fusion_manifest.append(node.to_dict())
    return fusion_manifest


def save_manifest(
    manifest: list[dict],
    output_path: str = "fusion_manifest.json",
) -> None:
    """Save the manifest to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def main() -> None:
    """CLI entry point for generating a fusion manifest."""
    parser = argparse.ArgumentParser(description="Generate a fusion manifest")
    parser.add_argument("base_dir", help="Path containing repositories to scan")
    parser.add_argument(
        "--output",
        default="fusion_manifest.json",
        help="Output JSON file for the manifest",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.base_dir):
        parser.error(f"{args.base_dir} is not a valid directory")

    manifest = fuse_repos(args.base_dir)
    save_manifest(manifest, args.output)
    print(f"Fusion manifest generated at {args.output}")


if __name__ == "__main__":
    main()
